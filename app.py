# ═══════════════════════════════════════════════════════════════════════════════
#  PAI Corpus – Pattern Search Interface  v3
#  Sources docs from the Recordings sheet in Google Sheets.
#  Searches only italic text runs (the actual transcription).
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import streamlit.components.v1 as components
import re
import io
import html as html_lib
import unicodedata
import json
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# ── Declare bridge component (zero-height iframe that relays right-click tags) ─
_TAG_BRIDGE = components.declare_component(
    "pai_tag_bridge",
    path=str(Path(__file__).parent / "tagbridge"),
)

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

/* ── Advanced options expander ── */
div[data-testid="stExpander"] > details {
  background: var(--sky-100) !important;
  border: 1.5px solid var(--sky-200) !important;
  border-radius: 12px !important;
}
div[data-testid="stExpander"] > details > summary {
  background: var(--sky-100) !important;
  color: var(--sky-800) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.88rem !important;
}
/* Streamlit newer versions nest the label inside spans/p — force color */
div[data-testid="stExpander"] > details > summary *,
div[data-testid="stExpander"] > details > summary span,
div[data-testid="stExpander"] > details > summary p,
div[data-testid="stExpander"] > details > summary svg {
  color: var(--sky-800) !important;
  fill:  var(--sky-800) !important;
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
  font-family: 'Source Serif 4', serif; font-size: 0.97rem; line-height: 1.9; color: var(--ink);
  box-shadow: 0 2px 10px rgba(32,117,199,0.07);
  max-height: 65vh; overflow-y: auto; word-break: break-word;
}
.full-doc p { margin: 0.35rem 0; }
.full-doc mark { background: #b6f2c8; border-radius: 3px; padding: 0 2px; font-weight: 700; color: #0d4a22; }
.full-doc .doc-header-section {
  color: #8899aa; font-size: 0.88rem;
  border-bottom: 1px solid var(--sky-100); margin-bottom: 1rem; padding-bottom: 0.8rem;
}
.full-doc .doc-header-section p { margin: 0.1rem 0; }
.italic-run { font-style: italic; }
.body-label { color: #556677; font-weight: 600; font-style: normal; font-size: 0.9rem; margin-top: 0.6rem; }

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


_MARK_STYLE = (
    'background:#b6f2c8;border-radius:3px;padding:0 2px;'
    'font-weight:700;color:#0d4a22'
)

_TURN_MARKER_HL = re.compile(r'^[-.][ \t\u00a0]')

def _is_transcription_para(para_html: str) -> bool:
    """Same structural test used by extract_transcription_text."""
    text = html_lib.unescape(re.sub(r'<[^>]+>', '', para_html)).strip()
    non_ascii = re.findall(r'[^\x00-\x7F]', text)
    # Require ≥8 % of characters to be non-ASCII: PAI transcription lines are
    # dense with ā/ī/ħ/ʿ/š/ġ… (~20–40 %), while English summaries that happen
    # to contain a single place-name like "Rīḥa" are only ~1–2 %.
    if not non_ascii or len(non_ascii) / len(text) < 0.08:
        return False
    return bool(_TURN_MARKER_HL.match(text) or text[:1].isdigit())

def _highlight_text_nodes(fragment: str, rx: re.Pattern) -> str:
    """Highlight regex matches inside text nodes only (not inside HTML tags)."""
    parts = re.split(r'(<[^>]+>)', fragment)
    return ''.join(
        part if part.startswith('<')
        else rx.sub(lambda m: f'<mark style="{_MARK_STYLE}">{m.group()}</mark>', part)
        for part in parts
    )

def highlight_in_exported_html(html_doc: str, rx: re.Pattern) -> str:
    """
    Apply highlighting only inside transcription paragraphs (those that start
    with a digit or turn marker and contain PAI characters).  Speaker bios,
    the FEATURES section, and the metadata header are left untouched.
    """
    result   = []
    last_end = 0
    for m in re.finditer(r'(<p\b[^>]*>)(.*?)(</p>)', html_doc, re.DOTALL | re.IGNORECASE):
        result.append(html_doc[last_end:m.start()])
        open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)
        if _is_transcription_para(body):
            result.append(open_tag + _highlight_text_nodes(body, rx) + close_tag)
        else:
            result.append(m.group(0))
        last_end = m.end()
    result.append(html_doc[last_end:])
    return ''.join(result)


def inject_interaction_js(html_doc: str, doc_id: str) -> str:
    """
    Inject right-click context menu and edit-mode support into a Google Docs
    HTML export before it is rendered in the iframe.
    """
    # Serialize feature list for JavaScript
    features_js = json.dumps([
        {'name': fd[2], 'type': fd[3], 'opts': fd[4] or []}
        for fd in FEATURE_DEFS
    ])

    script = f"""
<style>
#pai-ctx-menu {{
  position:fixed; z-index:999999; min-width:250px; max-width:310px;
  max-height:min(78vh, 500px);
  background:#1c1c1e; border-radius:12px;
  box-shadow:0 8px 40px rgba(0,0,0,.6);
  padding:0; display:none; flex-direction:column;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:13px; color:#f2f2f7; user-select:none;
  overflow:hidden;
}}
#pai-ctx-header {{
  padding:7px 14px 6px; font-size:11px; color:#aaa;
  letter-spacing:.08em; text-transform:uppercase;
  border-bottom:1px solid #333; background:#1c1c1e;
  flex-shrink:0;
}}
#pai-ctx-scroll {{
  flex:1; min-height:0;
  overflow-y:auto;
  overflow-x:hidden;
  padding:4px 0;
  scrollbar-width:thin;
  scrollbar-color:#444 transparent;
}}
#pai-ctx-scroll::-webkit-scrollbar {{ width:4px; }}
#pai-ctx-scroll::-webkit-scrollbar-thumb {{ background:#444; border-radius:2px; }}
.ctx-item {{
  padding:6px 16px; cursor:pointer; display:flex;
  align-items:center; gap:10px; position:relative;
}}
.ctx-item:hover {{ background:rgba(255,255,255,.09); }}
.ctx-icon {{ color:#60aee8; font-size:11px; min-width:14px; flex-shrink:0; }}
.ctx-label {{ flex:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.ctx-badge {{
  font-size:10px; color:#666; background:#2c2c2e;
  border-radius:4px; padding:1px 5px; flex-shrink:0;
}}
.ctx-sub {{
  position:fixed; left:0; top:0;
  background:#1c1c1e; border-radius:12px;
  box-shadow:0 6px 28px rgba(0,0,0,.6);
  padding:5px 0; min-width:190px; display:none;
  font-size:13px; color:#f2f2f7; z-index:1000000;
  max-height:min(50vh,300px); overflow-y:auto;
  scrollbar-width:thin; scrollbar-color:#444 transparent;
}}
.ctx-sub-item {{ padding:7px 16px; cursor:pointer; white-space:nowrap; }}
.ctx-sub-item:hover {{ background:rgba(255,255,255,.09); }}
/* ── inline edit section ── */
#ctx-edit-section {{
  padding:8px 12px 10px; border-bottom:1px solid #333;
  background:#1c1c1e; flex-shrink:0;
}}
#ctx-edit-label {{
  font-size:10px; color:#aaa; letter-spacing:.07em;
  text-transform:uppercase; margin-bottom:6px;
}}
#ctx-edit-row {{
  display:flex; gap:6px; align-items:center;
}}
#ctx-edit-input {{
  flex:1; background:#2c2c2e; border:1px solid #444;
  border-radius:7px; color:#f2f2f7; font-size:13px;
  padding:5px 9px; outline:none; font-family:inherit;
  min-width:0;
}}
#ctx-edit-input:focus {{ border-color:#60aee8; }}
#ctx-edit-btn {{
  background:#2075c7; border:none; border-radius:7px;
  color:white; font-size:16px; padding:4px 10px;
  cursor:pointer; flex-shrink:0; line-height:1;
}}
#ctx-edit-btn:hover {{ background:#1a5fa8; }}
#ctx-edit-note {{
  font-size:10px; color:#666; margin-top:5px;
}}
</style>
<div id="pai-ctx-menu">
  <div id="pai-ctx-header">TAG FEATURE</div>
  <!-- inline edit section -->
  <div id="ctx-edit-section">
    <div id="ctx-edit-label">✏️ Replace word</div>
    <div id="ctx-edit-row">
      <input id="ctx-edit-input" type="text" placeholder="replacement…" autocomplete="off" spellcheck="false"/>
      <button id="ctx-edit-btn" title="Apply">↵</button>
    </div>
    <div id="ctx-edit-note">Replaces all occurrences in the document</div>
  </div>
  <div id="pai-ctx-scroll"></div>
</div>
<div id="pai-ctx-sub" class="ctx-sub"></div>
<script>
(function(){{
  const FEATURES   = {features_js};
  const DOC_ID     = {json.dumps(doc_id)};
  const menu       = document.getElementById('pai-ctx-menu');
  const header     = document.getElementById('pai-ctx-header');
  const scroll     = document.getElementById('pai-ctx-scroll');
  const subMenu    = document.getElementById('pai-ctx-sub');
  const editInput  = document.getElementById('ctx-edit-input');
  const editBtn    = document.getElementById('ctx-edit-btn');
  const editSect   = document.getElementById('ctx-edit-section');
  let   selText    = '';
  let   activeItem = null;

  // ── Edit section: stop clicks bubbling to the close-menu handler ────────
  editSect.addEventListener('click',   function(e) {{ e.stopPropagation(); }});
  editSect.addEventListener('mousedown', function(e) {{ e.stopPropagation(); }});

  function applyEdit() {{
    const repl = editInput.value;
    if (!repl || repl === selText) return;
    menu.style.display = 'none';
    hideSubMenu();
    try {{
      localStorage.setItem('pai_pending_tag', JSON.stringify({{
        type:      'edit',
        find:      selText,
        replace:   repl,
        docId:     DOC_ID,
        timestamp: Date.now()
      }}));
    }} catch(e) {{}}
  }}
  editBtn.addEventListener('click', applyEdit);
  editInput.addEventListener('keydown', function(e) {{
    if (e.key === 'Enter') {{ e.preventDefault(); applyEdit(); }}
    e.stopPropagation();
  }});

  // ── Build feature menu items ────────────────────────────────────────────
  FEATURES.forEach(function(fd) {{
    const item = document.createElement('div');
    item.className = 'ctx-item';

    if (fd.type === 'bool') {{
      item.innerHTML = '<span class="ctx-icon">☐</span>'
        + '<span class="ctx-label">' + fd.name + '</span>'
        + '<span class="ctx-badge">✓/✗</span>';
      item.addEventListener('click', function() {{ storeTag(fd.name, true); }});
      item.addEventListener('mouseenter', function() {{ hideSubMenu(); }});
    }} else {{
      item.innerHTML = '<span class="ctx-icon">◈</span>'
        + '<span class="ctx-label">' + fd.name + '</span>'
        + '<span class="ctx-badge">▸</span>';
      item.addEventListener('mouseenter', function() {{
        activeItem = item;
        // Build submenu content
        subMenu.innerHTML = '';
        fd.opts.forEach(function(opt) {{
          const si = document.createElement('div');
          si.className = 'ctx-sub-item';
          si.textContent = opt;
          si.addEventListener('click', function(e) {{
            e.stopPropagation();
            storeTag(fd.name, opt);
          }});
          subMenu.appendChild(si);
        }});
        // Position submenu to the right of (or left of) the main menu
        const mr = menu.getBoundingClientRect();
        const ir = item.getBoundingClientRect();
        const vw = window.innerWidth, vh = window.innerHeight;
        subMenu.style.display = 'block';
        const sr = subMenu.getBoundingClientRect();
        let sx = mr.right + 4;
        if (sx + sr.width > vw) sx = mr.left - sr.width - 4;
        let sy = ir.top;
        if (sy + sr.height > vh) sy = vh - sr.height - 8;
        subMenu.style.left = sx + 'px';
        subMenu.style.top  = sy + 'px';
      }});
    }}
    scroll.appendChild(item);
  }});

  function hideSubMenu() {{
    subMenu.style.display = 'none';
    subMenu.innerHTML = '';
    activeItem = null;
  }}

  // ── Right-click handler ─────────────────────────────────────────────────
  document.addEventListener('contextmenu', function(e) {{
    const sel = window.getSelection();
    selText = sel ? sel.toString().trim() : '';
    if (!selText) return;
    e.preventDefault();
    hideSubMenu();

    header.textContent = 'TAG: "' + selText.slice(0, 28) + (selText.length > 28 ? '…' : '') + '"';

    // First position at click, then adjust to keep fully inside viewport
    const vw = window.innerWidth, vh = window.innerHeight;
    menu.style.left = '0'; menu.style.top = '0';
    menu.style.display = 'flex';
    scroll.scrollTop = 0;
    const mr = menu.getBoundingClientRect();
    let x = e.clientX, y = e.clientY;
    if (x + mr.width  > vw) x = vw - mr.width  - 6;
    if (y + mr.height > vh) y = vh - mr.height - 6;
    if (x < 4) x = 4;
    if (y < 4) y = 4;
    menu.style.left = x + 'px';
    menu.style.top  = y + 'px';
  }});

  document.addEventListener('click', function(e) {{
    if (!menu.contains(e.target) && !subMenu.contains(e.target)) {{
      menu.style.display = 'none';
      hideSubMenu();
    }}
  }});
  document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{ menu.style.display = 'none'; hideSubMenu(); }}
  }});

  // ── Store tag in localStorage → bridge component picks it up ───────────
  function storeTag(featureName, value) {{
    menu.style.display = 'none';
    try {{
      localStorage.setItem('pai_pending_tag', JSON.stringify({{
        feature:   featureName,
        value:     value,
        docId:     DOC_ID,
        selText:   selText,
        timestamp: Date.now()
      }}));
    }} catch(e) {{}}
  }}
}})();
</script>
"""
    if '</body>' in html_doc:
        return html_doc.replace('</body>', script + '</body>')
    return html_doc + script


def extract_transcription_text(html_doc: str) -> str:
    """
    Extract the transcription-body search index from a Google Docs HTML export.

    Filters applied — derived from the structural rules of the PAI corpus:

      1. ≥1 non-ASCII (PAI) char       → skips plain-ASCII lines like
                                          FEATURES, VERB, PRONS, 1sg:, PERFECT …
      2. Starts with a digit OR a
         turn/continuation marker
         ("- " / ". ")                 → the ONLY reliable structural rule:
                                          every transcription turn is numbered
                                          ("1. rāħet …") or begins with a marker
                                          ("- w-šāfet …" / ". ʾana …").
                                          FEATURES examples and speaker bios
                                          NEVER start this way → no false matches.
      3. CSS italic ≥ 80 % of chars    → extra guard (only applied when Google
                                          Docs exports italic classes); falls back
                                          to rules 1+2 alone if it kills all lines.
    """
    # ── Parse italic CSS classes from Google Docs <style> block ──────────────
    italic_classes: set = set()
    style_m = re.search(r'<style[^>]*>(.*?)</style>', html_doc, re.DOTALL | re.IGNORECASE)
    if style_m:
        for rule_m in re.finditer(r'\.([\w-]+)\s*\{([^}]+)\}', style_m.group(1)):
            if re.search(r'font-style\s*:\s*italic', rule_m.group(2), re.IGNORECASE):
                italic_classes.add(rule_m.group(1))

    def _italic_ratio(para_html: str) -> float:
        total = italic = 0
        for attrs, content in re.findall(r'<span\b([^>]*)>(.*?)</span>', para_html, re.DOTALL):
            t = len(re.sub(r'<[^>]+>', '', content))
            total += t
            s = re.search(r'style="([^"]*)"', attrs)
            c = re.search(r'class="([^"]*)"', attrs)
            if (s and re.search(r'font-style\s*:\s*italic', s.group(1), re.IGNORECASE)) \
               or (c and set(c.group(1).split()) & italic_classes):
                italic += t
        return italic / total if total > 0 else 0.0

    paragraphs = re.findall(r'<p\b[^>]*>(.*?)</p>', html_doc, re.DOTALL | re.IGNORECASE)

    # Continuation / turn markers: "- text" or ". text"
    TURN_MARKER = re.compile(r'^[-.][ \t\u00a0]')

    def _passes_base_filters(para_html: str, text: str) -> bool:
        """
        Structural filter: keeps only PAI transcription turns.
        Every such turn starts with a digit (numbered) or a turn marker (- / .).
        FEATURES examples, speaker bios, and header lines never start this way.
        Requires ≥8 % non-ASCII density to exclude English summaries that
        happen to contain a single PAI proper noun (e.g. "Rīḥa").
        """
        non_ascii = re.findall(r'[^\x00-\x7F]', text)
        if not non_ascii or len(non_ascii) / max(len(text), 1) < 0.08:
            return False
        if not (TURN_MARKER.match(text) or text[:1].isdigit()):
            return False
        return True

    # First pass: structural filter + CSS italic guard (if italic classes found)
    lines = []
    for para in paragraphs:
        text = html_lib.unescape(unicodedata.normalize('NFC', re.sub(r'<[^>]+>', '', para))).strip()
        if not _passes_base_filters(para, text):
            continue
        if italic_classes and _italic_ratio(para) < 0.8:
            continue
        lines.append(text)

    # Safety fallback: drop CSS italic requirement if it killed all results
    if not lines:
        for para in paragraphs:
            text = html_lib.unescape(unicodedata.normalize('NFC', re.sub(r'<[^>]+>', '', para))).strip()
            if _passes_base_filters(para, text):
                lines.append(text)

    return '\n'.join(lines)


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

# ── Feature column definitions: (1-based col, col_letter, display_name, type, options) ──
# type: 'bool' = checkbox  |  'select' = fixed options  |  'text' = free text
FEATURE_DEFS: list[tuple] = [
    (13, 'M',  'aCC>iCC',                              'bool',   None),
    (14, 'N',  'diphthongs',                           'bool',   None),
    (15, 'O',  'fem. ending',                          'select', ['-i', '-e', '-a', 'pausal']),
    (16, 'P',  'med. Imāla',                           'bool',   None),
    (17, 'Q',  '-a+n (Aram. sub.)',                    'bool',   None),
    (18, 'R',  'pausal -u>-o#, -i>-e#',               'bool',   None),
    (19, 'S',  'ج',                                    'select', ['ž', 'ǧ', 'conditioned']),
    (20, 'T',  'ق',                                    'select', ['q', 'ʾ', 'g', 'k', 'g/ǧ/k (conditioned)']),
    (21, 'U',  'assimilation of gutturals to the left','bool',   None),
    (22, 'V',  'vowel epenthesis',                     'select', ['*CCC > CvCC', '*CCC > CCvC']),
    (23, 'W',  'vocal harmonizing',                    'bool',   None),
    (24, 'X',  'lowering of -uC>-oC/-iC>-eC',         'bool',   None),
    (25, 'Y',  'independent pronoun 1.pl نحن',         'select', ['niḥna', 'iḥna']),
    (26, 'Z',  'independent pronoun 3.pl هم',          'select', ['hinne/hinne', 'hunne', 'hunni', 'humme/homme', 'hum/hom']),
    (27, 'AA', '2.m.pl pron. كم-',                     'select', ['-ku/-ko', '-kum/-kom', '-čin']),
    (28, 'AB', '3.m.pl (poss. pro) هم-',               'select', ['-h- > -∅- (e.g. -on)', '-hum/-hom', '-hin/-hen']),
    (29, 'AC', '3.f.sg pron. ها-',                     'select', ['-a', '-a / -ya (after -i-)', '-ha',
                                                                   '-a; -ha only after -ū-',
                                                                   '-a; -ha only after -ū- / -i-', '-hä#/-he#']),
    (30, 'AD', 'impf. prefix 3.m.sg',                  'select', ['bi-', 'byi-', 'yi-']),
    (31, 'AE', '"want"',                               'select', ['badd', 'bidd', 'widd']),
    (32, 'AF', '"now"',                                'select', ['issa/hassāʿa', 'hallaʾ/halʾēt/halkēt/halgēt', 'alḥīn']),
    (33, 'AG', '"when?"',                              'select', ['ēmta', 'wēnta', 'wagtēš']),
    (34, 'AH', '"here"',                               'select', ['hōn', 'hīn', 'hān', 'hina']),
    (35, 'AI', '"was"',                                'select', ['kān', 'kān / čān', 'baka~biki / yibki~yibka',
                                                                  'baka/biki', 'baka~biki / yikbi~yikba']),
]

# Features that appear in the doc FEATURES section but are NOT in the M-AI spreadsheet columns
DOC_ONLY_FEATURES: list[str] = [
    'long particles',
    'sandhi',
    '-a~-ä/-e#',
    'ḌLL+pron.',
    'Continuous modifier',
    'Anticipatory pronominal suffix',
]

# Map from feature display_name → FEATURE_DEFS entry (for fast lookup)
_FEAT_BY_NAME: dict = {fd[2]: fd for fd in FEATURE_DEFS}


@st.cache_resource
def get_services():
    creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/documents',
            'https://www.googleapis.com/auth/spreadsheets',
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

    for grid_row_idx, row in enumerate(grid[1:], start=2):   # skip header; sheet row = grid_idx+1
        cells = row.get('values', [])

        def cell_val(idx, _cells=cells):
            if idx >= len(_cells): return None
            return _cells[idx].get('formattedValue')

        def cell_link(idx, _cells=cells):
            if idx >= len(_cells): return None
            return _cells[idx].get('hyperlink')

        trans_name = cell_val(COL_TRANS_LINK)
        trans_url  = cell_link(COL_TRANS_LINK)

        # Only include rows that have a real Google Doc transcription link
        if not trans_url or 'docs.google.com/document' not in trans_url:
            continue

        doc_id = _extract_doc_id(trans_url)
        if not doc_id:
            continue

        corpus.append({
            'name':       trans_name or cell_val(COL_REC_LINK) or doc_id,
            'doc_id':     doc_id,
            'village':    cell_val(COL_VILLAGE)   or '',
            'community':  cell_val(COL_COMMUNITY) or '',
            'gender':     cell_val(COL_GENDER)    or '',
            'sheet_row':  grid_row_idx,   # 1-based row number in the Recordings sheet
        })

    return corpus


@st.cache_data(ttl=3600, show_spinner=False)
def get_doc_content(doc_id: str) -> dict:
    """
    Fetches a Google Doc via the Drive API HTML export.
      - display_html: full Google Docs HTML — rendered pixel-perfect in the viewer
      - italic_text:  italic body text (after ***) extracted from the HTML CSS classes
                      — used as the search index (reliable, no Docs API needed)
    """
    try:
        drive_svc, _, _ = get_services()

        export_req = drive_svc.files().export_media(fileId=doc_id, mimeType='text/html')
        buf = io.BytesIO()
        dl  = MediaIoBaseDownload(buf, export_req)
        done = False
        while not done:
            _, done = dl.next_chunk()
        display_html = buf.getvalue().decode('utf-8')

    except Exception:
        return {'italic_text': '', 'display_html': ''}

    italic_text = extract_transcription_text(display_html)

    return {
        'italic_text':  italic_text,
        'display_html': display_html,
    }


# ════════════════════════════════════════════════════════════════════════════════
#  FEATURE READ / WRITE
# ════════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_sheet_features(sheet_row: int) -> dict:
    """
    Read feature values (columns M–AI) for a single Recordings sheet row.
    Returns {col_letter: value} where value is True/False for bool cols or str for select cols.
    """
    _, _, sheets_svc = get_services()
    first_col, last_col = FEATURE_DEFS[0][1], FEATURE_DEFS[-1][1]   # 'M', 'AI'
    range_a1 = f"Recordings!{first_col}{sheet_row}:{last_col}{sheet_row}"
    result = sheets_svc.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_a1,
        valueRenderOption='UNFORMATTED_VALUE',
    ).execute()
    raw = (result.get('values') or [[]])[0]
    out = {}
    for i, fd in enumerate(FEATURE_DEFS):
        val = raw[i] if i < len(raw) else None
        if fd[3] == 'bool':
            out[fd[1]] = bool(val) if val is not None else None
        else:
            out[fd[1]] = str(val) if val else None
    return out


