"""
Phantom Signal — Gemini API Client (PRD-004 FR-006)
Wrapper around google-generativeai with rate limiting and retry logic.
"""
import json
import logging
import time
import re
from typing import Optional, Any

import google.generativeai as genai
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log,
)

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FLASH_MODEL
from data.database import log_llm_usage

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",       "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

_GEN_CONFIG = genai.types.GenerationConfig(
    temperature=0.1,
    top_p=0.95,
    max_output_tokens=8192,
)

# Rate limiting: track last call timestamps
_call_timestamps: list = []
MAX_CALLS_PER_MINUTE = 50  # conservative limit


def _enforce_rate_limit():
    """Simple in-process rate limiter."""
    global _call_timestamps
    now = time.time()
    _call_timestamps = [t for t in _call_timestamps if now - t < 60]
    if len(_call_timestamps) >= MAX_CALLS_PER_MINUTE:
        sleep_for = 60 - (now - _call_timestamps[0]) + 1
        logger.warning("Rate limit: sleeping %.1fs", sleep_for)
        time.sleep(max(0, sleep_for))
    _call_timestamps.append(time.time())


def _extract_json(text: str) -> Optional[Any]:
    """Extract JSON from Gemini response, stripping markdown fences."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object/array
        match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
    return None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type(Exception),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def call_gemini(
    system_prompt: str,
    user_prompt: str,
    model_name: Optional[str] = None,
    expect_json: bool = True,
) -> Optional[Any]:
    """
    Call Gemini with system + user prompt.
    Returns parsed JSON if expect_json=True, raw text otherwise.
    """
    _enforce_rate_limit()
    model_to_use = model_name or GEMINI_MODEL

    try:
        model = genai.GenerativeModel(
            model_name=model_to_use,
            system_instruction=system_prompt,
            generation_config=_GEN_CONFIG,
            safety_settings=_SAFETY_SETTINGS,
        )
        response = model.generate_content(user_prompt)
        raw_text = response.text

        # Log usage
        try:
            usage = response.usage_metadata
            log_llm_usage(
                model=model_to_use,
                input_tokens=getattr(usage, "prompt_token_count", 0),
                output_tokens=getattr(usage, "candidates_token_count", 0),
                operation="call_gemini",
            )
        except Exception:
            pass

        if not expect_json:
            return raw_text

        result = _extract_json(raw_text)
        if result is None:
            logger.warning("Failed to parse JSON from Gemini response: %s...", raw_text[:200])
        return result

    except Exception as e:
        logger.error("Gemini API error (%s): %s", model_to_use, str(e))
        raise


def call_gemini_flash(
    system_prompt: str,
    user_prompt: str,
    expect_json: bool = True,
) -> Optional[Any]:
    """Use Flash model for faster, cheaper calls (intervention rules, summaries)."""
    return call_gemini(system_prompt, user_prompt, GEMINI_FLASH_MODEL, expect_json)


def fix_json_with_gemini(broken_json: str, schema_description: str) -> Optional[Any]:
    """Ask Gemini to fix a broken JSON response."""
    system = "You are a JSON repair tool. Fix the provided JSON to match the schema. Return ONLY valid JSON, no explanation."
    user = f"Fix this JSON to match {schema_description}:\n\n{broken_json}"
    return call_gemini(system, user, GEMINI_FLASH_MODEL, expect_json=True)


def test_connection() -> bool:
    """Test that Gemini API key is valid."""
    try:
        model = genai.GenerativeModel(GEMINI_FLASH_MODEL)
        resp = model.generate_content("Say 'OK' and nothing else.")
        return bool(resp.text)
    except Exception as e:
        logger.error("Gemini connection test failed: %s", e)
        return False
