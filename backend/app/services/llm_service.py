"""

Centralised LLM service layer.

Purpose:
- Single place for ALL LLM calls
- Keeps prompts consistent
- Easy to mock in tests
- Easy to swap provider in future (OpenAI / Anthropic / etc.)
- Forces JSON-only structured responses
- Gracefully falls back if API key missing or API fails

Implementation:
- Uses OpenAI Responses API
- Default model: gpt-5-mini
- Returns {} on failure (services handle fallback logic)

Setup:
- Add LLM_API_KEY to .env file
- Get key from: https://platform.openai.com/api-keys
"""

import json
import logging
from typing import Optional

from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy-loaded OpenAI client instance
_client: Optional[OpenAI] = None


# ---------------------------------------------------------------------
# Client Initialisation
# ---------------------------------------------------------------------

def _get_client() -> Optional[OpenAI]:
    """
    Lazily initialise OpenAI client.

    Why lazy load?
    - Prevents startup failure if API key missing
    - Avoids unnecessary object creation
    - Enables safe fallback mode

    Returns:
        OpenAI client if configured correctly
        None if key missing or init fails
    """
    global _client

    if _client is not None:
        return _client

    if not settings.LLM_API_KEY or settings.LLM_API_KEY == "your-openai-api-key-here":
        logger.warning("LLM_API_KEY not configured. Using fallback mode.")
        return None

    try:
        _client = OpenAI(api_key=settings.LLM_API_KEY)
        return _client
    except Exception as e:
        logger.error(f"Failed to initialise OpenAI client: {e}")
        return None


# ---------------------------------------------------------------------
# Core LLM JSON Call
# ---------------------------------------------------------------------

def call_llm_json(*, system: str, user: str, model: str = "gpt-5-mini") -> dict:
    """
    Call OpenAI Responses API and enforce JSON-only output.

    Args:
        system: System-level instructions
        user: User prompt (context + request)
        model: Model name (default: gpt-5-mini)

    Returns:
        Parsed JSON dict
        {} on any failure (never raises)

    Notes:
    - JSON mode enforced via response_format
    - Temperature balanced for structured advice generation
    - max_output_tokens capped to control cost
    """

    client = _get_client()

    if client is None:
        logger.debug("LLM client unavailable - returning empty dict.")
        return {}

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            text={"format": {"type": "json_object"}},
            max_output_tokens=2500,
        )

        content = response.output_text

        if not content:
            logger.warning("LLM returned empty content.")
            return {}

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON returned from LLM: {e}\n"
                f"Preview: {content[:200]}"
            )
            return {}

    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        return {}


# ---------------------------------------------------------------------
# Health Check / Manual Test
# ---------------------------------------------------------------------

def test_llm_connection() -> dict:
    """
    Verifies LLM connectivity and JSON enforcement.

    Returns:
        dict containing:
            status
            message
            api_key_set
            test_response (if successful)
    """

    client = _get_client()

    if client is None:
        return {
            "status": "error",
            "message": "LLM_API_KEY not configured. Set it in .env file.",
            "api_key_set": False,
        }

    try:
        result = call_llm_json(
            system="Return JSON only with key 'message'.",
            user="Say hello in JSON format."
        )

        if result:
            return {
                "status": "success",
                "message": "LLM integration working.",
                "api_key_set": True,
                "test_response": result,
            }

        return {
            "status": "error",
            "message": "LLM returned empty JSON.",
            "api_key_set": True,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"LLM test failed: {str(e)}",
            "api_key_set": True,
        }