def write_sheet_features(sheet_row: int, changes: dict[str, object]) -> list[str]:
    """
    Write feature changes to Google Sheets.
    changes: {col_letter: new_value}
    Returns list of conflict messages (non-empty if any existing value differs).
    """
    _, _, sheets_svc = get_services()
    current = get_sheet_features(sheet_row)
    conflicts = []

    # Detect conflicts: existing non-null value that differs from the proposed change
    for col_letter, new_val in changes.items():
        cur_val = current.get(col_letter)
        if cur_val is not None and cur_val != new_val:
            fd = next((f for f in FEATURE_DEFS if f[1] == col_letter), None)
            name = fd[2] if fd else col_letter
            conflicts.append(
                f"**{name}**: spreadsheet has `{cur_val}`, you tagged `{new_val}`"
            )

    if conflicts:
        return conflicts

    # Write each changed cell
    data = []
    for col_letter, new_val in changes.items():
        fd = next((f for f in FEATURE_DEFS if f[1] == col_letter), None)
        if fd is None:
            continue
        cell_a1 = f"Recordings!{col_letter}{sheet_row}"
        if fd[3] == 'bool':
            data.append({'range': cell_a1, 'values': [[bool(new_val)]]})
        else:
            data.append({'range': cell_a1, 'values': [[new_val]]})

    if data:
        sheets_svc.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'valueInputOption': 'RAW', 'data': data},
        ).execute()
        get_sheet_features.clear()   # invalidate cache

    return []


