import asyncio
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db_logger
from gemini_client import analyze_worksheet_request, generate_worksheet_tasks, generate_activity
from image_generator import generate_image
from smartbot_client import send_message
from generators.worksheet import save_worksheet
from generators.activities.render import save_activity

ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_me")

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8002")
CONTENT_DIR = Path(__file__).parent / "content"

logger = logging.getLogger("metodist")


# ── Content safety ───────────────────────────────────────────────────────────

_UNSAFE_KEYWORDS = re.compile(
    r"\b("
    # real weapons (NOT fantasy: swords, lightsabers etc are OK)
    r"пистолет|ружь[её]|автомат|пулемёт|граната|бомб[аы]|взрывчатк[аи]"
    r"|gun|pistol|rifle|bomb|grenade|cannon"
    # violence
    r"|насили[ея]|убийств[ао]|убийц[аы]|убить|убивать|кров[иь]|смерт[иь]|мёртв"
    r"|violence|murder|kill|killing|blood|death|dead|dying|gore"
    # horror
    r"|демон|дьявол"
    r"|demon|devil"
    # adult
    r"|секс|порно|голый|голая|нагой"
    r"|sex|porn|nude|naked"
    # substances
    r"|алкоголь|пиво|водк[аи]|наркотик|куритель|сигарет"
    r"|alcohol|beer|vodka|drug|drugs|smoking|cigarette"
    r")\b",
    re.IGNORECASE,
)

_SAFE_REPLACEMENT = "нейтральный мир приключений"


def _sanitize_question(question: str) -> str:
    if _UNSAFE_KEYWORDS.search(question):
        return _UNSAFE_KEYWORDS.sub(_SAFE_REPLACEMENT, question)
    return question


# ── Helpers ──────────────────────────────────────────────────────────────────

def _check_password(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Forbidden")


def _notify_admin(error_message: str, user_id: str) -> None:
    if not ADMIN_BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    text = f"Ошибка metodist: {error_message}, user: {user_id}"
    try:
        httpx.post(
            f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_CHAT_ID, "text": text},
            timeout=10,
        )
    except Exception:
        logger.exception("Не удалось отправить уведомление администратору")


# ── Image generation with fallback ───────────────────────────────────────────

def _generate_image_with_fallback(coloring_prompt: str) -> bytes | None:
    """Generate B&W coloring image. Returns bytes or None on failure."""
    try:
        return generate_image(coloring_prompt, aspect_ratio="1:1")
    except Exception as e:
        logger.warning("Image generation failed: %s", e)
        if "IMAGE_PROHIBITED_CONTENT" in str(e):
            try:
                fallback_prompt = (
                    "Black and white coloring book page for kids, simple clean outlines, "
                    "no shading, a friendly child in a school setting reading a book, "
                    "educational theme, safe for children"
                )
                return generate_image(fallback_prompt, aspect_ratio="1:1")
            except Exception as e2:
                logger.warning("Fallback image also failed: %s", e2)
        return None


# ── Request model ────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    user_id: str
    question: str
    channel_id: str
    callback_url: str | None = None


# ── App setup ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    CONTENT_DIR.mkdir(exist_ok=True)
    yield


app = FastAPI(lifespan=lifespan)

app.mount("/content", StaticFiles(directory=str(CONTENT_DIR)), name="content")


# ── Core pipeline ────────────────────────────────────────────────────────────

def _generate_worksheet_and_send(
    user_id: str, question: str, channel_id: str, callback_url: str | None = None
) -> None:
    """Full worksheet pipeline — runs in a background thread."""
    try:
        # 0. Sanitize
        sanitized = _sanitize_question(question)
        if sanitized != question:
            db_logger.log("WARNING", "INPUT_SANITIZED", "Unsafe keywords replaced", user_id=user_id, channel_id=channel_id)
        question = sanitized

        # 1. LLM Step 1: Analyze request
        db_logger.log("INFO", "STEP1_START", "Analyzing request", user_id=user_id, channel_id=channel_id)
        analysis = analyze_worksheet_request(question)
        db_logger.log(
            "INFO", "STEP1_DONE",
            f"{analysis.get('subject')} · {analysis.get('grade')} кл · {analysis.get('topic')}",
            user_id=user_id, channel_id=channel_id,
        )

        # 2. CONCURRENT: Image gen (from coloring_prompt) + LLM Step 2 (tasks)
        db_logger.log("INFO", "CONCURRENT_START", "Image + Tasks generation", user_id=user_id, channel_id=channel_id)

        with ThreadPoolExecutor(max_workers=2) as pool:
            image_future = pool.submit(_generate_image_with_fallback, analysis.get("coloring_prompt", ""))
            tasks_future = pool.submit(generate_worksheet_tasks, analysis)

            tasks_data = tasks_future.result()
            image_bytes = image_future.result()

        db_logger.log("INFO", "CONCURRENT_DONE", "Image + Tasks ready", user_id=user_id, channel_id=channel_id)

        # 3. Save HTML (post-processing handled inside save_worksheet)
        content_id = save_worksheet(
            image_bytes=image_bytes,
            analysis=analysis,
            tasks_data=tasks_data,
            server_url=SERVER_URL,
        )
        db_logger.log("INFO", "WORKSHEET_DONE", f"Saved: {content_id}", user_id=user_id, channel_id=channel_id)

        # 5. Send via SmartBot
        web_url = f"{SERVER_URL}/e/{content_id}"
        try:
            send_message(peer_id=user_id, status="success", channel_id=channel_id, web_url=web_url)
            db_logger.log("INFO", "SENT", f"URL sent: {content_id}", user_id=user_id, channel_id=channel_id)
        except Exception as e:
            db_logger.log("ERROR", "SEND_ERROR", f"SmartBot error: {e}", user_id=user_id, channel_id=channel_id)
            raise

    except Exception as e:
        error_msg = str(e)
        db_logger.log("ERROR", "ERROR", f"Pipeline error: {error_msg}", user_id=user_id, channel_id=channel_id)
        logger.exception("Worksheet error for user_id=%s", user_id)
        send_message(peer_id=user_id, status="error", channel_id=channel_id)
        _notify_admin(error_message=error_msg, user_id=user_id)


