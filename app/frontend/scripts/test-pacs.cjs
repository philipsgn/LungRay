const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const zlib = require("node:zlib");
const ts = require("typescript");
require.extensions[".ts"] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
}).outputText, filename);
const { cardiothoracicRatio, installPopoverDismissal } = require("../app/lib/pacsUtils.ts");
const edge = require("../app/lib/edgeFallback.ts");
const api = require("../app/lib/api.ts");

test("CTR supports reverse drags and zero-width protection", () => {
  assert.equal(cardiothoracicRatio(-40, -80), 0.5);
  assert.ok(Number.isFinite(cardiothoracicRatio(40, 0)));
});
test("Offline prediction never fabricates a filename-dependent diagnosis", async () => {
  for (const name of ["normal.png", "tb.png", "effusion.png", "anything.dcm"]) {
    const result = await edge.edgePredictImage({ name }, "standard", false, true);
    assert.equal(result.inference_source, "unavailable");
    assert.equal(result.safety.is_safe, false);
    assert.equal(result.report.is_blocked, true);
    assert.deepEqual(result.head_a_prediction, {});
    assert.equal(result.passes_executed, 0);
  }
});
test("Offline heatmap and contour are valid transparent RGBA PNGs", async () => {
  const result = await edge.edgeExplainImage({}, "head_a", 0, "Atelectasis");
  assert.equal(result.heatmap_has_activation, false);
  assert.equal(result.audit_pass, null);
  for (const key of ["heatmap_rgba_base64", "contour_rgba_base64"]) {
    const data = Buffer.from(result[key], "base64");
    assert.equal(data.subarray(1,4).toString(), "PNG");
    assert.equal(data[25], 6); // PNG color type RGBA.
    const size = data.readUInt32BE(33);
    const scanline = zlib.inflateSync(data.subarray(41, 41 + size));
    assert.equal(scanline[4], 0); // alpha.
  }
});
test("Offline RAG preserves OOD lockout", async () => {
  const result = await edge.edgeQueryClinicalRag({ question: "TB?", active_findings: ["Tuberculosis"], is_safe: false });
  assert.equal(result.status, "BLOCKED_OOD");
  assert.deepEqual(result.retrieved_cards, []);
});
test("Network failure, timeout and HTTP 503 fall back; 422 remains an error", async () => {
  const original = global.fetch;
  try {
    for (const failure of [() => { throw new TypeError("offline"); }, () => { throw new DOMException("timeout", "AbortError"); }, () => new Response("unavailable", { status: 503 })]) {
      global.fetch = failure;
      assert.equal((await api.predictImage({}, "standard")).inference_source, "unavailable");
      assert.equal((await api.explainImage({}, "head_a", 0)).audit_pass, null);
      assert.equal((await api.queryClinicalRag({ is_safe: false })).status, "BLOCKED_OOD");
    }
    global.fetch = () => new Response("invalid image", { status: 422 });
    await assert.rejects(api.predictImage({}, "standard"), /422/);
  } finally { global.fetch = original; }
});