def _build_features_block(sheet_vals: dict, doc_only_vals: dict) -> str:
    """Build the FEATURES text block to write into the Google Doc."""
    lines = ['FEATURES:']
    # M-AI features (from spreadsheet)
    for fd in FEATURE_DEFS:
        col_l, name, ftype = fd[1], fd[2], fd[3]
        val = sheet_vals.get(col_l)
        if ftype == 'bool':
            lines.append(f'{name}  [{"+" if val else ""}]')
        else:
            lines.append(f'{name}  [{val or ""}]')
    # Doc-only features
    for name in DOC_ONLY_FEATURES:
        val = doc_only_vals.get(name)
        if isinstance(val, bool):
            lines.append(f'{name}  [{"+" if val else ""}]')
        elif val:
            lines.append(f'{name}  [{val}]')
        else:
            lines.append(f'{name}  []')
    return '\n'.join(lines)


def update_gdoc_features_section(doc_id: str, sheet_vals: dict, doc_only_vals: dict):
    """
    Replace (or append) the FEATURES section in the Google Doc.
    Uses the Docs API batchUpdate with deleteContentRange + insertText.
    """
    _, docs_svc, _ = get_services()
    doc = docs_svc.documents().get(documentId=doc_id).execute()
    body_content = doc.get('body', {}).get('content', [])

    all_feature_names = {fd[2] for fd in FEATURE_DEFS} | set(DOC_ONLY_FEATURES)

    feat_start = None   # startIndex of "FEATURES:" paragraph
    feat_end   = None   # startIndex of paragraph AFTER the features block

    for elem in body_content:
        if 'paragraph' not in elem:
            continue
        text = ''.join(
            e.get('textRun', {}).get('content', '')
            for e in elem['paragraph'].get('elements', [])
        ).strip()

        if text == 'FEATURES:':
            feat_start = elem['startIndex']
            continue

        if feat_start is not None:
            # End the block when we hit an empty line or something outside the feature list
            if text and not any(text.startswith(fn) for fn in all_feature_names):
                feat_end = elem['startIndex']
                break

    new_block = _build_features_block(sheet_vals, doc_only_vals)

    if feat_start is None:
        # No FEATURES section — append at the end of the document
        end_idx = body_content[-1]['endIndex'] - 1
        docs_svc.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [{'insertText': {
                'location': {'index': end_idx},
                'text': '\n\n' + new_block,
            }}]},
        ).execute()
    else:
        end_idx = feat_end if feat_end else body_content[-1]['endIndex'] - 1
        # Delete old block, then insert new one at same position
        docs_svc.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': [
                {'deleteContentRange': {'range': {
                    'startIndex': feat_start, 'endIndex': end_idx,
                }}},
                {'insertText': {
                    'location': {'index': feat_start},
                    'text': new_block,
                }},
            ]},
        ).execute()

    get_doc_content.clear()   # force re-fetch of the display HTML


