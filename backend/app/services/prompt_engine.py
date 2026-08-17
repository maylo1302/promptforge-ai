from dataclasses import dataclass
from re import findall

from app.models import Prompt
from app.services.ai_providers import enhance_prompt


@dataclass(frozen=True)
class GenerationResult:
    content: str
    score: int
    analysis: dict[str, object]


class PromptEngine:
    vague_terms = {"coś", "czegokolwiek", "pomóż", "zrób", "stwórz", "napisz"}
    generic_phrases = {"ma działać", "po prostu", "jakoś", "dobrze", "fajnie", "najlepiej", "wszystko", "szybko"}
    category_roles = {
        "programming": "inżynierem oprogramowania",
        "marketing": "specjalistą marketingu",
        "business": "analitykiem biznesowym",
        "copywriting": "copywriterem",
        "seo": "specjalistą SEO",
        "science": "analitykiem naukowym",
        "law": "specjalistą od analizy prawnej",
        "medicine": "specjalistą komunikacji medycznej",
        "data_analysis": "analitykiem danych",
        "translation": "tłumaczem i redaktorem",
        "education": "projektantem materiałów edukacyjnych",
        "other": "specjalistą dopasowanym do opisanego zadania",
    }

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

    def quality_assessment(self, prompt: Prompt) -> tuple[int, dict[str, object]]:
        """Measures completeness of inputs; it is not an AI-model score."""
        brief = prompt.brief.strip()
        answers = [answer.strip() for answer in prompt.answers.values() if answer.strip()]
        all_text = " ".join([brief, *answers]).lower()
        brief_words = findall(r"\w+", brief)
        answer_words = sum(len(findall(r"\w+", answer)) for answer in answers)
        generic_count = sum(all_text.count(phrase) for phrase in self.generic_phrases)
        concrete_markers = ("np.", "przykład", "termin", "budżet", "limit", "liczb", "data", "nie ", "mus", "zakres", "kryter")
        format_markers = ("format", "tabela", "lista", "markdown", "json", "pdf", "slajd", "raport")
        audience_markers = ("dla ", "odbior", "klient", "użytkownik", "zespół", "początkują")

        goal = min(30, 8 + min(18, len(brief_words)) + (4 if any(char.isdigit() for char in brief) else 0))
        context = min(25, min(15, answer_words // 4) + min(10, len(answers) * 4))
        constraints = min(20, sum(marker in all_text for marker in concrete_markers) * 4)
        format_score = 15 if any(marker in all_text for marker in format_markers) else 3
        audience_score = 10 if any(marker in all_text for marker in audience_markers) else 2
        vagueness_penalty = min(24, generic_count * 8)
        raw_score = goal + context + constraints + format_score + audience_score - vagueness_penalty
        score = max(20, min(100, raw_score))

        breakdown = {
            "Cel i zakres": goal,
            "Kontekst i dane wejściowe": context,
            "Ograniczenia i kryteria": constraints,
            "Format rezultatu": format_score,
            "Odbiorca": audience_score,
            "Kara za ogólniki": -vagueness_penalty,
        }
        thresholds = {"Cel i zakres": 22, "Kontekst i dane wejściowe": 16, "Ograniczenia i kryteria": 12, "Format rezultatu": 12, "Odbiorca": 8}
        strengths = [name for name, value in breakdown.items() if name in thresholds and value >= thresholds[name]]
        weaknesses: list[str] = []
        missing: list[str] = []
        if context < 16:
            weaknesses.append("Doprecyzowania są zbyt krótkie lub zbyt ogólne.")
            missing.append("Dane wejściowe, przykłady albo szczegóły użycia rezultatu.")
        if constraints < 12:
            weaknesses.append("Nie opisano wystarczająco ograniczeń ani kryteriów akceptacji.")
            missing.append("Ograniczenia, termin, budżet lub mierzalne kryteria sukcesu.")
        if format_score < 12:
            weaknesses.append("Format oczekiwanego rezultatu nie jest jasno określony.")
            missing.append("Preferowany format, np. tabela, lista, JSON lub raport.")
        if audience_score < 8:
            weaknesses.append("Nie wskazano odbiorcy ani poziomu wiedzy.")
            missing.append("Odbiorca, jego cel i poziom zaawansowania.")
        if vagueness_penalty:
            weaknesses.append("Wykryto ogólnikowe sformułowania; obniżają przewidywalność wyniku.")

        analysis = {
            "strengths": [f"Dobrze opisano: {name.lower()}." for name in strengths] or ["Brief zawiera podstawowy cel zadania."],
            "weaknesses": weaknesses,
            "missing_information": list(dict.fromkeys(missing)),
            "suggestions": ["Dodaj przykład poprawnego rezultatu.", "Zastąp ogólniki mierzalnymi wymaganiami."],
            "quality_breakdown": breakdown,
            "quality_explanation": "To ocena kompletności danych wejściowych, a nie ocena jakości odpowiedzi modelu AI.",
        }
        return score, analysis

    def generate(self, prompt: Prompt) -> GenerationResult:
        context = "\n".join(f"- {question}: {answer}" for question, answer in prompt.answers.items()) or "- Brak dodatkowych odpowiedzi."
        model_label = {"chatgpt": "ChatGPT", "claude": "Claude", "both": "ChatGPT lub Claude"}[prompt.model_target]
        level_label = {"standard": "standardowym", "professional": "profesjonalnym", "expert": "eksperckim"}[prompt.level]
        role = self.category_roles.get(prompt.category, self.category_roles["other"])
        content = f"""# Prompt dla {model_label}

## Rola
Jesteś {role}. Pracujesz na poziomie {level_label} i podejmujesz przejrzyste, uzasadnione decyzje.

## Cel
{prompt.brief.strip()}

## Kontekst i doprecyzowania
{context}

## Wymagania
1. Najpierw krótko potwierdź rozumienie celu i wypisz przyjęte założenia.
2. Opracuj rezultat krok po kroku, stosując sprawdzone praktyki dla tego zadania.
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
        score, analysis = self.quality_assessment(prompt)
        return GenerationResult(content=content, score=score, analysis=analysis)


prompt_engine = PromptEngine()
