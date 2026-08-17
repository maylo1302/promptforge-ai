import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { Check, Clipboard, Download, Edit3, Heart, LoaderCircle, MessageCircleQuestion, Save, Sparkles, WandSparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useSearchParams } from "react-router-dom";
import { z } from "zod";
import { QualityReport } from "../components/prompt/QualityReport";
import { PageHeading } from "../components/layout/AppShell";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import { Card, CardTitle } from "../components/ui/card";
import { categoryOptions } from "../lib/prompts";
import { ApiError, api, download } from "../lib/api";
import type { Prompt } from "../types";

const schema = z.object({
  brief: z.string().trim().min(3, "Opisz cel w co najmniej trzech znakach.").max(8000),
  model_target: z.enum(["chatgpt", "claude", "both"]),
  level: z.enum(["standard", "professional", "expert"]),
  category: z.string().min(2),
});
type Values = z.infer<typeof schema>;

export function GeneratorPage() {
  const queryClient = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const draftId = searchParams.get("szkic");
  const [prompt, setPrompt] = useState<Prompt | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [editing, setEditing] = useState(false);
  const [copied, setCopied] = useState(false);
  const [loadingDraft, setLoadingDraft] = useState(false);
  const [answering, setAnswering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const form = useForm<Values>({ resolver: zodResolver(schema), mode: "onChange", defaultValues: { brief: "", model_target: "chatgpt", level: "professional", category: "programming" } });

  useEffect(() => {
    if (!draftId) return;
    let active = true;
    setLoadingDraft(true);
    setError(null);
    void api<Prompt>(`/prompts/${draftId}`)
      .then((next) => {
        if (!active) return;
        setPrompt(next);
        setAnswers(next.answers);
        form.reset({ brief: next.brief, model_target: next.model_target, level: next.level, category: next.category });
      })
      .catch((reason) => active && setError(reason instanceof ApiError ? reason.message : "Nie udało się otworzyć szkicu."))
      .finally(() => active && setLoadingDraft(false));
    return () => { active = false; };
  }, [draftId, form]);

  const create = form.handleSubmit(async (values) => {
    setError(null);
    setNotice(null);
    try {
      const next = await api<Prompt>("/prompts", { method: "POST", body: JSON.stringify(values) });
      setPrompt(next);
      setAnswers(next.answers);
      form.reset({ brief: next.brief, model_target: next.model_target, level: next.level, category: next.category });
      setEditing(false);
      setSearchParams({});
      await queryClient.invalidateQueries({ queryKey: ["prompts"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      setNotice("Szkic został zapisany w historii. Możesz teraz odpowiedzieć na pytania albo wrócić do niego później.");
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Nie udało się zapisać szkicu.");
    }
  });
  const answer = async () => {
    if (!prompt) return;
    setError(null);
    setAnswering(true);
    try {
      const next = await api<Prompt>(`/prompts/${prompt.id}/answers`, { method: "POST", body: JSON.stringify({ answers }) });
      setPrompt(next);
      setAnswers(next.answers);
      setNotice(next.status === "needs_clarification" ? "Dziękujemy. Na podstawie odpowiedzi dobraliśmy jeszcze brakujące pytania." : "Kontekst jest wystarczający — wygenerowaliśmy dopracowany prompt.");
      await queryClient.invalidateQueries({ queryKey: ["prompts"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Nie udało się zapisać odpowiedzi.");
    } finally {
      setAnswering(false);
    }
  };
  const update = async (changes: Partial<Prompt>) => {
    if (!prompt) return;
    setError(null);
    try {
      const next = await api<Prompt>(`/prompts/${prompt.id}`, { method: "PATCH", body: JSON.stringify(changes) });
      setPrompt(next);
      await queryClient.invalidateQueries({ queryKey: ["prompts"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    } catch (reason) {
      setError(reason instanceof ApiError ? reason.message : "Nie udało się zapisać zmian w prompcie.");
    }
  };
  const copy = async () => {
    if (!prompt?.content) return;
    try {
      await navigator.clipboard.writeText(prompt.content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Przeglądarka nie pozwoliła skopiować tekstu. Zaznacz go ręcznie.");
    }
  };
  const allAnswered = Boolean(prompt?.questions.length && prompt.questions.every((question) => answers[question]?.trim()));
  const currentValues = form.watch();
  const draftIsOutdated = Boolean(prompt && (
    currentValues.brief.trim() !== prompt.brief
    || currentValues.model_target !== prompt.model_target
    || currentValues.level !== prompt.level
    || currentValues.category !== prompt.category
  ));

  return <>
    <PageHeading eyebrow="Generator promptów" title={draftId ? "Kontynuuj zapisany szkic" : "Opisz, co chcesz osiągnąć"} description={draftId ? "Szkic został wcześniej zapisany. Uzupełnij brakujące odpowiedzi, aby go dokończyć." : "Nie musisz znać idealnego promptu. Zacznij od celu — pomożemy wydobyć kontekst, który zmienia wynik."} />
    {notice && <p role="status" className="mb-5 rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">{notice} <Link to="/app/historia" className="underline underline-offset-2">Otwórz historię</Link></p>}
    <div className="grid items-start gap-6 xl:grid-cols-[.9fr_1.1fr]">
      <Card><CardTitle>{draftId ? "Dane szkicu" : "Twój zamiar"}</CardTitle><form onSubmit={create} className="space-y-5">
        <div><label htmlFor="generator-brief" className="label">Co chcesz osiągnąć?</label><textarea id="generator-brief" aria-describedby="generator-brief-help" className="input min-h-48 resize-y leading-relaxed" placeholder="Np. Chcę stworzyć aplikację do zarządzania magazynem dla firmy handlowej." {...form.register("brief")} /><span id="generator-brief-help" className="mt-1.5 block text-xs text-slate-400">Po kliknięciu zapisujemy szkic w historii. Możesz wrócić do niego później.</span>{form.formState.errors.brief && <span className="mt-1 block text-xs font-bold text-rose-600">{form.formState.errors.brief.message}</span>}</div>
        <div className="grid gap-4 sm:grid-cols-2"><Select id="generator-model-target" label="Model docelowy" {...form.register("model_target")}>{[["chatgpt", "ChatGPT"], ["claude", "Claude"], ["both", "Oba modele"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</Select><Select id="generator-level" label="Poziom promptu" {...form.register("level")}>{[["standard", "Standard"], ["professional", "Profesjonalny"], ["expert", "Ekspercki"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</Select></div>
        <Select id="generator-category" label="Kategoria" {...form.register("category")}>{categoryOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</Select>
        {error && <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-200">{error}</p>}
        <Button type="submit" className="w-full py-3" disabled={!form.formState.isValid || form.formState.isSubmitting || loadingDraft}>{form.formState.isSubmitting ? <LoaderCircle className="animate-spin" size={17} /> : <WandSparkles size={17} />}{draftId ? "Utwórz nowy szkic" : "Przeanalizuj i zapisz szkic"}</Button>
      </form></Card>
      {loadingDraft && <Card className="grid min-h-64 place-items-center"><LoaderCircle className="animate-spin text-violet-600" size={24} /></Card>}
      {!loadingDraft && !prompt && <StarterPanel />}
      {!loadingDraft && draftIsOutdated && <OutdatedDraftPanel />}
      {!loadingDraft && !draftIsOutdated && prompt?.status === "needs_clarification" && <Questions prompt={prompt} answers={answers} setAnswers={setAnswers} onAnswer={answer} disabled={!allAnswered || answering} />}
      {!loadingDraft && !draftIsOutdated && prompt?.status === "generated" && <Result prompt={prompt} editing={editing} setEditing={setEditing} onUpdate={update} onCopy={copy} copied={copied} />}
    </div>
  </>;
}

function Select({ label, children, id, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string; children: React.ReactNode }) {
  return <label htmlFor={id}><span className="label">{label}</span><select id={id} className="input" {...props}>{children}</select></label>;
}

function StarterPanel() {
  return <Card className="relative overflow-hidden bg-gradient-to-br from-[#17112f] to-[#30226a] text-white dark:border-violet-400/20"><div className="absolute -right-16 -top-16 size-56 rounded-full bg-fuchsia-500/25 blur-3xl" /><Sparkles className="relative text-violet-200" size={28} /><h2 className="relative mt-8 text-3xl font-black tracking-tight">Zamieniamy intuicję w jasną instrukcję.</h2><ol className="relative mt-8 space-y-5 text-sm text-violet-100">{[["1", "Opisujesz cel własnymi słowami."], ["2", "Zapisujemy szkic i doprecyzowujemy brakujący kontekst."], ["3", "Otrzymujesz prompt oraz ocenę kompletności briefu."]].map(([number, copy]) => <li className="flex items-center gap-4" key={number}><span className="grid size-8 place-items-center rounded-full border border-violet-300/30 font-black">{number}</span>{copy}</li>)}</ol></Card>;
}

function OutdatedDraftPanel() {
  return <Card className="border-amber-200 bg-amber-50/70 dark:border-amber-400/20 dark:bg-amber-500/10"><div className="flex size-11 items-center justify-center rounded-xl bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-200"><Edit3 size={22} /></div><h2 className="mt-5 text-xl font-black">Opis został zmieniony</h2><p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">Widoczne wcześniej pytania należą do poprzedniego szkicu. Kliknij „Przeanalizuj i zapisz szkic”, aby utworzyć nowy szkic i otrzymać pytania dopasowane do aktualnego opisu.</p></Card>;
}

function Questions({ prompt, answers, setAnswers, onAnswer, disabled }: { prompt: Prompt; answers: Record<string, string>; setAnswers: (value: Record<string, string>) => void; onAnswer: () => Promise<void>; disabled: boolean }) {
  return <Card><div className="flex size-11 items-center justify-center rounded-xl bg-amber-100 text-amber-600 dark:bg-amber-500/15"><MessageCircleQuestion size={22} /></div><h2 className="mt-5 text-xl font-black">Pytania dopasowane do Twojego zadania</h2><p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">Pytamy wyłącznie o brakujący kontekst. Jeśli po tej rundzie nadal zabraknie ważnej informacji, pokażemy krótkie pytanie uzupełniające.</p><div className="mt-6 space-y-4">{prompt.questions.map((question, index) => { const fieldId = `generator-question-${index}`; return <label key={question} htmlFor={fieldId} className="block"><span className="label">{question}</span><textarea id={fieldId} value={answers[question] ?? ""} onChange={(event) => setAnswers({ ...answers, [question]: event.target.value })} className="input min-h-20 resize-y" placeholder="Wpisz konkretną odpowiedź…" /></label>; })}</div><Button onClick={() => void onAnswer()} disabled={disabled} className="mt-6 w-full"><Sparkles size={17} />Sprawdź kontekst i wygeneruj prompt</Button></Card>;
}

function Result({ prompt, editing, setEditing, onUpdate, onCopy, copied }: { prompt: Prompt; editing: boolean; setEditing: (value: boolean) => void; onUpdate: (changes: Partial<Prompt>) => Promise<void>; onCopy: () => Promise<void>; copied: boolean }) {
  const [content, setContent] = useState(prompt.content ?? "");
  useEffect(() => setContent(prompt.content ?? ""), [prompt.content]);
  return <div className="space-y-6"><Card className="overflow-hidden"><div className="flex flex-wrap items-center justify-between gap-3 border-b pb-4"><div><p className="eyebrow">Gotowe do użycia</p><h2 className="mt-1 text-xl font-black">Twój dopracowany prompt</h2></div><div className="flex gap-2"><Badge tone="green">Kompletność {prompt.quality_score}/100</Badge><Button variant="ghost" className="px-2.5" onClick={() => void onUpdate({ is_favorite: !prompt.is_favorite })} aria-label={prompt.is_favorite ? "Usuń z ulubionych" : "Dodaj do ulubionych"}><Heart size={18} fill={prompt.is_favorite ? "currentColor" : "none"} className={prompt.is_favorite ? "text-rose-500" : ""} /></Button></div></div><div className="mt-4">{editing ? <textarea value={content} onChange={(event) => setContent(event.target.value)} className="input min-h-[370px] font-mono text-xs leading-relaxed" aria-label="Treść promptu do edycji" /> : <pre className="max-h-[410px] overflow-auto whitespace-pre-wrap rounded-xl bg-slate-950 p-5 font-mono text-xs leading-6 text-slate-100">{prompt.content}</pre>}</div><div className="mt-4 flex flex-wrap gap-2">{editing ? <Button onClick={async () => { await onUpdate({ content }); setEditing(false); }}><Save size={16} />Zapisz zmiany</Button> : <Button variant="secondary" onClick={() => setEditing(true)}><Edit3 size={16} />Edytuj</Button>}<Button variant="secondary" onClick={() => void onCopy()}>{copied ? <Check size={16} className="text-emerald-500" /> : <Clipboard size={16} />}{copied ? "Skopiowano" : "Kopiuj"}</Button><Button variant="ghost" onClick={() => download(`/prompts/${prompt.id}/export?format=markdown`, "promptforge-prompt.md")}><Download size={16} />Markdown</Button><Button variant="ghost" onClick={() => download(`/prompts/${prompt.id}/export?format=pdf`, "promptforge-prompt.pdf")}><Download size={16} />PDF</Button><Link className="inline-flex items-center rounded-xl px-3 text-sm font-bold text-violet-600 hover:bg-violet-50 dark:hover:bg-violet-500/10" to={`/app/prompty/${prompt.id}`}>Szczegóły</Link></div></Card><QualityReport prompt={prompt} /></div>;
}
