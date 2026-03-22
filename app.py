# ═══════════════════════════════════════════════════════════════════════════════
#  PAI Corpus – Pattern Search Interface  v3
#  Sources docs from the Recordings sheet in Google Sheets.
#  Searches only italic text runs (the actual transcription).
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

/* ── Header ── */
.pai-header { text-align: center; padding: 2.5rem 0 1rem; }
.pai-header .title {
  font-family: 'Source Serif 4', serif;
  font-size: 2.6rem; font-weight: 600;
  color: var(--sky-800); letter-spacing: -0.02em;
}
.pai-header .subtitle {
  font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
  color: var(--sky-600); letter-spacing: 0.14em; margin-top: 0.4rem; text-transform: uppercase;
}

/* ── Legend pills ── */
.legend-row { display:flex; gap:0.5rem; flex-wrap:wrap; margin-bottom:1.2rem; justify-content:center; }
.legend-pill {
  background: var(--sky-100); border: 1px solid var(--sky-200);
  border-radius: 999px; padding: 0.25rem 0.9rem;
  font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; color: var(--sky-800);
}
.legend-pill b { color: var(--sky-600); }

/* ── Main search input ── */
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

/* ── Advanced options expander: fix white-on-white ── */
div[data-testid="stExpander"] > details {
  background: var(--sky-100) !important;
  border: 1.5px solid var(--sky-200) !important;
  border-radius: 12px !important;
}
div[data-testid="stExpander"] > details > summary {
  color: var(--sky-800) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.88rem !important;
}
div[data-testid="stExpander"] > details[open] > div {
  background: var(--sky-50) !important;
  border-top: 1px solid var(--sky-200) !important;
  padding: 1rem 1.2rem !important;
}
/* Radio labels inside advanced panel */
div[data-testid="stExpander"] label,
div[data-testid="stExpander"] p {
  color: var(--ink) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.85rem !important;
}

/* ── Search button ── */
div[data-testid="stButton"] button[kind="primary"] {
  background: var(--sky-600) !important; color: white !important;
  border-radius: 12px !important; font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.9rem !important; border: none !important; padding: 0.6rem 1.5rem !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
  background: var(--sky-800) !important;
}

/* ── Result expanders ── */
div[data-testid="stExpander"].result-expander > details {
  background: white !important;
  border: 1.5px solid var(--sky-200) !important;
  border-radius: 12px !important;
  margin-bottom: 0.5rem !important;
  box-shadow: 0 2px 8px rgba(32,117,199,0.08) !important;
}
div[data-testid="stExpander"].result-expander > details > summary svg {
  display: none !important;
}

