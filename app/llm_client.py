"""Thin, testable wrapper around the Google Gemini API.

Both versions talk to the model only through :class:`LLMClient`, so tests can
substitute :class:`MockLLMClient` and CI never needs a real API key.

Gemini access uses the official ``google-genai`` SDK
(https://googleapis.github.io/python-genai/):

    client = genai.Client(api_key=...)
    client.models.generate_content(model=..., contents=[...],
                                   config=types.GenerateContentConfig(...))

Every provider error is converted into an :class:`LLMError` subclass that
carries a short, player-safe message.  Raw exception text (which can include
request details) is never shown to players.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3.8-flash"
DEFAULT_TIMEOUT_SECONDS = 30


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class LLMError(Exception):
    """Base class for all LLM failures. ``user_message`` is safe to display."""

    user_message = "The Game Master is momentarily lost in thought. Please try again."


class LLMConfigError(LLMError):
    user_message = (
        "No valid Gemini API key is configured. Add GEMINI_API_KEY to your .env file "
        "(see .env.example) and restart the app."
    )


class LLMAuthError(LLMError):
    user_message = "The Gemini API rejected the API key or model name. Check GEMINI_API_KEY and GEMINI_MODEL."


class LLMRateLimitError(LLMError):
    user_message = "The free Gemini quota is busy (rate limit reached). Wait a minute and try again."


class LLMTimeoutError(LLMError):
    user_message = "The Game Master took too long to answer (request timed out). Please try again."


class LLMConnectionError(LLMError):
    user_message = "Could not reach the Gemini service. Check your internet connection and try again."


class LLMResponseError(LLMError):
    user_message = "The Game Master returned an empty or unreadable answer. Please try again."


# --------------------------------------------------------------------------- #
# Interface
# --------------------------------------------------------------------------- #
@dataclass
class ChatMessage:
    """One turn of conversation. ``role`` is ``"user"`` or ``"assistant"``."""

    role: str
    content: str


class LLMClient(Protocol):
    name: str

    def generate(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.7,
    ) -> str:
        """Return the model's text reply (a JSON string when ``json_schema`` is given)."""
        ...


# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
@dataclass
class LLMSettings:
    api_key: str | None
    model: str
    mode: str  # "gemini" or "mock"
    timeout_seconds: int

    @property
    def uses_gemini(self) -> bool:
        return self.mode == "gemini" and bool(self.api_key)


def load_settings() -> LLMSettings:
    """Read settings from the environment (and a local ``.env`` file if present)."""
    try:
        from dotenv import load_dotenv

        load_dotenv(override=False)
    except ImportError:  # python-dotenv is optional at runtime
        pass

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip() or None
    if api_key in {"your_api_key_here", "changeme"}:
        api_key = None
    mode = (os.getenv("LLM_MODE") or "gemini").strip().lower()
    if mode not in {"gemini", "mock"}:
        mode = "gemini"
    try:
        timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
    except ValueError:
        timeout = DEFAULT_TIMEOUT_SECONDS
    return LLMSettings(
        api_key=api_key,
        model=(os.getenv("GEMINI_MODEL") or DEFAULT_MODEL).strip(),
        mode=mode,
        timeout_seconds=max(5, timeout),
    )


# --------------------------------------------------------------------------- #
# Gemini implementation
# --------------------------------------------------------------------------- #
class GeminiClient:
    """Calls Gemini through the ``google-genai`` SDK."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS):
        if not api_key:
            raise LLMConfigError("missing api key")
        from google import genai
        from google.genai import types

        self._types = types
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout_seconds * 1000),  # milliseconds
        )
        self.model = model
        self.name = f"Gemini ({model})"

    def generate(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.7,
    ) -> str:
        types = self._types
        contents = [
            types.Content(
                role="model" if m.role == "assistant" else "user",
                parts=[types.Part(text=m.content)],
            )
            for m in messages
        ]
        config_kwargs: dict[str, Any] = {
            "system_instruction": system_prompt,
            "temperature": temperature,
        }
        if json_schema is not None:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_json_schema"] = json_schema

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
        except Exception as exc:  # converted to a safe error below
            raise _translate_exception(exc) from exc

        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise LLMResponseError("empty response")
        return text.strip()


def _translate_exception(exc: Exception) -> LLMError:
    """Map SDK / network exceptions to player-safe :class:`LLMError` types."""
    logger.warning("LLM call failed: %s", type(exc).__name__)
    try:
        from google.genai import errors as genai_errors
    except ImportError:  # pragma: no cover
        genai_errors = None

    if genai_errors is not None and isinstance(exc, genai_errors.APIError):
        code = getattr(exc, "code", None)
        if code == 429:
            return LLMRateLimitError(str(code))
        if code in (400, 401, 403, 404):
            return LLMAuthError(str(code))
        if code in (408, 504):
            return LLMTimeoutError(str(code))
        return LLMConnectionError(str(code))

    name = type(exc).__name__.lower()
    if "timeout" in name:
        return LLMTimeoutError(name)
    if "connect" in name or "network" in name or isinstance(exc, OSError):
        return LLMConnectionError(name)
    return LLMError(name)


# --------------------------------------------------------------------------- #
# Mock implementations (tests, CI and keyless demos)
# --------------------------------------------------------------------------- #
@dataclass
class MockLLMClient:
    """Deterministic stand-in for Gemini.

    ``responses`` may be a list of strings (returned in order, the last one is
    repeated) or a callable ``(system_prompt, messages, json_schema) -> str``.
    Every call is recorded in ``calls`` so tests can inspect exactly what
    context would have been sent to a real model.
    """

    responses: list[str] | Callable[[str, list[ChatMessage], dict | None], str] = field(default_factory=list)
    raise_error: LLMError | None = None
    name: str = "Mock LLM"
    calls: list[dict[str, Any]] = field(default_factory=list)

    def generate(
        self,
        system_prompt: str,
        messages: list[ChatMessage],
        *,
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.7,
    ) -> str:
        self.calls.append(
            {"system_prompt": system_prompt, "messages": list(messages), "json_schema": json_schema}
        )
        if self.raise_error is not None:
            raise self.raise_error
        if callable(self.responses):
            return self.responses(system_prompt, messages, json_schema)
        if not self.responses:
            raise LLMResponseError("mock has no responses")
        index = min(len(self.calls) - 1, len(self.responses) - 1)
        return self.responses[index]


def create_client(settings: LLMSettings | None = None) -> LLMClient | None:
    """Return a Gemini client when configured, otherwise ``None`` (offline mode)."""
    settings = settings or load_settings()
    if not settings.uses_gemini:
        return None
    return GeminiClient(settings.api_key or "", settings.model, settings.timeout_seconds)
