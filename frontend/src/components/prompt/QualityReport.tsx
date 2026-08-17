import { CircleHelp } from "lucide-react";
import { Card } from "../ui/card";
import type { Prompt } from "../../types";

export function QualityReport({ prompt }: { prompt: Prompt }) {
  const groups = [
    ["Mocne strony", prompt.analysis.strengths, "emerald"],
    ["Do dopracowania", prompt.analysis.weaknesses, "amber"],
    ["Brakujące informacje", prompt.analysis.missing_information, "rose"],
    ["Sugestie", prompt.analysis.suggestions, "violet"],
  ] as const;
  const breakdown = Object.entries(prompt.analysis.quality_breakdown ?? {});
  return <section aria-labelledby="quality-title" className="space-y-3">
    <Card className="p-5">
      <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="eyebrow">Ocena kompletności briefu</p><h2 id="quality-title" className="mt-1 text-xl font-black">{prompt.quality_score ?? "—"}/100</h2></div><CircleHelp className="text-violet-500" aria-hidden="true" size={21} /></div>
      <p className="mt-3 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{prompt.analysis.quality_explanation || "Ocena pokazuje, ile konkretnych informacji zawiera brief."}</p>
      {breakdown.length > 0 && <dl className="mt-5 grid gap-2 sm:grid-cols-2">{breakdown.map(([name, value]) => <div key={name} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm dark:bg-white/5"><dt className="text-slate-600 dark:text-slate-300">{name}</dt><dd className={value < 0 ? "font-black text-rose-600" : "font-black text-slate-900 dark:text-white"}>{value > 0 ? `+${value}` : value}</dd></div>)}</dl>}
    </Card>
    <div className="grid gap-3 sm:grid-cols-2">{groups.map(([title, items, tone]) => <Card key={title} className="p-4"><h3 className={`text-sm font-black ${tone === "emerald" ? "text-emerald-600" : tone === "amber" ? "text-amber-600" : tone === "rose" ? "text-rose-600" : "text-violet-600"}`}>{title}</h3>{items.length ? <ul className="mt-2 space-y-1.5 text-xs leading-relaxed text-slate-500 dark:text-slate-400">{items.map((item) => <li key={item}>• {item}</li>)}</ul> : <p className="mt-2 text-xs text-slate-400">Brak krytycznych uwag.</p>}</Card>)}</div>
  </section>;
}