/* ── Badges ── */
.doc-card-meta {
  font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;
  color: var(--sky-600); display: flex; gap: 1.2rem; flex-wrap: wrap; margin-bottom: 0.7rem;
}
.badge { background: var(--sky-100); border-radius: 999px; padding: 0.15rem 0.7rem; color: var(--sky-800); font-weight: 600; }
.badge-green { background: #d4f7e0; color: #1a6e38; border-radius: 999px; padding: 0.15rem 0.7rem; font-weight: 600; }

/* ── Word chips ── */
.word-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1rem; }
.word-chip {
  background: var(--sky-50); border: 1px solid var(--sky-200); border-radius: 8px;
  padding: 0.25rem 0.7rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; color: var(--ink);
}
.word-chip mark { background: #b6f2c8; border-radius: 2px; padding: 0 1px; font-weight: 700; color: #0d4a22; }

/* ── Full document viewer ── */
.full-doc {
  background: white; border: 1px solid var(--sky-200); border-radius: 12px;
  padding: 1.6rem 2rem; margin-top: 0.5rem;
  font-family: 'Source Serif 4', serif; font-size: 0.97rem; line-height: 2; color: var(--ink);
  box-shadow: 0 2px 10px rgba(32,117,199,0.07);
  max-height: 65vh; overflow-y: auto; white-space: pre-wrap; word-break: break-word;
}
.full-doc mark { background: #b6f2c8; border-radius: 3px; padding: 0 2px; font-weight: 700; color: #0d4a22; }
.full-doc .doc-header-section {
  color: #8899aa; font-style: italic; font-size: 0.88rem;
  border-bottom: 1px solid var(--sky-100); margin-bottom: 1rem; padding-bottom: 0.8rem;
}

/* ── Stats bar ── */
.stats-bar {
  background: var(--sky-100); border: 1px solid var(--sky-200); border-radius: 10px;
  padding: 0.6rem 1.2rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem;
  color: var(--sky-800); margin-bottom: 1rem; display: flex; gap: 1.5rem;
}

#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
#  LINGUISTIC SETS  (from official PAI transcription table)
# ════════════════════════════════════════════════════════════════════════════════

CONSONANTS: set = {
    'b','t','ṯ','ǧ','ž','ḥ','x','d','ḏ','r','z','s','š','ṣ','ḍ','ẓ','ṭ',
    'ġ','f','q','g','k','č','ḳ','l','m','n','h','w','y','ʿ','ʾ','p',
}
VOWELS: set = { 'a','e','i','u','o','ā','ō','ū','ī','ē','ɑ̄','ə' }
DIPHTHONGS: list = ['aw','ay','ōw','ēy']
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
#  GOOGLE SERVICES
# ════════════════════════════════════════════════════════════════════════════════

SPREADSHEET_ID = "1qzh4OZ_gIjaTs__ENPkP7eROpTl2jjtTyb4GLMRljGw"

# Column indices in the Recordings sheet (0-based after row 0 header)
COL_REC_LINK   = 39   # קישורים להקלטות  — catalog name + Drive link
COL_TRANS_LINK = 43   # קישורים לתעתיקים — Google Doc link
COL_VILLAGE    = 1    # שם יישוב בתעתיק
COL_COMMUNITY  = 4    # קהילה
COL_GENDER     = 8    # מגדר דובר


@st.cache_resource
def get_services():
    creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/documents.readonly',
            'https://www.googleapis.com/auth/spreadsheets.readonly',
        ]
    )
    drive   = build('drive',   'v3', credentials=creds)
    docs    = build('docs',    'v1', credentials=creds)
    sheets  = build('sheets',  'v4', credentials=creds)
    return drive, docs, sheets


def _extract_doc_id(url: str) -> str | None:
    """Extract Google Doc ID from a docs.google.com URL."""
    m = re.search(r'/document/d/([a-zA-Z0-9_-]+)', url)
    return m.group(1) if m else None


@st.cache_data(ttl=3600, show_spinner=False)
def load_corpus_index() -> list[dict]:
    """
    Reads the Recordings sheet and returns a list of dicts, one per transcribed doc:
      { name, doc_id, village, community, gender }
    Uses the Sheets API with includeGridData=True to access cell hyperlinks.
    """
    _, _, sheets_svc = get_services()
    result = sheets_svc.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        ranges=['Recordings'],
        includeGridData=True,
    ).execute()

    grid = result['sheets'][0]['data'][0]['rowData']
    corpus = []

    for row in grid[1:]:   # skip header row
        cells = row.get('values', [])

        def cell_val(idx):
            if idx >= len(cells): return None
            return cells[idx].get('formattedValue')

        def cell_link(idx):
            if idx >= len(cells): return None
            return cells[idx].get('hyperlink')

        trans_name = cell_val(COL_TRANS_LINK)
        trans_url  = cell_link(COL_TRANS_LINK)

        # Only include rows that have a real Google Doc transcription link
        if not trans_url or 'docs.google.com/document' not in trans_url:
            continue

        doc_id = _extract_doc_id(trans_url)
        if not doc_id:
            continue

        corpus.append({
            'name':      trans_name or cell_val(COL_REC_LINK) or doc_id,
            'doc_id':    doc_id,
            'village':   cell_val(COL_VILLAGE)   or '',
            'community': cell_val(COL_COMMUNITY) or '',
            'gender':    cell_val(COL_GENDER)    or '',
        })

    return corpus


