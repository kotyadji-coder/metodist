"""Worksheet HTML renderer: builds final HTML from analysis + tasks data."""

import json
import random
import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from generators.grids import build_word_search_grid, build_crossword_grid

CONTENT_DIR = Path(__file__).parent.parent / "content"
CONTENT_DIR.mkdir(exist_ok=True)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))
_jinja_env.filters["tojson"] = json.dumps


def _shuffle_until_different(items: list) -> list:
    """Shuffle a list, ensuring result differs from original (if len > 1)."""
    if len(items) <= 1:
        return items
    original = list(items)
    shuffled = list(items)
    for _ in range(20):
        random.shuffle(shuffled)
        if shuffled != original:
            return shuffled
    return shuffled


def _postprocess_tasks(tasks: list[dict]) -> list[dict]:
    """Run code generators and fix ordering for tasks that need them."""
    for task in tasks:
        t = task.get("type")

        # Build grids
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

        # Shuffle right_column in matching so answers aren't obvious
        elif t == "matching" and "right_column" in task:
            task["right_column"] = _shuffle_until_different(task["right_column"])

        # Shuffle words inside each sentence for sentence_order / sentence_build
        elif t in ("sentence_order", "sentence_build") and "scrambled_sentences" in task:
            task["scrambled_sentences"] = [
                _shuffle_until_different(sent) for sent in task["scrambled_sentences"]
            ]

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
