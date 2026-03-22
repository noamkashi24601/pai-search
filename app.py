# ═══════════════════════════════════════════════════════════════════════════════
#  PAI Corpus – Pattern Search Interface  v2
#  app.py  |  run: streamlit run app.py
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import re
import unicodedata
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

st.set_page_config(page_title="PAI Corpus Search", layout="wide", page_icon="◌")

# ── CSS ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Source+Serif+4:ital,wght@0,300;0,600;1,300&display=swap');

:root {
  --sky-50:  #f0f8ff;
  --sky-100: #daeeff;
  --sky-200: #b8deff;
  --sky-400: #60aee8;
  --sky-600: #2075c7;
  --sky-800: #0d3f75;
  --ink:     #1a2b3c;
}

html, body, .stApp { background: var(--sky-50) !important; }

.pai-header { text-align: center; padding: 2.5rem 0 1rem; }
.pai-header .title {
  font-family: 'Source Serif 4', serif;
  font-size: 2.6rem; font-weight: 600;
  color: var(--sky-800); letter-spacing: -0.02em;
}
.pai-header .subtitle {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.78rem; color: var(--sky-600);
  letter-spacing: 0.14em; margin-top: 0.4rem; text-transform: uppercase;
}

.legend-row { display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:1.2rem; justify-content:center; }
.legend-pill {
  background: var(--sky-100); border: 1px solid var(--sky-200);
  border-radius: 999px; padding: 0.25rem 0.9rem;
  font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; color: var(--sky-800);
}
.legend-pill b { color: var(--sky-600); }

div[data-testid="stTextInput"] input {
  border-radius: 12px !important; border: 2px solid var(--sky-200) !important;
  padding: 0.7rem 1.2rem !important;
  font-family: 'IBM Plex Mono', monospace !important; font-size: 1.15rem !important;
  background: var(--sky-50) !important; color: var(--ink) !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
div[data-testid="stTextInput"] input:focus {
  border-color: var(--sky-600) !important;
  box-shadow: 0 0 0 3px rgba(32,117,199,0.12) !important;
  background: white !important;
}
div[data-testid="stButton"] button[kind="primary"] {
  background: var(--sky-600) !important; color: white !important;
  border-radius: 12px !important; font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.9rem !important; border: none !important; padding: 0.6rem 1.5rem !important;
}

.doc-card-meta {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.78rem; color: var(--sky-600);
  display: flex; gap: 1.2rem; flex-wrap: wrap; margin-bottom: 0.7rem;
}
.badge {
  background: var(--sky-100); border-radius: 999px;
  padding: 0.15rem 0.7rem; color: var(--sky-800); font-weight: 600;
}
.badge-green {
  background: #d4f7e0; color: #1a6e38; border-radius: 999px;
  padding: 0.15rem 0.7rem; font-weight: 600;
}

/* Full document viewer */
.full-doc {
  background: white;
  border: 1px solid var(--sky-200);
  border-radius: 12px;
  padding: 1.6rem 2rem;
  margin-top: 0.5rem;
  font-family: 'Source Serif 4', serif;
  font-size: 0.97rem; line-height: 2;
  color: var(--ink);
  box-shadow: 0 2px 10px rgba(32,117,199,0.07);
  max-height: 65vh;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
}
.full-doc mark {
  background: #b6f2c8;
  border-radius: 3px;
  padding: 0 2px;
  font-weight: 700;
  color: #0d4a22;
}
.full-doc .doc-header-section {
  color: #8899aa;
  font-style: italic;
  font-size: 0.88rem;
  border-bottom: 1px solid var(--sky-100);
  margin-bottom: 1rem;
  padding-bottom: 0.8rem;
}

/* Word preview chips */
.word-chips {
  display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem;
}
.word-chip {
  background: var(--sky-50); border: 1px solid var(--sky-200);
  border-radius: 8px; padding: 0.25rem 0.7rem;
  font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;
  color: var(--ink);
}
.word-chip mark {
  background: #b6f2c8; border-radius: 2px;
  padding: 0 1px; font-weight: 700; color: #0d4a22;
}

.stats-bar {
  background: var(--sky-100); border: 1px solid var(--sky-200);
  border-radius: 10px; padding: 0.6rem 1.2rem;
  font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem;
  color: var(--sky-800); margin-bottom: 1rem;
  display: flex; gap: 1.5rem;
}

#MainMenu, footer { visibility: hidden; }
/* ── Fix expander visibility ── */
div[data-testid="stExpander"] {
  background: white !important;
  border: 1.5px solid var(--sky-200) !important;
  border-radius: 12px !important;
  margin-bottom: 0.5rem !important;
  box-shadow: 0 2px 8px rgba(32,117,199,0.08) !important;
}
div[data-testid="stExpander"]:hover {
  border-color: var(--sky-400) !important;
  box-shadow: 0 4px 16px rgba(32,117,199,0.14) !important;
}
div[data-testid="stExpander"] summary svg {
  display: none !important;
}
div[data-testid="stExpander"] summary p {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.9rem !important;
  font-weight: 600 !important;
  color: var(--sky-800) !important;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  LINGUISTIC SETS
# ════════════════════════════════════════════════════════════════════════════════

CONSONANTS: set = {
    'b','t','ṯ','ǧ','ž','ḥ','x','d','ḏ','r','z','s','š','ṣ','ḍ','ẓ','ṭ',
    'ġ','f','q','g','k','č','ḳ','l','m','n','h','w','y','ʿ','ʾ','p',
}
VOWELS: set = {
    'a','e','i','u','o','ā','ō','ū','ī','ē','ɑ̄','ə',
}
DIPHTHONGS: list = ['aw','ay','ōw','ēy']

# Word boundaries: whitespace, punctuation, # (morpheme boundary), ʿ‿ʿ (undertie)
WORD_DELIM = re.compile(r'[\s,.:;!?()\[\]{}"\'—–\-#]+|ʿ\u203Fʿ')


def _alts(items) -> str:
    return '(?:' + '|'.join(re.escape(c) for c in sorted(items, key=len, reverse=True)) + ')'

_C = _alts(CONSONANTS)
_V = _alts(VOWELS)
_D = _alts(DIPHTHONGS)


def pattern_to_regex(pattern: str) -> re.Pattern:
    parts = []
    for ch in unicodedata.normalize('NFC', pattern):
        if   ch == 'C': parts.append(_C)
        elif ch == 'V': parts.append(_V)
        elif ch == 'D': parts.append(_D)
        elif ch == '$': parts.append('.')
        else:           parts.append(re.escape(ch))
    return re.compile(''.join(parts))


def tokenize(text: str) -> list:
    return [w for w in WORD_DELIM.split(unicodedata.normalize('NFC', text)) if w.strip()]


def match_word(word: str, rx: re.Pattern, position: str) -> list:
    out = []
    for m in rx.finditer(word):
        s, e, wl = m.start(), m.end(), len(word)
        if   position == 'anywhere':                       out.append(m)
        elif position == 'start'   and s == 0:             out.append(m)
        elif position == 'end'     and e == wl:            out.append(m)
        elif position == 'middle'  and 0 < s and e < wl:  out.append(m)
    return out


def highlight_word(word: str, matches: list) -> str:
    out = word
    for m in sorted(matches, key=lambda x: x.start(), reverse=True):
        out = out[:m.start()] + f'<mark>{out[m.start():m.end()]}</mark>' + out[m.end():]
    return out


def highlight_in_text(text: str, rx: re.Pattern) -> str:
    return rx.sub(lambda m: f'<mark>{m.group()}</mark>', text)


# ════════════════════════════════════════════════════════════════════════════════
#  GOOGLE DRIVE / DOCS
# ════════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_services():
    creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/documents.readonly',
        ]
    )
    return build('drive', 'v3', credentials=creds), build('docs', 'v1', credentials=creds)


