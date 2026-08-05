import { useQuery } from "@tanstack/react-query";
import { BarChart3, FileText, ShieldCheck, Users } from "lucide-react";
import { PageHeading } from "../components/layout/AppShell";
import { Badge } from "../components/ui/badge";
import { Card } from "../components/ui/card";
import { api } from "../lib/api";
import { formatDate } from "../lib/utils";
import type { User } from "../types";

type Stats = { users: number; prompts: number; generated_prompts: number; active_last_30_days: number };

export function AdminPage() {
  const stats = useQuery({ queryKey: ["admin-stats"], queryFn: () => api<Stats>("/admin/stats") });
  const users = useQuery({ queryKey: ["admin-users"], queryFn: () => api<User[]>("/admin/users") });
  const tiles = [["Użytkownicy", stats.data?.users, Users, "violet"], ["Wszystkie prompty", stats.data?.prompts, FileText, "green"], ["Wygenerowane", stats.data?.generated_prompts, BarChart3, "amber"], ["Aktywni (30 dni)", stats.data?.active_last_30_days, ShieldCheck, "violet"]] as const;
  return <><PageHeading eyebrow="Administracja" title="Stan platformy" description="Przegląd użytkowników i najważniejszych wskaźników przestrzeni PromptForge." /><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{tiles.map(([label, value, Icon, tone]) => <Card key={label}><div className={`grid size-10 place-items-center rounded-xl ${tone === "green" ? "bg-emerald-100 text-emerald-600" : tone === "amber" ? "bg-amber-100 text-amber-600" : "bg-violet-100 text-violet-600"}`}><Icon size={19} /></div><p className="mt-5 text-sm text-slate-500">{label}</p><p className="mt-1 text-3xl font-black">{stats.isLoading ? "—" : value ?? 0}</p></Card>)}</div><Card className="mt-7 overflow-hidden p-0"><div className="flex items-center justify-between p-5"><div><h2 className="font-black">Użytkownicy</h2><p className="mt-1 text-sm text-slate-500">Najnowsze konta na platformie.</p></div><Badge tone="violet">{users.data?.length ?? 0} widocznych</Badge></div><div className="overflow-x-auto border-t"><table className="w-full min-w-[620px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-400 dark:bg-white/[.035]"><tr><th className="px-5 py-3 font-bold">Użytkownik</th><th className="px-5 py-3 font-bold">Rejestracja</th><th className="px-5 py-3 font-bold">Rola</th><th className="px-5 py-3 font-bold">Status</th></tr></thead><tbody>{users.data?.map((user) => <tr className="border-t" key={user.id}><td className="px-5 py-4"><p className="font-bold">{user.first_name} {user.last_name}</p><p className="mt-1 text-xs text-slate-500">{user.email}</p></td><td className="px-5 py-4 text-slate-500">{formatDate(user.created_at)}</td><td className="px-5 py-4">{user.is_admin ? <Badge tone="violet">Administrator</Badge> : <Badge>Użytkownik</Badge>}</td><td className="px-5 py-4"><Badge tone="green">Aktywne</Badge></td></tr>)}</tbody></table>{!users.isLoading && !users.data?.length && <p className="p-8 text-center text-sm text-slate-500">Brak użytkowników do pokazania.</p>}</div></Card></>;
}
