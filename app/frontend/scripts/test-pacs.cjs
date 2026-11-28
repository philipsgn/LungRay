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
const vm = require("node:vm");
const path = require("node:path");
const atlasRoot = path.resolve(__dirname, "../../..");
const atlasHtml = fs.readFileSync(path.join(__dirname, "../public/pipeline-atlas.html"), "utf8");
const atlasTrees = [...atlasHtml.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m =>
  ts.createSourceFile("atlas.js", m[1], ts.ScriptTarget.Latest, true, ts.ScriptKind.JS));
function atlasNode(predicate) {
  let found;
  function walk(node) { if (predicate(node)) found = node; if (!found) ts.forEachChild(node, walk); }
  for (const tree of atlasTrees) { walk(tree); if (found) return found; }
  throw Error("Missing atlas declaration");
}
function atlasFunction(name, context) {
  const node = atlasNode(n => ts.isFunctionDeclaration(n) && n.name?.text === name);
  return vm.runInNewContext("(" + node.getText() + ")", context);
}
function atlasData(name) {
  const node = atlasNode(n => ts.isVariableDeclaration(n) && n.name.getText() === name);
  return JSON.parse(JSON.stringify(vm.runInNewContext("(" + node.initializer.getText() + ")")));
}
const atlasThresholds = JSON.parse(atlasHtml.match(/id="atlas-thresholds"[^>]*>([\s\S]*?)<\/script>/)[1]);
function atlasCsv(filename) {
  const [header, ...rows] = fs.readFileSync(path.join(atlasRoot, filename), "utf8").trim().split(/\r?\n/).map(line => line.split(","));
  return rows.map(row => Object.fromEntries(header.map((key, i) => [key, row[i]])));
}

test("Atlas scripts parse and all 16 displayed cutoffs match the dated config", () => {
  for (const tree of atlasTrees) assert.deepEqual(tree.parseDiagnostics, []);
  const source = JSON.parse(fs.readFileSync(path.join(atlasRoot, "configs/optimal_thresholds_20_11.json")));
  const threshold = atlasFunction("findingThreshold", { THRESHOLDS: atlasThresholds });
  const findings = atlasData("D");
  assert.equal(findings.length, 16);
  for (const finding of findings) {
    const expected = finding.head === "B" ? source.head_b_tb : finding.head === "C" ? source.head_c_covid_binary : source.head_a[finding.name.replaceAll(" ", "_")];
    assert.equal(threshold(finding), expected, finding.name);
  }
  assert.match(atlasNode(n => ts.isFunctionDeclaration(n) && n.name?.text === "tilesUpdate").getText(), /findingThreshold\(d\)\.toFixed\(4\)/);
});

test("Atlas metric bars match stored validation/test artifacts and segmentation manifest", () => {
  const bars = atlasData("DENSENET_BARS");
  const history = atlasCsv("results/baseline/training_history_20_11.csv");
  const best = history.find(r => Number(r.epoch) === 16);
  const testRows = atlasCsv("results/baseline/independent_test_metrics_20_11.csv");
  const validation = Object.entries(best).filter(([key]) => /auc/i.test(key) && !/mean/i.test(key));
  for (const value of [0.7858, 0.9966, 0.9786]) assert.ok(validation.some(([, actual]) => Number(Number(actual).toFixed(4)) === value));
  for (const [index, row] of [[0, testRows[1]], [4, testRows[2]], [5, testRows[0]]]) assert.equal(bars[index].v, Number(Number(row.AUROC).toFixed(4)));
  assert.deepEqual(bars.filter(b => b.l.includes("Validation")).map(b => b.v).sort(), [0.7858, 0.9786, 0.9966]);
  const manifest = JSON.parse(fs.readFileSync(path.join(atlasRoot, "configs/dense_unet_manifest.json")));
  const seg = atlasData("DENSEUNET_BARS");
  assert.equal(seg[0].v, Number(manifest.val_dice.toFixed(4)));
  assert.equal(seg[1].v, Number(manifest.val_iou.toFixed(4)));
  assert.match(seg[2].l, /Target/); // A policy threshold must not become a measured Dice score.
});