@st.cache_data(ttl=3600, show_spinner=False)
def get_all_docs(root_folder_id: str) -> list:
    drive, _ = get_services()

    def recurse(folder_id, path):
        found, page_token = [], None
        while True:
            resp = drive.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
            ).execute()
            for f in resp.get('files', []):
                fp = f"{path}/{f['name']}"
                if   f['mimeType'] == 'application/vnd.google-apps.folder':
                    found.extend(recurse(f['id'], fp))
                elif f['mimeType'] == 'application/vnd.google-apps.document':
                    found.append({'id': f['id'], 'name': f['name'], 'path': fp})
            page_token = resp.get('nextPageToken')
            if not page_token:
                break
        return found

    return recurse(root_folder_id, "1. Transcriptions")


@st.cache_data(ttl=3600, show_spinner=False)
def get_doc_content(doc_id: str) -> dict:
    """
    Returns paragraphs split into:
      - header: everything up to and including the *** separator
      - body:   the transcription text after ***
    The *** convention is the standard separator in the PAI template.
    """
    _, docs_svc = get_services()
    try:
        doc = docs_svc.documents().get(documentId=doc_id).execute()
    except HttpError:
        return {'header': '', 'body': '', 'paragraphs': []}

    paragraphs = []
    for elem in doc.get('body', {}).get('content', []):
        para = elem.get('paragraph')
        if not para:
            continue
        text = ''.join(
            pe.get('textRun', {}).get('content', '')
            for pe in para.get('elements', [])
        )
        paragraphs.append(unicodedata.normalize('NFC', text))

    # Find *** separator
    sep_idx = next(
        (i for i, p in enumerate(paragraphs) if p.strip() == '***'),
        None
    )

    if sep_idx is not None:
        header = '\n'.join(paragraphs[:sep_idx + 1])
        body   = '\n'.join(paragraphs[sep_idx + 1:])
    else:
        header = ''
        body   = '\n'.join(paragraphs)

    return {'header': header, 'body': body, 'paragraphs': paragraphs}


# ════════════════════════════════════════════════════════════════════════════════
#  SEARCH
# ════════════════════════════════════════════════════════════════════════════════

