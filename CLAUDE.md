# Metodist — Printable Worksheet Generator for Elementary School

## What It Is
Service that generates printable one-page A4 worksheets and activities for grades 1-4 (Russian FGOS curriculum).
Built on FastAPI + Vertex AI (Gemini). Two product types: **Worksheet** (4 mixed tasks) and **Full-Page Activity** (one big themed task).

## Two Product Types

### Type 1: Worksheet (mixed tasks)
One A4 page with 4 tasks. Task #1 is always a coloring image + related task. Tasks #2-4 are picked from the subject task library. All tasks are themed around the child's universe (Minecraft, Harry Potter, etc.) and match FGOS grade level.

### Type 2: Full-Page Activity (single themed task)
One A4 page with one large, beautifully designed activity. LLM generates the data (numbers, words, prices), code renders the themed template. Each activity type has its own HTML template.

**Activity types:**
| Activity | Description | Subjects |
|----------|-------------|----------|
| `color_by_value` | Coloring page divided into zones. Each zone has a problem (math expression, letter type, etc.). Solve → get color from legend. | all |
| `maze` | Large themed maze. Junctions have tasks — solve correctly to pick the right path. | all |
| `cafe` | Themed cafe (Hogwarts cafe, Minecraft tavern). Menu with prices, tasks: calculate total, make change, plan a meal for N coins. | math |
| `shop` | Themed shop. Price tags, shopping list, budget. Tasks: total cost, change, compare prices, discounts. | math |
| `cipher` | Decode a funny message using a key table (number→letter, solve expression→letter, etc.). | all |
| `number_chain` | Arrange numbers in order, find patterns, fill gaps in sequences. Large visual chain/spiral layout. | math |

---

## Architecture

### Pipeline (both types)
1. User sends: topic, grade, universe/character, **type** (worksheet or activity name)
2. **LLM Step 1** (`analyze_request`): parse → subject, grade, topic, theme, coloring_prompt
3. **Parallel**: image generation + **LLM Step 2** (generate task data for the chosen type)
4. Code renders the appropriate Jinja2 template → HTML
5. SmartBot sends the link

### File Structure
```
metodist/
├── main.py                     # FastAPI, endpoints, pipeline
├── gemini_client.py            # Vertex AI LLM calls
├── image_generator.py          # Gemini Flash image generation
├── prompts/
│   ├── analyze.py              # Step 1 prompt (shared)
│   ├── worksheet_tasks.py      # Step 2 prompt for Type 1
│   └── activities/             # Step 2 prompts per activity type
│       ├── color_by_value.py
│       ├── maze.py
│       ├── cafe.py
│       ├── shop.py
│       ├── cipher.py
│       └── number_chain.py
├── models/
│   ├── common.py               # SharedAnalysis model
│   ├── worksheet.py            # Worksheet task models (11 types)
│   └── activities/             # Pydantic models per activity type
│       ├── color_by_value.py
│       ├── maze.py
│       ├── cafe.py
│       ├── shop.py
│       ├── cipher.py
│       └── number_chain.py
├── generators/
│   ├── worksheet.py            # word_search grid, save worksheet
│   └── activities/             # Post-processing per activity (grid builders, etc.)
├── templates/
│   ├── worksheet.html          # Type 1 template
│   └── activities/             # Type 2 templates
│       ├── color_by_value.html
│       ├── maze.html
│       ├── cafe.html
│       ├── shop.html
│       ├── cipher.html
│       └── number_chain.html
├── smartbot_client.py
├── db_logger.py
└── test_render.py              # Test render all types without API
```

### Task Library for Type 1 (Worksheet)

**Math tasks** (pick 3 from):
matching, grid_maze, fill_blanks, empty_boxes, sorting_table, odd_one_out, number_chain_small, cafe_mini, shop_mini

**Language tasks** (Russian, English — pick 3 from):
matching, anagram, fill_blanks, word_search, sorting_table, odd_one_out, lines, cipher_mini

**Science tasks** (pick 3 from):
matching, fill_blanks, sorting_table, odd_one_out, lines, big_canvas, word_search

All tasks must be interactive (write, draw, connect, decode) — never just "pick the right answer".

---

## Constraints
- **Grades 1-4 only**. Higher grades clamped to 4.
- **1 A4 page** when printed — critical priority for both types.
- Tasks themed around the child's universe — not just decorative, but woven into task content.
- No multiple-choice / checkmark tasks. Every task requires the child to write, draw, or connect.
- `anagram`, `word_search`, `lines` forbidden for math.

## Env Variables
See `.env.example`. Main groups: Google Cloud, SmartBot Pro, Server URL, Admin.

## Running
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8002
```

## Testing Layout (no API needed)
```bash
python test_render.py
# Opens HTML in browser -> Cmd+P -> verify A4
```

## Admin Endpoints
- `/admin/logs?password=...` — logs
- `/admin/stats?password=...` — stats
- `/health` — healthcheck

## Deploy Info
- **Port:** 8002
- **VPS path:** `/opt/metodist`
- **Not yet deployed** — no git repo initialized

---

## TODO

**Rule: when completing a task, Claude MUST check it off `[x]` in this file.**

### TODO
- [ ] Endpoint: `POST /generate-activity` with activity type parameter
- [ ] Polish templates after review

### Deploy
- [ ] Initialize git repository
- [ ] Create GitHub repo (kotyadji-coder)
- [ ] First deploy to VPS (port 8002, /opt/metodist)
- [ ] Configure nginx + SSL (needs domain)
- [ ] Copy google-credentials.json to VPS
- [ ] Create .env on VPS
- [ ] Configure SmartBot Pro buttons

### Phase 4: Polish
- [ ] Fine-tune CSS after real content tests
- [ ] Add child name to header
- [ ] Caching — don't regenerate identical sheets
- [ ] Rate limiting
- [ ] Prompt iteration after real user feedback

---

## LLM Dashboard Integration

Token usage from every Gemini call is sent to the centralized LLM Dashboard (`http://5.42.101.215:8005/`).

- **How:** fire-and-forget `httpx.post()` in a daemon thread after each `generate_content()` call
- **Where:** `gemini_client.py` — `_send_to_dashboard()` function, called from `_call_with_fallback()`
- **Dashboard project:** `~/Documents/projects/llm-dashboard`
- **If dashboard is down:** errors silently logged at DEBUG level, bot works normally
