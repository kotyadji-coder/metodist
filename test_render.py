"""Render test worksheets for all mechanics without API calls.

Run: python test_render.py
Opens HTML files in browser.
"""

import webbrowser
from pathlib import Path

from generators.worksheet import save_worksheet


# ── MATH: Minecraft ─────────────────────────────────────────────────────────

MATH_ANALYSIS = {
    "subject": "Математика",
    "grade": 2,
    "topics": [
        {"subject": "Математика", "topic": "Сложение и вычитание в пределах 100"},
        {"subject": "Математика", "topic": "Таблица умножения на 2 и 3"},
    ],
    "theme": "Minecraft",
    "child_name": "Артём",
    "title": "Шахта чисел Стива",
    "coloring_prompt": "...",
}

MATH_TASKS = {
    "tasks": [
        {
            "type": "coloring",
            "instruction": "Раскрась Стива и выполни задание!",
            "prompt_text": "Стив нашёл в шахте алмазы и изумруды. Посчитай все сокровища на картинке и запиши.",
            "line_count": 2,
        },
        {
            "type": "number_pyramid",
            "instruction": "Пирамида из блоков: каждый = сумма двух под ним.",
            "rows": [
                [""],
                ["", ""],
                ["5", "", "3"],
            ],
        },
        {
            "type": "comparison_chain",
            "instruction": "Поставь знак >, < или =",
            "pairs": [
                ["15 алмазов + 3", "20 алмазов"],
                ["2 стака x 3", "5 стаков"],
                ["48 блоков", "50 - 2 блока"],
                ["3 зелья x 3", "10 зелий"],
            ],
        },
        {
            "type": "expression_builder",
            "instruction": "Расставь знаки +, -, x в рецептах крафта.",
            "equations": [
                "3 O 2 O 1 = 4 блока",
                "8 O 4 O 2 = 6 мечей",
                "5 O 3 O 2 = 16 факелов",
            ],
        },
    ]
}

# ── MATH 2: Человек-паук ───────────────────────────────────────────────────

MATH_ANALYSIS_2 = {
    "subject": "Математика",
    "grade": 3,
    "topics": [{"subject": "Математика", "topic": "Таблица умножения"}],
    "theme": "Человек-паук",
    "child_name": None,
    "title": "Паутина умножения",
    "coloring_prompt": "...",
}

MATH_TASKS_2 = {
    "tasks": [
        {
            "type": "coloring",
            "instruction": "Раскрась героя и реши задачу!",
            "prompt_text": "Паук сплёл 3 паутины. В каждой поймал по 4 злодея. Сколько всего злодеев поймал Паук?",
            "line_count": 2,
        },
        {
            "type": "magic_square",
            "instruction": "Магический щит Паука: суммы строк = столбцов.",
            "grid": [
                ["8", "", "6"],
                ["", "5", ""],
                ["4", "", ""],
            ],
            "target_sum": 15,
        },
        {
            "type": "number_sequence",
            "instruction": "Паук прыгает по крышам — найди закономерность!",
            "sequences": [
                ["3", "6", "9", "", ""],
                ["20", "16", "12", "", ""],
            ],
        },
        {
            "type": "grid_maze",
            "instruction": "Помоги Пауку: иди по правильным ответам!",
            "grid_size": 4,
            "cells": [
                "2x3=6", "4x2=9", "3x3=8", "5x1=6",
                "1x7=8", "2x3=6", "7x1=7", "3x4=11",
                "5x2=9", "3x2=5", "2x4=8", "6x2=11",
                "4x3=11", "2x5=9", "3x3=8", "4x2=8",
            ],
            "correct_path": [0, 5, 6, 10, 15],
        },
    ]
}

# ── RUSSIAN: Щенячий патруль ────────────────────────────────────────────────

RUSSIAN_ANALYSIS = {
    "subject": "Русский язык",
    "grade": 2,
    "topics": [
        {"subject": "Русский язык", "topic": "Правописание ЖИ-ШИ, ЧА-ЩА, ЧУ-ЩУ"},
    ],
    "theme": "Щенячий патруль",
    "child_name": "Соня",
    "title": "Грамотный патруль",
    "coloring_prompt": "...",
}

RUSSIAN_TASKS = {
    "tasks": [
        {
            "type": "coloring",
            "instruction": "Раскрась щенка и выполни задание!",
            "prompt_text": "Придумай 2 предложения про спасательную миссию Гонщика.",
            "line_count": 3,
        },
        {
            "type": "syllable_builder",
            "instruction": "Собери слова из слогов — помоги щенкам!",
            "syllable_groups": [
                ["МА", "ШИ", "НА"],
                ["ЧА", "ШКА"],
                ["ЩУ", "КА"],
            ],
        },
        {
            "type": "missing_vowels",
            "instruction": "Щенки потеряли гласные — впиши их!",
            "words_with_gaps": [
                "ж_знь", "ш_шка", "ч_до", "щ_ка", "ч_йник", "ш_на",
            ],
        },
        {
            "type": "sorting_table",
            "instruction": "Маршалл просит рассортировать слова!",
            "column_headers": ["ЖИ-ШИ", "ЧА-ЩА"],
            "word_bank": ["жизнь", "чаша", "шина", "роща", "живот", "чайка"],
        },
    ]
}