const history = require("../app/lib/scanHistoryDb.ts");
// Async IDB double records close timing, commits atomically and discards aborted writes.
// This is a unit model; it is not a real-browser E2E substitute.
function fakeDb(options = {}) {
  const state = { rows: new Map(), closes: 0, earlyCloses: 0 };
  state.open = () => {
    if (options.throwOpen) throw Error("private mode");
    const request = {};
    const db = {
      objectStoreNames: { contains: () => true },
      close() { state.closes++; if (this.active) state.earlyCloses++; },
      transaction() {
        const draft = new Map(state.rows), tx = {};
        let pending = 0, ended = false; db.active = true;
        const end = abort => {
          if (ended) return; ended = true; db.active = false;
          if (!abort) state.rows = draft;
          if (abort) tx.onerror?.();
          (abort ? tx.onabort : tx.oncomplete)?.();
        };
        const schedule = operation => {
          const req = {}; pending++;
          setImmediate(() => {
            if (ended) return;
            if (options.abortNext) { options.abortNext = false; end(true); return; }
            req.result = operation(); req.onsuccess?.(); pending--;
            setImmediate(() => { if (!pending) end(false); });
          }); return req;
        };
        tx.abort = () => setImmediate(() => end(true));
        tx.objectStore = () => ({ put: item => schedule(() => draft.set(item.id, structuredClone(item))),
          getAll: () => schedule(() => structuredClone([...draft.values()])),
          delete: id => schedule(() => draft.delete(id)), clear: () => schedule(() => draft.clear()) });
        setImmediate(() => { if (!pending) end(false); }); return tx;
      },
    };
    setImmediate(() => {
      request.result = db;
      if (options.blocked) { request.onblocked?.(); setImmediate(() => request.onsuccess?.()); }
      else if (options.openError) request.onerror?.(); else request.onsuccess?.();
    }); return request;
  }; return state;
}
function item(n) {
  return { id: `case-${n}`, createdAt: n, filename: `${n}.png`, file: new File(["image"], `${n}.png`, {type:"image/png"}),
    previewUrl:"unused", analyzedAt:"now", summaryLabel:"result", tone:"clear", prediction:{}, heatmapUrl:null, contourUrl:null,
    heatmapHasAlpha:false, contourHasAlpha:false, inLungRatio:null, selectedHead:"head_a", selectedClass:0, selectedDiseaseName:"Atelectasis", signedOffAt:null };
}
async function withDb(options, action) {
  const previous = global.window, db = fakeDb(options); global.window = {indexedDB:db};
  try { await action(db); } finally { global.window = previous; }
}
test("History commits before close and prunes the oldest createdAt to twenty", async () => {
  await withDb({}, async db => {
    for (const n of [24,0,23,1,...Array.from({length:21},(_,i)=>i+2)]) assert.equal(await history.saveHistoryItemToDb(item(n)), true);
    assert.equal(db.rows.size,20);
    const loaded=await history.loadHistoryFromDb();
    assert.deepEqual(loaded.map(x=>x.createdAt),Array.from({length:20},(_,i)=>24-i));
    assert.equal(db.earlyCloses,0); history.releaseHistoryPreviews(loaded);
  });
});
test("History rehydration preserves sign-off, edited impression and provenance", async () => {
  await withDb({}, async db => {
    const original={...item(1),signedOffAt:"27/11/2026 10:00",customImpression:"Physician edit",modelName:"standard",maskWarning:"approximate",auditPass:null};
    await history.saveHistoryItemToDb(original);
    const loaded=await history.loadHistoryFromDb();
    for(const key of ["signedOffAt","customImpression","modelName","maskWarning","auditPass"]) assert.equal(loaded[0][key],original[key]);
    assert.equal(db.earlyCloses,0); history.releaseHistoryPreviews(loaded);
  });
});
test("Queued save/delete/clear cannot resurrect removed history", async () => {
  await withDb({}, async db => {
    await Promise.all([history.saveHistoryItemToDb(item(1)),history.deleteHistoryItemFromDb("case-1")]); assert.equal(db.rows.size,0);
    await Promise.all([history.saveHistoryItemToDb(item(2)),history.clearHistoryDb()]); assert.equal(db.rows.size,0);
  });
});
test("An aborted history transaction resolves false with no committed write", async () => {
  await withDb({abortNext:true},async db=>{
    assert.equal(await history.saveHistoryItemToDb(item(1)),false); assert.equal(db.rows.size,0); assert.equal(db.earlyCloses,0);
  });
});
test("Missing, denied, private or blocked IndexedDB cannot crash history", async () => {
  const previous=global.window;
  try {
    delete global.window; assert.deepEqual(await history.loadHistoryFromDb(),[]); assert.equal(await history.saveHistoryItemToDb(item(1)),false);
    global.window={}; Object.defineProperty(global.window,"indexedDB",{get(){throw Error("denied");}});
    assert.deepEqual(await history.loadHistoryFromDb(),[]);
  } finally {global.window=previous;}
  for(const options of [{throwOpen:true},{openError:true},{blocked:true}]) await withDb(options,async db=>{
    assert.deepEqual(await history.loadHistoryFromDb(),[]); await new Promise(resolve=>setImmediate(resolve));
    if(options.blocked) assert.equal(db.closes,1);
  });
});
test("Deleting the history thumbnail does not revoke the restored active image", async()=>{
  const file=item(1).file, thumbnail=history.createScanPreview(file), active=history.createScanPreview(file);
  assert.notEqual(active,thumbnail); history.releaseHistoryPreviews([{previewUrl:thumbnail}]);
  assert.equal(await (await fetch(active)).text(),"image"); URL.revokeObjectURL(active);
});
test("A delayed CAM patch targets its captured ID without recreating deleted cases",()=>{
  const a=item(1),b=item(2), patched=history.patchScanHistory([a,b],a.id,{heatmapUrl:"CAM-A"});
  assert.equal(patched[0].heatmapUrl,"CAM-A"); assert.equal(patched[1].heatmapUrl,null);
  assert.deepEqual(history.patchScanHistory([b],a.id,{heatmapUrl:"CAM-A"}),[b]);
});
test("Settings close on outside click/Escape and detach listeners",()=>{
  const previous=global.document,listeners=new Map(); let closed=0,focused=0;
  global.document={addEventListener:(name,fn)=>listeners.set(name,fn),removeEventListener:name=>listeners.delete(name)};
  try {
    const cleanup=installPopoverDismissal({contains:target=>target==="inside",querySelector:()=>({focus:()=>focused++})},()=>closed++);
    listeners.get("mousedown")({target:"inside"}); assert.equal(closed,0);
    listeners.get("mousedown")({target:"outside"}); listeners.get("keydown")({key:"Escape"});
    assert.equal(closed,2); assert.equal(focused,1); cleanup(); assert.equal(listeners.size,0);
  } finally {global.document=previous;}
});
test("Safety and Precision flags reach the prediction request",async()=>{
  const previous=global.fetch,urls=[];
  global.fetch=async url=>{urls.push(new URL(url));return new Response("{}");};
  try {
    for(const safety of [true,false]) for(const tta of [true,false]) {
      await api.predictImage(new File(["image"],"cxr.png"),"standard",safety,tta);
      assert.equal(urls.at(-1).searchParams.get("failsafe_enabled"),String(safety));
      assert.equal(urls.at(-1).searchParams.get("tta_enabled"),String(tta));
    }
  } finally {global.fetch=previous;}
});
