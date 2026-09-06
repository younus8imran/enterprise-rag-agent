import os
from typing import Any, Dict, List, Optional

from mistralai.client import Mistral

from app.core.config import settings
from app.core.logging import logger

DEBUG_LLM_FALLBACK = os.environ.get("DEBUG_LLM_FALLBACK", "1") == "1"


def _fallback_answer(query: str, context: Optional[str] = None) -> str:
    """Used only when real Mistral is unavailable (key missing / 429 / network)."""
    if context and context.strip():
        return (
            "[MISTRAL_UNAVAILABLE - set MISTRAL_API_KEY or unset DEBUG_LLM_FALLBACK]\n\n"
            f"Synthetic answer based on {len(context)} chars of evidence for: {query}"
        )
    return (
        "[MISTRAL_UNAVAILABLE - set MISTRAL_API_KEY to see real output]\n\n"
        f"Synthetic answer for: {query}"
    )


class MistralChatProvider:
    """
    Real Mistral chat provider (mistralai SDK v2.x).
    Replaces the prior mock-based stub.
    """

    def __init__(self, model: str = "mistral-small-latest") -> None:
        self.model = model
        self._client: Optional[Mistral] = None

    @property
    def client(self) -> Mistral:
        if self._client is None:
            self._client = Mistral(api_key=settings.MISTRAL_API_KEY or "placeholder")
        return self._client

    async def generate_answer(
        self,
        query: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a completion using Mistral's chat API.

        Args:
            query: The user's question.
            context: Optional retrieved evidence to ground the answer.
            system_prompt: Optional system prompt to override the default.

        Returns:
            The model's textual response.
        """
        messages: List[Dict[str, str]] = []

        # Try primary model first, then retry with a different free Mistral model on 429
        primary_model = self.model
        fallback_models = ["codestral-latest", "open-mixtral-8x7b", "mistral-large-latest"]
        last_exception: Optional[Exception] = None

        for attempt_model in [primary_model] + fallback_models:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                else:
                    base_system = (
                        "You are a precise enterprise assistant. Answer strictly based on the "
                        "provided evidence. If the evidence is insufficient, say so. "
                        "Cite sources inline as [1], [2], etc."
                    )
                    messages.append({"role": "system", "content": base_system})
                user_content = f"Evidence:\n{context or '(none)'}\n\nQuestion: {query}" if context else query
                messages.append({"role": "user", "content": user_content})

                resp = await self.client.chat.complete_async(
                    model=attempt_model,
                    messages=messages,
                )
                content = resp.choices[0].message.content
                if content is None:
                    raise RuntimeError("Mistral returned an empty completion")
                return content
            except Exception as e:
                last_exception = e
                err_str = str(e).lower()
                is_429 = "429" in err_str or "rate" in err_str or "limit" in err_str
                # Only retry with alternate model for rate-limit / exhaustion errors
                if is_429 and attempt_model != primary_model:
                    logger.info("mistral_retry_model", model=attempt_model, error=str(e)[:120])
                    continue
                # For 429 on primary, try first fallback; for other errors, break
                if is_429 and attempt_model == primary_model:
                    logger.info("mistral_retry_first_fallback", error=str(e)[:120])
                    continue
                break

        # All attempts exhausted (real Mistral unavailable)
        if DEBUG_LLM_FALLBACK:
            logger.warning("mistral_chat_fallback", error=str(last_exception)[:200], model=primary_model)
            return _fallback_answer(query, context)
        logger.error("mistral_chat_failed", error=str(last_exception), model=primary_model)
        raise last_exception

    async def generate_json(
        self,
        query: str,
        context: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a JSON-mode completion. Returns the parsed dict.
        """
        messages: List[Dict[str, str]] = []

        sys_msg = system_prompt or (
            "You are a precise enterprise assistant. Respond with valid JSON only, "
            "no markdown fences, no commentary."
        )
        messages.append({"role": "system", "content": sys_msg})

        user_content = f"Context:\n{context or ''}\n\nTask: {query}" if context else query
        messages.append({"role": "user", "content": user_content})

        try:
            resp = await self.client.chat.complete_async(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or "{}"
            import json
            return json.loads(content)
        except Exception as e:
            if DEBUG_LLM_FALLBACK:
                logger.warning("mistral_json_fallback", error=str(e), model=self.model)
                return {"_fallback": True, "query": query}
            logger.error("mistral_json_failed", error=str(e), model=self.model)
            raise
