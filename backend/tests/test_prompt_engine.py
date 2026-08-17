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
    assert result.score < 60
    assert result.analysis["quality_breakdown"]["Kara za ogólniki"] < 0
