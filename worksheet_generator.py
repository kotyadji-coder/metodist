"""Worksheet post-processing: word search grid builder and HTML save."""

import json
import random
import uuid
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

CONTENT_DIR = Path(__file__).parent / "content"
CONTENT_DIR.mkdir(exist_ok=True)

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)))
_jinja_env.filters["tojson"] = json.dumps

CYRILLIC = "АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ"


def build_word_search_grid(words: list[str], grid_size: int = 8) -> list[list[str]]:
    """Place words horizontally or vertically into a grid, fill the rest with random Cyrillic."""
    grid = [["" for _ in range(grid_size)] for _ in range(grid_size)]

    for word in words:
        upper = word.upper().replace("Ё", "Е").replace("Й", "И")
        placed = False
        for _ in range(200):
            direction = random.choice(["H", "V"])
            if direction == "H":
                row = random.randint(0, grid_size - 1)
                max_col = grid_size - len(upper)
                if max_col < 0:
                    continue
                col = random.randint(0, max_col)
                if all(grid[row][col + i] in ("", upper[i]) for i in range(len(upper))):
                    for i, ch in enumerate(upper):
                        grid[row][col + i] = ch
                    placed = True
                    break
            else:
                max_row = grid_size - len(upper)
                if max_row < 0:
                    continue
                row = random.randint(0, max_row)
                col = random.randint(0, grid_size - 1)
                if all(grid[row + i][col] in ("", upper[i]) for i in range(len(upper))):
                    for i, ch in enumerate(upper):
                        grid[row + i][col] = ch
                    placed = True
                    break

        if not placed:
            # Force horizontal placement in first available row
            for r in range(grid_size):
                max_c = grid_size - len(upper)
                if max_c < 0:
                    break
                for c in range(max_c + 1):
                    if all(grid[r][c + i] in ("", upper[i]) for i in range(len(upper))):
                        for i, ch in enumerate(upper):
                            grid[r][c + i] = ch
                        placed = True
                        break
                if placed:
                    break

    # Fill empty cells with random letters
    for r in range(grid_size):
        for c in range(grid_size):
            if grid[r][c] == "":
                grid[r][c] = random.choice(CYRILLIC)

    return grid


def save_worksheet(
    image_bytes: bytes | None,
    analysis: dict,
    tasks_data: dict,
    server_url: str = "http://localhost:8000",
) -> str:
    """Render worksheet HTML template and save to content/ directory. Returns content_id."""
    content_id = str(uuid.uuid4())[:8]

    # Save coloring image
    if image_bytes is not None:
        image_path = CONTENT_DIR / f"{content_id}.png"
        image_path.write_bytes(image_bytes)
        coloring_image_url = f"{server_url}/content/{content_id}.png"
    else:
        coloring_image_url = None

    # Check if there's a coloring task
    tasks = tasks_data.get("tasks", [])
    has_coloring_task = any(t.get("type") == "coloring" for t in tasks)

    # Build template context
    context = {
        "title": analysis.get("title", "Рабочий лист"),
        "subject": analysis.get("subject", ""),
        "grade": analysis.get("grade", ""),
        "topic": analysis.get("topic", ""),
        "theme": analysis.get("theme", ""),
        "child_name": analysis.get("child_name"),
        "coloring_image_url": coloring_image_url,
        "has_coloring_task": has_coloring_task,
        "tasks": tasks,
    }

    # Render HTML
    html = _jinja_env.get_template("worksheet.html").render(**context)
    (CONTENT_DIR / f"{content_id}.html").write_text(html, encoding="utf-8")

    # Save context JSON for potential re-rendering
    (CONTENT_DIR / f"{content_id}.json").write_text(
        json.dumps(context, ensure_ascii=False), encoding="utf-8"
    )

    return content_id
