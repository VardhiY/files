import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from urllib.error import HTTPError, URLError
import csv
import io
import os

# ── PAGE CONFIG ─────────────────────────
st.set_page_config(
    page_title="LEXIS AI",
    page_icon="⚡",
    layout="wide"
)

# ── LOAD API KEY ───────────────────────
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        pass

if not api_key:
    st.error("⚠️ GROQ_API_KEY missing. Add it in Render → Environment Variables.")
    st.stop()

client = Groq(api_key=api_key)

# ── STYLING ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Sora:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── BASE ── */
.stApp {
    background: #0c0c10 !important;
    color: #e8e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Subtle ambient background ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 900px 700px at -5% 0%,   rgba(139,92,246,0.11) 0%, transparent 55%),
        radial-gradient(ellipse 700px 600px at 105% 100%, rgba(236,72,153,0.09) 0%, transparent 55%),
        radial-gradient(ellipse 600px 500px at 50%  110%, rgba(6,182,212,0.06)  0%, transparent 55%);
    pointer-events: none;
    z-index: 0;
}

.block-container {
    padding-top: 0 !important;
    padding-bottom: 3rem !important;
    max-width: 1300px !important;
    position: relative;
    z-index: 1;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

/* ══════════════════════════════════
   NAV
══════════════════════════════════ */
.lx-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 2.5rem;
}
.lx-logo-wrap { display: flex; align-items: center; gap: 0.6rem; }
.lx-logo-icon {
    width: 34px; height: 34px;
    background: linear-gradient(135deg, #7c3aed, #db2777);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.95rem;
    box-shadow: 0 4px 14px rgba(124,58,237,0.4);
}
.lx-logo-text {
    font-family: 'Sora', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: #f0f0f8;
    letter-spacing: -0.3px;
}
.lx-logo-text span {
    background: linear-gradient(90deg, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.lx-nav-center {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.22);
    border: 1px solid rgba(255,255,255,0.07);
    padding: 0.28rem 0.9rem;
    border-radius: 100px;
}
.lx-status {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.78rem;
    font-weight: 500;
    color: rgba(255,255,255,0.38);
}
.lx-status-dot {
    width: 7px; height: 7px;
    background: #4ade80;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(74,222,128,0.55);
    animation: sDot 2.5s ease-in-out infinite;
}
@keyframes sDot { 0%,100%{opacity:1;} 50%{opacity:0.35;} }

/* ══════════════════════════════════
   HERO
══════════════════════════════════ */
.lx-hero {
    text-align: center;
    padding: 0.5rem 0 3rem;
}
.lx-hero-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(139,92,246,0.09);
    border: 1px solid rgba(139,92,246,0.18);
    border-radius: 100px;
    padding: 0.28rem 0.85rem;
    font-size: 0.73rem;
    font-weight: 500;
    color: #a78bfa;
    letter-spacing: 0.04em;
    margin-bottom: 1.4rem;
}
.lx-hero-tag::before {
    content: '';
    width: 6px; height: 6px;
    background: #8b5cf6;
    border-radius: 50%;
    flex-shrink: 0;
}
.lx-h1 {
    font-family: 'Sora', sans-serif;
    font-size: clamp(2.6rem, 5.5vw, 4.5rem);
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -1.5px;
    color: #f0f0f8;
    margin-bottom: 0.85rem;
}
.lx-h1 .grad {
    background: linear-gradient(135deg, #a78bfa 0%, #f472b6 55%, #fb923c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.lx-hero-sub {
    font-size: 0.97rem;
    color: rgba(255,255,255,0.35);
    max-width: 400px;
    margin: 0 auto;
    line-height: 1.72;
}

/* ══════════════════════════════════
   CARD WRAPPERS
══════════════════════════════════ */
.lx-card {
    background: #13131a;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
    padding: 1.4rem 1.5rem 0.5rem;
    margin-bottom: 1.1rem;
}
.lx-card-hdr {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.1rem;
}
.lx-card-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.12em;
    color: rgba(255,255,255,0.18);
    background: rgba(255,255,255,0.05);
    border-radius: 5px;
    padding: 0.12rem 0.38rem;
}
.lx-card-ttl {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.3);
}
.lx-card-line { flex:1; height:1px; background:rgba(255,255,255,0.05); }