def find_replace_in_gdoc(doc_id: str, find_text: str, replace_text: str) -> int:
    """
    Apply replaceAllText in a Google Doc.  Returns the number of replacements made.
    Raises on API error.
    """
    _, docs_svc, _ = get_services()
    resp = docs_svc.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': [{
            'replaceAllText': {
                'containsText': {'text': find_text, 'matchCase': True},
                'replaceText':  replace_text,
            }
        }]},
    ).execute()
    count = (
        resp.get('replies', [{}])[0]
           .get('replaceAllText', {})
           .get('occurrencesChanged', 0)
    )
    if count:
        get_doc_content.clear()
    return count


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
        content      = get_doc_content(doc['doc_id'])
        search_text  = content['italic_text']

        match_count   = 0
        matched_words = []

        for word in tokenize(search_text):
            hits = match_word(word, rx, position)
            if hits:
                match_count += len(hits)
                matched_words.append(highlight_word(word, hits))

        if match_count > 0:
            # Highlight matches in the exported Google Docs HTML (all text nodes)
            display_html = highlight_in_exported_html(content['display_html'], rx)

            results.append({
                'name':          doc['name'],
                'doc_id':        doc['doc_id'],
                'sheet_row':     doc.get('sheet_row'),
                'village':       doc['village'],
                'community':     doc['community'],
                'gender':        doc['gender'],
                'match_count':   match_count,
                'word_count':    len(tokenize(search_text)),
                'matched_words': matched_words[:15],
                'display_html':  display_html,
            })

    bar.empty()
    results.sort(key=lambda r: r['match_count'], reverse=True)
    return results