test("Atlas initializes WebGL only after a visible tab supplies nonzero dimensions", () => {
  let initialized = 0, projections = 0;
  const sizes = [];
  const context = { stage: { clientWidth: 0, clientHeight: 0 }, ok: true, renderer: undefined,
    cam: { updateProjectionMatrix() { projections++; } },
    initGL() { initialized++; context.renderer = { setSize(...args) { sizes.push(args); } }; }
  };
  context.resize = atlasFunction("resize", context);
  const ensure = atlasFunction("ensureGL", context);
  assert.equal(ensure(), false); assert.equal(initialized, 0);
  context.stage.clientWidth = 900; context.stage.clientHeight = 600;
  assert.equal(ensure(), true); assert.equal(initialized, 1);
  assert.deepEqual(sizes[0], [900, 600, false]); assert.equal(context.cam.aspect, 1.5);
  context.stage.clientWidth = 1200; ensure(); assert.equal(context.cam.aspect, 2);
  context.stage.clientHeight = 0; assert.equal(ensure(), false);
  assert.equal(initialized, 1); assert.equal(projections, 2);
  context.ok = false; context.renderer = undefined; context.stage.clientHeight = 600;
  const fallback = { style: {} }; context.$ = () => fallback;
  assert.equal(ensure(), false); assert.equal(fallback.style.display, "grid");
});

test("Atlas tab switching schedules resize after display changes; tile navigation restores Stack", () => {
  const screens = ["arch", "wsol", "atlas", "metrics"].map(id => ({ id: "screen-" + id, classList: { toggle(_, value) { this.active = value; } } }));
  const buttons = screens.map(sc => ({ dataset: { tab: sc.id.slice(7) }, setAttribute(_, value) { this.selected = value; } }));
  const scheduled = []; let resized = 0;
  const switchTab = atlasFunction("switchTab", { $$: selector => selector === ".screen" ? screens : buttons,
    window: { __wsolResize() { assert.equal(screens[1].classList.active, true); resized++; } }, requestAnimationFrame: cb => scheduled.push(cb) });
  switchTab("wsol"); assert.equal(resized, 0); scheduled.shift()(); assert.equal(resized, 1);
  assert.equal(buttons[1].selected, "true"); assert.equal(screens[0].classList.active, false);
  switchTab("arch"); assert.equal(scheduled.length, 0);
  const build = atlasNode(n => ts.isFunctionDeclaration(n) && n.name?.text === "build").getText();
  assert.match(build, /select\(d.id\);resetStack\(\);if\(window.__switchAtlasTab\)/);
});

test("Atlas camera presets work and Reset restores all six layers and labels", () => {
  const inputs = Array.from({ length: 6 }, () => ({ checked: false }));
  const stepButtons = Array.from({ length: 7 }, () => ({ setAttribute(_, value) { this.pressed = value; } }));
  const caption = { children: [{}, {}, {}] }, rotation = { checked: true };
  const context = { state: { step: 4, rot: true, hl: 3 }, STEPS: atlasData("STEPS"),
    document: { querySelectorAll: () => inputs },
    $: selector => selector === "#steps" ? { children: stepButtons } : selector === "#cap" ? caption : rotation };
  context.setStep = atlasFunction("setStep", context);
  const reset = atlasFunction("resetStack", context);
  const calls = [], active = new Set();
  const presets = ["flat", "tilt", "side", "reset"].map(mode => ({ mode, classList: { remove() { active.delete(mode); }, add() { active.add(mode); } } }));
  const apply = atlasFunction("applyCameraPreset", { window: { __wsolResize() {}, __wsolResetStack: reset, __wsolCam: { set: (...args) => calls.push(args) } },
    $$: () => presets, $: selector => presets.find(p => selector.includes('"' + p.mode + '"')) });
  for (const mode of ["flat", "tilt", "side", "reset"]) apply(mode);
  assert.deepEqual(calls, [[0, 0, 0], [-0.92, 0.48, 0.55], [-1.32, 0.95, 0.92], [-0.92, 0.48, 0.55]]);
  assert.equal(context.state.step, 0); assert.equal(context.state.rot, false); assert.equal(context.state.hl, -1);
  assert.equal(rotation.checked, false); assert.ok(inputs.every(input => input.checked));
  assert.deepEqual(Array.from(context.vis), [1, 1, 1, 1, 1, 1]);
  assert.equal(stepButtons[0].pressed, "true"); assert.deepEqual([...active], ["tilt"]);
  assert.equal(atlasData("LAYERS").length, 6);
});