# ── Activity pipeline ────────────────────────────────────────────────────────

def _generate_activity_and_send(
    activity_type: str, user_id: str, question: str, channel_id: str
) -> None:
    """Full activity pipeline — runs in a background thread."""
    try:
        sanitized = _sanitize_question(question)
        question = sanitized

        # 1. Analyze
        db_logger.log("INFO", "ACT_STEP1", f"Analyzing {activity_type}", user_id=user_id, channel_id=channel_id)
        analysis = analyze_worksheet_request(question)

        # 2. Generate activity data (+ image for cipher)
        db_logger.log("INFO", "ACT_STEP2", f"Generating {activity_type}", user_id=user_id, channel_id=channel_id)

        if activity_type == "cipher":
            with ThreadPoolExecutor(max_workers=2) as pool:
                image_future = pool.submit(_generate_image_with_fallback, analysis.get("coloring_prompt", ""))
                activity_future = pool.submit(generate_activity, activity_type, analysis)
                activity_data = activity_future.result()
                image_bytes = image_future.result()
        else:
            activity_data = generate_activity(activity_type, analysis)
            image_bytes = None

        # 3. Save HTML
        content_id = save_activity(
            activity_type=activity_type,
            analysis=analysis,
            activity_data=activity_data,
            server_url=SERVER_URL,
            image_bytes=image_bytes,
        )
        db_logger.log("INFO", "ACT_DONE", f"Saved {activity_type}: {content_id}", user_id=user_id, channel_id=channel_id)

        # 4. Send via SmartBot
        web_url = f"{SERVER_URL}/e/{content_id}"
        send_message(peer_id=user_id, status="success", channel_id=channel_id, web_url=web_url)
        db_logger.log("INFO", "SENT", f"URL sent: {content_id}", user_id=user_id, channel_id=channel_id)

    except Exception as e:
        error_msg = str(e)
        db_logger.log("ERROR", "ERROR", f"Activity error: {error_msg}", user_id=user_id, channel_id=channel_id)
        logger.exception("Activity error for user_id=%s", user_id)
        send_message(peer_id=user_id, status="error", channel_id=channel_id)
        _notify_admin(error_message=error_msg, user_id=user_id)


def _parse_request(body_bytes: bytes) -> GenerateRequest:
    """Parse SmartBot request body."""
    body_str = body_bytes.decode("utf-8")
    body_str = re.sub(
        r'("question":\s*"[^"]*)',
        lambda m: m.group(0).replace("\n", " "),
        body_str,
    )
    data = json.loads(body_str)
    return GenerateRequest(**data)


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/generate")
@app.post("/generate-worksheet")
async def generate_worksheet(request: Request):
    """Accept worksheet request and return 200 immediately."""
    body_bytes = await request.body()
    req = _parse_request(body_bytes)
    db_logger.log(
        "INFO", "REQUEST",
        f"Worksheet request: {req.question[:80]}",
        user_id=req.user_id, channel_id=req.channel_id,
    )
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _generate_worksheet_and_send, req.user_id, req.question, req.channel_id, req.callback_url)
    return {"status": "ok"}


@app.post("/generate-cipher")
async def generate_cipher(request: Request):
    body_bytes = await request.body()
    req = _parse_request(body_bytes)
    db_logger.log("INFO", "REQUEST", f"Cipher request: {req.question[:80]}", user_id=req.user_id, channel_id=req.channel_id)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _generate_activity_and_send, "cipher", req.user_id, req.question, req.channel_id)
    return {"status": "ok"}