def search_by_name(query: str, corpus: list[dict]) -> list[dict]:
    """
    Find documents whose name (or village / community) contains the query
    as a literal substring (case-insensitive).  Used for the 'Find document'
    mode so users can look up identifiers like Xḏ̣.2M.R1(t) directly.
    """
    q = query.strip().lower()
    matches = [
        doc for doc in corpus
        if q in doc['name'].lower()
        or q in doc.get('village', '').lower()
        or q in doc.get('community', '').lower()
    ]
    if not matches:
        return []

    results = []
    bar = st.progress(0.0, text="Loading document…")
    for i, doc in enumerate(matches):
        bar.progress((i + 1) / max(len(matches), 1), text=f"Loading · {doc['name']}")
        try:
            content = get_doc_content(doc['doc_id'])
        except Exception:
            continue
        results.append({
            'name':          doc['name'],
            'doc_id':        doc['doc_id'],
            'sheet_row':     doc.get('sheet_row'),
            'village':       doc['village'],
            'community':     doc['community'],
            'gender':        doc['gender'],
            'match_count':   1,
            'word_count':    len(tokenize(content['italic_text'])),
            'matched_words': [],
            'display_html':  content['display_html'],
        })
    bar.empty()
    return results


# ════════════════════════════════════════════════════════════════════════════════
#  FEATURE TAGGING PANEL
# ════════════════════════════════════════════════════════════════════════════════

