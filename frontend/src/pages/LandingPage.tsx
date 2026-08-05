import { motion } from "framer-motion";
import { CheckCircle2, ChevronDown, FileText, Layers3, ShieldCheck, Sparkles, UserPlus, UserRound } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Logo } from "../components/Logo";
import { Button } from "../components/ui/button";

const features = [
  ["Inteligentne doprecyzowanie", "Zanim powstanie prompt, system wykrywa brakujące informacje i zadaje trafne pytania.", Sparkles],
  ["Struktura, która działa", "Role, kontekst, wymagania, ograniczenia i kryteria sukcesu w jednym gotowym szablonie.", Layers3],
  ["Ocena jakości", "Przejrzysta punktacja oraz sugestie pomagają iterować prompt przed użyciem modelu.", CheckCircle2],
  ["Historia i eksport", "Przechowuj, taguj i eksportuj najlepsze prompty do Markdown lub PDF.", FileText],
] as const;

const faqs = [
  ["Czy PromptForge działa z ChatGPT i Claude?", "Tak. W generatorze wybierasz ChatGPT, Claude albo oba modele. Prompt ma niezależną, czytelną strukturę."],
  ["Czy muszę podawać klucz API?", "Nie do pracy z generatorem struktury. Klucze OpenAI i Anthropic są opcjonalne i konfigurujesz je wyłącznie po stronie serwera."],
  ["Czy mogę wrócić do wcześniejszego promptu?", "Tak. Każda praca zapisuje się w historii; możesz ją wyszukać, oznaczyć jako ulubioną, poprawić i wyeksportować."],
];

export function LandingPage() {
  const [openFaq, setOpenFaq] = useState(0);
  return <div className="overflow-hidden">
    <header className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 lg:px-10">
      <Logo />
      <nav className="hidden items-center gap-7 text-sm font-semibold text-slate-500 md:flex"><a href="#funkcje" className="hover:text-slate-950 dark:hover:text-white">Funkcje</a><a href="#faq" className="hover:text-slate-950 dark:hover:text-white">FAQ</a></nav>
      <div className="flex items-center gap-2"><Link to="/logowanie?tryb=rejestracja"><Button variant="ghost"><UserPlus size={16} />Zarejestruj się</Button></Link><Link to="/logowanie"><Button><UserRound size={16} />Zaloguj się</Button></Link></div>
    </header>
    <main>
      <section className="relative mx-auto max-w-7xl px-5 pb-24 pt-16 text-center lg:px-10 lg:pb-32 lg:pt-24">
        <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[460px] w-[760px] -translate-x-1/2 rounded-full bg-violet-400/20 blur-3xl dark:bg-violet-500/15" />
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="mx-auto inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-1.5 text-xs font-bold text-violet-700 dark:border-violet-400/20 dark:bg-violet-400/10 dark:text-violet-200"><Sparkles size={14} />Prompt engineering bez zgadywania</motion.div>
        <motion.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .08 }} className="mx-auto mt-7 max-w-4xl text-5xl font-black tracking-[-.055em] sm:text-6xl lg:text-7xl">Twórz prompty, które <span className="bg-gradient-to-r from-violet-600 to-fuchsia-500 bg-clip-text text-transparent">prowadzą do celu.</span></motion.h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-500 dark:text-slate-400">PromptForge AI zamienia nieprecyzyjny pomysł w kompletną instrukcję dla ChatGPT i Claude — z kontekstem, kryteriami sukcesu i kontrolą jakości.</p>
        <div className="mx-auto mt-12 grid max-w-4xl grid-cols-1 gap-3 rounded-[2rem] border bg-white/80 p-4 text-left shadow-glow dark:bg-white/[.045] md:grid-cols-3">
          <div className="rounded-2xl bg-violet-600 p-5 text-white md:col-span-2"><p className="text-sm font-bold text-violet-100">Twój opis</p><p className="mt-3 text-xl font-semibold leading-relaxed">„Chcę stworzyć aplikację do zarządzania magazynem.”</p><div className="mt-7 flex items-center gap-2 text-sm text-violet-100"><Sparkles size={16} />PromptForge prosi o kluczowe szczegóły</div></div>
          <div className="rounded-2xl bg-slate-50 p-5 dark:bg-white/5"><p className="text-sm font-bold">Gotowa struktura</p><ul className="mt-4 space-y-2 text-sm text-slate-500 dark:text-slate-400">{["Rola i cel", "Kontekst", "Ograniczenia", "Checklista"].map((item) => <li key={item} className="flex gap-2"><CheckCircle2 size={16} className="text-emerald-500" />{item}</li>)}</ul></div>
        </div>
      </section>
      <section id="funkcje" className="border-y bg-slate-50/70 py-24 dark:bg-white/[.025]"><div className="mx-auto max-w-7xl px-5 lg:px-10"><p className="eyebrow">Mniej prób. Lepsze wyniki.</p><div className="mt-3 flex flex-wrap items-end justify-between gap-6"><h2 className="max-w-xl text-4xl font-black tracking-tight">Od pomysłu do promptu gotowego do działania.</h2><p className="max-w-sm text-sm leading-relaxed text-slate-500">Jeden uporządkowany proces zamiast wielokrotnego poprawiania poleceń metodą prób i błędów.</p></div><div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{features.map(([title, description, Icon], index) => <motion.article initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: index * .06 }} key={title} className="surface p-6"><div className="grid size-11 place-items-center rounded-xl bg-violet-100 text-violet-600 dark:bg-violet-400/15 dark:text-violet-300"><Icon size={21} /></div><h3 className="mt-5 font-bold">{title}</h3><p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{description}</p></motion.article>)}</div></div></section>
      <section id="faq" className="border-t bg-slate-50/70 py-24 dark:bg-white/[.025]"><div className="mx-auto max-w-3xl px-5"><p className="eyebrow text-center">FAQ</p><h2 className="mt-3 text-center text-4xl font-black tracking-tight">Pytania, zanim zaczniesz</h2><div className="mt-10 space-y-3">{faqs.map(([question, answer], index) => <article key={question} className="surface overflow-hidden"><button onClick={() => setOpenFaq(index === openFaq ? -1 : index)} className="flex w-full items-center justify-between gap-5 p-5 text-left font-bold">{question}<ChevronDown className={openFaq === index ? "rotate-180 transition" : "transition"} size={18} /></button>{openFaq === index && <p className="border-t px-5 pb-5 pt-4 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{answer}</p>}</article>)}</div></div></section>
    </main>
    <footer className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-9 text-sm text-slate-500 lg:px-10"><Logo /><p>© 2026 PromptForge AI. Projektuj instrukcje z intencją.</p><span className="flex items-center gap-2"><ShieldCheck size={16} className="text-emerald-500" />Bezpieczna przestrzeń pracy</span></footer>
  </div>;
}
