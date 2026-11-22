# api-contracts.md – חוזה API בין הליבה לדשבורד

הבעלים: אביאל. שינוי בחוזה רק ב-Pull Request שמאושר על ידי שני המייסדים ומעדכן גם את admin/mock-data.
גרסה: 0.1 (טיוטה, ממתינה לאישור בשבוע 1).

## כללי פרטיות
אין מספרי טלפון ואין תוכן שיחה בחוזה. מזהה שיחה בלבד.

## נקודות קריאה

### GET /calls
רשימת שיחות. פרמטרים: limit, offset, from, to, status.
תשובה: מערך של { call_id, started_at, duration_seconds, status, total_cost, turns_count }.

### GET /calls/{call_id}
פרטי שיחה, כולל עלות לפי רכיב.
תשובה: { call_id, started_at, ended_at, duration_seconds, status, total_cost, cost_breakdown: { stt, llm, tts, search, telephony }, turns: [ { turn_id, latency_ms_by_component, classification, had_search, error } ] }.
ללא תוכן שיחה.

### GET /summary
סיכום מצטבר. פרמטרים: from, to.
תשובה: { calls_count, total_minutes, total_cost, avg_cost_per_minute, median_cost_per_call, cost_by_component, search_vs_no_search: { avg_latency_ms, avg_cost } }.

## רשימות פתוחות
- רשימת ערכי status (הכרעה בשבוע 1).
- הזדהות בסיסית ל-API (הכרעה עד שער 4).

## נתוני דמה
admin/mock-data תואם לחוזה, ומתעדכן בכל שינוי בו. כשהשרת מוכן מחליפים הגדרה אחת (כתובת השרת).
