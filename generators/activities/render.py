"""Render full-page activity HTML from LLM data."""

import base64
import json
import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

CONTENT_DIR = Path(__file__).parent.parent.parent / "content"
CONTENT_DIR.mkdir(exist_ok=True)

_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))
_jinja_env.filters["tojson"] = json.dumps


def save_activity(
    activity_type: str,
    analysis: dict,
    activity_data: dict,
    server_url: str = "http://localhost:8002",
    image_bytes: bytes | None = None,
) -> str:
    """Render activity HTML and save to content/. Returns content_id."""
    content_id = str(uuid.uuid4())[:8]

    topics = analysis.get("topics", [])
    topic_str = " / ".join(t.get("topic", "") for t in topics) if topics else analysis.get("topic", "")

    context = {
        "subject": analysis.get("subject", ""),
        "grade": analysis.get("grade", ""),
        "topic": topic_str,
        "child_name": analysis.get("child_name"),
        **activity_data,
    }

    # Embed image as data URL for cipher
    if image_bytes:
        b64 = base64.b64encode(image_bytes).decode("ascii")
        context["image_url"] = f"data:image/png;base64,{b64}"

    template_name = f"activities/{activity_type}.html"
    html = _jinja_env.get_template(template_name).render(**context)
    (CONTENT_DIR / f"{content_id}.html").write_text(html, encoding="utf-8")
    (CONTENT_DIR / f"{content_id}.json").write_text(
        json.dumps({k: v for k, v in context.items() if k != "image_url"}, ensure_ascii=False),
        encoding="utf-8",
    )

    return content_id
