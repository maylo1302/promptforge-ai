from dataclasses import dataclass
from re import findall

from app.models import Prompt
from app.services.ai_providers import enhance_prompt


@dataclass(frozen=True)
class GenerationResult:
    content: str
    score: int
    analysis: dict[str, object]


@dataclass(frozen=True)
class TaskProfile:
    slug: str
    label: str
    role: str
    questions: tuple[tuple[str, str], ...]


class PromptEngine:
    """Turns a short brief into a task-specific prompt and a transparent input-quality score."""

    vague_terms = {"coś", "czegokolwiek", "pomóż", "zrób", "stwórz", "napisz"}
    generic_phrases = {"ma działać", "po prostu", "jakoś", "dobrze", "fajnie", "najlepiej", "wszystko", "szybko", "nie wiem", "dowolnie", "bez znaczenia"}
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
        "marketing": "strategiem marketingowym",
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
    category_requirements = {
        "programming": (
            "Rozdziel zakres MVP od funkcji późniejszych etapów.",
            "Zdefiniuj użytkowników, przepływy, dane, integracje i granice systemu.",
            "Podaj kryteria akceptacji oraz testy dla najważniejszych scenariuszy.",
        ),
        "business": (
            "Oddziel problem biznesowy, decyzje, ryzyka i mierzalne rezultaty.",
            "Zaproponuj kolejne kroki wraz z właścicielem, terminem i kryterium akceptacji.",
        ),
        "marketing": (
            "Zdefiniuj personę, kanały, komunikat, budżet i mierniki kampanii.",
            "Przygotuj warianty do testu oraz sposób interpretacji wyników.",
        ),
        "data_analysis": (
            "Opisz źródła danych, jakość danych, metryki i ograniczenia interpretacji.",
            "Oddziel obserwacje od wniosków i wskaż, czego dane nie potwierdzają.",
        ),
    }

    office_agent_profile = TaskProfile(
        slug="office_agent",
        label="agent pracy biurowej",
        role="architektem osobistych agentów pracy biurowej",
        questions=(
            ("narzedzia_dane", "Narzędzia i dane: Z jakich narzędzi (e-mail, kalendarz, dokumenty, zadania) agent ma korzystać i do jakich danych może mieć dostęp?"),
            ("rutyny", "Rutyny: Jakie powtarzalne obowiązki ma wykonywać codziennie lub cyklicznie? Podaj 2–3 przykłady."),
            ("autonomia", "Autonomia: Które działania agent może wykonywać sam, a które muszą zostać zatwierdzone przed wysłaniem, zmianą lub usunięciem?"),
            ("pamiec_prywatnosc", "Pamięć i prywatność: Co agent może zapamiętywać, jak długo oraz jakich danych wrażliwych nie wolno mu zapisywać ani ujawniać?"),
            ("bledy_sukces", "Błędy i sukces: Co agent ma zrobić przy braku danych lub błędzie oraz po czym poznasz, że działa poprawnie?"),
        ),
    )
    software_profile = TaskProfile(
        slug="software_product",
        label="produkt cyfrowy",
        role="architektem produktu i inżynierem oprogramowania",
        questions=(
            ("uzytkownicy", "Użytkownicy: Kto będzie korzystać z produktu i jakie zadanie ma wykonać w pierwszej wersji?"),
            ("mvp", "Zakres MVP: Jakie 3–5 funkcji są niezbędne na start, a co świadomie odkładamy na później?"),
            ("dane_integracje", "Dane i integracje: Jakie dane są przetwarzane oraz z jakimi systemami lub API produkt ma się łączyć?"),
            ("bezpieczenstwo", "Bezpieczeństwo: Kto ma dostęp do danych, jakie są ograniczenia prywatności i co wymaga autoryzacji?"),
            ("akceptacja", "Akceptacja: Po czym użytkownik i zespół poznają, że najważniejszy przepływ działa poprawnie?"),
        ),
    )
    marketing_profile = TaskProfile(
        slug="marketing_campaign",
        label="kampania marketingowa",
        role="strategiem kampanii marketingowych",
        questions=(
            ("persona", "Odbiorca: Do kogo mówimy, z jakim problemem i na jakim etapie decyzji?"),
            ("oferta", "Oferta: Co dokładnie promujemy, jaka jest główna korzyść i czym różni się od alternatyw?"),
            ("kanaly", "Kanały: Gdzie kampania ma się pojawić i jakie materiały są potrzebne dla każdego kanału?"),
            ("budzet", "Ograniczenia: Jaki jest budżet, termin oraz ograniczenia prawne lub wizerunkowe?"),
            ("metryki", "Sukces: Jakie mierniki i progi sukcesu będą decydować o kontynuacji lub zmianie kampanii?"),
        ),
    )
    data_profile = TaskProfile(
        slug="data_analysis",
        label="analiza danych",
        role="analitykiem danych i konsultantem decyzyjnym",
        questions=(
            ("pytanie", "Pytanie decyzyjne: Jaką konkretną decyzję ma wesprzeć analiza?"),
            ("zrodla", "Źródła: Jakie dane są dostępne, z jakiego okresu i jakie znasz ograniczenia ich jakości?"),
            ("metryki", "Metryki: Jakie wskaźniki, segmenty lub porównania są najważniejsze?"),
            ("odbiorca", "Odbiorca: Kto podejmie decyzję na podstawie analizy i jaki ma poziom wiedzy?"),
            ("format", "Rezultat: W jakiej formie ma być wynik — tabela, raport, wykresy czy rekomendacje z uzasadnieniem?"),
        ),
    )

    def classify_task(self, brief: str, category: str) -> TaskProfile | None:
        text = brief.lower()
        if (("biurow" in text or "administracyj" in text) and ("agent" in text or "asystent" in text)) or any(phrase in text for phrase in ("osobisty asystent", "agent do e-mail", "agent do mail")):
            return self.office_agent_profile
        if any(word in text for word in ("kampani", "reklam", "lead", "newsletter", "social media")) or category == "marketing":
            return self.marketing_profile
        if any(word in text for word in ("analiz", "dashboard", "raport danych", "zbiór danych")) or category == "data_analysis":
            return self.data_profile
        if category == "programming" or any(word in text for word in ("aplikac", "strona internet", "system", "api", "oprogramowanie")):
            return self.software_profile
        return None

    def profile_topic_evidence(self, topic: str, text: str) -> bool:
        markers = {
            "narzedzia_dane": ("e-mail", "email", "outlook", "gmail", "kalendarz", "calendar", "dokument", "drive", "notion", "zadani", "dane", "kontakt", "folder"),
            "rutyny": ("codzien", "co tydzień", "cyklicz", "regular", "powtarzal", "rano", "miesięcz"),
            "autonomia": ("zatwierdz", "akceptac", "samodziel", "autonom", "przed wysłaniem", "zgoda"),
            "pamiec_prywatnosc": ("pamię", "histori", "przechow", "dane osobowe", "wrażliw", "rodo", "prywat"),
            "bledy_sukces": ("błąd", "brak danych", "niepewn", "powiadom", "eskal", "kryter", "sukces", "mierzal", "test"),
            "uzytkownicy": ("użytkownik", "klient", "zespół", "dla "),
            "mvp": ("mvp", "pierwsza wers", "funkcj", "zakres"),
            "dane_integracje": ("dane", "api", "integrac", "baza", "system"),
            "bezpieczenstwo": ("dostęp", "uprawnien", "bezpiecze", "prywat", "autoryzac"),
            "akceptacja": ("kryter", "akceptac", "test", "działa poprawnie"),
            "persona": ("persona", "odbior", "klient", "grupa"),
            "oferta": ("oferta", "produkt", "korzy", "wyróż"),
            "kanaly": ("kanał", "social", "e-mail", "newsletter", "google", "linkedin"),
            "budzet": ("budżet", "termin", "limit", "data"),
            "metryki": ("kpi", "metryk", "konwers", "zasięg", "sprzedaż"),
            "pytanie": ("decyz", "pytanie", "sprawdzić", "porównać"),
            "zrodla": ("źródł", "dane", "plik", "baza", "okres"),
            "odbiorca": ("odbior", "zarząd", "zespół", "klient"),
            "format": self.format_markers,
        }
        return any(marker in text.lower() for marker in markers.get(topic, ()))

    def clarification_questions(self, brief: str, category: str) -> list[str]:
        profile = self.classify_task(brief, category)
        if profile:
            if profile.slug == "office_agent":
                return [question for _, question in profile.questions]
            missing = [question for topic, question in profile.questions if not self.profile_topic_evidence(topic, brief)]
            return missing[:5]

        words = findall(r"\w+", brief.lower())
        questions: list[str] = []
        if len(words) < 12 or len(set(words) & self.vague_terms) > 0:
            questions.append("Jaki konkretny rezultat ma powstać i jak będzie wykorzystywany?")
        if not any(term in brief.lower() for term in self.audience_markers):
            questions.append("Kim jest odbiorca rezultatu i jaki ma poziom wiedzy?")
        if not any(term in brief.lower() for term in self.format_markers):
            questions.append("W jakim formacie powinna być przedstawiona odpowiedź?")
        if category in {"programming", "business", "law", "medicine"}:
            questions.append("Jakie ograniczenia, dane wejściowe lub kryteria akceptacji są najważniejsze?")
        return questions[:4]

    def meaningful_words(self, text: str) -> list[str]:
        return [word for word in findall(r"\w+", text.lower()) if len(word) > 2 and word not in self.stop_words]

    def generic_hits(self, text: str) -> int:
        return sum(text.lower().count(phrase) for phrase in self.generic_phrases)

    def placeholder_answer_questions(self, answers: dict[str, str]) -> list[str]:
        return [question for question, answer in answers.items() if self.generic_hits(answer)]

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

    def profile_answers(self, prompt: Prompt, profile: TaskProfile) -> dict[str, str]:
        answers = prompt.answers or {}
        return {topic: answers.get(question, "").strip() for topic, question in profile.questions}

    def office_quality_assessment(self, prompt: Prompt, profile: TaskProfile) -> tuple[int, dict[str, object]]:
        answers = self.profile_answers(prompt, profile)
        combined = " ".join([prompt.brief, *answers.values()]).lower()
        goal = min(15, 3 + min(10, len(self.meaningful_words(prompt.brief))) + (2 if any(char.isdigit() for char in prompt.brief) else 0))
        completion = sum(bool(answer) for answer in answers.values()) / len(profile.questions)
        detail = sum(self.answer_detail(answer) for answer in answers.values()) / len(profile.questions)
        answers_score = round(7 * completion + 8 * detail)

        tool_score = round(8 * self.profile_topic_evidence("narzedzia_dane", answers["narzedzia_dane"]) + 7 * any(marker in answers["narzedzia_dane"].lower() for marker in ("dane", "kontakt", "folder", "dokument", "kalendarz")))
        routines_score = 10 if self.profile_topic_evidence("rutyny", answers["rutyny"]) else 0
        autonomy_score = 12 if self.profile_topic_evidence("autonomia", answers["autonomia"]) else 0
        memory_score = round(6 * self.profile_topic_evidence("pamiec_prywatnosc", answers["pamiec_prywatnosc"]) + 6 * any(marker in answers["pamiec_prywatnosc"].lower() for marker in ("wrażliw", "rodo", "prywat", "dane osobowe")))
        resilience_score = round(6 * any(marker in answers["bledy_sukces"].lower() for marker in ("błąd", "brak danych", "niepewn", "powiadom", "eskal")) + 6 * any(marker in answers["bledy_sukces"].lower() for marker in ("kryter", "sukces", "mierzal", "test")))
        parameter_score = min(9, sum(any(marker in combined for marker in markers) for markers in self.evidence_groups.values()) * 2 + (3 if any(char.isdigit() for char in combined) else 0))
        generic_penalty = min(30, self.generic_hits(combined) * 7)
        normalized_answers = [" ".join(self.meaningful_words(answer)) for answer in answers.values() if answer]
        duplicate_answers = max(0, len(normalized_answers) - len(set(normalized_answers)))
        repetition_penalty = min(12, duplicate_answers * 5)
        raw_score = goal + answers_score + tool_score + routines_score + autonomy_score + memory_score + resilience_score + parameter_score - generic_penalty - repetition_penalty
        score = max(0, min(100, raw_score))

        breakdown = {
            "Cel i zakres": goal,
            "Odpowiedzi na pytania": answers_score,
            "Narzędzia i dostęp do danych": tool_score,
            "Rutyny i obowiązki": routines_score,
            "Zakres autonomii": autonomy_score,
            "Pamięć i prywatność": memory_score,
            "Błędy i kryteria sukcesu": resilience_score,
            "Konkretne parametry": parameter_score,
            "Kara za ogólniki": -generic_penalty,
            "Kara za powtórzenia": -repetition_penalty,
        }
        missing: list[str] = []
        weaknesses: list[str] = []
        missing_map = {
            "Narzędzia i dostęp do danych": "Narzędzia, zakres danych i poziom dostępu.",
            "Rutyny i obowiązki": "Cykliczne obowiązki z częstotliwością i przykładem rezultatu.",
            "Zakres autonomii": "Działania automatyczne oraz wymagające zatwierdzenia.",
            "Pamięć i prywatność": "Zasady pamięci, retencji i ochrony danych wrażliwych.",
            "Błędy i kryteria sukcesu": "Reakcje na błąd, brak danych i mierzalne testy akceptacyjne.",
        }
        thresholds = {"Cel i zakres": 12, "Odpowiedzi na pytania": 12, "Narzędzia i dostęp do danych": 12, "Rutyny i obowiązki": 8, "Zakres autonomii": 10, "Pamięć i prywatność": 10, "Błędy i kryteria sukcesu": 10, "Konkretne parametry": 6}
        for name in missing_map:
            if breakdown[name] < thresholds[name]:
                weaknesses.append(f"Do dopracowania: {name.lower()}.")
                missing.append(missing_map[name])
        if generic_penalty:
            weaknesses.append("Wykryto odpowiedź pozorną lub ogólnik; nie zastępuje ona konkretnego wymagania.")
        if repetition_penalty:
            weaknesses.append("Powtarzające się odpowiedzi nie wnoszą dodatkowego kontekstu.")
        strengths = [f"Dobrze opisano: {name.lower()}." for name, value in breakdown.items() if name in thresholds and value >= thresholds[name]]
        return score, {
            "strengths": strengths or ["Opis zawiera podstawowy cel agenta."],
            "weaknesses": weaknesses,
            "missing_information": missing,
            "suggestions": ["Podaj jeden rzeczywisty przykład zadania agenta od wejścia do rezultatu.", "Zamień opis „ma działać” na regułę, uprawnienie albo mierzalny test."],
            "quality_breakdown": breakdown,
            "quality_explanation": "To ocena kompletności specyfikacji agenta biurowego: narzędzi, danych, rutyn, autonomii, pamięci, prywatności, błędów i kryteriów sukcesu. Nie ocenia jakości odpowiedzi modelu AI.",
        }

    def general_quality_assessment(self, prompt: Prompt) -> tuple[int, dict[str, object]]:
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
        return score, {
            "strengths": [f"Dobrze opisano: {name.lower()}." for name in strengths] or ["Brief zawiera podstawowy cel zadania."],
            "weaknesses": weaknesses,
            "missing_information": list(dict.fromkeys(missing)),
            "suggestions": ["Dodaj przykład poprawnego rezultatu.", "Zastąp ogólniki konkretnymi danymi, ograniczeniami lub kryteriami."],
            "quality_breakdown": breakdown,
            "quality_explanation": "To deterministyczna ocena kompletności opisu i odpowiedzi: cel, pokrycie pytań, dane, format, odbiorca i spójność. Nie jest oceną jakości odpowiedzi modelu AI.",
        }

    def quality_assessment(self, prompt: Prompt) -> tuple[int, dict[str, object]]:
        profile = self.classify_task(prompt.brief, prompt.category)
        if profile and profile.slug == "office_agent":
            return self.office_quality_assessment(prompt, profile)
        return self.general_quality_assessment(prompt)

    def answer_for_topic(self, prompt: Prompt, profile: TaskProfile, topic: str) -> str:
        for question_topic, question in profile.questions:
            if question_topic == topic:
                return (prompt.answers or {}).get(question, "Nie podano.").strip() or "Nie podano."
        return "Nie podano."

    def build_office_agent_prompt(self, prompt: Prompt, profile: TaskProfile, model_label: str) -> str:
        tools = self.answer_for_topic(prompt, profile, "narzedzia_dane")
        routines = self.answer_for_topic(prompt, profile, "rutyny")
        autonomy = self.answer_for_topic(prompt, profile, "autonomia")
        memory = self.answer_for_topic(prompt, profile, "pamiec_prywatnosc")
        resilience = self.answer_for_topic(prompt, profile, "bledy_sukces")
        return f"""# Specyfikacja agenta pracy biurowej dla {model_label}

## Rola i cel
Jesteś {profile.role}. Zaprojektuj osobistego agenta do codziennej pracy biurowej na podstawie poniższej specyfikacji. Nie dopisuj niepotwierdzonych integracji, uprawnień ani automatyzacji.

**Cel użytkownika:** {prompt.brief.strip()}

## Uzgodniona specyfikacja
- **Narzędzia i dane:** {tools}
- **Cykliczne obowiązki:** {routines}
- **Zakres autonomii i zatwierdzeń:** {autonomy}
- **Pamięć i prywatność:** {memory}
- **Błędy i kryteria sukcesu:** {resilience}

## Zasady projektowania agenta
1. Zanim agent wykona działanie zewnętrzne (wysłanie wiadomości, utworzenie wydarzenia, zmianę dokumentu lub zadania), sprawdza swoje uprawnienia i zasady zatwierdzania.
2. Agent rozdziela działania na: automatyczne, wymagające akceptacji oraz zabronione. Nie zgaduje brakujących danych ani odbiorcy wiadomości.
3. Pamięta wyłącznie informacje dozwolone w specyfikacji; dla danych wrażliwych stosuje minimalny zakres dostępu i nie ujawnia ich w podsumowaniach.
4. Przy błędzie, konflikcie terminu lub braku danych zatrzymuje ryzykowne działanie, opisuje problem, proponuje bezpieczny następny krok i prosi o decyzję, jeśli jest potrzebna.

## Przygotuj rezultat w tej kolejności
1. **Zakres MVP** — cele, użytkownik, granice i funkcje nieobjęte pierwszą wersją.
2. **Codzienne przepływy pracy** — dla każdego obowiązku: sygnał startu, dane wejściowe, kroki, wynik, właściciel zatwierdzenia i sytuacje wyjątkowe.
3. **Integracje oraz model uprawnień** — narzędzie, dozwolone odczyty/zapisy, zakres danych i wymagane potwierdzenie.
4. **Model pamięci** — co zapamiętywać, przez jaki czas, jak użytkownik może to sprawdzić lub usunąć.
5. **Obsługa błędów i braków danych** — konkretne reakcje, komunikaty dla użytkownika i zasady eskalacji.
6. **Mierzalne testy akceptacyjne** — minimum pięć scenariuszy w formacie: warunek początkowy → działanie agenta → oczekiwany rezultat → kryterium zaliczenia.

## Jakość odpowiedzi
- Każdy przepływ musi odwoływać się do podanych narzędzi i zasad autonomii.
- Oznacz założenia oraz elementy, których nie da się zaprojektować bez dalszych danych.
- Stawiaj na konkretne reguły i testowalne zachowania, nie na ogólne deklaracje typu „ma działać”.
"""

    def build_general_prompt(self, prompt: Prompt, model_label: str, level_label: str) -> str:
        context = "\n".join(f"- {question}: {answer}" for question, answer in (prompt.answers or {}).items()) or "- Brak dodatkowych odpowiedzi."
        role = self.category_roles.get(prompt.category, self.category_roles["other"])
        requirements = self.category_requirements.get(prompt.category, ("Zamień cel na konkretne kroki, dane wejściowe, ograniczenia i kryteria akceptacji.",))
        domain_requirements = "\n".join(f"- {item}" for item in requirements)
        return f"""# Prompt dla {model_label}

## Rola i cel
Jesteś {role}. Pracujesz na poziomie {level_label}.

**Cel:** {prompt.brief.strip()}

## Kontekst potwierdzony przez użytkownika
{context}

## Wymagania właściwe dla tego typu zadania
{domain_requirements}

## Sposób pracy
1. Najpierw wypisz potwierdzone fakty, założenia i brakujące dane krytyczne.
2. Nie zastępuj szczegółów ogólnymi poradami; każda rekomendacja ma wskazywać działanie, właściciela lub odbiorcę oraz kryterium weryfikacji.
3. Gdy dane są niepełne, przedstaw bezpieczny wariant i pytanie, które odblokuje decyzję.

## Format rezultatu
1. Krótkie podsumowanie decyzji lub rozwiązania.
2. Plan działań albo struktura rezultatu dopasowana do celu.
3. Ryzyka, zależności i założenia.
4. Mierzalne kryteria akceptacji oraz następne kroki.
"""

    def generate(self, prompt: Prompt) -> GenerationResult:
        model_label = {"chatgpt": "ChatGPT", "claude": "Claude", "both": "ChatGPT lub Claude"}[prompt.model_target]
        level_label = {"standard": "standardowym", "professional": "profesjonalnym", "expert": "eksperckim"}[prompt.level]
        profile = self.classify_task(prompt.brief, prompt.category)
        content = self.build_office_agent_prompt(prompt, profile, model_label) if profile and profile.slug == "office_agent" else self.build_general_prompt(prompt, model_label, level_label)
        content = enhance_prompt(content, prompt.model_target)
        score, analysis = self.quality_assessment(prompt)
        return GenerationResult(content=content, score=score, analysis=analysis)


prompt_engine = PromptEngine()
