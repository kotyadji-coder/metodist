"""Pydantic models for all worksheet task mechanics.

Each model has a `type` literal so the LLM output can be parsed as a discriminated union.
Tasks are grouped by which subjects can use them.
"""

from __future__ import annotations

from typing import Literal, Union

from pydantic import BaseModel, Field


# ── UNIVERSAL TASKS (all subjects) ──────────────────────────────────────────

class ColoringTask(BaseModel):
    """Always task #1. Coloring image + related task. Image inserted by code."""
    type: Literal["coloring"]
    instruction: str = Field(description="Short instruction (max 60 chars)")
    prompt_text: str = Field(description="Task related to the coloring image")
    line_count: int = Field(default=3, ge=2, le=4)


class MatchingTask(BaseModel):
    """Connect pairs with lines. Works for any subject."""
    type: Literal["matching"]
    instruction: str
    left_column: list[str] = Field(min_length=4, max_length=4)
    right_column: list[str] = Field(min_length=4, max_length=4)


class FillBlanksTask(BaseModel):
    """Fill in missing words/numbers/letters in text."""
    type: Literal["fill_blanks"]
    instruction: str
    text_with_blanks: str = Field(description="Text with ____ for blanks")
    correct: list[str] = Field(description="Correct answers in order")


class SortingTableTask(BaseModel):
    """Sort items into 2-column table."""
    type: Literal["sorting_table"]
    instruction: str
    column_headers: list[str] = Field(min_length=2, max_length=2)
    word_bank: list[str] = Field(min_length=4, max_length=8)


class OddOneOutTask(BaseModel):
    """Find the item that doesn't belong and explain why."""
    type: Literal["odd_one_out"]
    instruction: str
    items: list[str] = Field(min_length=4, max_length=4)


# ── MATH TASKS ──────────────────────────────────────────────────────────────

class GridMazeTask(BaseModel):
    """Navigate 4x4 grid by choosing correct answers at each step."""
    type: Literal["grid_maze"]
    instruction: str
    grid_size: Literal[4] = 4
    cells: list[str] = Field(min_length=16, max_length=16, description="16 cell values left-to-right top-to-bottom")
    correct_path: list[int] = Field(description="Indices of correct-path cells")


class NumberPyramidTask(BaseModel):
    """Pyramid where each cell = sum of two cells below. Some cells are empty."""
    type: Literal["number_pyramid"]
    instruction: str
    rows: list[list[str]] = Field(
        description="Rows from top (1 cell) to bottom (3-4 cells). Empty cells = empty string.",
    )


class MagicSquareTask(BaseModel):
    """Fill a 3x3 grid so all rows, columns, diagonals sum to the same value."""
    type: Literal["magic_square"]
    instruction: str
    grid: list[list[str]] = Field(
        description="3x3 grid. Pre-filled cells have numbers, empty cells = empty string.",
    )
    target_sum: int = Field(description="The magic sum")


class ComparisonChainTask(BaseModel):
    """Put >, <, = between pairs of values."""
    type: Literal["comparison_chain"]
    instruction: str
    pairs: list[list[str]] = Field(
        min_length=3, max_length=6,
        description="Each pair is [left_value, right_value]. Child writes >, < or = between them.",
    )


class ExpressionBuilderTask(BaseModel):
    """Place +, -, x, / signs to make the equation true."""
    type: Literal["expression_builder"]
    instruction: str
    equations: list[str] = Field(
        min_length=3, max_length=4,
        description="Equations with circles for signs: '3 O 2 O 1 = 4'",
    )


class NumberSequenceTask(BaseModel):
    """Continue a number pattern."""
    type: Literal["number_sequence"]
    instruction: str
    sequences: list[list[str]] = Field(
        min_length=2, max_length=3,
        description="Each sequence is a list of values. Empty strings = blanks to fill.",
    )


# ── RUSSIAN LANGUAGE TASKS ──────────────────────────────────────────────────

class AnagramTask(BaseModel):
    """Unscramble letters to form a word."""
    type: Literal["anagram"]
    instruction: str
    scrambled: str = Field(description="Scrambled letters, e.g. ОЛШАК")
    hint: str
    answer_length: int


class WordSearchTask(BaseModel):
    """Find hidden words in a letter grid. Grid is built by Python code."""
    type: Literal["word_search"]
    instruction: str
    words: list[str] = Field(min_length=3, max_length=5)
    grid_size: Literal[8] = 8


class SyllableBuilderTask(BaseModel):
    """Build words from syllable blocks."""
    type: Literal["syllable_builder"]
    instruction: str
    syllable_groups: list[list[str]] = Field(
        min_length=3, max_length=4,
        description="Each group is a list of syllables that form one word. E.g. ['МО','ЛО','КО']",
    )


class SentenceOrderTask(BaseModel):
    """Arrange scrambled words into a correct sentence."""
    type: Literal["sentence_order"]
    instruction: str
    scrambled_sentences: list[list[str]] = Field(
        min_length=2, max_length=3,
        description="Each item is a list of words in wrong order",
    )


