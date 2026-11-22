# mock-data

נתוני דמה פיקטיביים (נוצרו ב-`python3 -m scripts.make_mock_data`, זרע קבוע). המחירים והמספרים בדויים ואינם מחירי ספק. מתאימים ל-docs/api-contracts.md גרסה 0.1.

- `calls.json` = GET /calls
- `calls/<call_id>.json` = GET /calls/{call_id}
- `summary.json` = GET /summary
- `sample_log.jsonl` = לוג תורות לדוגמה (קלט ל-`scripts.cost_report`)
