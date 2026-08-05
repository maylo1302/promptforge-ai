import { ArrowLeft, CheckCircle2, KeyRound, LoaderCircle } from "lucide-react";
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Logo } from "../components/Logo";
import { Button } from "../components/ui/button";
import { ApiError, api } from "../lib/api";

export function PasswordRecoveryPage() {
  const [params] = useSearchParams();
  const token = params.get("token");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setError(null); setMessage(null); setLoading(true);
    try {
      if (token) {
        await api("/auth/password-reset/confirm", { method: "POST", body: JSON.stringify({ token, new_password: password }) });
        setMessage("Hasło zostało zmienione. Możesz się teraz zalogować.");
      } else {
        await api("/auth/password-reset", { method: "POST", body: JSON.stringify({ email }) });
        setMessage("Jeżeli konto istnieje, wysłaliśmy instrukcję odzyskania hasła.");
      }
    } catch (reason) { setError(reason instanceof ApiError ? reason.message : "Nie udało się wysłać żądania."); } finally { setLoading(false); }
  };
  return <div className="grid min-h-screen place-items-center p-5"><div className="w-full max-w-md"><Link to="/logowanie" className="mb-8 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-violet-600"><ArrowLeft size={16} />Wróć do logowania</Link><Logo /><div className="mt-9 surface p-7"><div className="grid size-11 place-items-center rounded-xl bg-violet-100 text-violet-600 dark:bg-violet-500/15"><KeyRound size={21} /></div><h1 className="mt-5 text-2xl font-black">{token ? "Ustaw nowe hasło" : "Odzyskaj dostęp"}</h1><p className="mt-2 text-sm leading-relaxed text-slate-500">{token ? "Wybierz nowe, unikalne hasło do swojego konta." : "Podaj adres e-mail. Otrzymasz bezpieczny link do ustawienia nowego hasła."}</p>{message ? <div className="mt-6 rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200"><CheckCircle2 className="mr-2 inline" size={17} />{message}</div> : <form onSubmit={submit} className="mt-6 space-y-4"><label><span className="label">{token ? "Nowe hasło" : "Adres e-mail"}</span><input required className="input" type={token ? "password" : "email"} value={token ? password : email} minLength={token ? 12 : undefined} onChange={(event) => token ? setPassword(event.target.value) : setEmail(event.target.value)} placeholder={token ? "Minimum 12 znaków" : "ty@firma.pl"} /></label>{error && <p className="text-sm font-medium text-rose-600">{error}</p>}<Button className="w-full" type="submit" disabled={loading}>{loading && <LoaderCircle className="animate-spin" size={17} />}{token ? "Zmień hasło" : "Wyślij link odzyskiwania"}</Button></form>}</div></div></div>;
}
