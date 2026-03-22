# PAI Search — Setup Guide

## קבצים
```
pai_search/
├── app.py
├── requirements.txt
└── .streamlit/
    └── secrets.toml        ← אתה יוצר אותו (לא מועלה ל-GitHub!)
```

---

## שלב 1 — Service Account ב-Google Cloud

1. היכנס ל-https://console.cloud.google.com
2. צור פרויקט חדש (או השתמש בקיים)
3. **Enable APIs**:
   - Google Drive API
   - Google Docs API
4. **IAM & Admin → Service Accounts → Create**
   - תן שם (למשל `pai-search`)
   - לא צריך לתת לו Role ברמת הפרויקט
5. לחץ על ה-Service Account שיצרת → **Keys → Add Key → JSON**
   - שמור את הקובץ (נראה כמו `pai-search-xxxx.json`)
6. העתק את ה-**email** של ה-Service Account (נראה כמו `pai-search@project.iam.gserviceaccount.com`)

---

## שלב 2 — Share תיקיית Drive עם ה-Service Account

בגוגל דרייב, לחץ ימני על תיקיית **"1. Transcriptions"** →
Share → הוסף את ה-email של ה-Service Account → Viewer

---

## שלב 3 — secrets.toml (לריצה מקומית)

צור את הקובץ `.streamlit/secrets.toml`:

```toml
ROOT_FOLDER_ID = "1ORlDa5DLY4UnNgeZOeOnFOgnDMxiXVyK"

GOOGLE_SERVICE_ACCOUNT = '''
{
  "type": "service_account",
  "project_id": "YOUR_PROJECT_ID",
  "private_key_id": "...",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n",
  "client_email": "pai-search@YOUR_PROJECT.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
'''
```

העתק את כל התוכן של קובץ ה-JSON ישירות לתוך הגרשיים המשולשות.

---

## שלב 4 — ריצה מקומית

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## שלב 5 — פרסום ב-Streamlit Cloud

1. העלה את הקוד ל-GitHub (ללא `.streamlit/secrets.toml`!)
2. היכנס ל-https://share.streamlit.io → **New app**
3. בחר את ה-repo ואת `app.py`
4. **Advanced settings → Secrets** — הוסף שם את אותו תוכן של ה-`secrets.toml`
5. Deploy

---

## תחביר חיפוש

| תו   | משמעות                        | דוגמה         |
|------|-------------------------------|---------------|
| `C`  | כל עיצור                      | `aCC`         |
| `V`  | כל תנועה                      | `VCC`         |
| `D`  | דיפתונג (aw / ay)             | `DC`          |
| `$`  | כל תו כלשהו                   | `f$m`         |
| ליטרל | תו ספציפי                   | `ḥVCC`        |

**חיפוש לפי מיקום** — ניתן לסנן תבניות שמופיעות בתחילת מילה, אמצע או סוף.
