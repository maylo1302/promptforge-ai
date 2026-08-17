import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, ExternalLink, Heart, LoaderCircle, Search, SlidersHorizontal, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { PageHeading } from "../components/layout/AppShell";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { api } from "../lib/api";
import { categoryLabels, promptStatusLabel } from "../lib/prompts";
import { formatDate } from "../lib/utils";
import type { Prompt } from "../types";

type Response = { items: Prompt[]; total: number };
type Feedback = { kind: "success" | "error"; message: string } | null;

export function HistoryPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [favorite, setFavorite] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Feedback>(null);
  const queryClient = useQueryClient();
  const params = new URLSearchParams({ page_size: "50", ...(search ? { search } : {}), ...(category ? { category } : {}), ...(favorite ? { favorite: "true" } : {}) });
  const queryKey = ["prompts", search, category, favorite];
  const { data, isLoading } = useQuery({ queryKey, queryFn: () => api<Response>(`/prompts?${params}`) });

  const update = async (prompt: Prompt, changes: Partial<Prompt>) => {
    try {
      await api(`/prompts/${prompt.id}`, { method: "PATCH", body: JSON.stringify(changes) });
      await Promise.all([queryClient.invalidateQueries({ queryKey: ["prompts"] }), queryClient.invalidateQueries({ queryKey: ["dashboard"] })]);
    } catch {
      setFeedback({ kind: "error", message: "Nie udało się zapisać zmiany. Spróbuj ponownie." });
    }
  };
  const remove = async (prompt: Prompt) => {
    if (!window.confirm(`Usunąć prompt „${prompt.brief}”? Tej operacji nie można cofnąć.`)) return;
    setDeletingId(prompt.id);
    setFeedback(null);
    try {
      await api(`/prompts/${prompt.id}`, { method: "DELETE" });
      await Promise.all([queryClient.invalidateQueries({ queryKey: ["prompts"] }), queryClient.invalidateQueries({ queryKey: ["dashboard"] })]);
      setFeedback({ kind: "success", message: "Prompt został usunięty." });
    } catch {
      setFeedback({ kind: "error", message: "Nie udało się usunąć promptu. Wpis pozostał w historii." });
    } finally {
      setDeletingId(null);
    }
  };

  return <>
    <PageHeading eyebrow="Biblioteka promptów" title="Historia pracy" description="Każdy szkic zapisuje się dopiero po kliknięciu „Przeanalizuj i zapisz szkic”. Otwórz wpis, aby zobaczyć pełną treść lub wrócić do pytań." />
    {feedback && <p role={feedback.kind === "error" ? "alert" : "status"} className={`mb-5 rounded-xl p-3 text-sm font-semibold ${feedback.kind === "success" ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200" : "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-200"}`}>{feedback.message}</p>}
    <Card className="p-4"><div className="flex flex-col gap-3 md:flex-row"><label className="relative flex-1"><Search className="absolute left-3 top-3 text-slate-400" size={17} /><span className="sr-only">Szukaj w historii promptów</span><input value={search} onChange={(event) => setSearch(event.target.value)} className="input pl-10" placeholder="Szukaj w opisie lub treści promptu…" /></label><label className="sr-only" htmlFor="history-category">Kategoria</label><select id="history-category" value={category} onChange={(event) => setCategory(event.target.value)} className="input md:w-52"><option value="">Wszystkie kategorie</option>{Object.entries(categoryLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><Button variant={favorite ? "primary" : "secondary"} onClick={() => setFavorite(!favorite)}><Heart size={16} fill={favorite ? "currentColor" : "none"} />Ulubione</Button></div></Card>
    <div className="mt-5 flex items-center justify-between text-sm text-slate-500"><span>{isLoading ? "Pobieramy historię…" : `${data?.total ?? 0} promptów`}</span><span className="inline-flex items-center gap-2"><SlidersHorizontal size={15} />Najnowsze na górze</span></div>
    <div className="mt-4 grid gap-3">{data?.items.map((prompt) => <Card key={prompt.id} className="p-5"><div className="flex flex-col gap-4 sm:flex-row sm:items-start"><Link to={`/app/prompty/${prompt.id}`} className="min-w-0 flex-1 rounded-xl outline-offset-4 focus:outline focus:outline-2 focus:outline-violet-500"><div className="flex flex-wrap items-center gap-2"><Badge tone={prompt.status === "generated" ? "green" : "amber"}>{promptStatusLabel(prompt.status)}</Badge>{prompt.quality_score !== null && <Badge tone="violet">Kompletność {prompt.quality_score}/100</Badge>}<span className="text-xs text-slate-400">{formatDate(prompt.updated_at)}</span></div><h2 className="mt-3 line-clamp-1 font-bold hover:text-violet-600">{prompt.brief}</h2><p className="mt-1 line-clamp-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{prompt.content ?? "Otwórz szkic, aby odpowiedzieć na pytania i wygenerować prompt."}</p><div className="mt-3 flex flex-wrap gap-1.5"><span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-500 dark:bg-white/10 dark:text-slate-300">{categoryLabels[prompt.category] ?? prompt.category}</span>{prompt.tags.map((tag) => <span key={tag} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-500 dark:bg-white/10 dark:text-slate-300">#{tag}</span>)}</div></Link><div className="flex shrink-0 flex-wrap justify-end gap-1 self-end sm:self-start">{prompt.status === "needs_clarification" && <Link to={`/app/generator?szkic=${prompt.id}`} className="inline-flex items-center gap-1 rounded-xl bg-violet-600 px-3 py-2 text-xs font-bold text-white hover:bg-violet-500" aria-label="Kontynuuj szkic"><ArrowRight size={15} />Kontynuuj szkic</Link>}<Link to={`/app/prompty/${prompt.id}`} className="rounded-xl p-2.5 text-slate-500 hover:bg-violet-50 hover:text-violet-600 dark:hover:bg-violet-500/10" aria-label="Otwórz szczegóły promptu"><ExternalLink size={18} /></Link><button onClick={() => void update(prompt, { is_favorite: !prompt.is_favorite })} className="rounded-xl p-2.5 text-slate-400 hover:bg-rose-50 hover:text-rose-500 dark:hover:bg-rose-500/10" aria-label={prompt.is_favorite ? "Usuń z ulubionych" : "Dodaj do ulubionych"}><Heart size={18} fill={prompt.is_favorite ? "currentColor" : "none"} className={prompt.is_favorite ? "text-rose-500" : ""} /></button><button onClick={() => void remove(prompt)} disabled={deletingId === prompt.id} className="rounded-xl p-2.5 text-slate-400 hover:bg-rose-50 hover:text-rose-500 disabled:cursor-wait disabled:opacity-60 dark:hover:bg-rose-500/10" aria-label="Usuń prompt">{deletingId === prompt.id ? <LoaderCircle className="animate-spin" size={18} /> : <Trash2 size={18} />}</button></div></div></Card>)}{!isLoading && !data?.items.length && <Card className="grid min-h-64 place-items-center text-center"><div><Search className="mx-auto text-slate-300" size={30} /><h2 className="mt-4 font-bold">Nie znaleźliśmy promptów</h2><p className="mt-1 text-sm text-slate-500">Zmień kryteria wyszukiwania albo utwórz nowy, świadomie zapisany szkic.</p></div></Card>}</div>
  </>;
}
