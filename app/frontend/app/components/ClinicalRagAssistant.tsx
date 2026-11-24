"use client";

import { useEffect, useRef, useState } from "react";
import { PredictionResponse, RagQueryResponse } from "../types";
import { queryClinicalRag } from "../lib/api";

const PROMPTS = ["Tiêu chuẩn hình ảnh X-quang?", "Hướng xử trí & cận lâm sàng?", "Giải thích độ tin cậy & vùng giải phẫu?"];

export default function ClinicalRagAssistant({ prediction, ratio }: { prediction: PredictionResponse; ratio: number | null }) {
  const [result, setResult] = useState<RagQueryResponse | null>(null);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const generation = useRef(0);
  const safe = prediction.safety?.is_safe === true && prediction.safety.decision !== "REJECT" && !prediction.report?.is_blocked;

  async function ask(text: string) {
    const current = ++generation.current;
    setBusy(true); setError(""); setResult(null);
    try {
      const response = await queryClinicalRag({ question: text, active_findings: prediction.report?.active_findings ?? [],
        anatomical_locations: prediction.report?.anatomical_locations ?? [], is_safe: safe, in_lung_ratio: ratio });
      if (current === generation.current) setResult(response);
    } catch {
      if (current === generation.current) setError("Không truy xuất được tri thức. Vui lòng thử lại.");
    } finally {
      if (current === generation.current) setBusy(false);
    }
  }

  useEffect(() => {
    void ask(PROMPTS[0]);
    return () => { generation.current += 1; };
    // Parent remounts this component whenever the case or audit context changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-3" aria-label="Grounded Clinical RAG Assistant">
    <h3 className="text-sm font-semibold text-slate-900">Grounded Clinical RAG Assistant</h3>
    <p className="text-xs text-slate-500">Tra cứu tham khảo theo ca. Mã ICD-10 cần bác sĩ xác nhận.</p>
    {!safe ? <p role="alert" className="text-sm text-red-700">OOD Fail-Safe: khóa diễn giải bệnh lý. Kiểm tra ảnh đầu vào và phân tích lại.</p> : <>
      <div className="flex flex-wrap gap-2">{PROMPTS.map(prompt => <button key={prompt} type="button" disabled={busy} onClick={() => void ask(prompt)} className="rounded-lg border border-slate-300 px-2 py-1 text-xs text-slate-700 disabled:opacity-50">{prompt}</button>)}</div>
      <form className="flex gap-2" onSubmit={event => { event.preventDefault(); if (question.trim()) void ask(question.trim()); }}>
        <input aria-label="Câu hỏi y khoa" maxLength={2000} value={question} onChange={event => setQuestion(event.target.value)} placeholder="Hỏi về dấu hiệu hoặc kiến thức trong ca..." className="min-w-0 flex-1 rounded-lg border border-slate-300 p-2 text-sm" />
        <button disabled={busy || !question.trim()} className="rounded-lg bg-slate-800 px-3 text-sm text-white disabled:opacity-50">Gửi</button>
      </form>
      <div aria-live="polite" className="text-sm text-slate-700">{busy ? "Đang truy xuất..." : error || result?.answer}</div>
      {result?.retrieved_cards.map(card => <details key={card.disease} className="rounded-lg border border-slate-200 p-3">
        <summary className="cursor-pointer text-sm font-semibold">{card.disease} · ICD-10 {card.icd10}</summary>
        <dl className="mt-2 space-y-2 text-xs text-slate-700"><dt className="font-semibold">Đặc điểm X-quang</dt><dd>{card.hallmarks}</dd><dt className="font-semibold">Chẩn đoán phân biệt</dt><dd>{card.differential}</dd><dt className="font-semibold">Cận lâm sàng tham khảo</dt><dd>{card.followup}</dd></dl>
        <p className="mt-2 text-xs text-slate-500">{card.coding_note}</p>
      </details>)}
      {result && result.citations.length > 0 && <details><summary className="text-xs font-semibold">Nguồn tham chiếu</summary><ul className="space-y-2 pt-2 text-xs">{result.citations.map(source => { const url = source.match(/https:\/\/\S+$/)?.[0]; return <li key={source}>{url ? <a className="text-sky-700 underline" href={url} target="_blank" rel="noreferrer">{source.split(": https:")[0]}</a> : source}</li>; })}</ul></details>}
    </>}
  </section>;
}
