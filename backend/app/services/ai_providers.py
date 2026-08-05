"""Adaptery zewnętrznych modeli. Generator działa deterministycznie bez kluczy API."""
import logging
from typing import Protocol
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class PromptEnhancer(Protocol):
    def enhance(self, instruction: str) -> str: ...


class OpenAIEnhancer:
    def enhance(self, instruction: str) -> str:
        if not settings.openai_api_key:
            return instruction
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.openai_model, "input": instruction},
            timeout=30,
        )
        response.raise_for_status()
        return response.json().get("output_text", instruction)


class AnthropicEnhancer:
    def enhance(self, instruction: str) -> str:
        if not settings.anthropic_api_key:
            return instruction
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": settings.anthropic_api_key, "anthropic-version": "2023-06-01"},
            json={"model": settings.anthropic_model, "max_tokens": 2048, "messages": [{"role": "user", "content": instruction}]},
            timeout=30,
        )
        response.raise_for_status()
        content = response.json().get("content", [])
        return content[0].get("text", instruction) if content else instruction


def enhance_prompt(content: str, target: str) -> str:
    """Opcjonalnie dopracowuje prompt zewnętrznym modelem bez blokowania generatora."""
    instruction = """Dopracuj poniższy prompt po polsku. Zachowaj wszystkie nagłówki Markdown,
konkretność, ograniczenia i checklistę. Nie dodawaj komentarza ani wyjaśnienia — zwróć wyłącznie gotowy prompt.

""" + content
    try:
        if target == "chatgpt" and settings.openai_api_key:
            return OpenAIEnhancer().enhance(instruction)
        if target == "claude" and settings.anthropic_api_key:
            return AnthropicEnhancer().enhance(instruction)
        if target == "both":
            if settings.openai_api_key:
                return OpenAIEnhancer().enhance(instruction)
            if settings.anthropic_api_key:
                return AnthropicEnhancer().enhance(instruction)
    except httpx.HTTPError:
        logger.exception("Dostawca AI nie odpowiedział; zastosowano generator deterministyczny.")
    return content