/* ══════════════════════════════════
   TABS
══════════════════════════════════ */
div[data-baseweb="tab-list"] {
    background: #0c0c10 !important;
    border-radius: 11px !important;
    padding: 4px !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    gap: 2px !important;
    margin-bottom: 1.1rem !important;
}
div[data-baseweb="tab"] {
    border-radius: 8px !important;
    color: rgba(255,255,255,0.32) !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    padding: 0.48rem 1.1rem !important;
    transition: all 0.18s !important;
}
div[aria-selected="true"] {
    background: #1e1e2e !important;
    color: #e8e8f0 !important;
    box-shadow: 0 1px 5px rgba(0,0,0,0.4) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}
div[data-baseweb="tab-panel"] { background: transparent !important; padding: 0 !important; }

/* ══════════════════════════════════
   INPUTS
══════════════════════════════════ */
textarea, .stTextInput input {
    background: #0c0c10 !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 11px !important;
    color: #e8e8f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.8rem 0.95rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    line-height: 1.6 !important;
    caret-color: #a78bfa !important;
}
textarea:focus, .stTextInput input:focus {
    border-color: rgba(139,92,246,0.48) !important;
    box-shadow: 0 0 0 3px rgba(139,92,246,0.07) !important;
    outline: none !important;
}
textarea::placeholder, .stTextInput input::placeholder { color: rgba(255,255,255,0.15) !important; }

/* ══════════════════════════════════
   PRIMARY BUTTON
══════════════════════════════════ */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #6d28d9, #be185d) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.7rem 1.5rem !important;
    letter-spacing: 0.02em !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    margin-top: 0.7rem !important;
    box-shadow: 0 3px 12px rgba(109,40,217,0.28) !important;
}
.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 7px 22px rgba(109,40,217,0.38) !important;
}
.stButton > button:active { transform: translateY(0) !important; opacity: 1 !important; }

/* ══════════════════════════════════
   DOWNLOAD BUTTONS
══════════════════════════════════ */
.stDownloadButton > button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    color: rgba(255,255,255,0.45) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 9px !important;
    padding: 0.48rem 0.95rem !important;
    font-size: 0.8rem !important;
    transition: all 0.18s !important;
}
.stDownloadButton > button:hover {
    background: rgba(139,92,246,0.09) !important;
    border-color: rgba(139,92,246,0.3) !important;
    color: #a78bfa !important;
}