class WordChainTask(BaseModel):
    """Last letter of a word = first letter of the next. Child fills the gaps."""
    type: Literal["word_chain"]
    instruction: str
    given_words: list[str] = Field(
        min_length=2, max_length=3,
        description="Pre-filled words. Child fills words between them.",
    )
    chain_length: int = Field(ge=4, le=6, description="Total words in chain including given ones")


class MissingVowelsTask(BaseModel):
    """Words with vowels removed. Child fills them in."""
    type: Literal["missing_vowels"]
    instruction: str
    words_with_gaps: list[str] = Field(
        min_length=4, max_length=6,
        description="Words with underscores for missing vowels: к_р_в_",
    )


# ── ENGLISH LANGUAGE TASKS ──────────────────────────────────────────────────

class LetterUnscrambleTask(BaseModel):
    """Arrange jumbled letters into an English word."""
    type: Literal["letter_unscramble"]
    instruction: str
    scrambled_words: list[str] = Field(
        min_length=3, max_length=5,
        description="Scrambled English words, e.g. ['p-a-p-l-e', 'o-g-f-r']",
    )
    hints: list[str] = Field(description="One hint per word")


class SentenceBuildTask(BaseModel):
    """Build an English sentence from scrambled words."""
    type: Literal["sentence_build"]
    instruction: str
    scrambled_sentences: list[list[str]] = Field(
        min_length=2, max_length=3,
        description="Each item is list of English words in wrong order",
    )


class CrosswordMiniTask(BaseModel):
    """Small crossword with 3-4 words and clues."""
    type: Literal["crossword_mini"]
    instruction: str
    words: list[str] = Field(min_length=3, max_length=4, description="Words to place")
    clues: list[str] = Field(description="One clue per word")


# ── SCIENCE TASKS (Окружающий мир) ──────────────────────────────────────────

class SequenceOrderTask(BaseModel):
    """Arrange items in the correct order (life cycle, seasons, food chain)."""
    type: Literal["sequence_order"]
    instruction: str
    items: list[str] = Field(
        min_length=4, max_length=6,
        description="Items in SCRAMBLED order. Child must arrange them correctly.",
    )


class TrueFalseFixTask(BaseModel):
    """Find the error in a statement and fix it."""
    type: Literal["true_false_fix"]
    instruction: str
    statements: list[str] = Field(
        min_length=3, max_length=4,
        description="Mix of correct and incorrect statements. Child crosses out wrong ones and writes corrections.",
    )


class CauseEffectTask(BaseModel):
    """Connect causes to their effects."""
    type: Literal["cause_effect"]
    instruction: str
    causes: list[str] = Field(min_length=4, max_length=4)
    effects: list[str] = Field(min_length=4, max_length=4, description="Shuffled effects")


class RiddleBoxesTask(BaseModel):
    """Solve riddles and write answers in letter boxes."""
    type: Literal["riddle_boxes"]
    instruction: str
    riddles: list[str] = Field(min_length=3, max_length=4)
    answer_lengths: list[int] = Field(description="Number of letters in each answer")


# ── UNION TYPE ──────────────────────────────────────────────────────────────

WorksheetTask = Union[
    # Universal
    ColoringTask,
    MatchingTask,
    FillBlanksTask,
    SortingTableTask,
    OddOneOutTask,
    # Math
    GridMazeTask,
    NumberPyramidTask,
    MagicSquareTask,
    ComparisonChainTask,
    ExpressionBuilderTask,
    NumberSequenceTask,
    # Russian
    AnagramTask,
    WordSearchTask,
    SyllableBuilderTask,
    SentenceOrderTask,
    WordChainTask,
    MissingVowelsTask,
    # English
    LetterUnscrambleTask,
    SentenceBuildTask,
    CrosswordMiniTask,
    # Science
    SequenceOrderTask,
    TrueFalseFixTask,
    CauseEffectTask,
    RiddleBoxesTask,
]


class WorksheetTasks(BaseModel):
    """Step 2 output: exactly 4 tasks (coloring + 3 subject tasks)."""
    tasks: list[WorksheetTask] = Field(min_length=4, max_length=4)


# ── SUBJECT TASK POOLS ──────────────────────────────────────────────────────

MATH_TASKS = [
    "matching", "fill_blanks", "sorting_table", "odd_one_out",
    "grid_maze", "number_pyramid", "magic_square", "comparison_chain",
    "expression_builder", "number_sequence",
]

RUSSIAN_TASKS = [
    "matching", "fill_blanks", "sorting_table", "odd_one_out",
    "anagram", "word_search", "syllable_builder", "sentence_order",
    "word_chain", "missing_vowels",
]

ENGLISH_TASKS = [
    "matching", "fill_blanks", "sorting_table", "odd_one_out",
    "anagram", "word_search", "letter_unscramble", "sentence_build",
    "crossword_mini",
]

SCIENCE_TASKS = [
    "matching", "fill_blanks", "sorting_table", "odd_one_out",
    "word_search", "sequence_order", "true_false_fix", "cause_effect",
    "riddle_boxes",
]

SUBJECT_TASK_POOLS = {
    "Математика": MATH_TASKS,
    "Русский язык": RUSSIAN_TASKS,
    "Английский язык": ENGLISH_TASKS,
    "Окружающий мир": SCIENCE_TASKS,
}
