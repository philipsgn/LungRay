"use client";

import { useEffect, useRef, useState } from "react";
import { BookOpen, Search, Sparkles, ExternalLink, ShieldAlert, CheckCircle2, GitBranch } from "lucide-react";
import { PredictionResponse, RagQueryResponse } from "../types";
import { queryClinicalRag } from "../lib/api";
import { clinicalRagContextKey, ragVerificationLabel, ragSynthesisLabel } from "../lib/ragPresentation";

const QUICK_PROMPTS = [
  "What are the key imaging hallmarks?",
  "What are the differential diagnoses?",
  "Recommended follow-up and clinical workup?",
];

interface Props {
  prediction: PredictionResponse;
  ratio: number | null;
}

export default function ClinicalRagAssistant(props: Props) {
  return <ClinicalRagSession key={clinicalRagContextKey(props.prediction, props.ratio)} {...props} />;
}

function ClinicalRagSession({ prediction, ratio }: Props) {
  const [result, setResult] = useState<RagQueryResponse | null>(null);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const generation = useRef(0);
  const sourceChecked = ragVerificationLabel(result) === "Source text checked";
  const safe =
    prediction.safety?.is_safe === true &&
    prediction.safety.decision !== "REJECT" &&
    !prediction.report?.is_blocked;

  async function ask(text: string) {
    const current = ++generation.current;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const response = await queryClinicalRag({
        question: text,
        active_findings: prediction.report?.active_findings ?? [],
        anatomical_locations: prediction.report?.anatomical_locations ?? [],
        is_safe: safe,
        in_lung_ratio: ratio,
      });
      if (current === generation.current) setResult(response);
    } catch {
      if (current === generation.current) {
        setError("Unable to retrieve knowledge cards. Please retry.");
      }
    } finally {
      if (current === generation.current) setBusy(false);
    }
  }

  useEffect(() => {
    void ask(QUICK_PROMPTS[0]);
    return () => {
      generation.current += 1;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section
      className="rounded-xl border border-[#1C2937] bg-[#0D1520] p-4 space-y-4 font-sans select-none shadow-md"
      aria-label="Grounded Clinical RAG Assistant"
    >
      <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-[#1C2937]">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#0A7A74]/30 text-[#3FD0C4] border border-[#3FD0C4]/40">
            <BookOpen className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#E6EDF4]">
              Grounded Clinical Knowledge Assistant (RAG)
            </h3>
            <p className="text-xs text-[#8C9DB0]">
              Clinical reference retrieval (BM25 + TF-IDF RRF) · WHO ICD-10 &amp; Fleischner Society (2024)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {ragSynthesisLabel(result) && (
            <span className="rounded-md bg-[#111C2B] border border-[#1C2937] px-2 py-1 text-[10px] font-mono text-[#8C9DB0]">
              {ragSynthesisLabel(result)}
            </span>
          )}
          {typeof result?.latency_ms === "number" && (
            <span className="rounded-md bg-[#111C2B] border border-[#1C2937] px-2 py-1 text-[10px] font-mono text-[#8C9DB0]">
              {result.latency_ms.toFixed(1)} ms
            </span>
          )}
          <span className={`rounded-md bg-[#111C2B] border border-[#1C2937] px-2.5 py-1 text-[10px] font-mono font-medium inline-flex items-center gap-1 ${sourceChecked ? "text-[#3FD0C4]" : "text-[#8C9DB0]"}`}>
            {sourceChecked ? <CheckCircle2 className="w-3 h-3" /> : <ShieldAlert className="w-3 h-3" />}
            {ragVerificationLabel(result)}
          </span>
        </div>
      </div>

      {!safe ? (
        <div className="p-3.5 rounded-lg bg-rose-950/40 border border-rose-800 text-xs text-rose-300 flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
          <span>
            Fail-Safe Gatekeeper: Radiograph flagged as OOD or degraded. Clinical knowledge retrieval is withheld to prevent automated bias.
          </span>
        </div>
      ) : (
        <>
          {/* Quick Prompt Pills */}
          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                disabled={busy}
                onClick={() => void ask(prompt)}
                className="rounded-lg border border-[#1C2937] bg-[#111C2B] px-3 py-1.5 text-xs text-[#8C9DB0] hover:text-[#E6EDF4] hover:border-[#3FD0C4] transition-all disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Interactive Search Query Input */}
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (question.trim()) void ask(question.trim());
            }}
          >
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#8C9DB0]" />
              <input
                aria-label="Clinical inquiry"
                maxLength={2000}
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about detected findings, differential criteria, or follow-up guidelines..."
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-[#111C2B] border border-[#1C2937] text-xs text-[#E6EDF4] placeholder-[#566475] focus:outline-none focus:border-[#3FD0C4] transition"
              />
            </div>
            <button
              disabled={busy || !question.trim()}
              className="rounded-lg bg-[#0A7A74] border border-[#3FD0C4]/60 px-4 text-xs font-semibold text-white hover:bg-[#0A7A74]/80 disabled:opacity-40 transition"
            >
              Search
            </button>
          </form>

          {/* Retrieval Status or Structured Answer */}
          <div aria-live="polite" className="text-xs text-[#E6EDF4] leading-relaxed space-y-2">
            {busy ? (
              <div className="flex items-center gap-2 text-[#3FD0C4] animate-pulse">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Retrieving clinical reference evidence...</span>
              </div>
            ) : error ? (
              <span className="text-rose-400">{error}</span>
            ) : (
              <>
                {result?.graph_trace && result.graph_trace.length > 0 && (
                  <div
                    className="flex items-center gap-1.5 flex-wrap text-[10px] font-mono text-[#8C9DB0]"
                    aria-label="Clinical retrieval execution trace"
                  >
                    <GitBranch className="w-3 h-3 text-[#3FD0C4] shrink-0" />
                    {result.graph_trace.map((step, idx) => (
                      <span key={`${step}-${idx}`} className="inline-flex items-center gap-1">
                        <span className="rounded bg-[#111C2B] border border-[#1C2937] px-1.5 py-0.5 text-[#C8D4E2]">
                          {step}
                        </span>
                        {idx < (result.graph_trace?.length ?? 0) - 1 && (
                          <span className="text-[#566475]">→</span>
                        )}
                      </span>
                    ))}
                  </div>
                )}
                <div className="p-3 rounded-lg bg-[#111C2B]/80 border border-[#1C2937] text-xs text-[#E6EDF4] leading-relaxed">
                  {result?.answer}
                </div>
              </>
            )}
          </div>

          {/* Retrieved Disease Knowledge Cards */}
          {result?.retrieved_cards && result.retrieved_cards.length > 0 && (
            <div className="space-y-2 pt-1">
              <span className="text-[10px] font-mono uppercase tracking-wider text-[#8C9DB0]">
                Curated Reference Cards ({result.retrieved_cards.length}):
              </span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.retrieved_cards.map((card) => {
                  const cardChunks = (result.retrieval_chunks ?? []).filter(
                    (ch) => ch.disease === card.disease
                  );
                  const topRel = cardChunks.reduce(
                    (best, ch) => Math.max(best, ch.relevance_score),
                    0
                  );
                  return (
                  <details
                    key={card.disease}
                    open
                    className="rounded-xl border border-[#1C2937] bg-[#111C2B]/60 p-3.5 space-y-2"
                  >
                    <summary className="cursor-pointer text-xs font-bold text-[#E6EDF4] flex items-center justify-between gap-2">
                      <span className="text-[#3FD0C4]">{card.disease}</span>
                      <span className="flex items-center gap-1.5">
                        {topRel > 0 && (
                          <span title="Heuristic retrieval score, not diagnostic confidence" className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-[#0A7A74]/25 text-[#3FD0C4] border border-[#3FD0C4]/30">
                            Lexical score {topRel.toFixed(2)}
                          </span>
                        )}
                        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#070B12] text-[#F2A93B] border border-[#1C2937]">
                          ICD-10: {card.icd10}
                        </span>
                      </span>
                    </summary>

                    <dl className="mt-2 space-y-2 text-xs">
                      <div>
                        <dt className="text-[10px] font-mono uppercase text-[#8C9DB0] font-semibold">
                          Imaging Hallmarks:
                        </dt>
                        <dd className="text-[#E6EDF4] mt-0.5">{card.hallmarks}</dd>
                      </div>
                      <div>
                        <dt className="text-[10px] font-mono uppercase text-[#8C9DB0] font-semibold">
                          Differential Diagnoses:
                        </dt>
                        <dd className="text-[#E6EDF4] mt-0.5">{card.differential}</dd>
                      </div>
                      <div>
                        <dt className="text-[10px] font-mono uppercase text-[#8C9DB0] font-semibold">
                          Follow-Up Workup:
                        </dt>
                        <dd className="text-[#E6EDF4] mt-0.5">{card.followup}</dd>
                      </div>
                    </dl>

                    <p className="text-[10px] text-[#566475] italic pt-1 border-t border-[#1C2937]">
                      {card.coding_note}
                    </p>
                  </details>
                  );
                })}
              </div>
            </div>
          )}

          {/* Official Citations */}
          {result && result.citations.length > 0 && (
            <details className="text-xs text-[#8C9DB0] pt-1">
              <summary className="cursor-pointer font-mono text-[11px] font-semibold hover:text-[#E6EDF4]">
                Reference Sources (editorial summaries; clinician review) ({result.citations.length})
              </summary>
              <ul className="space-y-1.5 pt-2 pl-4 list-disc text-[11px]">
                {result.citations.map((source) => {
                  const url = source.match(/https:\/\/\S+$/)?.[0];
                  return (
                    <li key={source}>
                      {url ? (
                        <a
                          className="text-[#3FD0C4] hover:underline inline-flex items-center gap-1"
                          href={url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <span>{source.split(": https:")[0]}</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      ) : (
                        source
                      )}
                    </li>
                  );
                })}
              </ul>
            </details>
          )}
        </>
      )}
    </section>
  );
}
