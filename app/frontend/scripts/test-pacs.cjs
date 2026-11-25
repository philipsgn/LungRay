const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const zlib = require("node:zlib");
const ts = require("typescript");
require.extensions[".ts"] = (module, filename) => module._compile(ts.transpileModule(fs.readFileSync(filename, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }
}).outputText, filename);
const { cardiothoracicRatio, csvRow, filterStudies } = require("../app/lib/pacsUtils.ts");
const edge = require("../app/lib/edgeFallback.ts");
const api = require("../app/lib/api.ts");

test("CTR supports reverse drags and zero-width protection", () => {
  assert.equal(cardiothoracicRatio(-40, -80), 0.5);
  assert.ok(Number.isFinite(cardiothoracicRatio(40, 0)));
});
test("CSV quotes every field including commas, quotes and newlines", () => {
  assert.equal(csvRow(['A"B', 'C,D', 'E\nF', 0]), '"A""B","C,D","E\nF","0"');
});
test("Worklist combines priority AND case-insensitive query", () => {
  const studies = [{ studyId: "A", patientId: "PAT", indication: "Cough", priority: "STAT" }, { studyId: "B", patientId: "PAT", indication: "Cough", priority: "ROUTINE" }];
  assert.deepEqual(filterStudies(studies, " pat ", "STAT").map(s => s.studyId), ["A"]);
  assert.equal(filterStudies(studies, "unknown", "ALL").length, 0);
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