def _render_feature_panel(doc_id: str, doc_name: str, sheet_row: int):
    """
    Renders the feature tagging expander below a document viewer.
    Loads current values from Google Sheets, lets the user edit them,
    and on Submit writes back to the sheet and updates the Google Doc.
    """
    sk = f"feat_{doc_id}"   # unique session-state namespace for this doc

    with st.expander("✏️  Tag features for this document", expanded=False):
        st.caption(
            f"Changes are written to the **Recordings** sheet row {sheet_row} "
            f"(columns M–AI) and to the Google Doc's FEATURES section. "
            f"Right-click the transcript above to copy a word, then record the feature below."
        )

        # Load current sheet values (cached)
        try:
            current = get_sheet_features(sheet_row)
        except Exception as e:
            st.error(f"Could not load spreadsheet values: {e}")
            return

        # Session-state keys for pending edits
        if f"{sk}_pending" not in st.session_state:
            st.session_state[f"{sk}_pending"] = {}   # {col_letter: new_value}
        if f"{sk}_doc_only" not in st.session_state:
            st.session_state[f"{sk}_doc_only"] = {}  # {feature_name: value}

        pending   = st.session_state[f"{sk}_pending"]
        doc_only  = st.session_state[f"{sk}_doc_only"]

        st.markdown("#### Spreadsheet features (M–AI)")
        # Render in 2-column grid
        col_pairs = list(zip(FEATURE_DEFS[::2], FEATURE_DEFS[1::2]))
        if len(FEATURE_DEFS) % 2:
            col_pairs.append((FEATURE_DEFS[-1], None))

        for fd_left, fd_right in col_pairs:
            c1, c2 = st.columns(2)
            for col, fd in [(c1, fd_left), (c2, fd_right)]:
                if fd is None:
                    continue
                col_l, name, ftype, opts = fd[1], fd[2], fd[3], fd[4]
                cur_val = pending.get(col_l, current.get(col_l))
                widget_key = f"{sk}_{col_l}"

                with col:
                    if ftype == 'bool':
                        new_val = st.checkbox(
                            name, value=bool(cur_val), key=widget_key,
                        )
                    else:
                        choices = ['(not set)'] + (opts or [])
                        cur_idx = (choices.index(cur_val)
                                   if cur_val in choices else 0)
                        sel = st.selectbox(
                            name, choices, index=cur_idx, key=widget_key,
                        )
                        new_val = None if sel == '(not set)' else sel

                    # Track change vs. original sheet value
                    orig = current.get(col_l)
                    if new_val != orig:
                        pending[col_l] = new_val
                    elif col_l in pending and pending[col_l] == orig:
                        del pending[col_l]

        st.markdown("#### Document-only features")
        for name in DOC_ONLY_FEATURES:
            cur_val = doc_only.get(name)
            new_val = st.checkbox(name, value=bool(cur_val),
                                  key=f"{sk}_donly_{name}")
            doc_only[name] = new_val

        # ── Submit button ─────────────────────────────────────────────────
        has_changes = bool(pending) or any(doc_only.values())
        if has_changes:
            n_changes = len(pending) + sum(1 for v in doc_only.values() if v)
            if st.button(
                f"💾  Submit {n_changes} change(s) for **{doc_name}**",
                key=f"{sk}_submit", type="primary",
            ):
                st.session_state[f"{sk}_confirm"] = True

        if st.session_state.get(f"{sk}_confirm"):
            st.warning(
                f"⚠️  You are about to write **{len(pending)}** spreadsheet "
                f"change(s) and update the Google Doc for **{doc_name}**. "
                f"This cannot be undone. Proceed?"
            )
            yes_col, no_col = st.columns(2)
            with yes_col:
                if st.button("✅  Yes, submit", key=f"{sk}_yes"):
                    # 1. Write to Google Sheets
                    conflicts = []
                    if pending:
                        try:
                            conflicts = write_sheet_features(sheet_row, pending)
                        except Exception as e:
                            st.error(f"Spreadsheet write failed: {e}")
                            st.session_state[f"{sk}_confirm"] = False
                            return

                    if conflicts:
                        st.error(
                            "⚠️  Some values already exist in the spreadsheet "
                            "and differ from your tagging — **not written**:\n\n"
                            + "\n".join(f"- {c}" for c in conflicts)
                        )
                        st.session_state[f"{sk}_confirm"] = False
                        return

                    # 2. Update Google Doc FEATURES section
                    try:
                        # Merge sheet values: original + accepted changes
                        merged_sheet = {**current, **pending}
                        update_gdoc_features_section(doc_id, merged_sheet, doc_only)
                    except Exception as e:
                        st.error(f"Google Doc update failed: {e}")
                        st.session_state[f"{sk}_confirm"] = False
                        return

                    # 3. Clear pending state
                    st.session_state[f"{sk}_pending"] = {}
                    st.session_state[f"{sk}_doc_only"] = {}
                    st.session_state[f"{sk}_confirm"] = False
                    st.success(f"✅  Features saved for **{doc_name}**!")
                    st.rerun()

            with no_col:
                if st.button("❌  Cancel", key=f"{sk}_no"):
                    st.session_state[f"{sk}_confirm"] = False
                    st.rerun()


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
    # ── Search mode toggle ────────────────────────────────────────────────────
    search_mode = st.radio(
        "search_mode",
        options=['transcription', 'document'],
        format_func=lambda x: '🔍  Search transcriptions' if x == 'transcription' else '📄  Find document by name / ID',
        horizontal=True,
        label_visibility="collapsed",
        key="search_mode",
    )

    if search_mode == 'transcription':
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
    else:
        pattern_input = st.text_input(
            "Document name or ID",
            placeholder="Type document name or ID…   e.g.  Xḏ̣.2M.R1(t)  or  Galilee",
            label_visibility="collapsed",
            key="pattern"
        )

    with st.expander("⚙️  Advanced options"):
        if search_mode == 'transcription':
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
        else:
            st.info("In document search mode the query is matched literally (no regex) against document names and metadata.", icon="ℹ️")
            position    = 'anywhere'
            name_filter = ''


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