@app.post("/generate-cafe")
async def generate_cafe(request: Request):
    body_bytes = await request.body()
    req = _parse_request(body_bytes)
    db_logger.log("INFO", "REQUEST", f"Cafe request: {req.question[:80]}", user_id=req.user_id, channel_id=req.channel_id)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _generate_activity_and_send, "cafe", req.user_id, req.question, req.channel_id)
    return {"status": "ok"}


@app.post("/generate-shop")
async def generate_shop(request: Request):
    body_bytes = await request.body()
    req = _parse_request(body_bytes)
    db_logger.log("INFO", "REQUEST", f"Shop request: {req.question[:80]}", user_id=req.user_id, channel_id=req.channel_id)
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _generate_activity_and_send, "shop", req.user_id, req.question, req.channel_id)
    return {"status": "ok"}


@app.get("/e/{content_id}", response_class=HTMLResponse)
async def get_worksheet(content_id: str):
    html_path = CONTENT_DIR / f"{content_id}.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Рабочий лист не найден")
    return html_path.read_text(encoding="utf-8")


@app.get("/admin/logs", response_class=HTMLResponse)
async def admin_logs(password: str = Query(...)):
    _check_password(password)
    rows = db_logger.get_recent_logs(100)

    level_colors = {"INFO": "#2ecc71", "ERROR": "#e74c3c", "WARNING": "#f39c12"}

    rows_html = ""
    for r in rows:
        color = level_colors.get(r["level"], "#aaa")
        rows_html += (
            f'<tr>'
            f'<td>{r["timestamp"]}</td>'
            f'<td style="color:{color};font-weight:bold">{r["level"]}</td>'
            f'<td>{r["action"] or ""}</td>'
            f'<td>{r["user_id"] or ""}</td>'
            f'<td>{r["channel_id"] or ""}</td>'
            f'<td style="word-break:break-word">{r["message"]}</td>'
            f'</tr>\n'
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Logs — Metodist</title>
  <meta http-equiv="refresh" content="30">
  <style>
    body {{ font-family: monospace; background: #111; color: #eee; padding: 20px; }}
    h1 {{ color: #fff; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    th {{ background: #222; color: #aaa; padding: 8px; text-align: left; }}
    td {{ padding: 6px 8px; border-bottom: 1px solid #222; vertical-align: top; }}
    tr:hover td {{ background: #1a1a1a; }}
    .meta {{ color: #666; font-size: 12px; margin-bottom: 12px; }}
    a {{ color: #aaa; }}
  </style>
</head>
<body>
  <h1>Metodist Logs</h1>
  <div class="meta">Последние 100 записей · <a href="/admin/stats?password={password}">Stats</a></div>
  <table>
    <tr><th>Время</th><th>Уровень</th><th>Действие</th><th>User ID</th><th>Channel</th><th>Сообщение</th></tr>
    {rows_html}
  </table>
</body>
</html>"""
    return html


@app.get("/admin/stats", response_class=HTMLResponse)
async def admin_stats(password: str = Query(...)):
    _check_password(password)
    stats = db_logger.get_stats_today()

    last_error_html = "—"
    if stats["last_error"]:
        last_error_html = (
            f'<span style="color:#e74c3c">{stats["last_error"]["message"]}</span>'
            f'<br><small style="color:#666">{stats["last_error"]["timestamp"]}</small>'
        )

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Stats — Metodist</title>
  <meta http-equiv="refresh" content="30">
  <style>
    body {{ font-family: monospace; background: #111; color: #eee; padding: 20px; }}
    h1 {{ color: #fff; }}
    .card {{ background: #1a1a1a; border-radius: 8px; padding: 20px; margin: 12px 0; display: inline-block; min-width: 200px; }}
    .card .val {{ font-size: 48px; font-weight: bold; }}
    .green {{ color: #2ecc71; }}
    .red {{ color: #e74c3c; }}
    .meta {{ color: #666; font-size: 12px; margin-bottom: 12px; }}
    a {{ color: #aaa; }}
  </style>
</head>
<body>
  <h1>Metodist Stats</h1>
  <div class="meta">Сегодня · <a href="/admin/logs?password={password}">Logs</a></div>
  <div class="card">
    <div class="green val">{stats["worksheets_today"]}</div>
    <div>Рабочих листов</div>
  </div>
  &nbsp;
  <div class="card">
    <div class="green val">{stats["activities_today"]}</div>
    <div>Активностей</div>
  </div>
  &nbsp;
  <div class="card">
    <div class="red val">{stats["errors_today"]}</div>
    <div>Ошибок</div>
  </div>
  <br><br>
  <div>
    <b>Последняя ошибка:</b><br>
    {last_error_html}
  </div>
</body>
</html>"""
    return html


@app.get("/health")
async def health():
    return {"status": "ok"}
