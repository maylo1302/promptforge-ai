import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Bookmark, FileText, Plus, Sparkles, Target } from "lucide-react";
import { Link } from "react-router-dom";
import { PageHeading } from "../components/layout/AppShell";
import { Badge } from "../components/ui/badge";
import { Card, CardTitle } from "../components/ui/card";
import { api } from "../lib/api";
import { categoryLabels } from "../lib/prompts";
import { formatDate } from "../lib/utils";
import type { DashboardData } from "../types";

const cards = [
  ["total_prompts", "Wszystkie prompty", FileText, "violet"],
  ["generated_this_month", "W tym miesiącu", Sparkles, "green"],
  ["favorite_prompts", "Ulubione", Bookmark, "amber"],
  ["average_quality_score", "Średnia kompletność", Target, "violet"],
] as const;

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: () => api<DashboardData>("/dashboard") });
  return <><PageHeading eyebrow="Dzień dobry" title="Twoje centrum promptów" description="Twórz, dopracowuj i wracaj do sprawdzonych instrukcji dla modeli AI." action={<Link to="/app/generator" className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-bold text-white shadow-lg shadow-violet-600/20 transition hover:bg-violet-500"><Plus size={17} />Nowy prompt</Link>} /><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([key, label, Icon, tone]) => <Card key={key} className="relative overflow-hidden"><div className={`absolute right-4 top-4 grid size-10 place-items-center rounded-xl ${tone === "green" ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15" : tone === "amber" ? "bg-amber-100 text-amber-600 dark:bg-amber-500/15" : "bg-violet-100 text-violet-600 dark:bg-violet-500/15"}`}><Icon size={19} /></div><p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p><p className="mt-3 text-3xl font-black">{isLoading ? "—" : key === "average_quality_score" ? `${data?.[key] ?? "—"}${data?.[key] !== null && data?.[key] !== undefined ? "/100" : ""}` : data?.[key] ?? 0}</p></Card>)}</div><div className="mt-7 grid gap-6 lg:grid-cols-[1.5fr_.8fr]"><Card><CardTitle action={<Link to="/app/historia" className="inline-flex items-center gap-1 text-xs font-bold text-violet-600 hover:underline">Zobacz historię <ArrowRight size={14} /></Link>}>Ostatnio tworzone</CardTitle>{isLoading ? <div className="space-y-3">{[1, 2, 3].map((item) => <div key={item} className="h-16 animate-pulse rounded-xl bg-slate-100 dark:bg-white/5" />)}</div> : data?.recent_prompts.length ? <div className="divide-y">{data.recent_prompts.map((prompt) => <Link to={`/app/prompty/${prompt.id}`} key={prompt.id} className="flex items-center gap-3 py-4 first:pt-0 last:pb-0"><div className="grid size-9 shrink-0 place-items-center rounded-xl bg-violet-100 text-violet-600 dark:bg-violet-500/15"><Sparkles size={17} /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-bold">{prompt.brief}</p><p className="mt-1 text-xs text-slate-400">{formatDate(prompt.updated_at)} · {categoryLabels[prompt.category] ?? prompt.category}</p></div>{prompt.quality_score !== null && <Badge tone="green">{prompt.quality_score}/100</Badge>}</Link>)}</div> : <Empty />}</Card><Card className="bg-gradient-to-br from-violet-600 to-indigo-700 text-white dark:border-violet-400/20"><p className="eyebrow text-violet-200">Jak zacząć?</p><h2 className="mt-3 text-2xl font-black">Opisz zamiar, nie gotowy prompt.</h2><p className="mt-3 text-sm leading-relaxed text-violet-100">Napisz, co chcesz osiągnąć. Szkic zapisze się dopiero po świadomym kliknięciu przycisku, a potem zobaczysz pytania doprecyzowujące.</p><Link to="/app/generator" className="mt-7 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-violet-700 transition hover:bg-violet-50">Przejdź do generatora <ArrowRight size={16} /></Link></Card></div></>;
}

function Empty() { return <div className="grid min-h-52 place-items-center rounded-xl border border-dashed text-center"><div><p className="font-bold">Jeszcze tu pusto</p><p className="mt-1 text-sm text-slate-500">Utwórz pierwszy szkic w generatorze, aby pojawił się w historii.</p></div></div>; }
