# CONTRIBUTING – איך עובדים על ORIN INFO

מסמך תפעולי לשני המייסדים. כללי העבודה המלאים (כולל מה נחשב "בוצע") ב-`CLAUDE.md`.

## התקנה מקומית (Windows או WSL)

```bash
python -m venv .venv
# Windows (Git Bash):  .venv/Scripts/python
# WSL / Linux:         .venv/bin/python
.venv/Scripts/python -m pip install -e ".[dev]"     # Windows
python -m pytest -q                                  # חייב לעבור לפני PR
```

הרצת השרת: `.venv/Scripts/python -m uvicorn core.app:app --reload` → http://127.0.0.1:8000/health

## חלוקת בעלות

| תיקייה | בעלים |
|---|---|
| `core/`, `products/`, `config/`, `scripts/` | אביאל |
| `admin/` (דשבורד ונתוני דמה) | יאיר |
| `docs/api-contracts.md` | שינוי רק באישור **שניהם** |
| `docs/`, `tests/`, `.github/` | משותף |

שינוי בתיקייה של השני עובר דרך Pull Request ומאושר על ידו. הכלל הזה גם מוגדר אוטומטית ב-`.github/CODEOWNERS`.

## זרימת עבודה

1. `git switch main && git pull` — מתחילים תמיד מ-main מעודכן.
2. `git switch -c feature/<נושא>` — ענף לכל משימה, לא עובדים על main.
3. קומיטים קטנים, הודעה באנגלית, למשל `T-04: add calls/turns schema`.
4. דוחפים, פותחים Pull Request, ממלאים את התבנית.
5. ה-CI חייב להיות ירוק, ובעל התיקייה מאשר.
6. מיזוג ל-main. אין force push ואין מחיקת ענפים בלי אישור מפורש.

## סודות

- מפתחות רק ב-`.env` מקומי (ב-`.gitignore`). לא מעלים ל-Git אפילו לא בטעות.
- `.env.example` מתעד שמות משתנים בלבד, בלי ערכים.
- בסביבת staging הסודות מוגדרים בלוח הבקרה של ספק האירוח.

## נתוני דמה

`admin/mock-data` נוצר אוטומטית: `python -m scripts.make_mock_data`. אין לערוך אותו ידנית.
שינוי בחוזה ה-API מחייב עדכון `docs/api-contracts.md`, הרצת המחולל ו-PR מאושר.

## סגנון

- הסברים ותיעוד בעברית; קוד, שמות והערות טכניות באנגלית.
- עבודה קטנה וצעד-אחר-צעד. שינוי ארכיטקטורה, ספרייה חדשה או מבנה נתונים — vysvětל קודם וקבל אישור.
- מה שלא הורץ לא נחשב "בוצע" — כתוב "לא נבדק".

## שאלות

פותחים Issue (תבנית "משימה" או "באג"), לא דנים בדברים פתוחים ב-WhatsApp בלבד.
