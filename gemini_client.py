import json
import logging
import os
import re
import threading
import time

import httpx
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

LLM_DASHBOARD_URL = "http://5.42.101.215:8005/api/usage"


def _send_to_dashboard(model: str, response):
    try:
        input_tokens = getattr(getattr(response, "usage_metadata", None), "prompt_token_count", 0) or 0
        output_tokens = getattr(getattr(response, "usage_metadata", None), "candidates_token_count", 0) or 0
        if not (input_tokens or output_tokens):
            return
        httpx.post(LLM_DASHBOARD_URL, json={
            "project": "metodist",
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }, timeout=5)
    except Exception:
        logger.debug("Failed to send usage to LLM dashboard", exc_info=True)


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
                    threading.Thread(target=_send_to_dashboard, args=(model_name, response), daemon=True).start()
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


def _build_custom_words_block(analysis: dict) -> str:
    """Build an explicit prompt block that forces LLM to use custom_words."""
    words = analysis.get("custom_words")
    if not words:
        return ""
    words_str = ", ".join(words)
    return f"""
╔══════════════════════════════════════════════════════════════╗
║  ОБЯЗАТЕЛЬНАЯ ЛЕКСИКА — ПРИОРИТЕТ №1                        ║
╚══════════════════════════════════════════════════════════════╝

Учитель задал КОНКРЕТНЫЙ список слов: [{words_str}]

ВСЕ задания 2, 3, 4 ОБЯЗАНЫ использовать ТОЛЬКО слова из этого списка.
НЕ ПРИДУМЫВАЙ свои слова. НЕ ЗАМЕНЯЙ слова из списка.

Вот как использовать эти слова в каждом типе задания:
- matching: left_column = слова из списка, right_column = их переводы/определения
- fill_blanks: пропуски = слова из списка, предложения содержат эти слова
- sorting_table: word_bank = слова из списка
- odd_one_out: items = 3 слова из списка + 1 лишнее (НЕ из списка)
- anagram: scrambled = одно из слов списка с перемешанными буквами
- word_search: words = слова из списка (3-6 букв, без Ё и Й)
- letter_unscramble: scrambled_words = слова из списка с перемешанными буквами
- sentence_build: предложения используют слова из списка
- crossword_mini: words = слова из списка, clues = подсказки к ним
- coloring: prompt_text использует слова из списка

ПРОВЕРЬ СЕБЯ: каждое задание содержит слова [{words_str}]? Если нет — переделай.
"""


def _extract_words_from_tasks(tasks_data: dict) -> set[str]:
    """Extract all words/strings used in generated tasks for validation."""
    text_parts = []
    for task in tasks_data.get("tasks", []):
        for key, val in task.items():
            if key in ("type", "instruction", "line_count", "grid_size", "answer_length", "chain_length", "target_sum"):
                continue
            if isinstance(val, str):
                text_parts.append(val)
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, list):
                        text_parts.extend(str(x) for x in item)
    full_text = " ".join(text_parts).lower()
    return set(full_text.split())


def _check_custom_words_used(analysis: dict, tasks_data: dict) -> list[str]:
    """Return list of custom_words NOT found in the generated tasks."""
    custom_words = analysis.get("custom_words")
    if not custom_words:
        return []
    full_text = _extract_words_from_tasks(tasks_data)
    # Also check as substring (for compound forms, fill_blanks text, etc.)
    all_text = " ".join(
        str(v) for task in tasks_data.get("tasks", [])
        for v in task.values() if isinstance(v, (str, list))
    ).lower()
    missing = []
    for word in custom_words:
        w = word.lower().strip()
        if w not in full_text and w not in all_text:
            missing.append(word)
    return missing


def generate_worksheet_tasks(analysis: dict) -> dict:
    """Step 2: Generate 4 tasks based on analysis. Validates custom_words usage."""
    custom_words_block = _build_custom_words_block(analysis)
    prompt = WORKSHEET_TASKS_PROMPT.format(
        analysis_json=json.dumps(_strip_personal_data(analysis), ensure_ascii=False),
        custom_words_block=custom_words_block,
    )
    data = _call_and_validate(prompt, model_class=WorksheetTasks)

    # Validate custom_words usage — retry once if too many missing
    custom_words = analysis.get("custom_words")
    if custom_words:
        missing = _check_custom_words_used(analysis, data)
        if len(missing) > len(custom_words) * 0.4:
            logger.warning("Custom words validation failed. Missing %d/%d: %s. Retrying.",
                           len(missing), len(custom_words), missing)
            words_str = ", ".join(custom_words)
            retry_prompt = (
                prompt
                + f"\n\nОШИБКА: ты НЕ использовал слова учителя! Пропущены: {', '.join(missing)}."
                + f"\nВСЕ задания ОБЯЗАНЫ содержать слова из списка: [{words_str}]."
                + "\nПеределай JSON. Каждое задание должно включать слова из списка."
            )
            data = _call_and_validate(retry_prompt, model_class=WorksheetTasks)
            missing2 = _check_custom_words_used(analysis, data)
            if missing2:
                logger.warning("After retry still missing %d words: %s", len(missing2), missing2)

    return data


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
