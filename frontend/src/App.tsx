import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AdminPage } from "./pages/AdminPage";
import { AuthPage } from "./pages/AuthPage";
import { DashboardPage } from "./pages/DashboardPage";
import { GeneratorPage } from "./pages/GeneratorPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LandingPage } from "./pages/LandingPage";
import { ProfilePage } from "./pages/ProfilePage";
import { PromptDetailPage } from "./pages/PromptDetailPage";
import { PasswordRecoveryPage } from "./pages/PasswordRecoveryPage";
import { SettingsPage } from "./pages/SettingsPage";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 15_000 } } });

function Protected({ children }: { children: React.ReactNode }) { const { user, isLoading } = useAuth(); if (isLoading) return <div className="grid min-h-screen place-items-center text-sm text-slate-500">Przygotowujemy Twoją przestrzeń…</div>; return user ? <AppShell>{children}</AppShell> : <Navigate to="/logowanie" replace />; }
function AdminOnly() { const { user } = useAuth(); return user?.is_admin ? <AdminPage /> : <Navigate to="/app" replace />; }

export function App() { return <QueryClientProvider client={queryClient}><BrowserRouter><AuthProvider><Routes><Route path="/" element={<LandingPage />} /><Route path="/logowanie" element={<AuthPage />} /><Route path="/odzyskaj-haslo" element={<PasswordRecoveryPage />} /><Route path="/app" element={<Protected><DashboardPage /></Protected>} /><Route path="/app/generator" element={<Protected><GeneratorPage /></Protected>} /><Route path="/app/historia" element={<Protected><HistoryPage /></Protected>} /><Route path="/app/prompty/:promptId" element={<Protected><PromptDetailPage /></Protected>} /><Route path="/app/profil" element={<Protected><ProfilePage /></Protected>} /><Route path="/app/ustawienia" element={<Protected><SettingsPage /></Protected>} /><Route path="/app/admin" element={<Protected><AdminOnly /></Protected>} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></AuthProvider></BrowserRouter></QueryClientProvider>; }
