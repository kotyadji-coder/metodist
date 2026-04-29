"""Worksheet HTML renderer: builds final HTML from analysis + tasks data."""

import json
import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from generators.grids import build_word_search_grid, build_crossword_grid

CONTENT_DIR = Path(__file__).parent.parent / "content"
CONTENT_DIR.mkdir(exist_ok=True)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))
_jinja_env.filters["tojson"] = json.dumps


def _postprocess_tasks(tasks: list[dict]) -> list[dict]:
    """Run code generators for tasks that need them."""
    for task in tasks:
        t = task.get("type")
        if t == "word_search" and "grid" not in task:
            task["grid"] = build_word_search_grid(
                task.get("words", []),
                task.get("grid_size", 8),
            )
        elif t == "crossword_mini" and "crossword" not in task:
            task["crossword"] = build_crossword_grid(
                task.get("words", []),
                task.get("clues", []),
            )
    return tasks


def save_worksheet(
    image_bytes: bytes | None,
    analysis: dict,
    tasks_data: dict,
    server_url: str = "http://localhost:8002",
) -> str:
    """Render worksheet HTML and save to content/. Returns content_id."""
    content_id = str(uuid.uuid4())[:8]

    # Save coloring image
    if image_bytes is not None:
        image_path = CONTENT_DIR / f"{content_id}.png"
        image_path.write_bytes(image_bytes)
        coloring_image_url = f"{server_url}/content/{content_id}.png"
    else:
        coloring_image_url = None

    tasks = tasks_data.get("tasks", [])
    tasks = _postprocess_tasks(tasks)
    has_coloring_task = any(t.get("type") == "coloring" for t in tasks)

    # Build topics string for display
    topics = analysis.get("topics", [])
    if topics:
        topic_str = " / ".join(t.get("topic", "") for t in topics)
    else:
        topic_str = analysis.get("topic", "")

    context = {
        "title": analysis.get("title", "Рабочий лист"),
        "subject": analysis.get("subject", ""),
        "grade": analysis.get("grade", ""),
        "topic": topic_str,
        "theme": analysis.get("theme", ""),
        "child_name": analysis.get("child_name"),
        "coloring_image_url": coloring_image_url,
        "has_coloring_task": has_coloring_task,
        "tasks": tasks,
    }

    html = _jinja_env.get_template("worksheet.html").render(**context)
    (CONTENT_DIR / f"{content_id}.html").write_text(html, encoding="utf-8")
    (CONTENT_DIR / f"{content_id}.json").write_text(
        json.dumps(context, ensure_ascii=False), encoding="utf-8"
    )

    return content_id
