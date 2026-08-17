// @vitest-environment jsdom
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { HistoryPage } from "./HistoryPage";
import { GeneratorPage } from "./GeneratorPage";
import { PromptDetailPage } from "./PromptDetailPage";
import { api } from "../lib/api";
import type { Prompt } from "../types";

vi.mock("../lib/api", () => ({ api: vi.fn(), download: vi.fn() }));

const prompt: Prompt = {
  id: "prompt-1",
  brief: "Przygotuj plan wdrożenia aplikacji dla zespołu operacyjnego",
  model_target: "chatgpt",
  level: "professional",
  category: "business",
  status: "generated",
  questions: [],
  answers: {},
  content: "# Plan wdrożenia\n\nKonkretny etap pierwszy.",
  quality_score: 78,
  analysis: { strengths: ["Cel i zakres"], weaknesses: [], missing_information: [], suggestions: [], quality_breakdown: { "Cel i zakres": 26, "Kara za ogólniki": 0 }, quality_explanation: "Ocena kompletności danych wejściowych." },
  tags: [],
  is_favorite: false,
  created_at: "2026-08-17T10:00:00Z",
  updated_at: "2026-08-17T10:00:00Z",
};

const renderPage = (element: React.ReactNode, entry = "/app/historia") => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[entry]}>{element}</MemoryRouter></QueryClientProvider>);
};

afterEach(() => vi.restoreAllMocks());

describe("workflow promptów", () => {
  it("blokuje analizę pustego opisu i zapisuje szkic dopiero po jawnym kliknięciu", async () => {
    const draft: Prompt = { ...prompt, status: "needs_clarification", content: null, quality_score: null, questions: ["Jaki jest termin realizacji?"] };
    vi.mocked(api).mockResolvedValueOnce(draft);

    renderPage(<Routes><Route path="/app/generator" element={<GeneratorPage />} /></Routes>, "/app/generator");
    const submit = screen.getByRole("button", { name: "Przeanalizuj i zapisz szkic" });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Co chcesz osiągnąć?"), { target: { value: "Przygotuj plan wdrożenia dla zespołu operacyjnego." } });
    await waitFor(() => expect(submit).toBeEnabled());
    fireEvent.click(submit);

    await waitFor(() => expect(api).toHaveBeenCalledWith("/prompts", expect.objectContaining({ method: "POST" })));
    expect(await screen.findByText(/Szkic został zapisany w historii/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Zanim wygenerujemy prompt" })).toBeInTheDocument();
  });

  it("otwiera pełny prompt i kopiuje jego treść", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    vi.mocked(api).mockResolvedValueOnce(prompt);

    renderPage(<Routes><Route path="/app/prompty/:promptId" element={<PromptDetailPage />} /></Routes>, "/app/prompty/prompt-1");
    expect(await screen.findByText("Szczegóły promptu")).toBeInTheDocument();
    expect(screen.getByText(/Konkretny etap pierwszy/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Kopiuj" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(prompt.content));
    expect(screen.getByText("Prompt został skopiowany do schowka.")).toBeInTheDocument();
  });

  it("usuwa wpis i odświeża historię wraz z licznikiem", async () => {
    let deleted = false;
    vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.mocked(api).mockImplementation(async (path: string, options?: RequestInit) => {
      if (path.startsWith("/prompts?") && !deleted) return { items: [prompt], total: 1 };
      if (path.startsWith("/prompts?") && deleted) return { items: [], total: 0 };
      if (path === "/prompts/prompt-1" && options?.method === "DELETE") { deleted = true; return undefined; }
      throw new Error(`Nieobsługiwane żądanie ${path}`);
    });

    renderPage(<HistoryPage />);
    expect(await screen.findByText("1 promptów")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Usuń prompt" }));
    await waitFor(() => expect(screen.getByText("Prompt został usunięty.")).toBeInTheDocument());
    await waitFor(() => expect(screen.getByText("0 promptów")).toBeInTheDocument());
  });

  it("pokazuje bezpośrednią akcję kontynuowania zapisanego szkicu", async () => {
    const draft: Prompt = { ...prompt, status: "needs_clarification", content: null, quality_score: null, questions: ["Jaki jest termin realizacji?"] };
    vi.mocked(api).mockResolvedValueOnce({ items: [draft], total: 1 });

    renderPage(<HistoryPage />);
    const resume = await screen.findByRole("link", { name: "Kontynuuj szkic" });
    expect(resume).toHaveAttribute("href", "/app/generator?szkic=prompt-1");
  });
});
