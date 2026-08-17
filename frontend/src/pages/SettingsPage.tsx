import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, KeyRound, LoaderCircle, Moon, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { PageHeading } from "../components/layout/AppShell";
import { Button } from "../components/ui/button";
import { Card, CardTitle } from "../components/ui/card";
import { ApiError, api } from "../lib/api";

const passwordSchema = z.object({ current_password: z.string().min(1, "Podaj obecne hasło."), new_password: z.string().min(12, "Hasło musi mieć co najmniej 12 znaków.") });

export function SettingsPage() {
  const [message, setMessage] = useState<string | null>(null);
  const password = useForm<z.infer<typeof passwordSchema>>({ resolver: zodResolver(passwordSchema), defaultValues: { current_password: "", new_password: "" } });
  const changePassword = password.handleSubmit(async (values) => { try { await api("/auth/change-password", { method: "POST", body: JSON.stringify(values) }); password.reset(); setMessage("Hasło zostało zmienione. Przy kolejnym użyciu zaloguj się nowym hasłem."); } catch (error) { password.setError("root", { message: error instanceof ApiError ? error.message : "Nie udało się zmienić hasła." }); } });
  return <>
    <PageHeading eyebrow="Preferencje" title="Ustawienia" description="Zarządzaj bezpieczeństwem konta i wyglądem aplikacji. Dane osobowe edytujesz w profilu." />
    {message && <div role="status" className="mb-5 flex items-center gap-2 rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200"><CheckCircle2 size={17} />{message}</div>}
    <div className="grid items-start gap-6 lg:grid-cols-[1fr_.7fr]"><Card><CardTitle>Zmiana hasła</CardTitle><form onSubmit={changePassword} className="space-y-4"><Field label="Obecne hasło" error={password.formState.errors.current_password?.message}><input className="input" type="password" autoComplete="current-password" {...password.register("current_password")} /></Field><Field label="Nowe hasło" error={password.formState.errors.new_password?.message}><input className="input" type="password" autoComplete="new-password" placeholder="Minimum 12 znaków" {...password.register("new_password")} /></Field>{password.formState.errors.root && <p role="alert" className="text-sm text-rose-600">{password.formState.errors.root.message}</p>}<Button type="submit" variant="secondary" disabled={password.formState.isSubmitting}>{password.formState.isSubmitting ? <LoaderCircle className="animate-spin" size={17} /> : <KeyRound size={17} />}Zmień hasło</Button></form></Card><div className="space-y-6"><Card><CardTitle>Wygląd</CardTitle><div className="mt-4 flex gap-3 text-sm"><Moon className="shrink-0 text-violet-500" size={19} /><div><strong>Motyw aplikacji</strong><p className="mt-1 text-slate-500">Wybierz tryb wygodny dla Twojego otoczenia.</p><button onClick={() => document.documentElement.classList.toggle("dark")} className="mt-3 font-bold text-violet-600 hover:underline">Przełącz jasny / ciemny</button></div></div></Card><Card><CardTitle>Bezpieczeństwo</CardTitle><div className="mt-4 flex gap-3 text-sm"><ShieldCheck className="shrink-0 text-emerald-500" size={19} /><p><strong>Sesja chroniona</strong><br /><span className="text-slate-500">Aplikacja używa krótkiego tokenu dostępu i odświeżania przez bezpieczne ciasteczko.</span></p></div></Card></div></div>
  </>;
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return <label className="block"><span className="label">{label}</span>{children}{error && <span className="mt-1 block text-xs font-bold text-rose-600">{error}</span>}</label>;
}
