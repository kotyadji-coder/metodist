"""Pydantic models for the Worksheet Generator."""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, Field


# ── Step 1: LLM Analysis Output ─────────────────────────────────────────────

class WorksheetAnalysis(BaseModel):
    subject: str = Field(description="Предмет: Математика, Русский язык, Окружающий мир, etc.")
    grade: int = Field(ge=1, le=4, description="Класс, зажатый в диапазон 1-4")
    topic: str = Field(description="Точная тема по ФГОС для данного класса")
    theme: str = Field(description="Визуальная тема/вселенная: Batman, Minecraft, etc.")
    child_name: str | None = Field(default=None, description="Имя ребёнка, если указано")
    title: str = Field(description="Креативное название рабочего листа")
    coloring_prompt: str = Field(description="English prompt for B&W coloring page image")


# ── Step 2: Task Mechanic Models ─────────────────────────────────────────────

class MatchingTask(BaseModel):
    type: Literal["matching"]
    instruction: str
    left_column: list[str] = Field(min_length=4, max_length=4)
    right_column: list[str] = Field(min_length=4, max_length=4)


class GridMazeTask(BaseModel):
    type: Literal["grid_maze"]
    instruction: str
    grid_size: Literal[4] = 4
    cells: list[str] = Field(min_length=16, max_length=16)
    correct_path: list[int]


class AnagramTask(BaseModel):
    type: Literal["anagram"]
    instruction: str
    scrambled: str
    hint: str
    answer_length: int


class FillBlanksTask(BaseModel):
    type: Literal["fill_blanks"]
    instruction: str
    text_with_blanks: str
    correct: list[str]


class EmptyBoxesTask(BaseModel):
    type: Literal["empty_boxes"]
    instruction: str
    box_count: int = Field(ge=4, le=6)
    labels: list[str] | None = None


class LinesTask(BaseModel):
    type: Literal["lines"]
    instruction: str
    prompt_text: str
    line_count: Literal[3] = 3


class SortingTableTask(BaseModel):
    type: Literal["sorting_table"]
    instruction: str
    column_headers: list[str] = Field(min_length=2, max_length=2)
    word_bank: list[str] = Field(min_length=4, max_length=8)


class OddOneOutTask(BaseModel):
    type: Literal["odd_one_out"]
    instruction: str
    items: list[str] = Field(min_length=4, max_length=4)


class WordSearchTask(BaseModel):
    type: Literal["word_search"]
    instruction: str
    words: list[str] = Field(min_length=3, max_length=5)
    grid_size: Literal[8] = 8


class BigCanvasTask(BaseModel):
    type: Literal["big_canvas"]
    instruction: str
    prompt_text: str


class ColoringTask(BaseModel):
    type: Literal["coloring"]
    instruction: str
    prompt_text: str
    line_count: int = Field(default=3, ge=2, le=4)


WorksheetTask = Union[
    MatchingTask,
    GridMazeTask,
    AnagramTask,
    FillBlanksTask,
    EmptyBoxesTask,
    LinesTask,
    SortingTableTask,
    OddOneOutTask,
    WordSearchTask,
    BigCanvasTask,
    ColoringTask,
]


# ── Step 2: Top-Level Output ─────────────────────────────────────────────────

class WorksheetTasks(BaseModel):
    tasks: list[WorksheetTask] = Field(min_length=4, max_length=4)
