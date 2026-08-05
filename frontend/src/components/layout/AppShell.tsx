import { BarChart3, BookOpen, LayoutDashboard, LogOut, Menu, Settings, ShieldCheck, Sparkles, UserRound } from "lucide-react";
import { useState, type ReactNode } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { cn } from "../../lib/utils";
import { Logo } from "../Logo";

const navigation = [
  ["/app", "Panel", LayoutDashboard], ["/app/generator", "Generator", Sparkles], ["/app/historia", "Historia", BookOpen], ["/app/profil", "Profil", UserRound], ["/app/ustawienia", "Ustawienia", Settings],
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const leave = async () => { await logout(); navigate("/"); };
  const sidebar = <aside className="flex h-full w-72 flex-col border-r bg-white p-5 dark:bg-[#0d0d13] dark:border-white/10"><div className="mb-10"><Logo /></div><nav className="space-y-1">{navigation.map(([to, label, Icon]) => <NavLink end={to === "/app"} onClick={() => setMobileOpen(false)} key={to} to={to} className={({ isActive }) => cn("flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition", isActive ? "bg-violet-600 text-white shadow-lg shadow-violet-500/20" : "text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-white")}><Icon size={18} />{label}</NavLink>)}{user?.is_admin && <NavLink onClick={() => setMobileOpen(false)} to="/app/admin" className={({ isActive }) => cn("flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition", isActive ? "bg-violet-600 text-white" : "text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-white/5")}><ShieldCheck size={18} />Administracja</NavLink>}</nav><div className="mt-auto rounded-2xl bg-violet-50 p-4 dark:bg-violet-500/10"><p className="text-xs font-bold text-violet-700 dark:text-violet-200">Twórz lepsze prompty</p><p className="mt-1 text-xs leading-relaxed text-violet-700/75 dark:text-violet-200/70">Doprecyzuj cel, a my zadbamy o strukturę.</p><Link to="/app/generator" className="mt-3 inline-flex text-xs font-bold text-violet-700 underline dark:text-violet-200">Otwórz generator</Link></div></aside>;
  return <div className="min-h-screen"><div className="fixed inset-y-0 left-0 z-30 hidden lg:block">{sidebar}</div>{mobileOpen && <div className="fixed inset-0 z-40 flex lg:hidden"><button className="absolute inset-0 bg-black/40" aria-label="Zamknij menu" onClick={() => setMobileOpen(false)} /><div className="relative">{sidebar}</div></div>}<main className="lg:pl-72"><header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b bg-[#fbfbfe]/85 px-5 backdrop-blur dark:bg-[#09090d]/85 dark:border-white/10 lg:px-10"><button className="rounded-xl p-2 hover:bg-slate-100 dark:hover:bg-white/10 lg:hidden" onClick={() => setMobileOpen(true)}><Menu size={20} /></button><div className="hidden items-center gap-2 text-sm text-slate-400 sm:flex"><BarChart3 size={16} />Przestrzeń robocza</div><div className="flex items-center gap-3"><button onClick={() => document.documentElement.classList.toggle("dark")} className="rounded-xl p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-white/10" aria-label="Zmień motyw">◐</button><Link to="/app/profil" className="hidden text-right sm:block"><p className="text-sm font-bold">{user?.first_name} {user?.last_name}</p><p className="text-xs text-slate-400">{user?.email}</p></Link><button onClick={leave} className="rounded-xl p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-500/10" aria-label="Wyloguj"><LogOut size={18} /></button></div></header><div className="mx-auto max-w-7xl p-5 lg:p-10">{children}</div></main></div>;
}

export function PageHeading({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="mb-8 flex flex-wrap items-end justify-between gap-4"><div>{eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}<h1 className="text-3xl font-black tracking-tight sm:text-4xl">{title}</h1>{description && <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500 dark:text-slate-400">{description}</p>}</div>{action}</div>;
}
