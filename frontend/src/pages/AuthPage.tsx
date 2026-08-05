import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, KeyRound, LoaderCircle, Sparkles } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { Logo } from "../components/Logo";
import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";

const loginSchema = z.object({ email: z.string().email("Podaj prawidłowy adres e-mail."), password: z.string().min(1, "Podaj hasło.") });
type LoginValues = z.infer<typeof loginSchema>;

export function AuthPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const form = useForm<LoginValues>({ resolver: zodResolver(loginSchema), defaultValues: { email: "", password: "" } });
  const submit = form.handleSubmit(async (values) => { try { await login(values.email, values.password); navigate("/app"); } catch (error) { form.setError("root", { message: error instanceof ApiError ? error.message : "Nie udało się połączyć z serwerem." }); } });
  return <div className="grid min-h-screen lg:grid-cols-2"><div className="relative hidden overflow-hidden bg-ink p-12 text-white lg:flex lg:flex-col"><div className="absolute -right-32 top-24 size-96 rounded-full bg-violet-500/30 blur-3xl" /><Logo link={false} /><div className="relative my-auto max-w-lg"><p className="eyebrow text-violet-300">PromptForge AI</p><h1 className="mt-4 text-5xl font-black tracking-tight">Mniej zgadywania.<br />Więcej intencji.</h1><p className="mt-5 max-w-md leading-relaxed text-slate-300">Twórz prompty z pełnym kontekstem, jasnymi ograniczeniami i konkretnymi kryteriami sukcesu.</p><div className="mt-10 rounded-2xl border border-white/10 bg-white/5 p-5 text-sm"><Sparkles className="mb-3 text-violet-300" size={22} />„Generator najpierw zapyta o to, co naprawdę ma znaczenie.”</div></div><p className="text-sm text-slate-500">Twoja przestrzeń do świadomej pracy z AI.</p></div><div className="flex items-center justify-center p-5 sm:p-10"><div className="w-full max-w-md"><Link to="/" className="mb-9 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-violet-600"><ArrowLeft size={16} />Wróć na stronę główną</Link><div className="mb-7 lg:hidden"><Logo /></div><p className="eyebrow">Witaj ponownie</p><h2 className="mt-2 text-3xl font-black">Zaloguj się do PromptForge</h2><p className="mt-2 text-sm text-slate-500">Twoja historia promptów czeka.</p><form onSubmit={submit} className="mt-8 space-y-4"><Field label="Adres e-mail" error={form.formState.errors.email?.message}><input className="input" type="email" autoComplete="email" placeholder="ty@firma.pl" {...form.register("email")} /></Field><Field label="Hasło" error={form.formState.errors.password?.message}><input className="input" type="password" autoComplete="current-password" placeholder="••••••••••••" {...form.register("password")} /></Field>{form.formState.errors.root && <p className="rounded-xl bg-rose-50 px-3 py-2.5 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-200">{form.formState.errors.root.message}</p>}<Button type="submit" className="mt-2 w-full py-3" disabled={form.formState.isSubmitting}>{form.formState.isSubmitting ? <LoaderCircle className="animate-spin" size={17} /> : <KeyRound size={17} />}Zaloguj się</Button></form><Link to="/odzyskaj-haslo" className="mt-6 block text-center text-sm font-bold text-violet-600 hover:underline">Nie pamiętasz hasła?</Link></div></div></div>;
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) { return <label className="block"><span className="label">{label}</span>{children}{error && <span className="mt-1.5 block text-xs font-medium text-rose-600">{error}</span>}</label>; }