# ── RUSSIAN 2: Гарри Поттер ────────────────────────────────────────────────

RUSSIAN_ANALYSIS_2 = {
    "subject": "Русский язык",
    "grade": 3,
    "topics": [{"subject": "Русский язык", "topic": "Состав слова"}],
    "theme": "Гарри Поттер",
    "child_name": None,
    "title": "Заклинания русского языка",
    "coloring_prompt": "...",
}

RUSSIAN_TASKS_2 = {
    "tasks": [
        {
            "type": "coloring",
            "instruction": "Раскрась волшебника и выполни задание!",
            "prompt_text": "Придумай заклинание для урока русского языка и запиши его.",
            "line_count": 2,
        },
        {
            "type": "anagram",
            "instruction": "Расшифруй заклинание Гермионы!",
            "scrambled": "НЬЕЛОК",
            "hint": "Часть слова в самом начале (как у заклинания — приставка!)",
            "answer_length": 6,
        },
        {
            "type": "sentence_order",
            "instruction": "Расколдуй предложения — расставь слова!",
            "scrambled_sentences": [
                ["волшебник", "заклинание", "произнёс", "Юный"],
                ["летит", "по", "метла", "небу", "Хогвартса"],
            ],
        },
        {
            "type": "word_chain",
            "instruction": "Волшебная цепочка: последняя буква = первая!",
            "given_words": ["метла", "алмаз"],
            "chain_length": 5,
        },
    ]
}

# ── ENGLISH: Pokemon ────────────────────────────────────────────────────────

ENGLISH_ANALYSIS = {
    "subject": "Английский язык",
    "grade": 2,
    "topics": [{"subject": "Английский язык", "topic": "Animals and colors"}],
    "theme": "Pokemon",
    "child_name": "Миша",
    "title": "Pokemon English Academy",
    "coloring_prompt": "...",
}

ENGLISH_TASKS = {
    "tasks": [
        {
            "type": "coloring",
            "instruction": "Color the Pokemon and answer!",
            "prompt_text": "What color is Pikachu? Write 2 sentences about your favorite Pokemon.",
            "line_count": 3,
        },
        {
            "type": "letter_unscramble",
            "instruction": "Расшифруй имена покемонов!",
            "scrambled_words": ["c-a-t-e-r-p-i-e", "b-i-d-r", "f-o-g-r", "f-h-s-i"],
            "hints": ["гусеничка", "птичка", "лягушка", "рыбка"],
        },
        {
            "type": "matching",
            "instruction": "Соедини покемона с его типом.",
            "left_column": ["Pikachu", "Squirtle", "Charmander", "Bulbasaur"],
            "right_column": ["water", "fire", "grass", "electric"],
        },
        {
            "type": "sentence_build",
            "instruction": "Составь предложение о покемонах.",
            "scrambled_sentences": [
                ["is", "yellow", "Pikachu"],
                ["likes", "Ash", "Pokemon"],
                ["can", "Charmander", "fire", "breathe"],
            ],
        },
    ]
}

# ── ENGLISH 2: Minecraft crossword ─────────────────────────────────────────

ENGLISH_ANALYSIS_2 = {
    "subject": "Английский язык",
    "grade": 3,
    "topics": [{"subject": "Английский язык", "topic": "Food and items"}],
    "theme": "Minecraft",
    "child_name": None,
    "title": "Minecraft Craft & Spell",
    "coloring_prompt": "...",
}

ENGLISH_TASKS_2 = {
    "tasks": [
        {
            "type": "coloring",
            "instruction": "Color the scene and describe!",
            "prompt_text": "What items can Steve craft? Write 2 in English.",
            "line_count": 2,
        },
        {
            "type": "crossword_mini",
            "instruction": "Кроссворд Стива — предметы из Minecraft.",
            "words": ["STONE", "TORCH", "OAK", "END"],
            "clues": [
                "You mine this grey block",
                "Lights up dark caves",
                "A type of wood tree",
                "The final dimension",
            ],
        },
        {
            "type": "matching",
            "instruction": "Соедини предмет с переводом.",
            "left_column": ["sword", "shield", "potion", "armor"],
            "right_column": ["зелье", "щит", "меч", "броня"],
        },
        {
            "type": "odd_one_out",
            "instruction": "Find the odd one out — what's NOT a Minecraft mob?",
            "items": ["Creeper", "Zombie", "Pikachu", "Enderman"],
        },
    ]
}

