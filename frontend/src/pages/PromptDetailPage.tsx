import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Clipboard, Download, Edit3, LoaderCircle, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { QualityReport } from "../components/prompt/QualityReport";
import { PageHeading } from "../components/layout/AppShell";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { categoryLabels, promptStatusLabel } from "../lib/prompts";
import { ApiError, api, download } from "../lib/api";
import type { Prompt } from "../types";

export function PromptDetailPage() {
  const { promptId = "" } = useParams();
  const queryClient = useQueryClient();
  const { data: prompt, isLoading, error } = useQuery({ queryKey: ["prompt", promptId], queryFn: () => api<Prompt>(`/prompts/${promptId}`), enabled: Boolean(promptId) });
  const [content, setContent] = useState("");
  const [editing, setEditing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => setContent(prompt?.content ?? ""), [prompt?.content]);
  const update = async (changes: Partial<Prompt>) => {
    if (!prompt) return;
    try {
      const next = await api<Prompt>(`/prompts/${prompt.id}`, { method: "PATCH", body: JSON.stringify(changes) });
      queryClient.setQueryData(["prompt", prompt.id], next);
      await queryClient.invalidateQueries({ queryKey: ["prompts"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      return next;
    } catch (reason) {
      setMessage(reason instanceof ApiError ? reason.message : "Nie udało się zapisać zmian.");
      return undefined;
    }
  };
  const copy = async () => {
    if (!prompt?.content) return;
    try {
      await navigator.clipboard.writeText(prompt.content);
      setCopied(true);
      setMessage("Prompt został skopiowany do schowka.");
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setMessage("Przeglądarka nie pozwoliła skopiować tekstu. Zaznacz go ręcznie.");
    }
  };

  if (isLoading) return <div className="grid min-h-64 place-items-center"><LoaderCircle className="animate-spin text-violet-600" size={26} /></div>;
  if (!prompt) return <Card className="grid min-h-64 place-items-center text-center"><div><h1 className="font-black">Nie znaleziono promptu</h1><p className="mt-2 text-sm text-slate-500">{error instanceof ApiError ? error.message : "Ten wpis mógł zostać usunięty."}</p><Link className="mt-4 inline-flex font-bold text-violet-600 hover:underline" to="/app/historia">Wróć do historii</Link></div></Card>;

  const isGenerated = prompt.status === "generated";
  return <>
    <PageHeading eyebrow="Biblioteka promptów" title="Szczegóły promptu" description="Otwórz pełną treść, skopiuj ją, wprowadź poprawki albo wróć do zapisanego szkicu." action={<Link to="/app/historia" className="inline-flex items-center rounded-xl border px-4 py-2.5 text-sm font-bold hover:bg-slate-50 dark:border-white/10 dark:hover:bg-white/5">Wróć do historii</Link>} />
    {message && <p role="status" className="mb-5 rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">{message}</p>}
    <div className="grid items-start gap-6 xl:grid-cols-[1fr_.55fr]">
      <Card className="overflow-hidden"><div className="flex flex-wrap items-start justify-between gap-3 border-b pb-4"><div><div className="flex flex-wrap gap-2"><Badge tone={isGenerated ? "green" : "amber"}>{promptStatusLabel(prompt.status)}</Badge>{isGenerated && <Badge tone="violet">Kompletność {prompt.quality_score}/100</Badge>}</div><h2 className="mt-3 text-xl font-black">{prompt.brief}</h2></div></div>
        {isGenerated ? <><div className="mt-5">{editing ? <textarea value={content} onChange={(event) => setContent(event.target.value)} className="input min-h-[460px] font-mono text-xs leading-relaxed" aria-label="Treść promptu do edycji" /> : <pre className="max-h-[560px] overflow-auto whitespace-pre-wrap rounded-xl bg-slate-950 p-5 font-mono text-xs leading-6 text-slate-100">{prompt.content}</pre>}</div><div className="mt-4 flex flex-wrap gap-2">{editing ? <Button onClick={async () => { const next = await update({ content }); if (next) { setEditing(false); setMessage("Zmiany w prompcie zostały zapisane."); } }}><Save size={16} />Zapisz zmiany</Button> : <Button variant="secondary" onClick={() => setEditing(true)}><Edit3 size={16} />Edytuj</Button>}<Button variant="secondary" onClick={() => void copy()}>{copied ? <Check size={16} className="text-emerald-500" /> : <Clipboard size={16} />}{copied ? "Skopiowano" : "Kopiuj"}</Button><Button variant="ghost" onClick={() => download(`/prompts/${prompt.id}/export?format=markdown`, "promptforge-prompt.md")}><Download size={16} />Markdown</Button><Button variant="ghost" onClick={() => download(`/prompts/${prompt.id}/export?format=pdf`, "promptforge-prompt.pdf")}><Download size={16} />PDF</Button></div></> : <DraftView prompt={prompt} />}
      </Card>
      <div className="space-y-6"><Card><h2 className="text-sm font-black">Informacje</h2><dl className="mt-4 space-y-3 text-sm"><Row label="Kategoria" value={categoryLabels[prompt.category] ?? prompt.category} /><Row label="Model" value={prompt.model_target === "both" ? "ChatGPT i Claude" : prompt.model_target === "chatgpt" ? "ChatGPT" : "Claude"} /><Row label="Poziom" value={prompt.level === "professional" ? "Profesjonalny" : prompt.level === "expert" ? "Ekspercki" : "Standardowy"} /></dl></Card>{isGenerated && <QualityReport prompt={prompt} />}</div>
    </div>
  </>;
}

function DraftView({ prompt }: { prompt: Prompt }) {
  const answered = Object.entries(prompt.answers);
  return <div className="mt-5"><h3 className="text-lg font-black">Ten szkic czeka na doprecyzowanie</h3><p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">Nie utworzyliśmy końcowego promptu. Wróć do szkicu i odpowiedz na pozostałe pytania.</p>{answered.length > 0 && <div className="mt-5 space-y-3"><h4 className="text-sm font-bold">Zapisane odpowiedzi</h4>{answered.map(([question, answer]) => <div key={question} className="rounded-xl bg-slate-50 p-3 text-sm dark:bg-white/5"><p className="font-bold">{question}</p><p className="mt-1 text-slate-500 dark:text-slate-400">{answer}</p></div>)}</div>}{prompt.questions.length > 0 && <div className="mt-5"><h4 className="text-sm font-bold">Pozostałe pytania</h4><ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-500 dark:text-slate-400">{prompt.questions.map((question) => <li key={question}>{question}</li>)}</ul></div>}<Link to={`/app/generator?szkic=${prompt.id}`} className="mt-6 inline-flex items-center rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-violet-500">Kontynuuj szkic</Link></div>;
}

function Row({ label, value }: { label: string; value: string }) {
  return <div className="flex items-start justify-between gap-3"><dt className="text-slate-500">{label}</dt><dd className="text-right font-bold">{value}</dd></div>;
}