# ── Bridge component: listens for right-click tags from document iframes ──────
_bridge_tag = _TAG_BRIDGE(key="tagbridge")
if _bridge_tag:
    _bt_type = _bridge_tag.get('type', '')
    doc_id   = _bridge_tag.get('docId', '')

    if _bt_type == 'edit':
        # ── Inline find-and-replace from context menu ──────────────────────────
        find_text = _bridge_tag.get('find', '').strip()
        repl_text = _bridge_tag.get('replace', '').strip()
        if find_text and repl_text and doc_id:
            try:
                n = find_replace_in_gdoc(doc_id, find_text, repl_text)
                st.session_state['_ctx_edit_result'] = (find_text, repl_text, n, None)
            except Exception as e:
                st.session_state['_ctx_edit_result'] = (find_text, repl_text, 0, str(e))
        st.session_state['_bridge_tag_processed'] = True

    else:
        # ── Feature tag from context menu ──────────────────────────────────────
        feat_name = _bridge_tag.get('feature', '')
        feat_val  = _bridge_tag.get('value')
        fd = _FEAT_BY_NAME.get(feat_name)
        if fd and doc_id:
            sk = f"feat_{doc_id}"
            if f"{sk}_pending" not in st.session_state:
                st.session_state[f"{sk}_pending"] = {}
            st.session_state[f"{sk}_pending"][fd[1]] = feat_val
            st.session_state[f"{sk}_auto_expand"] = True
            st.session_state['_bridge_tag_processed'] = True

