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
    stop_words = {"aby", "ale", "bardzo", "będzie", "być", "dla", "jest", "jaki", "jakie", "jako", "lub", "ma", "mnie", "moja", "moje", "oraz", "po", "przez", "się", "ten", "tego", "tej", "to", "wraz", "zostać"}
    evidence_groups = {
        "ograniczenia": ("limit", "budżet", "nie ", "bez ", "zgodn", "wyłącznie", "ryzyko"),
        "dane": ("dane", "plik", "api", "źródł", "baza", "dokument", "brief"),
        "termin": ("termin", "data", "tydzień", "miesiąc", "deadline", "do końca"),
        "przykład": ("np.", "przykład", "wzór", "referenc"),
        "sukces": ("kryter", "mierzal", "akceptac", "sukces", "kpi"),
    }
    format_markers = ("format", "tabela", "lista", "markdown", "json", "pdf", "slajd", "raport")
    audience_markers = ("dla ", "odbior", "klient", "użytkownik", "zespół", "początkują", "programist", "zarząd")
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

    def meaningful_words(self, text: str) -> list[str]:
        return [word for word in findall(r"\w+", text.lower()) if len(word) > 2 and word not in self.stop_words]

    def generic_hits(self, text: str) -> int:
        return sum(text.lower().count(phrase) for phrase in self.generic_phrases)

    def answer_detail(self, answer: str) -> float:
        """Returns 0..1 for the informational density of one clarification answer."""
        if self.generic_hits(answer):
            return 0.0
        words = self.meaningful_words(answer)
        unique_words = len(set(words))
        evidence = sum(any(marker in answer.lower() for marker in markers) for markers in self.evidence_groups.values())
        evidence += int(any(marker in answer.lower() for marker in self.format_markers))
        evidence += int(any(marker in answer.lower() for marker in self.audience_markers))
        return min(1.0, unique_words / 12 + evidence * 0.18)

    def quality_assessment(self, prompt: Prompt) -> tuple[int, dict[str, object]]:
        """Scores the completeness and specificity of a user's inputs, not AI output quality."""
        brief = prompt.brief.strip()
        prompt_answers = prompt.answers or {}
        answers = [answer.strip() for answer in prompt_answers.values() if answer.strip()]
        all_text = " ".join([brief, *answers]).lower()
        brief_words = self.meaningful_words(brief)
        expected_answers = max(len(prompt.questions or []), len(answers), 1)
        completion_ratio = min(1.0, len(answers) / expected_answers)
        detail_ratio = sum(self.answer_detail(answer) for answer in answers) / len(answers) if answers else 0.0
        evidence_count = sum(any(marker in all_text for marker in markers) for markers in self.evidence_groups.values())
        has_format = any(marker in all_text for marker in self.format_markers)
        has_audience = any(marker in all_text for marker in self.audience_markers)

        goal = min(25, 4 + min(14, len(brief_words)) + (3 if len(set(brief_words)) >= 7 else 0) + (4 if any(char.isdigit() for char in brief) else 0))
        context = round(14 * completion_ratio + 11 * detail_ratio)
        constraints = min(20, evidence_count * 4 + (4 if any(char.isdigit() for char in all_text) else 0))
        format_score = 15 if has_format else 0
        audience_score = 10 if has_audience else 0
        normalized_answers = [" ".join(self.meaningful_words(answer)) for answer in answers]
        duplicate_answers = max(0, len(normalized_answers) - len(set(normalized_answers)))
        coherence = 0 if not answers else 3 if len(answers) == 1 else 5 if duplicate_answers == 0 else 1
        vagueness_penalty = min(30, self.generic_hits(all_text) * 6)
        repetition_penalty = min(12, duplicate_answers * 5)
        raw_score = goal + context + constraints + format_score + audience_score + coherence - vagueness_penalty - repetition_penalty
        score = max(0, min(100, raw_score))

        breakdown = {
            "Cel i zakres": goal,
            "Odpowiedzi na pytania": context,
            "Konkretne dane i ograniczenia": constraints,
            "Format rezultatu": format_score,
            "Odbiorca": audience_score,
            "Spójność odpowiedzi": coherence,
            "Kara za ogólniki": -vagueness_penalty,
            "Kara za powtórzenia": -repetition_penalty,
        }
        thresholds = {"Cel i zakres": 18, "Odpowiedzi na pytania": 18, "Konkretne dane i ograniczenia": 12, "Format rezultatu": 12, "Odbiorca": 8, "Spójność odpowiedzi": 4}
        strengths = [name for name, value in breakdown.items() if name in thresholds and value >= thresholds[name]]
        weaknesses: list[str] = []
        missing: list[str] = []
        if context < 18:
            weaknesses.append("Odpowiedzi nie pokrywają jeszcze wszystkich pytań lub są zbyt krótkie.")
            missing.append("Dane wejściowe, przykłady albo szczegóły użycia rezultatu.")
        if constraints < 12:
            weaknesses.append("Brakuje konkretnych danych, ograniczeń albo kryteriów akceptacji.")
            missing.append("Termin, budżet, dane wejściowe lub mierzalne kryteria sukcesu.")
        if not has_format:
            weaknesses.append("Format oczekiwanego rezultatu nie jest jasno określony.")
            missing.append("Preferowany format, np. tabela, lista, JSON lub raport.")
        if not has_audience:
            weaknesses.append("Nie wskazano odbiorcy ani poziomu wiedzy.")
            missing.append("Odbiorca, jego cel i poziom zaawansowania.")
        if vagueness_penalty:
            weaknesses.append("Wykryto ogólnikowe sformułowania; obniżają przewidywalność wyniku.")
        if repetition_penalty:
            weaknesses.append("Część odpowiedzi się powtarza, więc nie wnosi nowego kontekstu.")

        analysis = {
            "strengths": [f"Dobrze opisano: {name.lower()}." for name in strengths] or ["Brief zawiera podstawowy cel zadania."],
            "weaknesses": weaknesses,
            "missing_information": list(dict.fromkeys(missing)),
            "suggestions": ["Dodaj przykład poprawnego rezultatu.", "Zastąp ogólniki konkretnymi danymi, ograniczeniami lub kryteriami."],
            "quality_breakdown": breakdown,
            "quality_explanation": "To deterministyczna ocena kompletności opisu i odpowiedzi: cel, pokrycie pytań, dane, format, odbiorca i spójność. Nie jest oceną jakości odpowiedzi modelu AI.",
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