def run_search(pattern: str, position: str, root_id: str) -> list:
    try:
        rx = pattern_to_regex(pattern)
    except re.error as e:
        st.error(f"Invalid pattern: {e}")
        return []

    all_docs = get_all_docs(root_id)
    results  = []
    bar      = st.progress(0.0, text="Loading corpus…")

    for i, doc in enumerate(all_docs):
        bar.progress((i + 1) / max(len(all_docs), 1), text=f"Searching · {doc['name']}")
        content = get_doc_content(doc['id'])
        body    = content['body']
        header  = content['header']

        match_count   = 0
        matched_words = []

        for word in tokenize(body):
            hits = match_word(word, rx, position)
            if hits:
                match_count += len(hits)
                matched_words.append(highlight_word(word, hits))

        if match_count > 0:
            # Build display HTML: greyed header + green-highlighted body
            hl_body = highlight_in_text(body, rx)
            display_html = (
                f'<div class="doc-header-section">{header}</div>'
                f'<div>{hl_body}</div>'
            )
            results.append({
                'doc_name':      doc['name'],
                'doc_path':      doc['path'],
                'match_count':   match_count,
                'word_count':    len(tokenize(body)),
                'matched_words': matched_words[:15],
                'display_html':  display_html,
            })

    bar.empty()
    results.sort(key=lambda r: r['match_count'], reverse=True)
    return results


# ════════════════════════════════════════════════════════════════════════════════
#  UI
# ════════════════════════════════════════════════════════════════════════════════

ROOT_FOLDER_ID = st.secrets.get("ROOT_FOLDER_ID", "1ORlDa5DLY4UnNgeZOeOnFOgnDMxiXVyK")

st.markdown("""
<div class="pai-header">
  <div class="title">PAI Corpus Search</div>
  <div class="subtitle">Palestinian Arabic — Pattern Search Interface</div>
</div>
""", unsafe_allow_html=True)

_, mid, _ = st.columns([1, 5, 1])
with mid:
    st.markdown("""
    <div class="legend-row">
      <span class="legend-pill"><b>C</b> = consonant</span>
      <span class="legend-pill"><b>V</b> = vowel</span>
      <span class="legend-pill"><b>D</b> = diphthong (aw / ay)</span>
      <span class="legend-pill"><b>$</b> = any character</span>
      <span class="legend-pill" style="background:#fff8e0;border-color:#ffe082">
        e.g.&nbsp;<b>aCC</b>&nbsp;·&nbsp;<b>f$m</b>&nbsp;·&nbsp;<b>VCC</b>&nbsp;·&nbsp;<b>ḥVCC</b>
      </span>
    </div>
    """, unsafe_allow_html=True)

    pattern_input = st.text_input(
        "Pattern",
        placeholder="Type a pattern…   e.g.  aCC  or  f$m  or  VCCa",
        label_visibility="collapsed",
        key="pattern"
    )

    with st.expander("⚙️  Advanced options"):
        position = st.radio(
            "Pattern position within word",
            options=['anywhere', 'start', 'middle', 'end'],
            horizontal=True,
            format_func=lambda x: {
                'anywhere': '🔀  Anywhere',
                'start':    '◀  Start of word',
                'middle':   '◼  Middle of word',
                'end':      '▶  End of word',
            }[x],
        )

    col_s, col_c = st.columns([5, 1])
    with col_s:
        search_clicked = st.button("Search corpus", type="primary", use_container_width=True)
    with col_c:
        if st.button("↺", help="Clear cache and reload corpus", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# ── Results ───────────────────────────────────────────────────────────────────
if search_clicked and pattern_input.strip():
    results = run_search(pattern_input.strip(), position, ROOT_FOLDER_ID)

    if not results:
        st.info("No matches found for this pattern.")
    else:
        total = sum(r['match_count'] for r in results)
        st.markdown(f"""
        <div class="stats-bar">
          <span>🔍 <b>{pattern_input.strip()}</b></span>
          <span>📄 {len(results)} document{'s' if len(results) != 1 else ''}</span>
          <span>◌ {total} total match{'es' if total != 1 else ''}</span>
        </div>
        """, unsafe_allow_html=True)

        for r in results:
            folder = '/'.join(r['doc_path'].split('/')[:-1]).lstrip('/')
            expander_label = f"📄  {r['doc_name']}   ·   {r['match_count']} match{'es' if r['match_count'] != 1 else ''}"

            with st.expander(expander_label):
                # Meta row
                chips_html = ''.join(
                    f'<span class="word-chip">{w}</span>'
                    for w in r['matched_words']
                )
                more = f' <span style="color:#8899aa;font-size:0.8rem">+ more…</span>' \
                       if r['match_count'] > len(r['matched_words']) else ''

                st.markdown(f"""
                <div class="doc-card-meta">
                  <span class="badge-green">✦ {r['match_count']} matches</span>
                  <span class="badge">{r['word_count']} words in transcript</span>
                  <span style="color:#8899aa">{folder}</span>
                </div>
                <div class="word-chips">{chips_html}{more}</div>
                """, unsafe_allow_html=True)

                # Full document with highlighted matches
                st.markdown(
                    f'<div class="full-doc">{r["display_html"]}</div>',
                    unsafe_allow_html=True
                )

elif search_clicked and not pattern_input.strip():
    st.warning("Please enter a pattern before searching.")
