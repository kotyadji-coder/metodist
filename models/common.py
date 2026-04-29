"""Shared models used across worksheet and activity pipelines."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TopicInfo(BaseModel):
    """A single parsed topic from the user's request."""
    subject: str = Field(description="Subject: Математика, Русский язык, Английский язык, Окружающий мир, etc.")
    topic: str = Field(description="Exact FGOS topic for this grade level")


class WorksheetAnalysis(BaseModel):
    """Step 1 output: parsed user request."""
    subject: str = Field(description="Primary subject (for task pool selection)")
    grade: int = Field(ge=1, le=4, description="Grade clamped to 1-4")
    topics: list[TopicInfo] = Field(
        min_length=1, max_length=4,
        description="1-4 topics parsed from user request. If user gave one topic, list has 1 item.",
    )
    theme: str = Field(description="Visual universe: Batman, Minecraft, Щенячий патруль, etc.")
    child_name: str | None = Field(default=None, description="Child's name if provided")
    title: str = Field(description="Creative worksheet title (3-6 words, references the universe)")
    coloring_prompt: str = Field(description="English prompt for B&W coloring page image generation")
