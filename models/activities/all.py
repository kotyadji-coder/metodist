"""Pydantic models for all 6 full-page activity types."""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal


class ActivityBase(BaseModel):
    """Common fields for all activities."""
    story: str = Field(default="", description="Mini story intro, 2-3 sentences, themed to the universe. Engaging hook like Banda Umnikov.")
    title: str = Field(description="Activity title, fun and themed")


# ── 1. CIPHER ───────────────────────────────────────────────────────────────

class CipherActivity(ActivityBase):
    type: Literal["cipher"] = "cipher"
    instruction: str = Field(description="Short instruction for the child")
    cipher_key: dict[str, str] = Field(
        description="Mapping: number/symbol -> letter. E.g. {'1': 'П', '2': 'Р', ...}"
    )
    encoded_lines: list[str] = Field(
        min_length=2, max_length=4,
        description="Encoded phrases using the cipher key numbers/symbols. E.g. ['1 2 3 4 5 6', '7 8 9 10']"
    )
    fun_answer_hint: str = Field(description="Funny hint about the decoded message")


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