/* ══════════════════════════════════
   KEYWORD ROWS
══════════════════════════════════ */
.kw-row {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 0.65rem 0.85rem;
    border-radius: 9px;
    margin-bottom: 0.35rem;
    background: rgba(255,255,255,0.018);
    border: 1px solid rgba(255,255,255,0.05);
    transition: background 0.18s, border-color 0.18s, transform 0.15s;
    cursor: default;
}
.kw-row:hover {
    background: rgba(255,255,255,0.04);
    border-color: rgba(255,255,255,0.09);
    transform: translateX(3px);
}
.kw-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: rgba(255,255,255,0.16);
    min-width: 22px;
}
.kw-word { flex:1; font-size: 0.9rem; font-weight: 500; color: #ddddf0; }
.kw-bar-wrap { display:flex; align-items:center; gap:0.6rem; min-width:120px; }
.kw-bar-bg { flex:1; height:3px; background:rgba(255,255,255,0.06); border-radius:100px; overflow:hidden; }
.kw-bar-fill { height:100%; border-radius:100px; }
.kw-sc { font-family:'JetBrains Mono',monospace; font-size:0.68rem; min-width:30px; text-align:right; font-weight:500; }

.r0 .kw-bar-fill{background:#a78bfa;} .r0 .kw-sc{color:#a78bfa;}
.r1 .kw-bar-fill{background:#f472b6;} .r1 .kw-sc{color:#f472b6;}
.r2 .kw-bar-fill{background:#fb923c;} .r2 .kw-sc{color:#fb923c;}
.r3 .kw-bar-fill{background:#34d399;} .r3 .kw-sc{color:#34d399;}
.r4 .kw-bar-fill{background:#38bdf8;} .r4 .kw-sc{color:#38bdf8;}
.r5 .kw-bar-fill,.r6 .kw-bar-fill,.r7 .kw-bar-fill,
.r8 .kw-bar-fill,.r9 .kw-bar-fill{background:rgba(255,255,255,0.22);}
.r5 .kw-sc,.r6 .kw-sc,.r7 .kw-sc,.r8 .kw-sc,.r9 .kw-sc{color:rgba(255,255,255,0.3);}

/* ══════════════════════════════════
   CHAT
══════════════════════════════════ */
.chat-from {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.16);
    margin-bottom: 0.2rem;
}
.chat-from.you { text-align:right; color:rgba(167,139,250,0.45); }
.chat-msg {
    padding: 0.7rem 0.95rem;
    border-radius: 13px;
    font-size: 0.87rem;
    line-height: 1.65;
    max-width: 85%;
    margin-bottom: 0.55rem;
}
.chat-msg.you {
    background: linear-gradient(135deg, #4c1d95, #9d174d);
    color: rgba(255,255,255,0.88);
    margin-left: auto;
    border-bottom-right-radius: 3px;
}
.chat-msg.ai {
    background: #18181f;
    border: 1px solid rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.68);
    border-bottom-left-radius: 3px;
}

/* form reset */
div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
div[data-testid="stForm"] .stButton > button {
    background: #18181f !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.5) !important;
    box-shadow: none !important;
    margin-top: 0 !important;
    font-size: 1rem !important;
    padding: 0.68rem 1rem !important;
    border-radius: 10px !important;
}
div[data-testid="stForm"] .stButton > button:hover {
    background: rgba(139,92,246,0.12) !important;
    border-color: rgba(139,92,246,0.28) !important;
    color: #a78bfa !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ══════════════════════════════════
   SIDEBAR CARDS
══════════════════════════════════ */
.sc { background:#13131a; border:1px solid rgba(255,255,255,0.07); border-radius:15px; padding:1.1rem; margin-bottom:0.9rem; }
.sc-ttl { font-size:0.65rem; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:rgba(255,255,255,0.26); margin-bottom:0.9rem; display:flex; align-items:center; gap:0.45rem; }
.sc-ttl::after { content:''; flex:1; height:1px; background:rgba(255,255,255,0.05); }

.sg { display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-bottom:0.6rem; }
.si { background:#0c0c10; border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:0.7rem; text-align:center; }
.sv { font-family:'Sora',sans-serif; font-size:1.4rem; font-weight:700; line-height:1; margin-bottom:0.18rem; }
.sl { font-size:0.58rem; font-weight:500; letter-spacing:0.1em; text-transform:uppercase; color:rgba(255,255,255,0.2); }
.tkb { background:#0c0c10; border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:0.7rem 0.9rem; }
.tkl { font-size:0.58rem; font-weight:500; letter-spacing:0.1em; text-transform:uppercase; color:rgba(255,255,255,0.2); margin-bottom:0.22rem; }
.tkv { font-size:0.95rem; font-weight:600; color:#c4b5fd; }

/* legend */
.lr { display:flex; align-items:center; gap:0.7rem; margin-bottom:0.5rem; font-size:0.8rem; color:rgba(255,255,255,0.4); }
.ld { width:8px; height:8px; border-radius:50%; flex-shrink:0; }

/* ══════════════════════════════════
   MISC
══════════════════════════════════ */
.stSpinner > div { border-top-color: #8b5cf6 !important; }
.stAlert { background:rgba(109,40,217,0.08) !important; border:1px solid rgba(109,40,217,0.2) !important; border-radius:9px !important; }
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { background:transparent !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ──────────────────────────────────────────────────────────────────
def render_kw_cards(kws):
    html = ""
    for i, k in enumerate(kws):
        rc  = f"r{min(i,9)}"
        pct = int(float(k.get("score", 0)) * 100)
        html += f"""
<div class="kw-row {rc}">
  <span class="kw-num">#{i+1:02d}</span>
  <span class="kw-word">{k['keyword']}</span>
  <div class="kw-bar-wrap">
    <div class="kw-bar-bg"><div class="kw-bar-fill" style="width:{pct}%"></div></div>
    <span class="kw-sc">{float(k.get('score',0)):.2f}</span>
  </div>
</div>"""
    return html

def kws_to_csv(kws):
    buf = io.StringIO()
    w   = csv.DictWriter(buf, fieldnames=["rank","keyword","score"])
    w.writeheader()
    for i, k in enumerate(kws, 1):
        w.writerow({"rank":i, "keyword":k["keyword"], "score":k.get("score","")})
    return buf.getvalue().encode()

def kws_to_plain(kws):
    return "\n".join(f"{i+1}. {k['keyword']} ({float(k.get('score',0)):.2f})"
                     for i, k in enumerate(kws))

def extract_keywords(text):
    prompt = f"""Extract top 10 important keywords from the following text.
Return ONLY a JSON array. No explanation. No markdown. Example:
[{{"keyword":"example","score":0.95}}]

TEXT:
{text[:6000]}"""
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2, max_tokens=800
    )
    cleaned = re.sub(r'```json|```','', r.choices[0].message.content.strip())
    return json.loads(cleaned)

def explain_keywords(kws, user_question=None):
    kw_list = ", ".join(k["keyword"] for k in kws)
    q = user_question or f"Explain why these keywords are significant and what themes they reveal: {kw_list}"
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":"You are LEXIS, an expert in text analysis and keyword intelligence. Be insightful, concise, and conversational."},
            {"role":"user","content":f"The extracted keywords are: {kw_list}\n\n{q}"}
        ],
        temperature=0.6, max_tokens=600
    )
    return r.choices[0].message.content.strip()


# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "kws"          not in st.session_state: st.session_state.kws = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []


# ══════════════════════════════════════════════════════════
# NAV
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="lx-nav">
  <div class="lx-logo-wrap">
    <div class="lx-logo-icon">⚡</div>
    <div class="lx-logo-text">LEXIS <span>AI</span></div>
  </div>
  <div class="lx-nav-center">Keyword Intelligence Engine</div>
  <div class="lx-status"><div class="lx-status-dot"></div>AI Online</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="lx-hero">
  <div class="lx-hero-tag">Powered by Llama 3.1 · Groq</div>
  <h1 class="lx-h1">Extract what<br><span class="grad">actually matters</span></h1>
  <p class="lx-hero-sub">Paste text or drop a URL — LEXIS surfaces the highest-signal keywords and explains why they matter.</p>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════
left, right = st.columns([2.4, 1.1], gap="large")


# ══════════════════════════════════════════════════════════
# LEFT — INPUT
# ══════════════════════════════════════════════════════════
with left:

    st.markdown("""
<div class="lx-card">
  <div class="lx-card-hdr">
    <span class="lx-card-num">01</span>
    <span class="lx-card-ttl">Input Source</span>
    <span class="lx-card-line"></span>
  </div>
</div>""", unsafe_allow_html=True)

    tab_text, tab_url = st.tabs(["📄  Paste Text", "🌐  From URL"])

    with tab_text:
        text_input = st.text_area(
            "", height=185,
            placeholder="Paste your article, research paper, blog post, or any text content here…",
            label_visibility="collapsed"
        )
        if st.button("⚡  Extract Keywords", key="btn_text"):
            if text_input.strip():
                with st.spinner("Analyzing with AI…"):
                    try:
                        st.session_state.kws = extract_keywords(text_input)
                        st.session_state.chat_history = []
                    except Exception as e:
                        st.error(f"Extraction failed: {e}")
            else:
                st.warning("Please paste some text first.")

    with tab_url:
        url_input = st.text_input(
            "", placeholder="https://example.com/article",
            label_visibility="collapsed"
        )
        if st.button("⚡  Fetch & Extract", key="btn_url"):
            if url_input.startswith("http"):
                blocked_exts = ('.pdf','.jpg','.jpeg','.png','.gif','.webp','.svg','.bmp')
                if url_input.lower().split('?')[0].endswith(blocked_exts):
                    st.session_state.kws = []
                    st.session_state.chat_history = []
                    st.error("🚫 PDF & image-only pages are not supported. Paste the text manually instead.")
                else:
                    try:
                        req = urllib.request.Request(url_input, headers={'User-Agent':'Mozilla/5.0'})
                        with st.spinner("Fetching page…"):
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                ct = resp.headers.get('Content-Type','')
                                if 'text/html' not in ct:
                                    st.session_state.kws = []
                                    st.session_state.chat_history = []
                                    st.error(f"🚫 Unsupported content type ({ct.split(';')[0].strip()}).")
                                    st.stop()
                                html = resp.read().decode('utf-8', errors='ignore')

                        plain = re.sub(r'<style[^>]*>.*?</style>',' ',html,flags=re.DOTALL)
                        plain = re.sub(r'<script[^>]*>.*?</script>',' ',plain,flags=re.DOTALL)
                        plain = re.sub(r'<[^>]+>',' ',plain)
                        plain = re.sub(r'\s+',' ',plain).strip()
                        pl    = plain.lower()

                        if any(s in pl for s in ['sign in to continue','log in to continue',
                            'please sign in','please log in','login required','you must be logged in','members only']):
                            st.session_state.kws=[]; st.session_state.chat_history=[]
                            st.error("🚫 This page requires login.")
                        elif any(s in pl for s in ['subscribe to read','subscription required',
                            'this article is for subscribers','unlock this article','paid subscribers only']):
                            st.session_state.kws=[]; st.session_state.chat_history=[]
                            st.error("🚫 This page is behind a paywall.")
                        elif any(s in pl for s in ['captcha','are you a robot','verify you are human',
                            'ddos protection','access denied','robot check']):
                            st.session_state.kws=[]; st.session_state.chat_history=[]
                            st.error("🚫 This site blocks automated access. Copy the text manually.")
                        elif len(plain) < 200:
                            st.session_state.kws=[]; st.session_state.chat_history=[]
                            st.error("🚫 Not enough readable text found on this page.")
                        else:
                            with st.spinner("Analyzing content…"):
                                st.session_state.kws = extract_keywords(plain)
                                st.session_state.chat_history = []

                    except HTTPError as e:
                        st.session_state.kws=[]; st.session_state.chat_history=[]
                        if e.code in (401,403): st.error(f"🚫 Access Denied (HTTP {e.code}).")
                        elif e.code == 402:     st.error("🚫 Payment Required — page is paywalled.")
                        else:                   st.error(f"🚫 HTTP Error {e.code}.")
                    except URLError:
                        st.session_state.kws=[]; st.session_state.chat_history=[]
                        st.error("🚫 Unable to reach this URL.")
                    except Exception as e:
                        st.session_state.kws=[]; st.session_state.chat_history=[]
                        st.error(f"Unexpected error: {e}")
            else:
                st.warning("Enter a valid URL starting with http(s)://")

    # ── RESULTS ──
    if st.session_state.kws:

        st.markdown("""
<div class="lx-card" style="margin-top:0.3rem;">
  <div class="lx-card-hdr">
    <span class="lx-card-num">02</span>
    <span class="lx-card-ttl">Keyword Results</span>
    <span class="lx-card-line"></span>
  </div>
</div>""", unsafe_allow_html=True)

        col_dl1, col_dl2, col_sp = st.columns([1,1,4])
        with col_dl1:
            st.download_button("⬇ CSV", data=kws_to_csv(st.session_state.kws),
                               file_name="lexis_keywords.csv", mime="text/csv")
        with col_dl2:
            st.download_button("⬇ TXT", data=kws_to_plain(st.session_state.kws).encode(),
                               file_name="lexis_keywords.txt", mime="text/plain")

        st.markdown(render_kw_cards(st.session_state.kws), unsafe_allow_html=True)

        # ── CHAT ──
        st.markdown("""
<div class="lx-card" style="margin-top:0.8rem;">
  <div class="lx-card-hdr">
    <span class="lx-card-num">03</span>
    <span class="lx-card-ttl">Ask LEXIS AI</span>
    <span class="lx-card-line"></span>
  </div>
</div>""", unsafe_allow_html=True)

        if not st.session_state.chat_history:
            with st.spinner("LEXIS is analyzing your keywords…"):
                initial = explain_keywords(st.session_state.kws)
            st.session_state.chat_history.append({"role":"ai","text":initial})

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-from you">You</div><div class="chat-msg you">{msg["text"]}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-from">LEXIS</div><div class="chat-msg ai">{msg["text"]}</div>',
                            unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            cc = st.columns([6,1])
            with cc[0]:
                user_q = st.text_input("", placeholder="Ask anything about these keywords…",
                                       label_visibility="collapsed")
            with cc[1]:
                sent = st.form_submit_button("↑")

        if sent and user_q.strip():
            st.session_state.chat_history.append({"role":"user","text":user_q})
            with st.spinner("Thinking…"):
                reply = explain_keywords(st.session_state.kws, user_question=user_q)
            st.session_state.chat_history.append({"role":"ai","text":reply})
            st.rerun()


# ══════════════════════════════════════════════════════════
# RIGHT COLUMN
# ══════════════════════════════════════════════════════════
with right:

    # ── STATS ──
    if st.session_state.kws:
        scores   = [float(k.get("score",0)) for k in st.session_state.kws]
        avg      = sum(scores)/len(scores)
        top_kw   = st.session_state.kws[0]["keyword"]
        sc_range = max(scores)-min(scores)

        st.markdown(f"""
<div class="sc">
  <div class="sc-ttl">Quick Stats</div>
  <div class="sg">
    <div class="si"><div class="sv" style="color:#a78bfa;">{max(scores):.2f}</div><div class="sl">Top Score</div></div>
    <div class="si"><div class="sv" style="color:#f472b6;">{avg:.2f}</div><div class="sl">Average</div></div>
    <div class="si"><div class="sv" style="color:#34d399;">{len(st.session_state.kws)}</div><div class="sl">Keywords</div></div>
    <div class="si"><div class="sv" style="color:#38bdf8;">{sc_range:.2f}</div><div class="sl">Range</div></div>
  </div>
  <div class="tkb"><div class="tkl">Top Keyword</div><div class="tkv">{top_kw}</div></div>
</div>
""", unsafe_allow_html=True)

        # ── LEGEND ──
        st.markdown("""
<div class="sc">
  <div class="sc-ttl">Score Legend</div>
  <div class="lr"><div class="ld" style="background:#a78bfa;"></div><span>#1 — Top Relevance</span></div>
  <div class="lr"><div class="ld" style="background:#f472b6;"></div><span>#2 — High Impact</span></div>
  <div class="lr"><div class="ld" style="background:#fb923c;"></div><span>#3 — Strong Signal</span></div>
  <div class="lr"><div class="ld" style="background:#34d399;"></div><span>#4 — Notable</span></div>
  <div class="lr"><div class="ld" style="background:#38bdf8;"></div><span>#5 — Notable</span></div>
  <div class="lr" style="margin-bottom:0;"><div class="ld" style="background:rgba(255,255,255,0.22);"></div><span>#6–10 — Supporting</span></div>
</div>
""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # GUIDELINES — 100% inline styles, no class dependencies
    # ══════════════════════════════════════════════════════
    st.markdown("""
<div style="background:#13131a;border:1px solid rgba(255,255,255,0.07);border-radius:15px;padding:1.1rem;margin-bottom:0.9rem;">

  <!-- header -->
  <div style="font-size:0.65rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:rgba(255,255,255,0.26);margin-bottom:0.9rem;display:flex;align-items:center;gap:0.45rem;font-family:Inter,sans-serif;">
    How It Works
    <span style="flex:1;height:1px;background:rgba(255,255,255,0.05);display:inline-block;"></span>
  </div>

  <!-- SUPPORTED -->
  <div style="font-size:0.68rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#4ade80;margin-bottom:0.55rem;font-family:Inter,sans-serif;">✓ &nbsp;Supported Sources</div>

  <div style="display:flex;align-items:center;gap:0.55rem;padding:0.35rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
    <span style="width:17px;height:17px;border-radius:5px;background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.18);display:inline-flex;align-items:center;justify-content:center;font-size:0.65rem;flex-shrink:0;color:#4ade80;line-height:1;">✓</span>
    <span style="font-size:0.81rem;color:rgba(255,255,255,0.45);font-family:Inter,sans-serif;">Public blogs &amp; articles</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.55rem;padding:0.35rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
    <span style="width:17px;height:17px;border-radius:5px;background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.18);display:inline-flex;align-items:center;justify-content:center;font-size:0.65rem;flex-shrink:0;color:#4ade80;line-height:1;">✓</span>
    <span style="font-size:0.81rem;color:rgba(255,255,255,0.45);font-family:Inter,sans-serif;">Wikipedia pages</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.55rem;padding:0.35rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
    <span style="width:17px;height:17px;border-radius:5px;background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.18);display:inline-flex;align-items:center;justify-content:center;font-size:0.65rem;flex-shrink:0;color:#4ade80;line-height:1;">✓</span>
    <span style="font-size:0.81rem;color:rgba(255,255,255,0.45);font-family:Inter,sans-serif;">Company &amp; docs sites</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.55rem;padding:0.35rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
    <span style="width:17px;height:17px;border-radius:5px;background:rgba(74,222,128,0.1);border:1px solid rgba(74,222,128,0.18);display:inline-flex;align-items:center;justify-content:center;font-size:0.65rem;flex-shrink:0;color:#4ade80;line-height:1;">✓</span>
    <span style="font-size:0.81rem;color:rgba(255,255,255,0.45);font-family:Inter,sans-serif;">Pasted raw text</span>
  </div>

  <!-- NOT SUPPORTED -->
  <div style="font-size:0.68rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#f87171;margin-top:0.85rem;margin-bottom:0.55rem;font-family:Inter,sans-serif;">✕ &nbsp;Not Supported</div>

  <div style="display:flex;align-items:center;gap:0.55rem;padding:0.35rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
    <span style="width:17px;height:17px;border-radius:5px;background:rgba(248,113,113,0.09);border:1px solid rgba(248,113,113,0.18);display:inline-flex;align-items:center;justify-content:center;font-size:0.65rem;flex-shrink:0;color:#f87171;line-height:1;">✕</span>
    <span style="font-size:0.81rem;color:rgba(255,255,255,0.45);font-family:Inter,sans-serif;">Login-gated pages</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.55rem;padding:0.35rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
    <span style="width:17px;height:17px;border-radius:5px;background:rgba(248,113,113,0.09);border:1px solid rgba(248,113,113,0.18);display:inline-flex;align-items:center;justify-content:center;font-size:0.65rem;flex-shrink:0;color:#f87171;line-height:1;">✕</span>
    <span style="font-size:0.81rem;color:rgba(255,255,255,0.45);font-family:Inter,sans-serif;">Paywalled content</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.55rem;padding:0.35rem 0;border-bottom:1px solid rgba(255,255,255,0.04);">
    <span style="width:17px;height:17px;border-radius:5px;background:rgba(248,113,113,0.09);border:1px solid rgba(248,113,113,0.18);display:inline-flex;align-items:center;justify-content:center;font-size:0.65rem;flex-shrink:0;color:#f87171;line-height:1;">✕</span>
    <span style="font-size:0.81rem;color:rgba(255,255,255,0.45);font-family:Inter,sans-serif;">Bot-blocking / CAPTCHA</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.55rem;padding:0.35rem 0;">
    <span style="width:17px;height:17px;border-radius:5px;background:rgba(248,113,113,0.09);border:1px solid rgba(248,113,113,0.18);display:inline-flex;align-items:center;justify-content:center;font-size:0.65rem;flex-shrink:0;color:#f87171;line-height:1;">✕</span>
    <span style="font-size:0.81rem;color:rgba(255,255,255,0.45);font-family:Inter,sans-serif;">PDF / image-only pages</span>
  </div>

</div>
""", unsafe_allow_html=True)
