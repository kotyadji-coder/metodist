"""Pydantic models for all 6 full-page activity types."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal


class ActivityBase(BaseModel):
    """Common fields for all activities."""
    story: str = Field(default="", description="Mini story intro, 2-3 sentences, themed to the universe. Engaging hook like Banda Umnikov.")
    title: str = Field(description="Activity title, fun and themed")


# ── 1. CIPHER ───────────────────────────────────────────────────────────────

class CipherTaskItem(BaseModel):
    question: str = Field(description="Task question, e.g. 'Сколько слогов в слове СОБАКА?' or 'Вставь букву: М_РОЗ'")
    answer: str = Field(description="Correct answer (number or letter)")
    options: list[str] = Field(default=[], description="For variant 1 only: ['А → К', 'О → С'] showing which choice gives which cipher letter")

class CipherActivity(ActivityBase):
    type: Literal["cipher"] = "cipher"
    cipher_mode: str = Field(
        default="expressions",
        description="'expressions' for math, 'tasks' for Russian/other subjects"
    )
    instruction: str = Field(description="Short instruction for the child")
    cipher_key: dict[str, str] = Field(
        description="Mapping: answer -> letter. E.g. {'5': 'П', '8': 'Р', ...}"
    )
    # For math mode (cipher_mode="expressions"):
    encoded_lines: list[str] = Field(
        default=[],
        description="Encoded phrases with math expressions. E.g. ['2+3 4+4 1+2', '6+6 3+4 5+5']"
    )
    # For task mode (cipher_mode="tasks"):
    cipher_tasks: list[CipherTaskItem] = Field(
        default=[],
        description="List of questions. Each answer maps via cipher_key to a letter of the secret word."
    )
    secret_word: str = Field(default="", description="The decoded secret word/phrase")
    fun_answer_hint: str = Field(description="Funny hint or bonus task after decoding")


# ── 2. CAFE ─────────────────────────────────────────────────────────────────

class CafeMenuItem(BaseModel):
    name: str
    price: int
    emoji: str = Field(description="One emoji for this item")

class CafeTask(BaseModel):
    question: str
    answer_lines: int = Field(default=1, ge=1, le=3)

class CafeActivity(ActivityBase):
    type: Literal["cafe"] = "cafe"
    cafe_name: str = Field(description="Themed cafe name, e.g. 'Кафе Хогвартса'")
    menu: list[CafeMenuItem] = Field(min_length=5, max_length=8)
    tasks: list[CafeTask] = Field(min_length=3, max_length=5)
    budget_task: str = Field(description="Final task: plan a meal for X coins/credits")
    budget_amount: int


# ── 3. SHOP ─────────────────────────────────────────────────────────────────

class ShopItem(BaseModel):
    name: str
    price: int
    emoji: str

class ShopTask(BaseModel):
    question: str
    answer_lines: int = Field(default=1, ge=1, le=3)

class ShopActivity(ActivityBase):
    type: Literal["shop"] = "shop"
    shop_name: str = Field(description="Themed shop name")
    items: list[ShopItem] = Field(min_length=5, max_length=8)
    tasks: list[ShopTask] = Field(min_length=3, max_length=5)
    shopping_list_task: str = Field(description="Final task: buy items from a list within budget")
    budget_amount: int


# ── 4. (removed — color_by_value)


# ── 5. MAZE ─────────────────────────────────────────────────────────────────

class MazeActivity(ActivityBase):
    type: Literal["maze"] = "maze"
    instruction: str = Field(description="E.g. 'Иди по верным примерам от СТАРТА до ФИНИША!'")
    grid_size: int = Field(default=7, description="Grid NxN size (6-8)")
    cells: list[str] = Field(
        description="grid_size*grid_size cells. Each cell is an expression like '3+4=7' or '2x3=8'. Mix correct and wrong."
    )
    correct_path: list[int] = Field(
        description="Indices of cells forming the path from top-left to bottom-right. Only adjacent cells (up/down/left/right)."
    )


# ── 6. (removed — number_chain moved to worksheet tasks)
