import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, LoaderCircle, Save, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { PageHeading } from "../components/layout/AppShell";
import { Button } from "../components/ui/button";
import { Card, CardTitle } from "../components/ui/card";
import { useAuth } from "../context/AuthContext";
import { ApiError, api } from "../lib/api";

const profileSchema = z.object({ first_name: z.string().min(1, "Podaj imię."), last_name: z.string().min(1, "Podaj nazwisko."), avatar_url: z.string().url("Podaj prawidłowy adres URL.").or(z.literal("")) });

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const [message, setMessage] = useState<string | null>(null);
  const profile = useForm<z.infer<typeof profileSchema>>({ resolver: zodResolver(profileSchema), defaultValues: { first_name: user?.first_name ?? "", last_name: user?.last_name ?? "", avatar_url: user?.avatar_url ?? "" } });
  useEffect(() => { profile.reset({ first_name: user?.first_name ?? "", last_name: user?.last_name ?? "", avatar_url: user?.avatar_url ?? "" }); }, [user, profile]);
  const saveProfile = profile.handleSubmit(async (values) => { try { await api("/users/me", { method: "PATCH", body: JSON.stringify({ ...values, avatar_url: values.avatar_url || null }) }); await refreshUser(); setMessage("Profil został zapisany."); } catch (error) { setMessage(error instanceof ApiError ? error.message : "Nie udało się zapisać profilu."); } });
  return <>
    <PageHeading eyebrow="Konto" title="Twój profil" description="Zarządzaj wyłącznie danymi widocznymi na Twoim koncie. Ustawienia bezpieczeństwa znajdziesz w osobnej sekcji." />
    {message && <div role="status" className="mb-5 flex items-center gap-2 rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200"><CheckCircle2 size={17} />{message}</div>}
    <div className="grid items-start gap-6 lg:grid-cols-[1fr_.7fr]"><Card><CardTitle>Podstawowe informacje</CardTitle><form onSubmit={saveProfile} className="space-y-4"><div className="grid gap-4 sm:grid-cols-2"><Field label="Imię" error={profile.formState.errors.first_name?.message}><input className="input" autoComplete="given-name" {...profile.register("first_name")} /></Field><Field label="Nazwisko" error={profile.formState.errors.last_name?.message}><input className="input" autoComplete="family-name" {...profile.register("last_name")} /></Field></div><Field label="Zdjęcie profilowe (URL)" error={profile.formState.errors.avatar_url?.message}><input className="input" placeholder="https://…" {...profile.register("avatar_url")} /></Field><Field label="Adres e-mail"><input className="input cursor-not-allowed opacity-60" value={user?.email ?? ""} disabled /></Field><Button type="submit" disabled={profile.formState.isSubmitting}>{profile.formState.isSubmitting ? <LoaderCircle className="animate-spin" size={17} /> : <Save size={17} />}Zapisz profil</Button></form></Card><Card><div className="grid size-12 place-items-center rounded-2xl bg-violet-100 text-violet-600 dark:bg-violet-500/15"><UserRound size={22} /></div><h2 className="mt-5 text-xl font-black">{user?.first_name} {user?.last_name}</h2><p className="mt-1 text-sm text-slate-500">{user?.email}</p><div className="mt-6 border-t pt-5 text-sm"><span className="text-slate-500">Konto utworzone</span><p className="mt-1 font-bold">{user ? new Intl.DateTimeFormat("pl-PL", { dateStyle: "long" }).format(new Date(user.created_at)) : "—"}</p></div></Card></div>
  </>;
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return <label className="block"><span className="label">{label}</span>{children}{error && <span className="mt-1 block text-xs font-bold text-rose-600">{error}</span>}</label>;
}
