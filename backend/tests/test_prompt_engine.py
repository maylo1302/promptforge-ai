from app.models import Prompt
from app.services.prompt_engine import prompt_engine


def test_brief_without_context_requires_clarification() -> None:
    questions = prompt_engine.clarification_questions("Chcę napisać książkę", "other")
    assert len(questions) >= 2


def test_questions_match_detected_domain_and_skip_already_described_context() -> None:
    legal = prompt_engine.classify_task("Przygotuj analizę umowy najmu dla firmy w Polsce.", "other")
    assert legal is not None
    assert legal.slug == "legal_analysis"
    assert any(question.startswith("Prawo właściwe") for question in prompt_engine.clarification_questions("Przygotuj analizę umowy najmu dla firmy w Polsce.", "other"))

    complete_translation = (
        "Przetłumacz opis produktu z polskiego na angielski dla klientów B2B w Wielkiej Brytanii. "
        "Tekst ma mieć formalny, techniczny ton, zachować nazwy własne i glosariusz marki, "
        "tabelę oraz limity znaków z pliku źródłowego. Rezultat wykorzysta dział sprzedaży w katalogu online."
    )
    assert prompt_engine.classify_task(complete_translation, "other").slug == "translation"
    assert prompt_engine.clarification_questions(complete_translation, "other") == []


def test_translation_request_is_not_mistaken_for_legal_analysis_due_to_a_regulation_document() -> None:
    brief = (
        "Przetłumacz regulamin sklepu internetowego z polskiego na angielski brytyjski. "
        "Odbiorcami są klienci w Wielkiej Brytanii. Zachowaj formalny styl oraz strukturę nagłówków. "
        "Wynik zwróć w Markdown."
    )

    profile = prompt_engine.classify_task(brief, "other")
    assert profile is not None
    assert profile.slug == "translation"
    questions = prompt_engine.clarification_questions(brief, "other")
    assert len(questions) == 1
    assert questions[0].startswith("Terminologia")


def test_translation_takes_priority_over_a_legal_document_or_legal_style() -> None:
    brief = (
        "Przetłumacz regulamin sklepu internetowego z polskiego na angielski brytyjski. "
        "Odbiorcami są klienci w Wielkiej Brytanii. Zachowaj formalny, prawny styl oraz strukturę nagłówków. "
        "Wynik zwróć w Markdown."
    )

    profile = prompt_engine.classify_task(brief, "other")
    assert profile is not None
    assert profile.slug == "translation"
    questions = prompt_engine.clarification_questions(brief, "other")
    assert len(questions) == 1
    assert questions[0].startswith("Terminologia")


def test_follow_up_questions_only_cover_the_remaining_gap() -> None:
    brief = "Przetłumacz instrukcję obsługi produktu dla klientów biznesowych."
    questions = prompt_engine.clarification_questions(brief, "translation")
    answers = {
        next(question for question in questions if question.startswith("Języki")): "Z polskiego na angielski.",
        next(question for question in questions if question.startswith("Odbiorca")): "Dla administratorów IT w firmach korzystających z urządzenia.",
        next(question for question in questions if question.startswith("Rejestr")): "Formalny i techniczny, zgodny z instrukcją producenta.",
        next(question for question in questions if question.startswith("Terminologia")): "Nazwy marki, modele urządzeń i terminy z glosariusza producenta pozostają bez zmian.",
    }
    follow_up = prompt_engine.clarification_questions(brief, "translation", answers)
    assert follow_up == [next(question for question in questions if question.startswith("Format"))]


def test_generator_creates_structured_prompt() -> None:
    prompt = Prompt(brief="Stwórz plan wdrożenia aplikacji do zarządzania magazynem dla zespołu operacyjnego.", model_target="chatgpt", level="professional", category="business", answers={"Jaki format?": "Tabela etapów z ryzykami"})
    result = prompt_engine.generate(prompt)
    assert "## Rola i cel" in result.content
    assert "## Wymagania właściwe dla tego typu zadania" in result.content
    assert 0 <= result.score <= 100
    assert "Kara za ogólniki" in result.analysis["quality_breakdown"]


