from app.models import Prompt
from app.services.prompt_engine import prompt_engine
import pytest


def test_brief_without_context_requires_clarification() -> None:
    questions = prompt_engine.clarification_questions("Chcę napisać książkę", "other")
    assert len(questions) >= 2


def test_the_api_acronym_is_not_detected_inside_an_unrelated_polish_word() -> None:
    profile = prompt_engine.classify_task("Chcę napisać książkę", "other")
    assert profile is not None
    assert profile.slug == "generic"


@pytest.mark.parametrize(
    ("brief", "category", "profile_slug", "question_prefix"),
    [
        ("Zbuduj aplikację do obsługi spraw kancelarii prawnej.", "law", "software_product", "Użytkownicy"),
        ("Przygotuj kampanię reklamową kursu języka angielskiego.", "other", "marketing_campaign", "Odbiorca"),
        ("Napisz tekst sprzedażowy dla aplikacji zdrowotnej.", "medicine", "copywriting", "Oferta"),
        ("Przygotuj lekcję o pierwszej pomocy dla licealistów.", "medicine", "education", "Uczestnicy"),
        ("Przeanalizuj dane sprzedażowe z pliku CSV za ostatni kwartał.", "business", "data_analysis", "Pytanie decyzyjne"),
        ("Przygotuj przegląd literatury o wpływie snu na pamięć.", "medicine", "science", "Pytanie badawcze"),
        ("Przeanalizuj umowę najmu lokalu użytkowego.", "other", "legal_analysis", "Sprawa"),
        ("Wyjaśnij objawy grypy i sytuacje wymagające pilnej pomocy.", "other", "medical_information", "Cel"),
        ("Przetłumacz instrukcję urządzenia z polskiego na angielski.", "other", "translation", "Języki"),
        ("Przygotuj plan SEO dla sklepu z kosmetykami naturalnymi.", "marketing", "seo", "Strona i cel"),
        ("Podejmij decyzję, czy otworzyć drugi punkt sprzedaży.", "other", "business_decision", "Decyzja"),
        ("Ułóż harmonogram przeprowadzki do nowego mieszkania.", "other", "generic", "Rezultat i użycie"),
    ],
)
def test_questions_follow_the_actual_task_even_when_selected_category_is_wrong(brief: str, category: str, profile_slug: str, question_prefix: str) -> None:
    profile = prompt_engine.classify_task(brief, category)
    assert profile is not None
    assert profile.slug == profile_slug
    assert any(question.startswith(question_prefix) for question in prompt_engine.clarification_questions(brief, category))


@pytest.mark.parametrize(
    ("question", "answer"),
    [
        ("Odbiorca: Kto skorzysta z rezultatu?", "Odbiorcą jestem ja."),
        ("Zakres MVP: Co ma powstać?", "ma działać"),
        ("Format: Jak ma wyglądać wynik?", "dowolnie"),
        ("Odbiorca: Dla kogo?", "dla mnie"),
    ],
)
def test_placeholder_answers_are_recognized_beyond_the_exact_phrase_ma_dzialac(question: str, answer: str) -> None:
    assert prompt_engine.is_placeholder_answer(question, answer)


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


def test_seo_goal_without_a_numeric_target_still_requires_a_measurement_question() -> None:
    brief = (
        "Przygotuj plan SEO dla sklepu sprzedającego ekologiczne kosmetyki w Polsce. "
        "Celem jest zwiększenie ruchu organicznego i sprzedaży w ciągu sześciu miesięcy."
    )

    questions = prompt_engine.clarification_questions(brief, "marketing")
    assert any(question.startswith("Pomiar") for question in questions)


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


