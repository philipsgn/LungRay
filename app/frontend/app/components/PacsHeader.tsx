"use client";

interface Props {
  selectedModel: string;
  onSelectModel: (model: string) => void;
  failsafeEnabled: boolean;
  onToggleFailsafe: (enabled: boolean) => void;
  ttaEnabled: boolean;
  onToggleTta: (enabled: boolean) => void;
  connected: boolean | null;
  disabled: boolean;
}
const models = [["standard", "Standard CADx"], ["ag_mtcnet", "AG-MTCNet"], ["wsol", "WSOL Specialist"], ["resnet50", "ResNet-50"], ["ensemble", "Consensus Ensemble"]];
export default function PacsHeader({selectedModel,onSelectModel,failsafeEnabled,onToggleFailsafe,ttaEnabled,onToggleTta,connected,disabled}: Props) {
  return <header className="border-b border-slate-200 bg-white px-5 py-4"><div className="mx-auto max-w-7xl space-y-3">
    <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-3"><span className="rounded-xl bg-sky-600 px-3 py-2 font-bold text-white">LR</span><div><h1 className="text-xl font-bold text-slate-900">LungRay <span className="rounded-full bg-sky-50 px-2 py-1 text-xs text-sky-700">Clinical Edition</span></h1><p className="text-xs text-slate-500">DSP391 · X-quang ngực đa nhiệm</p></div></div><span className="text-sm text-slate-600">{connected === null ? "Chưa kiểm tra API" : connected ? "● Đã kết nối API (Port 8000)" : "● Chưa kết nối API"}</span></div>
    <div className="flex flex-wrap items-center gap-2"><span className="text-sm font-semibold text-slate-600">Mô hình</span>{models.map(([id,label]) => <button key={id} type="button" disabled={disabled} onClick={() => onSelectModel(id)} className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${selectedModel === id ? "border-sky-600 bg-sky-600 text-white" : "border-slate-200 bg-white text-slate-600"}`}>{label}</button>)}<label className="ml-auto text-sm text-slate-700"><input type="checkbox" checked={failsafeEnabled} disabled={disabled} onChange={e => onToggleFailsafe(e.target.checked)} /> Fail-Safe</label><label className="text-sm text-slate-700"><input type="checkbox" checked={ttaEnabled} disabled={disabled} onChange={e => onToggleTta(e.target.checked)} /> 3-Pass TTA</label></div>
  </div></header>;
}
