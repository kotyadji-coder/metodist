"""Render test activities (Type 2) without API calls.

Run: python test_render_activities.py
Opens HTML files in browser.
"""

import webbrowser
from pathlib import Path

from generators.activities.render import save_activity

CONTENT_DIR = Path(__file__).parent / "content"
CONTENT_DIR.mkdir(exist_ok=True)

# ── Shared analysis ─────────────────────────────────────────────────────────

ANALYSIS_HP = {
    "subject": "Математика",
    "grade": 3,
    "topics": [{"subject": "Математика", "topic": "Сложение и вычитание в пределах 1000"}],
    "theme": "Гарри Поттер",
    "child_name": None,
}

ANALYSIS_MC = {
    "subject": "Математика",
    "grade": 2,
    "topics": [{"subject": "Математика", "topic": "Таблица умножения"}],
    "theme": "Minecraft",
    "child_name": "Артём",
}

ANALYSIS_FROZEN = {
    "subject": "Математика",
    "grade": 2,
    "topics": [{"subject": "Математика", "topic": "Сложение и вычитание в пределах 100"}],
    "theme": "Холодное сердце",
    "child_name": "Соня",
}

ANALYSIS_SPIDER = {
    "subject": "Русский язык",
    "grade": 3,
    "topics": [{"subject": "Русский язык", "topic": "Словарные слова"}],
    "theme": "Человек-паук",
    "child_name": None,
}

# ── CIPHER ──────────────────────────────────────────────────────────────────

CIPHER_MATH_DATA = {
    "title": "Тайное послание Дамблдора",
    "story": "Ты нашёл зашифрованную записку в библиотеке Хогвартса! Профессор Дамблдор спрятал секретное послание. Расшифруй его, пока Филч не нашёл тебя!",
    "cipher_mode": "expressions",
    "instruction": "Реши пример в каждой клетке, найди ответ в ключе и запиши букву!",
    "cipher_key": {
        "5": "М", "8": "А", "3": "Г", "12": "И", "7": "Я",
    },
    "encoded_lines": [
        "2+3 4+4 1+2 6+6 3+4",
    ],
    "cipher_tasks": [],
    "secret_word": "",
    "fun_answer_hint": "Подсказка: именно это делает тебя волшебником!",
}

CIPHER_RUSSIAN_DATA = {
    "title": "Заклинание грамотности",
    "story": "Гермиона нашла древний свиток с заклинанием! Но буквы зашифрованы — нужно решить задания по русскому языку, чтобы расшифровать магическое слово!",
    "cipher_mode": "tasks",
    "instruction": "Реши каждое задание. Найди ответ в ключе шифра — это буква секретного слова!",
    "cipher_key": {
        "3": "З", "2": "В", "5": "Е", "4": "З", "1": "Д", "6": "А",
    },
    "encoded_lines": [],
    "cipher_tasks": [
        {"question": "Сколько слогов в слове МОЛОКО?", "answer": "3", "options": []},
        {"question": "Сколько гласных в слове ЁЖИК?", "answer": "2", "options": []},
        {"question": "Сколько звуков в слове ЯМА?", "answer": "4", "options": []},
        {"question": "Сколько согласных в слове СТРОКА?", "answer": "4", "options": []},
        {"question": "Сколько букв в слове КОНЬ?", "answer": "4", "options": []},
        {"question": "Сколько слогов в слове КАРАНДАШ?", "answer": "3", "options": []},
    ],
    "secret_word": "ЗВЕЗДА",
    "fun_answer_hint": "Ты — настоящий волшебник! А теперь раздели все слова из заданий на слоги.",
}

CIPHER_ORTHO_DATA = {
    "title": "Орфографическое зелье",
    "story": "Профессор Снейп спрятал рецепт волшебного зелья! Чтобы его прочитать, вставь пропущенные буквы — каждая правильная буква откроет часть рецепта!",
    "cipher_mode": "tasks",
    "instruction": "Вставь пропущенную букву. Найди её в ключе шифра — узнаешь букву секретного слова!",
    "cipher_key": {
        "И": "С", "А": "О", "У": "В", "О": "А",
    },
    "encoded_lines": [],
    "cipher_tasks": [
        {"question": "Вставь букву: Ж_РАФФ", "answer": "И", "options": []},
        {"question": "Вставь букву: Ч_ШКА", "answer": "А", "options": []},
        {"question": "Вставь букву: Щ_КА", "answer": "У", "options": []},
        {"question": "Вставь букву: М_РОЗ", "answer": "О", "options": []},
    ],
    "secret_word": "СОВА",
    "fun_answer_hint": "Сова — символ мудрости Хогвартса! Вспомни правило ЖИ-ШИ пиши с И.",
}

# ── CAFE ────────────────────────────────────────────────────────────────────

