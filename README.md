# ORIN INFO

סוכן קולי בעברית דרך טלפון רגיל (כולל מכשירים כשרים): המשתמש מתקשר, שואל שאלות ידע, והסוכן מחפש באינטרנט בשמו (מחירים, טלפונים, שעות פתיחה). אבטיפוס.

## מצב נוכחי — נבדק 22.11.2026

| מה | תוצאה |
|---|---|
| בדיקות | `python -m pytest -q` → **30 passed** |
| API | רץ מקומית ב-uvicorn; `/health`, `/calls`, `/calls/{id}`, `/summary`, 404 — אומתו ב-curl |
| סקריפטים | `cost_report`, `eval`, `chat`, `make_mock_data` — רצו בהצלחה |
| ספקים | **mock בלבד** (STT/TTS/LLM/Search/Telephony). אין מפתחות, אין רשת |
| מסד נתונים | אין (תלוי בהחלטה D-004) |

## התחלה מהירה

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"     # Windows (Git Bash)
# .venv/bin/python -m pip install -e ".[dev]"       # WSL / Linux
.venv/Scripts/python -m pytest -q
.venv/Scripts/python -m uvicorn core.app:app --reload
```

אחר כך: http://127.0.0.1:8000/health

## מבנה

| תיקייה | תוכן | בעלים |
|---|---|---|
| `core/` | ליבת השיחה, ספקים, תקרות, עלות, לוג | אביאל |
| `products/info/` | התנהגות מוצר INFO | אביאל |
| `admin/` | דשבורד ונתוני דמה | יאיר |
| `config/` | ספקים, מחירים, תקרות | אביאל |
| `scripts/` | שיחה, דוח עלות, מבחן שאלות, מחולל דמה | אביאל |
| `tests/` | בדיקות אוטומטיות | משותף |
| `docs/` | אפיון, מצב, החלטות, חוזה API | משותף |

## תיעוד

1. [docs/PRODUCT.md](docs/PRODUCT.md) — מה בונים ומה נחשב הצלחה.
2. [docs/STATUS.md](docs/STATUS.md) — מה קיים, מה נשאר, ומה דורש בן אדם.
3. [docs/TASKS.md](docs/TASKS.md) — המשימות הבאות.
4. [CONTRIBUTING.md](CONTRIBUTING.md) — איך עובדים, מתפצלים וממזגים.
5. [docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md) — הפיכת הריפו למשותף בין שני המייסדים.
6. [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — staging חינמי.

## שימוש בקונפיגורציה

- `config/providers.yaml` בוחר ספק לכל רכיב. החלפה = עריכת קובץ בלבד.
- `config/limits.yaml` תקרות הגנה; חריגה עוצרת את השיחה.
- `config/pricing.yaml` מחירים. **ריק בכוונה** — מחיר חסר מסומן "לא ידוע", לא 0.
- סודות רק ב-`.env` מקומי (ראו `.env.example`); הוא ב-`.gitignore`.

## בדיקות ו-CI

כל PR מריץ `.github/workflows/ci.yml`: Ubuntu ו-Windows, Python 3.11 ו-3.12.
הוראות הפעלה מפורטות ב-[CONTRIBUTING.md](CONTRIBUTING.md).
