# GITHUB_SETUP – הפיכת הריפו למשותף בין יאיר לאביאל

מסמך תפעול. כל שלב מסומן לפי מי מבצע. מה שדורש חשבון GitHub לא ניתן לביצוע מ-Claude Code.

## מצב נוכחי (נבדק 22.11.2026)

- הריפו המקומי: `C:\Users\User\Documents\ORIN_P\orin-repo\orin`
- הענף הפעיל: `feature/staging`; קיימים גם `main` ו-`feature/skeleton`.
- remote בשם `repo` → `https://github.com/yair-26/Orin-Info.git`
- `gh` CLI **לא מותקן** במחשב (נבדק). את השלבים עושים בדפדפן.

## 1. ודאו שהריפו פרטי (יאיר)

GitHub → הריפו → **Settings → General → Danger Zone**. ליד "Change repository visibility" צריך להיות `Private`.
ריפו ציבורי חושף קוד, היסטוריה ו-CI. אסור בשלב הזה.

## 2. הוספת אביאל (יאיר)

**Settings → Collaborators → Add people** → שם המשתמש של אביאל → תפקיד:

| תפקיד | מה מאפשר | מומלץ |
|---|---|---|
| **Admin** | ניהול מלא: הגדרות, סודות, מחיקת הריפו | כן, אם אביאל צריך "ניהול" |
| **Maintain** | ניהול יומיומי בלי הגדרות הרסניות | חלופה בטוחה |

אביאל מקבל הזמנה במייל/GitHub ומאשר.

## 3. הגנת main (יאיר, אחרי שאביאל מצורף)

**Settings → Branches → Add branch protection rule** עבור `main`:

- [x] Require a pull request before merging
- [x] Require approvals: **1**
- [x] Dismiss stale approvals on new commits
- [x] Require status checks to pass → בחרו את `tests (ubuntu-latest, py3.11)`,
      `tests (ubuntu-latest, py3.12)`, `tests (windows-latest, py3.11)`, `tests (windows-latest, py3.12)`
      (השמות יופיעו אחרי ה-PR הראשון שמריץ CI)
- [x] Require conversation resolution before merging
- [ ] Do not allow force pushes
- [ ] Do not allow deletions

## 4. תיקון שם ה-remote (כל אחד במחשב שלו)

השם התקני הוא `origin`; כרגע הוא `repo`. פקודה חד-פעמית:

```bash
git remote rename repo origin
git remote -v          # אמור להציג origin ... Orin-Info.git
```

## 5. העלאת הענפים (יאיר)

```bash
git push -u origin main
git push -u origin feature/skeleton
git push -u origin feature/staging
```

`-u` מקשר את הענף המקומי לענף המרוחק, כך שאחר כך `git push` בלי ארגומנטים עובד.

## 6. אימות שה-CI עובד

כל PR מריץ `.github/workflows/ci.yml` על Ubuntu ו-Windows, Python 3.11 ו-3.12.
אם ה-CI אדום — לא ממזגים. אם הוא לא מופיע בכלל: **Settings → Actions → General → Allow all actions**.

## 7. סביבת staging (יאיר, אחרי 1–5)

1. Render → **New → Blueprint** → בחירת `Orin-Info` → Render קורא את `render.yaml`.
2. פרסום ראשון, ואז בדיקה: `https://<name>.onrender.com/health` מחזיר `{"status":"ok"}`.
3. משתני סביבה (אם וכשיהיו): **Environment → Environment Variables**, לא ב-Git.

## 8. מה כל אחד מריץ אחרי clone

```bash
git clone https://github.com/yair-26/Orin-Info.git
cd Orin-Info
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # Windows
python -m pytest -q
```

## אחריות

| פעולה | מי |
|---|---|
| הזמנת משתתפים, הגנת ענפים, סודות | יאיר (Admin) |
| מיזוג PR בתיקיות שלו | אביאל (`core/`, `products/`, `config/`, `scripts/`) |
| מיזוג PR בתיקיות שלו | יאיר (`admin/`) |
| שינוי חוזה API | שניהם |