# ── Show result of context-menu find-replace (survives the rerun) ─────────────
if '_ctx_edit_result' in st.session_state:
    _find, _repl, _n, _err = st.session_state.pop('_ctx_edit_result')
    if _err:
        st.error(f'Replace failed: {_err}')
    elif _n:
        st.success(f'✅  Replaced {_n} occurrence(s) of "{_find}" → "{_repl}"')
    else:
        st.info(f'No occurrences of "{_find}" found in this document.')

# ── Results ───────────────────────────────────────────────────────────────────
if search_clicked and pattern_input.strip() and corpus:
    try:
        if search_mode == 'document':
            results = search_by_name(pattern_input.strip(), corpus)
            if not results:
                st.warning(f'No documents found matching "{pattern_input.strip()}".')
        else:
            results = run_search(pattern_input.strip(), position, name_filter, corpus)
        st.session_state['_search_results']  = results
        st.session_state['_search_pattern']  = pattern_input.strip()
        st.session_state['_search_mode']     = search_mode
    except Exception as e:
        st.error(f"Search failed: {e}")
        results = []
        st.session_state['_search_results'] = []
elif search_clicked and not pattern_input.strip():
    st.warning("Please enter a pattern before searching.")

# Always display stored results (survive rerun after bridge tag)
results       = st.session_state.get('_search_results', [])
pattern_shown = st.session_state.get('_search_pattern', '')
mode_shown    = st.session_state.get('_search_mode', 'transcription')

if results:
    total = sum(r['match_count'] for r in results)
    if mode_shown == 'document':
        stats_label = f"📄 {len(results)} document{'s' if len(results) != 1 else ''} matched"
        st.markdown(f"""
        <div class="stats-bar">
          <span>📄 <b>{pattern_shown}</b></span>
          <span>{len(results)} document{'s' if len(results) != 1 else ''} found</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="stats-bar">
          <span>🔍 <b>{pattern_shown}</b></span>
          <span>📄 {len(results)} document{'s' if len(results) != 1 else ''}</span>
          <span>◌ {total} total match{'es' if total != 1 else ''}</span>
        </div>
        """, unsafe_allow_html=True)

    seen_doc_ids = set()
    for r in results:
        if r['doc_id'] in seen_doc_ids:
            continue          # skip duplicate doc_ids (same Google Doc listed twice in sheet)
        seen_doc_ids.add(r['doc_id'])

        meta  = ' · '.join(filter(None, [r['village'], r['community'], r['gender']]))
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

            # Document viewer — with right-click context menu injected
            interactive_html = inject_interaction_js(r['display_html'], r['doc_id'])
            components.html(interactive_html, height=550, scrolling=True)

            # ── Feature tagging panel ───────────────────────────────────────
            if r.get('sheet_row'):
                _render_feature_panel(r['doc_id'], r['name'], r['sheet_row'])

            # ── Find & Replace editor ───────────────────────────────────────
            with st.expander("✏️  Edit document text (find & replace)"):
                st.caption(
                    "Correct typos or transcription errors directly in the Google Doc. "
                    "Changes are applied immediately when you click **Apply**."
                )
                fe_col1, fe_col2, fe_col3 = st.columns([5, 5, 2])
                with fe_col1:
                    find_text = st.text_input(
                        "Find (exact, case-sensitive)",
                        key=f"find_{r['doc_id']}",
                        placeholder="e.g.  bidi",
                    )
                with fe_col2:
                    repl_text = st.text_input(
                        "Replace with",
                        key=f"repl_{r['doc_id']}",
                        placeholder="e.g.  badi",
                    )
                with fe_col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    apply_clicked = st.button(
                        "Apply", key=f"apply_{r['doc_id']}", type="primary",
                        use_container_width=True,
                    )

                if apply_clicked:
                    if not find_text.strip():
                        st.warning("Enter text to find.")
                    elif find_text.strip() == repl_text.strip():
                        st.warning("Find and Replace texts are identical.")
                    else:
                        try:
                            n = find_replace_in_gdoc(r['doc_id'], find_text, repl_text)
                            if n:
                                st.success(f'✅  Replaced {n} occurrence(s) of "{find_text}" → "{repl_text}"')
                            else:
                                st.info(f'No occurrences of "{find_text}" found in this document.')
                        except Exception as e:
                            st.error(f"Edit failed: {e}")

                st.markdown(
                    f"[Open full document in Google Docs ↗](https://docs.google.com/document/d/{r['doc_id']}/edit)",
                    unsafe_allow_html=False,
                )