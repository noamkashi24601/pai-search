# PAI Corpus Search

A pattern search interface for the Palestinian Arabic (PAI) corpus. Researchers can search transcriptions stored as Google Docs using phonological pattern syntax.

---

## How it works

The app reads the **Recordings** sheet from the PAI corpus Google Spreadsheet. Every row that has a Google Doc link in the "קישורים לתעתיקים" column is included in the searchable corpus. The app fetches each document via the Google Docs API and searches only the transcription body (the text after the `***` separator).

Search is performed on **italic text only**, since all transcriptions in the PAI template are formatted in italics, while metadata, headers, and linguistic notes are not.

---

## Pattern syntax

| Symbol | Matches |
|--------|---------|
| `C` | Any consonant from the PAI transcription table |
| `V` | Any vowel (a, e, i, u, o, ā, ō, ū, ī, ē, ə, ɑ̄) |
| `D` | Any diphthong (aw, ay, ōw, ēy) |
| `$` | Any single character |
| literal | Exact character match (e.g. `ḥ`, `š`, `ā`) |

**Examples:**

| Pattern | Finds |
|---------|-------|
| `aCC` | The vowel *a* followed by two consonants |
| `VCC` | Any vowel followed by two consonants |
| `f$m` | *f*, any character, then *m* |
| `ḥVCC` | *ḥ* followed by a vowel and two consonants |
| `iCC` | The vowel *i* followed by two consonants |

### Position filter (Advanced options)
Patterns can be restricted to appear at the **start**, **middle**, or **end** of a word. Words are delimited by spaces, punctuation, `#` (morpheme boundary marker), and the undertie sequence `ʿ‿ʿ`.

### Document filter (Advanced options)
Filter which documents are searched by typing part of a document name, village name, or community name.

---

## Results

Results are displayed as expandable cards, sorted from most matches to fewest. Each card shows:
- Number of matches and total word count in the transcript
- Village, community, and gender metadata
- Preview chips showing the matched words with the matching portion highlighted in green
- The full document with all matches highlighted in green, scrollable inline

---

## Setup

### 1. Google Cloud — Service Account

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Enable these three APIs:
   - Google Drive API
   - Google Docs API
   - Google Sheets API
3. Go to **IAM & Admin → Service Accounts → Create**
4. Download the key as JSON (**Keys → Add Key → JSON**)
5. Copy the service account email (e.g. `pai-search@project.iam.gserviceaccount.com`)

### 2. Share the Google Spreadsheet

Share the PAI corpus spreadsheet with the service account email as **Viewer**.

The spreadsheet ID is already set in the code:
```
1qzh4OZ_gIjaTs__ENPkP7eROpTl2jjtTyb4GLMRljGw
```

### 3. Create secrets.toml (local development)

Run this command to generate the base64-encoded key:
```bash
python3 -c "
import base64
with open('/path/to/your-key.json') as f:
    data = f.read()
print(base64.b64encode(data.encode()).decode())
"
```

Create `.streamlit/secrets.toml`:
```toml
ROOT_FOLDER_ID = "1ORlDa5DLY4UnNgeZOeOnFOgnDMxiXVyK"
GOOGLE_SERVICE_ACCOUNT_B64 = "paste the base64 output here"
```

> **Never commit this file to GitHub.** Add `.streamlit/secrets.toml` to `.gitignore`.

### 4. Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

### 5. Deploy to Streamlit Cloud

1. Push the repo to GitHub (without `secrets.toml`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Select the repo and `app.py`
4. Go to **Advanced settings → Secrets** and paste the contents of your `secrets.toml`
5. Click **Deploy**

To update the secret after generating a new key file, go to **Manage app → Settings → Secrets**.

---

## File structure

```
pai-search/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
└── .streamlit/
    └── secrets.toml        # Local credentials (not in Git)
```

---

## Transcription table

The consonant and vowel sets used for `C`, `V`, and `D` matching are defined according to the official PAI transcription table:

**Consonants:** b t ṯ ǧ ž ḥ x d ḏ r z s š ṣ ḍ ẓ ṭ ġ f q g k č ḳ l m n h w y ʿ ʾ p

**Vowels:** a e i u o ā ō ū ī ē ɑ̄ ə

**Diphthongs:** aw ay ōw ēy
