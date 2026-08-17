const API_URL = import.meta.env.VITE_API_URL ?? "/api/v1";
let accessToken: string | null = null;
let csrfToken: string | null = null;

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) { super(message); }
}

function readErrorMessage(body: unknown): string {
  if (!body || typeof body !== "object" || !("detail" in body)) return "Wystąpił nieoczekiwany błąd.";
  const detail = body.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.flatMap((item) => item && typeof item === "object" && "msg" in item && typeof item.msg === "string" ? [item.msg] : []);
    return messages.length ? messages.join(" ") : "Sprawdź poprawność danych formularza.";
  }
  return "Wystąpił nieoczekiwany błąd.";
}

export const session = {
  set: (token: string | null, csrf: string | null) => { accessToken = token; csrfToken = csrf; },
  clear: () => { accessToken = null; csrfToken = null; },
  csrf: () => csrfToken ?? document.cookie.split("; ").find((item) => item.startsWith("csrf_token="))?.split("=")[1] ?? null,
};

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const csrf = session.csrf();
  if (csrf && ["POST", "PATCH", "PUT", "DELETE"].includes(options.method ?? "GET") && path.startsWith("/auth/")) headers.set("X-CSRF-Token", csrf);
  const response = await fetch(`${API_URL}${path}`, { ...options, headers, credentials: "include" });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, readErrorMessage(body));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const download = async (path: string, filename: string) => {
  const headers = new Headers();
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  const response = await fetch(`${API_URL}${path}`, { headers, credentials: "include" });
  if (!response.ok) throw new ApiError(response.status, "Nie udało się pobrać pliku.");
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url; link.download = filename; link.click(); URL.revokeObjectURL(url);
};