CAFE_DATA = {
    "title": "Таверна Стива",
    "story": "После долгих раскопок в шахте ты проголодался! Заходи в таверну Стива и закажи обед. Только не забудь посчитать монеты!",
    "cafe_name": "Таверна Стива",
    "menu": [
        {"name": "Жареная свинина", "price": 12, "emoji": "🍖"},
        {"name": "Тыквенный суп", "price": 8, "emoji": "🥣"},
        {"name": "Яблочный пирог", "price": 15, "emoji": "🥧"},
        {"name": "Печенье", "price": 5, "emoji": "🍪"},
        {"name": "Молоко", "price": 4, "emoji": "🥛"},
        {"name": "Зелье скорости", "price": 20, "emoji": "⚗️"},
    ],
    "tasks": [
        {"question": "Стив заказал 2 порции свинины и молоко. Сколько он заплатит?", "answer_lines": 1},
        {"question": "Алекс взяла суп и пирог. Какая сдача с 30 монет?", "answer_lines": 2},
        {"question": "Крипер заказал 3 печенья и зелье. Хватит ли ему 40 монет?", "answer_lines": 2},
    ],
    "budget_task": "Закажи обед для компании из 3 шахтёров. Бюджет:",
    "budget_amount": 80,
}

# ── SHOP ────────────────────────────────────────────────────────────────────

SHOP_DATA = {
    "title": "Снежная математика в Эренделле",
    "story": "Принцесса Эльза готовит праздник для жителей Эренделла! Помоги ей закупить всё необходимое в лавке дядюшки Окена.",
    "shop_name": "Лавка дядюшки Окена",
    "items": [
        {"name": "Снежинка", "price": 5, "emoji": "❄️"},
        {"name": "Морковка для Олафа", "price": 8, "emoji": "🥕"},
        {"name": "Шоколадка", "price": 12, "emoji": "🍫"},
        {"name": "Тёплый шарф", "price": 18, "emoji": "🧣"},
        {"name": "Фонарик", "price": 15, "emoji": "🏮"},
        {"name": "Корона", "price": 25, "emoji": "👑"},
    ],
    "tasks": [
        {"question": "Эльза купила 3 снежинки и шарф. Сколько она заплатила?", "answer_lines": 1},
        {"question": "Олаф взял морковку и шоколадку. Какая сдача с 30 монет?", "answer_lines": 2},
        {"question": "Анна купила 2 фонарика и корону. Сколько стоит покупка?", "answer_lines": 1},
    ],
    "shopping_list_task": "Собери свой уникальный праздничный набор для друзей из Эренделла.",
    "budget_amount": 100,
}

# ── MAZE ────────────────────────────────────────────────────────────────────

MAZE_DATA = {
    "title": "Секретные миссии Человека-паука",
    "story": "Человек-паук ловит Зелёного Гоблина! Помоги ему пробраться через запутанные улицы Нью-Йорка. Иди только по верным примерам!",
    "instruction": "Иди по верным примерам от СТАРТА до ФИНИША! Можно двигаться вверх, вниз, влево, вправо.",
    "grid_size": 7,
    "cells": [
        # Row 0:  path: 0 → 1
        "3+4=7",  "2x3=6",  "5-1=3",  "8+2=9",  "4x2=6",  "9-3=5",  "7+1=9",
        # Row 1:  path: 8 (below 1)
        "2x5=8",  "9-2=7",  "6+3=8",  "3x3=6",  "5+4=8",  "7-2=4",  "4+3=6",
        # Row 2:  path: 15 → 16
        "8-3=4",  "12-5=7", "4+4=8",  "3x2=5",  "6-1=4",  "2+7=8",  "5x2=9",
        # Row 3:  path: 16 stays, go down to 23
        "7+2=8",  "3x4=11", "6-2=3",  "5+5=10", "2x4=7",  "8-1=6",  "9+1=8",
        # Row 4:  path: 23 → 24 → 25
        "4x3=11", "9-4=4",  "3+3=6",  "7-3=4",  "2x5=10", "6+1=7",  "8-5=4",
        # Row 5:  path: 25 stays, go down to 32
        "5+3=7",  "2x6=11", "8-2=5",  "4+5=8",  "3x3=8",  "15-8=7", "7-4=4",
        # Row 6:  path: 39 → ... → 41 → 42 → ... → 48
        "6x2=11", "8-3=6",  "3+2=5",  "4x2=8",  "5+6=11", "9-2=7",  "6+3=9",
    ],
    "correct_path": [0, 1, 8, 15, 16, 23, 24, 25, 32, 39, 40, 41, 47, 48],
}

# ── RENDER ──────────────────────────────────────────────────────────────────

def render_all():
    test_sets = [
        ("cipher_math", "cipher", ANALYSIS_HP, CIPHER_MATH_DATA),
        ("cipher_russian", "cipher", ANALYSIS_HP, CIPHER_RUSSIAN_DATA),
        ("cipher_ortho", "cipher", ANALYSIS_HP, CIPHER_ORTHO_DATA),
        ("cafe", "cafe", ANALYSIS_MC, CAFE_DATA),
        ("shop", "shop", ANALYSIS_FROZEN, SHOP_DATA),
    ]

    for test_name, activity_type, analysis, data in test_sets:
        content_id = save_activity(
            activity_type=activity_type,
            analysis=analysis,
            activity_data=data,
            server_url="http://localhost:8002",
        )
        src = CONTENT_DIR / f"{content_id}.html"
        dst = Path(__file__).parent / f"test_activity_{test_name}.html"
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[OK] test_activity_{test_name}.html")

    # Open in browser
    for name in ["cipher_math", "cipher_russian", "cipher_ortho", "cafe", "shop"]:
        p = Path(__file__).parent / f"test_activity_{name}.html"
        if p.exists():
            webbrowser.open(str(p))


if __name__ == "__main__":
    render_all()
