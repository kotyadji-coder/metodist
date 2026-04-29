import json
import logging
import os
import re
import time

import vertexai
from google.api_core.exceptions import ResourceExhausted
from vertexai.generative_models import GenerationConfig, GenerativeModel, HarmBlockThreshold, HarmCategory, SafetySetting

from prompts.analyze import ANALYZE_PROMPT
from prompts.worksheet_tasks import WORKSHEET_TASKS_PROMPT
from prompts.activities.generate import ACTIVITY_PROMPT
from models.common import WorksheetAnalysis
from models.worksheet import WorksheetTasks
from models.activities.all import (
    CipherActivity, CafeActivity, ShopActivity, MazeActivity,
)

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
REGION = "global"
MODEL_NAME = "gemini-3.1-pro-preview"
FALLBACK_MODEL_NAME = "gemini-2.5-pro"

logger = logging.getLogger("metodist")

CHILD_SAFETY_SETTINGS = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
]

MAX_RETRIES = 3


def _get_model(model_name: str = MODEL_NAME) -> GenerativeModel:
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        vertexai.init(project=PROJECT_ID, location=REGION, credentials=credentials)
    else:
        vertexai.init(project=PROJECT_ID, location=REGION)
    return GenerativeModel(model_name)


def _call_model_with_retry(prompt: str, model_name: str = MODEL_NAME):
    """Call Gemini with retry on 429, fallback to stable model."""
    model = _get_model(model_name)
    gen_config = GenerationConfig(response_mime_type="application/json")

    for attempt in range(MAX_RETRIES + 1):
        try:
            return model.generate_content(
                prompt,
                generation_config=gen_config,
                safety_settings=CHILD_SAFETY_SETTINGS,
            )
        except ResourceExhausted:
            if attempt == MAX_RETRIES:
                break
            wait = 2 ** attempt * 5  # 5s, 10s, 20s
            logger.warning("Gemini 429 rate limit, retry %d/%d after %ds", attempt + 1, MAX_RETRIES, wait)
            time.sleep(wait)

    # All retries exhausted — fallback
    logger.warning("Retries exhausted for %s, falling back to %s", model_name, FALLBACK_MODEL_NAME)
    fallback = _get_model(FALLBACK_MODEL_NAME)
    return fallback.generate_content(
        prompt,
        generation_config=gen_config,
        safety_settings=CHILD_SAFETY_SETTINGS,
    )


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