test("Atlas safety numbers and TTA wording follow backend configuration", () => {
  const safety = atlasData("SAFETY");
  const ood = JSON.parse(fs.readFileSync(path.join(atlasRoot, "configs/ood_thresholds.json")));
  for (const value of [ood.energy_score.threshold.toFixed(2), ood.energy_score.upper_threshold.toFixed(2), ood.entropy_score.threshold.toFixed(4)]) assert.ok(safety[0].code.includes(value));
  const services = fs.readFileSync(path.join(atlasRoot, "app/backend/services.py"), "utf8");
  const temperature = services.match(/def apply_temperature_scaling\([^\n]*temperature: float = ([\d.]+)/)[1];
  assert.ok(safety[2].code.includes("T = " + temperature));
  const clahe = services.match(/cv2.createCLAHE\(clipLimit=([\d.]+), tileGridSize=\((\d+), (\d+)\)\)/);
  assert.ok(safety[2].desc.includes("clipLimit=" + clahe[1]));
  assert.ok(safety[2].desc.includes("tileGridSize=" + clahe[2] + "×" + clahe[3]));
  assert.ok(/cv2.flip\([^,\n]+, 1\)/.test(services), "TTA must include a horizontal flip");
  assert.match(safety[2].code, /Original \+ HFlip \+ CLAHE/);
  assert.match(safety[2].desc, /Average probabilities first/);
  assert.match(safety[3].desc, /positive AG-MTCNet/);
});

test("Atlas can refresh synthetic data before lazy WebGL initialization", () => {
  const textures = [{ needsUpdate: false }], calls = [];
  const context = { renderer: undefined, axis: undefined, textures, resA: { peak: { x: 0.75, y: 0.25 } } };
  const sync = atlasFunction("syncScene", context);
  assert.doesNotThrow(sync); assert.equal(textures[0].needsUpdate, false);
  context.renderer = {}; context.axis = { position: { set: (...args) => calls.push(args) } };
  sync(); assert.equal(textures[0].needsUpdate, true); assert.deepEqual(calls, [[1, 1, 0]]);
  context.resA = undefined; assert.doesNotThrow(sync);
  const refresh = atlasNode(n => ts.isFunctionDeclaration(n) && n.name?.text === "doRefresh").getText();
  const init = atlasNode(n => ts.isFunctionDeclaration(n) && n.name?.text === "initGL").getText();
  assert.match(refresh, /syncScene\(\)/); assert.match(init, /syncScene\(\)/);
});

const ragPresentation = require("../app/lib/ragPresentation.ts");
test("RAG legacy and offline contracts never claim unverified citation faithfulness", async () => {
  assert.equal(ragPresentation.ragVerificationLabel(null), "Not verified");
  const legacy = { status: "GROUNDED_REFERENCE", answer: "reference", citations: [], retrieved_cards: [] };
  assert.equal(ragPresentation.ragVerificationLabel(legacy), "Not verified");
  assert.equal(ragPresentation.ragVerificationLabel({ ...legacy, faithfulness_verified: true }), "Not verified");
  assert.equal(ragPresentation.ragVerificationLabel({ ...legacy, faithfulness_verified: true, verification_scope: "extractive_source_match" }), "Source text checked");
  assert.equal(ragPresentation.ragSynthesisLabel(legacy), null);
  for (const safe of [true, false]) {
    const fallback = await edge.edgeQueryClinicalRag({ question: "TB?", active_findings: [], anatomical_locations: [], is_safe: safe });
    assert.match(ragPresentation.ragVerificationLabel(fallback), /unavailable|blocked/);
    assert.equal(ragPresentation.ragSynthesisLabel(fallback), null);
    assert.deepEqual(fallback.retrieval_chunks ?? [], []);
    assert.deepEqual(fallback.graph_trace ?? [], []);
  }
});

test("RAG session key changes with study, OOD context and updated lung audit", () => {
  const prediction = { active_model: "standard", safety: { is_safe: true }, report: { active_findings: ["Effusion"], anatomical_locations: [] } };
  const key = ragPresentation.clinicalRagContextKey(prediction, null);
  assert.equal(key, ragPresentation.clinicalRagContextKey(structuredClone(prediction), null));
  assert.notEqual(key, ragPresentation.clinicalRagContextKey(prediction, 0.79));
  assert.notEqual(key, ragPresentation.clinicalRagContextKey({ ...prediction, safety: { is_safe: false } }, null));
  assert.notEqual(key, ragPresentation.clinicalRagContextKey({ ...prediction, report: { active_findings: ["Tuberculosis"] } }, null));
});

test("RAG first render is safe without optional trace or retrieval metadata", () => {
  require.extensions[".tsx"] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX }
  }).outputText, filename);
  const React = require("react");
  const { renderToStaticMarkup } = require("react-dom/server");
  const Assistant = require("../app/components/ClinicalRagAssistant.tsx").default;
  const prediction = { safety: { is_safe: true }, report: { is_blocked: false, active_findings: [] } };
  const initial = Assistant({ prediction, ratio: null });
  const updated = Assistant({ prediction, ratio: 0.79 });
  assert.notEqual(initial.key, updated.key); // React remounts and invalidates the prior request generation.
  const html = renderToStaticMarkup(React.createElement(Assistant, { prediction, ratio: null }));
  assert.match(html, /Not verified/);
  assert.doesNotMatch(html, /Citation Verified|Gemini Grounded/);
});
