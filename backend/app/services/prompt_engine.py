from dataclasses import dataclass
from re import findall
from app.models import Prompt
from app.services.ai_providers import enhance_prompt


@dataclass(frozen=True)
class GenerationResult:
    content: str
    score: int
    analysis: dict[str, list[str]]


class PromptEngine:
    vague_terms = {"coś", "czegokolwiek", "pomóż", "zrób", "stwórz", "napisz"}

    def clarification_questions(self, brief: str, category: str) -> list[str]:
        words = findall(r"\w+", brief.lower())
        questions: list[str] = []
        if len(words) < 12 or len(set(words) & self.vague_terms) > 0:
            questions.append("Jaki konkretny rezultat ma powstać i jak będzie wykorzystywany?")
        if not any(term in brief.lower() for term in ("dla ", "odbior", "klient", "użytkownik", "zespół")):
            questions.append("Kim jest odbiorca rezultatu i jaki ma poziom wiedzy?")
        if not any(term in brief.lower() for term in ("format", "tabela", "lista", "pdf", "markdown", "json")):
            questions.append("W jakim formacie powinna być przedstawiona odpowiedź?")
        if category in {"programming", "business", "law", "medicine"}:
            questions.append("Jakie ograniczenia, dane wejściowe lub kryteria akceptacji są najważniejsze?")
        return questions[:3]

    def generate(self, prompt: Prompt) -> GenerationResult:
        context = "\n".join(f"- {question}: {answer}" for question, answer in prompt.answers.items()) or "- Brak dodatkowych odpowiedzi."
        model_label = {"chatgpt": "ChatGPT", "claude": "Claude", "both": "ChatGPT lub Claude"}[prompt.model_target]
        level_label = {"standard": "standardowym", "professional": "profesjonalnym", "expert": "eksperckim"}[prompt.level]
        content = f"""# Prompt dla {model_label}

## Rola
Jesteś doświadczonym specjalistą w kategorii: **{prompt.category}**. Pracujesz na poziomie {level_label} i podejmujesz przejrzyste, uzasadnione decyzje.

## Cel
{prompt.brief.strip()}

## Kontekst i doprecyzowania
{context}

## Wymagania
1. Najpierw krótko potwierdź rozumienie celu i wypisz przyjęte założenia.
2. Opracuj rezultat krok po kroku, stosując sprawdzone praktyki dla tej kategorii.
3. Gdy brakuje danych krytycznych, zadaj pytania zamiast ich wymyślać.
4. Podawaj konkretne, możliwe do wdrożenia rekomendacje.

## Ograniczenia
- Nie przedstawiaj niezweryfikowanych faktów jako pewników.
- Chroń dane wrażliwe; nie proś o sekrety, hasła ani klucze API.
- Nie używaj ogólników, jeżeli można wskazać mierzalne kryterium.

## Styl i ton
Pisz po polsku, jasno, rzeczowo i zwięźle. Dopasuj specjalistyczność języka do odbiorcy.

## Format odpowiedzi
1. Krótkie podsumowanie.
2. Główne rozwiązanie w logicznych sekcjach.
3. Tabela lub lista działań, gdy ułatwia podjęcie decyzji.
4. Ryzyka, założenia i kolejne kroki.

## Kryteria sukcesu i checklista
- [ ] Odpowiedź realizuje jasno zdefiniowany cel.
- [ ] Uwzględnia kontekst, odbiorcę i ograniczenia.
- [ ] Jest konkretna, kompletna i możliwa do użycia.
- [ ] Zaznacza obszary wymagające potwierdzenia.
"""
        content = enhance_prompt(content, prompt.model_target)
        richness = min(18, len(findall(r"\w+", prompt.brief)) // 4 + len(prompt.answers) * 3)
        score = min(100, 72 + richness + (5 if prompt.level == "expert" else 0))
        analysis = {
            "strengths": ["Prompt ma jasno wydzielone sekcje i kryteria sukcesu.", "Uwzględnia ograniczenia oraz bezpieczny sposób pracy."],
            "weaknesses": [] if len(prompt.answers) >= 2 else ["Liczba doprecyzowań jest ograniczona; wynik może wymagać dalszej iteracji."],
            "missing_information": [] if len(prompt.answers) >= 2 else ["Szczegółowe dane wejściowe lub przykłady oczekiwanego wyniku."],
            "suggestions": ["Dodaj przykład idealnej odpowiedzi, aby dodatkowo ustabilizować rezultat.", "Po pierwszym użyciu doprecyzuj kryteria akceptacji."],
        }
        return GenerationResult(content=content, score=score, analysis=analysis)


prompt_engine = PromptEngine()
