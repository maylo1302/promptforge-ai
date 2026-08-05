import { cn } from "../../lib/utils";

export function Badge({ children, tone = "neutral" }: { children: React.ReactNode; tone?: "neutral" | "violet" | "green" | "amber" }) {
  const tones = { neutral: "bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300", violet: "bg-violet-100 text-violet-700 dark:bg-violet-500/20 dark:text-violet-200", green: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200", amber: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-100" };
  return <span className={cn("inline-flex rounded-full px-2.5 py-1 text-xs font-semibold", tones[tone])}>{children}</span>;
}

