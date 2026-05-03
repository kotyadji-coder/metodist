import json
import logging
import os
import re
import time

from google import genai
from google.genai import types

from prompts.analyze import ANALYZE_PROMPT
from prompts.worksheet_tasks import WORKSHEET_TASKS_PROMPT
from prompts.activities.generate import ACTIVITY_PROMPT
from models.common import WorksheetAnalysis
from models.worksheet import WorksheetTasks
from models.activities.all import (
    CipherActivity, CafeActivity, ShopActivity, MazeActivity,
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
VERTEX_REGION = "global"

logger = logging.getLogger("metodist")

_last_backend = "unknown"

SAFETY_SETTINGS = [
    types.SafetySetting(
        category="HARM_CATEGORY_HARASSMENT",
        threshold="BLOCK_LOW_AND_ABOVE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_HATE_SPEECH",
        threshold="BLOCK_LOW_AND_ABOVE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
        threshold="BLOCK_LOW_AND_ABOVE",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_LOW_AND_ABOVE",
    ),
]

FALLBACK_CHAIN = [
    ("ai_studio", "gemini-2.5-pro"),
    ("ai_studio", "gemini-2.5-flash"),
    ("vertex", "gemini-2.5-pro"),
]


def _get_ai_studio_client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


def _get_vertex_client() -> genai.Client:
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return genai.Client(vertexai=True, project=PROJECT_ID, location=VERTEX_REGION, credentials=credentials)
    return genai.Client(vertexai=True, project=PROJECT_ID, location=VERTEX_REGION)


def _call_with_fallback(contents, config=None):
    """Try AI Studio gemini-2.5-pro -> AI Studio gemini-2.5-flash -> Vertex gemini-2.5-pro."""
    last_error = None
    for backend, model_name in FALLBACK_CHAIN:
        try:
            if backend == "ai_studio":
                if not GEMINI_API_KEY:
                    logger.info(f"Skipping AI Studio ({model_name}): no API key")
                    continue
                client = _get_ai_studio_client()
            else:
                client = _get_vertex_client()

            tag = f"{backend}/{model_name}"
            for attempt in range(4):
                try:
                    logger.info(f"Calling {tag} (attempt {attempt + 1})")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config,
                    )
                    logger.info(f"Success from {tag}")
                    global _last_backend
                    _last_backend = tag
                    return response
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str.upper():
                        if attempt < 3:
                            wait = 2 ** attempt * 5
                            logger.warning(f"{tag} rate limit, retry {attempt + 1}/3 after {wait}s")
                            time.sleep(wait)
                            continue
                        logger.warning(f"{tag} rate limit exhausted, moving to next backend")
                        last_error = e
                        break
                    else:
                        raise
        except Exception as e:
            logger.warning(f"Failed {backend}/{model_name}: {e}")
            last_error = e
            continue

    raise last_error or RuntimeError("All backends failed")


def get_last_backend() -> str:
    return _last_backend


def _call_model_with_retry(prompt: str):
    """Call Gemini with fallback chain, JSON response mode."""
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        safety_settings=SAFETY_SETTINGS,
    )
    return _call_with_fallback(prompt, config=config)


def _extract_json(raw: str) -> dict:
    """Strip markdown fences and extract the JSON object."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    cleaned = cleaned.strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)


def _call_and_validate(prompt: str, model_class=None) -> dict:
    """Call Gemini, parse JSON, validate with Pydantic. Retry on validation failure."""
    last_error = None
    for attempt in range(2):
        try:
            response = _call_model_with_retry(prompt)
            data = _extract_json(response.text)
            if model_class:
                model_class.model_validate(data)
            return data
        except Exception as e:
            last_error = e
            logger.warning("Validation attempt %d failed: %s", attempt + 1, e)
            if attempt == 0:
                prompt += f"\n\nПРЕДЫДУЩАЯ ПОПЫТКА ДАЛА ОШИБКУ: {e}\nИсправь и верни корректный JSON."
    raise last_error


def analyze_worksheet_request(question: str) -> dict:
    """Step 1: Analyze user's free-text request."""
    prompt = ANALYZE_PROMPT.format(question=question)
    return _call_and_validate(prompt, model_class=WorksheetAnalysis)


def _strip_personal_data(analysis: dict) -> dict:
    """Remove child_name before sending to external AI."""
    safe = {k: v for k, v in analysis.items() if k != "child_name"}
    return safe


def generate_worksheet_tasks(analysis: dict) -> dict:
    """Step 2: Generate 4 tasks based on analysis."""
    prompt = WORKSHEET_TASKS_PROMPT.format(
        analysis_json=json.dumps(_strip_personal_data(analysis), ensure_ascii=False),
    )
    return _call_and_validate(prompt, model_class=WorksheetTasks)


ACTIVITY_MODEL_MAP = {
    "cipher": CipherActivity,
    "cafe": CafeActivity,
    "shop": ShopActivity,
    "maze": MazeActivity,
}


def generate_activity(activity_type: str, analysis: dict) -> dict:
    """Generate full-page activity data."""
    prompt = ACTIVITY_PROMPT.format(
        activity_type=activity_type,
        analysis_json=json.dumps(_strip_personal_data(analysis), ensure_ascii=False),
    )
    model_class = ACTIVITY_MODEL_MAP.get(activity_type)
    return _call_and_validate(prompt, model_class=model_class)
