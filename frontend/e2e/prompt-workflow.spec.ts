import { expect, test } from "@playwright/test";

test("użytkownik tworzy, kopiuje, odnajduje i usuwa prompt po odświeżeniu strony", async ({ browser }) => {
  const context = await browser.newContext();
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  const page = await context.newPage();
  const suffix = `${Date.now()}-${Math.floor(Math.random() * 100_000)}`;
  const brief = `Zaprojektuj osobistego agenta biurowego do organizacji pracy ${suffix}`;

  await page.goto("/logowanie?tryb=rejestracja");
  await page.getByLabel("Imię").fill("Test");
  await page.getByLabel("Nazwisko").fill("E2E");
  await page.getByLabel("Adres e-mail").fill(`e2e-${suffix}@example.com`);
  await page.getByLabel("Hasło").fill("BezpieczneHaslo-E2E-2026!");
  await page.getByRole("button", { name: "Zarejestruj się" }).click();
  await expect(page).toHaveURL(/\/app$/);

  await page.goto("/app/generator");
  const saveDraft = page.getByRole("button", { name: "Przeanalizuj i zapisz szkic" });
  await expect(saveDraft).toBeDisabled();
  await page.getByLabel("Co chcesz osiągnąć?").fill(brief);
  await expect(saveDraft).toBeEnabled();
  await saveDraft.click();
  await expect(page.getByText("Szkic został zapisany w historii.")).toBeVisible();

  const questionFields = page.locator('textarea[id^="generator-question-"]');
  await expect(questionFields).toHaveCount(5);
  const answers = [
    "Korzysta z Gmaila, Google Calendar, Google Docs i Asany; może czytać wyłącznie moje służbowe dane.",
    "Każdego ranka podsumowuje wiadomości i zadania, a w piątek przygotowuje raport tygodniowy.",
    "Może tworzyć szkice, lecz wysłanie e-maila, utworzenie wydarzenia, edycja lub usunięcie danych wymaga zatwierdzenia.",
    "Zapamiętuje preferencje przez 30 dni; nie zapisuje haseł, danych klientów ani numerów dokumentów.",
    "Przy braku danych prosi o doprecyzowanie; sukces to raport przed 9:00 i brak wysłania wiadomości bez akceptacji.",
  ];
  for (const [index, answer] of answers.entries()) await questionFields.nth(index).fill(answer);
  await page.getByRole("button", { name: "Wygeneruj kompletny prompt" }).click();
  await expect(page.getByRole("heading", { name: "Twój dopracowany prompt" })).toBeVisible();
  await expect(page.locator("pre")).toContainText("Specyfikacja agenta pracy biurowej");

  await page.getByRole("button", { name: "Kopiuj" }).click();
  await expect(page.getByRole("button", { name: "Skopiowano" })).toBeVisible();
  await expect(page.evaluate(() => navigator.clipboard.readText())).resolves.toContain("Specyfikacja agenta pracy biurowej");

  await page.reload();
  await expect(page.getByRole("heading", { name: "Opisz, co chcesz osiągnąć" })).toBeVisible();
  await page.goto("/app/historia");
  await expect(page.getByText("1 promptów")).toBeVisible();
  await page.getByRole("link", { name: new RegExp(brief) }).click();
  await expect(page.locator("pre")).toContainText("Mierzalne testy akceptacyjne");

  await page.goto("/app/historia");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Usuń prompt" }).click();
  await expect(page.getByText("Prompt został usunięty.")).toBeVisible();
  await expect(page.getByText("0 promptów")).toBeVisible();
  await page.reload();
  await expect(page.getByText("0 promptów")).toBeVisible();

  await context.close();
});
