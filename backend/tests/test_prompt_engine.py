from app.models import Prompt
from app.services.prompt_engine import prompt_engine


def test_brief_without_context_requires_clarification() -> None:
    questions = prompt_engine.clarification_questions("Chcę napisać książkę", "other")
    assert len(questions) >= 2


def test_generator_creates_structured_prompt() -> None:
    prompt = Prompt(brief="Stwórz plan wdrożenia aplikacji do zarządzania magazynem dla zespołu operacyjnego.", model_target="chatgpt", level="professional", category="business", answers={"Jaki format?": "Tabela etapów z ryzykami"})
    result = prompt_engine.generate(prompt)
    assert "## Rola" in result.content
    assert "## Kryteria sukcesu i checklista" in result.content
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