# ── SCIENCE: Фиксики ───────────────────────────────────────────────────────

SCIENCE_ANALYSIS = {
    "subject": "Окружающий мир",
    "grade": 2,
    "topics": [
        {"subject": "Окружающий мир", "topic": "Живая и неживая природа"},
        {"subject": "Окружающий мир", "topic": "Времена года"},
    ],
    "theme": "Фиксики",
    "child_name": None,
    "title": "Лаборатория Фиксиков",
    "coloring_prompt": "...",
}

SCIENCE_TASKS = {
    "tasks": [
        {
            "type": "coloring",
            "instruction": "Раскрась Нолика и ответь на вопрос!",
            "prompt_text": "Нолик исследует природу. Что на картинке — живое, а что неживое? Запиши.",
            "line_count": 3,
        },
        {
            "type": "sequence_order",
            "instruction": "Помоги Симке расставить времена года!",
            "items": ["Лето", "Весна", "Зима", "Осень"],
        },
        {
            "type": "true_false_fix",
            "instruction": "Нолик написал факты — найди ошибки и исправь!",
            "statements": [
                "У паука 6 ног.",
                "Солнце — это звезда.",
                "Рыбы дышат лёгкими.",
            ],
        },
        {
            "type": "cause_effect",
            "instruction": "Дим Димыч спрашивает: что к чему приводит?",
            "causes": ["Наступила зима", "Пошёл дождь", "Подул ветер", "Выглянуло солнце"],
            "effects": ["Снег начал таять", "Появились лужи", "Листья полетели", "Река замёрзла"],
        },
    ]
}

# ── SCIENCE 2: Мир приключений ──────────────────────────────────────────────

SCIENCE_ANALYSIS_2 = {
    "subject": "Окружающий мир",
    "grade": 3,
    "topics": [{"subject": "Окружающий мир", "topic": "Растения"}],
    "theme": "Мир приключений",
    "child_name": "Лиза",
    "title": "Тайны зелёного мира",
    "coloring_prompt": "...",
}

SCIENCE_TASKS_2 = {
    "tasks": [
        {
            "type": "coloring",
            "instruction": "Раскрась волшебное растение!",
            "prompt_text": "Путешественница Лиза нашла необычное растение. Подпиши его части: корень, стебель, лист, цветок.",
            "line_count": 2,
        },
        {
            "type": "riddle_boxes",
            "instruction": "Разгадай загадки о растениях-сокровищах!",
            "riddles": [
                "Сидит дед, во сто шуб одет. Кто его раздевает, тот слёзы проливает.",
                "Красна девица сидит в темнице, а коса на улице.",
                "Стоит Алёна — платок зелёный, тонкий стан, белый сарафан.",
            ],
            "answer_lengths": [3, 7, 6],
        },
        {
            "type": "word_search",
            "instruction": "Найди растения, спрятанные на карте!",
            "words": ["РОЗА", "ДУБ", "КЛЕН", "МАК"],
            "grid_size": 8,
        },
        {
            "type": "odd_one_out",
            "instruction": "Что здесь лишнее? Объясни почему!",
            "items": ["берёза", "дуб", "ромашка", "клён"],
        },
    ]
}


# ── RENDER ──────────────────────────────────────────────────────────────────

def render_all():
    test_sets = [
        ("math", MATH_ANALYSIS, MATH_TASKS),
        ("math2", MATH_ANALYSIS_2, MATH_TASKS_2),
        ("russian", RUSSIAN_ANALYSIS, RUSSIAN_TASKS),
        ("russian2", RUSSIAN_ANALYSIS_2, RUSSIAN_TASKS_2),
        ("english", ENGLISH_ANALYSIS, ENGLISH_TASKS),
        ("english2", ENGLISH_ANALYSIS_2, ENGLISH_TASKS_2),
        ("science", SCIENCE_ANALYSIS, SCIENCE_TASKS),
        ("science2", SCIENCE_ANALYSIS_2, SCIENCE_TASKS_2),
    ]

    content_dir = Path(__file__).parent / "content"
    content_dir.mkdir(exist_ok=True)

    for name, analysis, tasks in test_sets:
        content_id = save_worksheet(
            image_bytes=None,
            analysis=analysis,
            tasks_data=tasks,
            server_url="http://localhost:8002",
        )
        src = content_dir / f"{content_id}.html"
        dst = Path(__file__).parent / f"test_{name}.html"
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[OK] test_{name}.html")

    # Open main ones in browser
    for name in ["math", "math2", "russian", "russian2", "english", "english2", "science", "science2"]:
        p = Path(__file__).parent / f"test_{name}.html"
        if p.exists():
            webbrowser.open(str(p))


if __name__ == "__main__":
    render_all()