@st.cache_data(ttl=3600, show_spinner=False)
def get_doc_content(doc_id: str) -> dict:
    """
    Fetches a Google Doc and splits content into:
      - italic_text:  only italic runs (the transcription body) — used for search
      - display_html: full document rendered as HTML for the viewer
                      (header greyed out, body searchable)
    """
    _, docs_svc, _ = get_services()
    try:
        doc = docs_svc.documents().get(documentId=doc_id).execute()
    except HttpError:
        return {'italic_text': '', 'display_html': '', 'body': ''}

    # ── Extract paragraph by paragraph, preserving italic info ──────────────
    paragraphs_italic = []   # (text, is_italic_dominant)
    body_content = doc.get('body', {}).get('content', [])

    for elem in body_content:
        para = elem.get('paragraph')
        if not para:
            continue

        runs = []
        for pe in para.get('elements', []):
            tr = pe.get('textRun')
            if not tr:
                continue
            text    = unicodedata.normalize('NFC', tr.get('content', ''))
            italic  = tr.get('textStyle', {}).get('italic', False)
            runs.append((text, italic))

        full_para_text = ''.join(t for t, _ in runs)
        # A paragraph counts as "italic" if the majority of non-whitespace chars are italic
        italic_chars = sum(len(t) for t, i in runs if i)
        total_chars  = sum(len(t) for t, _ in runs)
        is_italic    = (total_chars > 0) and (italic_chars / total_chars > 0.5)

        paragraphs_italic.append((full_para_text, is_italic, runs))

    # ── Split at *** separator ───────────────────────────────────────────────
    sep_idx = next(
        (i for i, (txt, _, __) in enumerate(paragraphs_italic) if txt.strip() == '***'),
        None
    )

    header_paras = paragraphs_italic[:sep_idx + 1] if sep_idx is not None else []
    body_paras   = paragraphs_italic[sep_idx + 1:] if sep_idx is not None else paragraphs_italic

    # ── italic_text: only italic body paragraphs, for search ────────────────
    italic_text = '\n'.join(
        txt for txt, is_italic, _ in body_paras if is_italic
    )

    # ── display_html: full doc, highlighting in body italic runs only ────────
    header_html = '<div class="doc-header-section">' + '\n'.join(
        txt for txt, _, __ in header_paras
    ) + '</div>'

    body_lines = []
    for txt, is_italic, runs in body_paras:
        if is_italic:
            # Mark italic runs; non-italic runs within italic paragraphs stay plain
            line = ''
            for run_txt, run_italic in runs:
                if run_italic:
                    line += f'<span class="italic-run">{run_txt}</span>'
                else:
                    line += run_txt
            body_lines.append(line)
        else:
            body_lines.append(f'<span style="color:#8899aa">{txt}</span>')

    body_html = '\n'.join(body_lines)

    return {
        'italic_text':  italic_text,
        'display_html': header_html + '\n' + body_html,
        'body':         '\n'.join(txt for txt, _, __ in body_paras),
    }


# ════════════════════════════════════════════════════════════════════════════════
#  SEARCH
# ════════════════════════════════════════════════════════════════════════════════

def run_search(
    pattern: str,
    position: str,
    name_filter: str,
    corpus: list[dict],
) -> list[dict]:

    try:
        rx = pattern_to_regex(pattern)
    except re.error as e:
        st.error(f"Invalid pattern: {e}")
        return []

    # Apply name filter
    if name_filter.strip():
        nf = name_filter.strip().lower()
        corpus = [d for d in corpus if nf in d['name'].lower()
                                    or nf in d['village'].lower()
                                    or nf in d['community'].lower()]

    if not corpus:
        st.warning("No documents match the name filter.")
        return []

    results  = []
    bar      = st.progress(0.0, text="Loading corpus…")

    for i, doc in enumerate(corpus):
        bar.progress((i + 1) / max(len(corpus), 1), text=f"Searching · {doc['name']}")
        content     = get_doc_content(doc['doc_id'])
        italic_text = content['italic_text']

        match_count   = 0
        matched_words = []

        for word in tokenize(italic_text):
            hits = match_word(word, rx, position)
            if hits:
                match_count += len(hits)
                matched_words.append(highlight_word(word, hits))

        if match_count > 0:
            # Re-highlight in the display HTML (apply to italic spans only)
            display_html = content['display_html']
            # Highlight within italic-run spans only
            display_html = re.sub(
                r'(<span class="italic-run">)(.*?)(</span>)',
                lambda m: m.group(1) + highlight_in_text(m.group(2), rx) + m.group(3),
                display_html,
                flags=re.DOTALL
            )

            results.append({
                'name':          doc['name'],
                'village':       doc['village'],
                'community':     doc['community'],
                'gender':        doc['gender'],
                'match_count':   match_count,
                'word_count':    len(tokenize(italic_text)),
                'matched_words': matched_words[:15],
                'display_html':  display_html,
            })

    bar.empty()
    results.sort(key=lambda r: r['match_count'], reverse=True)
    return results