def test_generic_answers_receive_a_low_completeness_score() -> None:
    prompt = Prompt(
        brief="Chcę zbudować prostą aplikację.",
        model_target="chatgpt",
        level="professional",
        category="programming",
        answers={"Rezultat": "ma działać", "Odbiorca": "ma działać", "Format": "ma działać"},
    )
    result = prompt_engine.generate(prompt)
    assert result.score < 35
    assert result.analysis["quality_breakdown"]["Kara za ogólniki"] < 0
    assert result.analysis["quality_breakdown"]["Kara za powtórzenia"] < 0


def test_specific_answers_score_higher_than_generic_ones() -> None:
    generic = Prompt(
        brief="Chcę zbudować prostą aplikację.",
        model_target="chatgpt",
        level="professional",
        category="programming",
        questions=["Rezultat", "Odbiorca", "Format"],
        answers={"Rezultat": "ma działać", "Odbiorca": "ma działać", "Format": "ma działać"},
    )
    specific = Prompt(
        brief="Przygotuj plan wdrożenia aplikacji do zarządzania magazynem dla 20-osobowego zespołu operacyjnego do 30 września.",
        model_target="chatgpt",
        level="professional",
        category="business",
        questions=["Rezultat", "Odbiorca", "Format"],
        answers={
            "Rezultat": "Plan etapów wdrożenia z właścicielami zadań, ryzykami i kryteriami akceptacji.",
            "Odbiorca": "Kierownik magazynu i zespół operacyjny pracujący na zmianach.",
            "Format": "Tabela z terminami, budżetem, zależnościami i listą działań na każdy tydzień.",
        },
    )

    generic_result = prompt_engine.generate(generic)
    specific_result = prompt_engine.generate(specific)
    assert specific_result.score >= 75
    assert specific_result.score >= generic_result.score + 45
    assert specific_result.analysis["quality_breakdown"]["Kara za ogólniki"] == 0


def test_office_agent_uses_five_domain_questions_and_specialized_prompt() -> None:
    brief = "Chcę zbudować osobistego agenta biurowego do organizacji codziennej pracy."
    profile = prompt_engine.classify_task(brief, "programming")
    assert profile is not None
    assert profile.slug == "office_agent"
    questions = prompt_engine.clarification_questions(brief, "programming")
    assert len(questions) == 5
    assert any(question.startswith("Narzędzia i dane") for question in questions)
    assert any(question.startswith("Autonomia") for question in questions)

    answers = {
        questions[0]: "Agent korzysta z Gmaila, Google Calendar, Google Drive i listy zadań. Ma dostęp tylko do mojego kalendarza, dokumentów projektowych i kontaktów służbowych.",
        questions[1]: "Codziennie rano podsumowuje kalendarz, priorytety i nieodczytane e-maile. W piątek przygotowuje tygodniowe podsumowanie zadań.",
        questions[2]: "Może sam tworzyć szkice odpowiedzi i listy zadań. Wysłanie e-maila, utworzenie spotkania i zmiana dokumentu zawsze wymagają mojego zatwierdzenia.",
        questions[3]: "Zapamiętuje nazwy projektów i ustalone preferencje przez 30 dni. Nie zapisuje haseł, danych zdrowotnych ani prywatnej treści e-maili.",
        questions[4]: "Przy braku danych prosi o doprecyzowanie, a przy błędzie pokazuje powiadomienie i nie wykonuje działania. Sukces mierzę brakiem pominiętych spotkań i 80% zadań zrealizowanych w terminie.",
    }
    prompt = Prompt(brief=brief, model_target="chatgpt", level="professional", category="programming", questions=list(questions), answers=answers)
    result = prompt_engine.generate(prompt)

    assert result.score >= 80
    assert "Codzienne przepływy pracy" in result.content
    assert "Integracje oraz model uprawnień" in result.content
    assert "Mierzalne testy akceptacyjne" in result.content
    assert "Gmail" in result.content
    assert "ma działać" in result.content


def test_office_agent_with_shallow_context_cannot_receive_high_score() -> None:
    brief = "Chcę zbudować osobistego agenta biurowego."
    questions = prompt_engine.clarification_questions(brief, "programming")
    prompt = Prompt(
        brief=brief,
        model_target="chatgpt",
        level="professional",
        category="programming",
        questions=list(questions),
        answers={question: "Odbiorcą jestem ja." for question in questions},
    )
    result = prompt_engine.generate(prompt)

    assert result.score < 55
    assert result.analysis["quality_breakdown"]["Zakres autonomii"] == 0
    assert result.analysis["missing_information"]
