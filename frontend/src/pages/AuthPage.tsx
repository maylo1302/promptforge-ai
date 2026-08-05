import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, KeyRound, LoaderCircle, Sparkles, UserPlus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { z } from "zod";
import { Logo } from "../components/Logo";
import { Button } from "../components/ui/button";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";

const loginSchema = z.object({
  email: z.string().email("Podaj prawidłowy adres e-mail."),
  password: z.string().min(1, "Podaj hasło."),
});
const registerSchema = z.object({
  firstName: z.string().trim().min(1, "Podaj imię."),
  lastName: z.string().trim().min(1, "Podaj nazwisko."),
  email: z.string().email("Podaj prawidłowy adres e-mail."),
  password: z.string().min(12, "Hasło musi mieć co najmniej 12 znaków."),
});
type LoginValues = z.infer<typeof loginSchema>;
type RegisterValues = z.infer<typeof registerSchema>;
type AuthMode = "login" | "register";

export function AuthPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<AuthMode>(searchParams.get("tryb") === "rejestracja" ? "register" : "login");
  const loginForm = useForm<LoginValues>({ resolver: zodResolver(loginSchema), defaultValues: { email: "", password: "" } });
  const registerForm = useForm<RegisterValues>({ resolver: zodResolver(registerSchema), defaultValues: { firstName: "", lastName: "", email: "", password: "" } });

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setSearchParams(nextMode === "register" ? { tryb: "rejestracja" } : {});
  };
  const loginSubmit = loginForm.handleSubmit(async (values) => {
    try {
      await login(values.email, values.password);
      navigate("/app");
    } catch (error) {
      loginForm.setError("root", { message: error instanceof ApiError ? error.message : "Nie udało się połączyć z serwerem." });
    }
  });
  const registerSubmit = registerForm.handleSubmit(async (values) => {
    try {
      await register(values.firstName, values.lastName, values.email, values.password);
      navigate("/app");
    } catch (error) {
      registerForm.setError("root", { message: error instanceof ApiError ? error.message : "Nie udało się utworzyć konta." });
    }
  });
  return <div className="grid min-h-screen lg:grid-cols-2">
    <aside className="relative hidden overflow-hidden bg-ink p-12 text-white lg:flex lg:flex-col">
      <div className="absolute -right-32 top-24 size-96 rounded-full bg-violet-500/30 blur-3xl" />
      <Logo link={false} />
      <div className="relative my-auto max-w-lg">
        <p className="eyebrow text-violet-300">PromptForge AI</p>
        <h1 className="mt-4 text-5xl font-black tracking-tight">Mniej zgadywania.<br />Więcej intencji.</h1>
        <p className="mt-5 max-w-md leading-relaxed text-slate-300">Twórz prompty z pełnym kontekstem, jasnymi ograniczeniami i konkretnymi kryteriami sukcesu.</p>
        <div className="mt-10 rounded-2xl border border-white/10 bg-white/5 p-5 text-sm"><Sparkles className="mb-3 text-violet-300" size={22} />„Generator najpierw zapyta o to, co naprawdę ma znaczenie.”</div>
      </div>
      <p className="text-sm text-slate-500">Twoja przestrzeń do świadomej pracy z AI.</p>
    </aside>
    <main className="flex items-center justify-center p-5 sm:p-10">
      <div className="w-full max-w-md">
        <Link to="/" className="mb-9 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-violet-600"><ArrowLeft size={16} />Wróć na stronę główną</Link>
        <div className="mb-7 lg:hidden"><Logo /></div>
        <p className="eyebrow">{mode === "login" ? "Witaj ponownie" : "Nowe konto"}</p>
        <h2 className="mt-2 text-3xl font-black">{mode === "login" ? "Zaloguj się do PromptForge" : "Zarejestruj się w PromptForge"}</h2>
        <p className="mt-2 text-sm text-slate-500">{mode === "login" ? "Twoja historia promptów czeka." : "Utwórz konto, aby zapisywać i rozwijać swoje prompty."}</p>

        {mode === "login" ? <form onSubmit={loginSubmit} className="mt-8 space-y-4">
          <Field label="Adres e-mail" error={loginForm.formState.errors.email?.message}><input className="input" type="email" autoComplete="email" placeholder="ty@firma.pl" {...loginForm.register("email")} /></Field>
          <Field label="Hasło" error={loginForm.formState.errors.password?.message}><input className="input" type="password" autoComplete="current-password" placeholder="••••••••••••" {...loginForm.register("password")} /></Field>
          <FormError message={loginForm.formState.errors.root?.message} />
          <Button type="submit" className="mt-2 w-full py-3" disabled={loginForm.formState.isSubmitting}>{loginForm.formState.isSubmitting ? <LoaderCircle className="animate-spin" size={17} /> : <KeyRound size={17} />}Zaloguj się</Button>
        </form> : <form onSubmit={registerSubmit} className="mt-8 space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Imię" error={registerForm.formState.errors.firstName?.message}><input className="input" autoComplete="given-name" placeholder="Jan" {...registerForm.register("firstName")} /></Field>
            <Field label="Nazwisko" error={registerForm.formState.errors.lastName?.message}><input className="input" autoComplete="family-name" placeholder="Kowalski" {...registerForm.register("lastName")} /></Field>
          </div>
          <Field label="Adres e-mail" error={registerForm.formState.errors.email?.message}><input className="input" type="email" autoComplete="email" placeholder="ty@firma.pl" {...registerForm.register("email")} /></Field>
          <Field label="Hasło" error={registerForm.formState.errors.password?.message}><input className="input" type="password" autoComplete="new-password" placeholder="Co najmniej 12 znaków" {...registerForm.register("password")} /></Field>
          <FormError message={registerForm.formState.errors.root?.message} />
          <Button type="submit" className="mt-2 w-full py-3" disabled={registerForm.formState.isSubmitting}>{registerForm.formState.isSubmitting ? <LoaderCircle className="animate-spin" size={17} /> : <UserPlus size={17} />}Zarejestruj się</Button>
        </form>}

        {mode === "login" && <Link to="/odzyskaj-haslo" className="mt-6 block text-center text-sm font-bold text-violet-600 hover:underline">Nie pamiętasz hasła?</Link>}
        <p className="mt-6 text-center text-sm text-slate-500">{mode === "login" ? "Nie masz jeszcze konta?" : "Masz już konto?"} <button type="button" onClick={() => switchMode(mode === "login" ? "register" : "login")} className="font-bold text-violet-600 hover:underline">{mode === "login" ? "Zarejestruj się" : "Zaloguj się"}</button></p>
      </div>
    </main>
  </div>;
}

function FormError({ message }: { message?: string }) {
  return message ? <p className="rounded-xl bg-rose-50 px-3 py-2.5 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-200">{message}</p> : null;
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return <label className="block"><span className="label">{label}</span>{children}{error && <span className="mt-1.5 block text-xs font-medium text-rose-600">{error}</span>}</label>;
}