# ════════════════════════════════════════════════════════════════════════════════
#  UI
# ════════════════════════════════════════════════════════════════════════════════

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
      <span class="legend-pill"><b>D</b> = diphthong (aw/ay)</span>
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
        st.markdown("**Pattern position within word**")
        position = st.radio(
            "position",
            options=['anywhere', 'start', 'middle', 'end'],
            horizontal=True,
            label_visibility="collapsed",
            format_func=lambda x: {
                'anywhere': '🔀  Anywhere',
                'start':    '◀  Start of word',
                'middle':   '◼  Middle of word',
                'end':      '▶  End of word',
            }[x],
        )
        st.markdown("**Filter documents by name / village / community**")
        name_filter = st.text_input(
            "name_filter",
            placeholder="e.g.  Br  or  Galilee  or  Christian  (leave blank for all)",
            label_visibility="collapsed",
            key="name_filter"
        )

    col_s, col_c = st.columns([5, 1])
    with col_s:
        search_clicked = st.button("Search corpus", type="primary", use_container_width=True)
    with col_c:
        if st.button("↺", help="Clear cache and reload", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

# ── Load corpus index once ────────────────────────────────────────────────────
with st.spinner("Loading corpus index from Google Sheets…"):
    try:
        corpus = load_corpus_index()
        st.caption(f"📚 Corpus: {len(corpus)} transcribed documents loaded from Google Sheets")
    except Exception as e:
        st.error(f"Could not load corpus index: {e}")
        corpus = []

# ── Results ───────────────────────────────────────────────────────────────────
if search_clicked and pattern_input.strip() and corpus:
    results = run_search(pattern_input.strip(), position, name_filter, corpus)

    if not results:
        st.info("No matches found for this pattern.")
    else:
        total = sum(r['match_count'] for r in results)
        st.markdown(f"""
        <div class="stats-bar">
          <span>🔍 <b>{pattern_input.strip()}</b></span>
          <span>📄 {len(results)} document{'s' if len(results) != 1 else ''}</span>
          <span>◌ {total} total match{'es' if total != 1 else ''}</span>
          <span style="color:#8899aa;font-size:0.78rem">italic text only</span>
        </div>
        """, unsafe_allow_html=True)

        for r in results:
            meta = ' · '.join(filter(None, [r['village'], r['community'], r['gender']]))
            label = f"📄  {r['name']}   ·   {r['match_count']} match{'es' if r['match_count'] != 1 else ''}"

            with st.expander(label):
                chips = ''.join(f'<span class="word-chip">{w}</span>' for w in r['matched_words'])
                more  = ' <span style="color:#8899aa;font-size:0.8rem">+ more…</span>' \
                        if r['match_count'] > len(r['matched_words']) else ''
                st.markdown(f"""
                <div class="doc-card-meta">
                  <span class="badge-green">✦ {r['match_count']} matches</span>
                  <span class="badge">{r['word_count']} words</span>
                  <span style="color:#8899aa">{meta}</span>
                </div>
                <div class="word-chips">{chips}{more}</div>
                """, unsafe_allow_html=True)

                st.markdown(
                    f'<div class="full-doc">{r["display_html"]}</div>',
                    unsafe_allow_html=True
                )

elif search_clicked and not pattern_input.strip():
    st.warning("Please enter a pattern before searching.")