def test_profile_score_requires_domain_coverage_and_generated_prompt_uses_domain_outline() -> None:
    brief = "Przygotuj plan SEO dla sklepu z ekologicznymi kosmetykami w Polsce."
    questions = prompt_engine.clarification_questions(brief, "marketing")
    answers = {
        next(question for question in questions if question.startswith("Strona i cel")): "Strona kategorii kremów do skóry wrażliwej w sklepie internetowym; ma zwiększać sprzedaż tej kategorii.",
        next(question for question in questions if question.startswith("Intencja")): "Użytkownik szuka odpowiedzi, jaki krem ekologiczny wybrać do skóry wrażliwej.",
        next(question for question in questions if question.startswith("Temat i frazy")): "Frazy: krem ekologiczny do skóry wrażliwej, naturalna pielęgnacja twarzy i kosmetyki bez zapachu.",
        next(question for question in questions if question.startswith("Kontekst rynkowy")): "Punktem odniesienia są trzy sklepy z naturalnymi kosmetykami; wyróżniamy się certyfikatami i składem bez substancji zapachowych.",
        next(question for question in questions if question.startswith("Pomiar")): "Mierzymy ruch organiczny, współczynnik konwersji i sprzedaż kategorii; celem jest wzrost ruchu o 25% oraz sprzedaży o 10% w 6 miesięcy.",
    }
    prompt = Prompt(brief=brief, model_target="chatgpt", level="professional", category="marketing", questions=list(questions), answers=answers)
    result = prompt_engine.generate(prompt)

    assert result.score >= 80
    assert "Klaster tematów oraz priorytetowe frazy" in result.content
    assert "Działania, mierniki, wartości docelowe" in result.content
    assert any(name.startswith("Pokrycie wymagań: treść SEO") for name in result.analysis["quality_breakdown"])


def test_personal_or_vague_answers_cannot_receive_a_high_domain_score() -> None:
    brief = "Zbuduj aplikację do zarządzania magazynem."
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

    assert result.score <= 45
    assert result.analysis["quality_breakdown"]["Kara za ogólniki"] < 0
    assert result.analysis["missing_information"]


def test_detailed_but_irrelevant_answers_leave_the_unanswered_domain_questions_open() -> None:
    brief = "Zbuduj aplikację do zarządzania magazynem."
    questions = prompt_engine.clarification_questions(brief, "programming")
    irrelevant = "To ważny opis dla zespołu, który potrzebuje dobrego rezultatu w kolejnym miesiącu."
    answers = {question: irrelevant for question in questions}

    follow_up = prompt_engine.clarification_questions(brief, "programming", answers)
    assert len(follow_up) >= 3
    assert any(question.startswith("Dane i integracje") for question in follow_up)
    assert any(question.startswith("Bezpieczeństwo") for question in follow_up)


@pytest.mark.parametrize(
    ("brief", "category", "expected_section"),
    [
        ("Zbuduj aplikację do zarządzania magazynem.", "programming", "Główne przepływy użytkownika"),
        ("Przygotuj kampanię reklamową kursu językowego.", "marketing", "Plan kanałów z materiałem"),
        ("Przeanalizuj dane sprzedażowe z pliku CSV.", "data_analysis", "Wnioski odróżnione od obserwacji"),
        ("Podejmij decyzję o otwarciu drugiego punktu sprzedaży.", "business", "Porównanie realistycznych opcji"),
        ("Napisz tekst sprzedażowy produktu.", "copywriting", "Gotową treść we wskazanym tonie"),
        ("Przygotuj plan SEO dla sklepu z kosmetykami.", "seo", "Klaster tematów oraz priorytetowe frazy"),
        ("Przeanalizuj umowę najmu.", "law", "Ryzyka oraz istotne zapisy dokumentów"),
        ("Wyjaśnij objawy grypy.", "medicine", "Sygnały alarmowe"),
        ("Przetłumacz instrukcję z polskiego na angielski.", "translation", "Tłumaczenie zachowujące znaczenie"),
        ("Przygotuj lekcję o pierwszej pomocy.", "education", "Sposób sprawdzenia efektu nauki"),
        ("Przygotuj przegląd literatury o śnie.", "science", "Wyniki oddzielone od interpretacji"),
    ],
)
def test_generated_prompt_uses_a_domain_specific_result_outline(brief: str, category: str, expected_section: str) -> None:
    prompt = Prompt(brief=brief, model_target="chatgpt", level="professional", category=category)
    result = prompt_engine.generate(prompt)

    assert expected_section in result.content


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
