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

# ── FULL INTERFACE STYLING ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Clash+Display:wght@400;500;600;700&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

/* ── ROOT / APP ── */
.stApp {
    background: #080612 !important;
    color: #f1f0ff !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* ── Animated blob background ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 700px 600px at -10% -10%, rgba(168,85,247,0.45) 0%, transparent 60%),
        radial-gradient(ellipse 600px 500px at 110% 60%, rgba(255,60,172,0.4) 0%, transparent 60%),
        radial-gradient(ellipse 500px 400px at 40% 110%, rgba(6,182,212,0.3) 0%, transparent 60%),
        radial-gradient(ellipse 350px 350px at 55% 25%, rgba(255,107,53,0.2) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
    animation: blobDrift 20s ease-in-out infinite alternate;
}
@keyframes blobDrift {
    0%   { filter: blur(60px) brightness(1);   transform: scale(1); }
    50%  { filter: blur(70px) brightness(1.05); transform: scale(1.02) translate(10px, -8px); }
    100% { filter: blur(65px) brightness(1);   transform: scale(0.98) translate(-8px, 12px); }
}

/* Grid overlay */
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
}

.block-container {
    padding-top: 0 !important;
    padding-bottom: 4rem !important;
    max-width: 1280px !important;
    position: relative;
    z-index: 2;
}

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── NAV BAR ── */
.lx-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.4rem 0 1.4rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 3rem;
    position: relative;
}
.lx-logo {
    font-family: 'Clash Display', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    background: linear-gradient(90deg, #ff3cac, #ffb347, #06b6d4, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    background-size: 300% auto;
    animation: shimmer 4s linear infinite;
    letter-spacing: -0.5px;
}
@keyframes shimmer {
    0%   { background-position: 0% center; }
    100% { background-position: 300% center; }
}
.lx-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.35);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 0.3rem 1rem;
    border-radius: 100px;
}
.lx-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: linear-gradient(135deg, rgba(168,85,247,0.18), rgba(255,60,172,0.18));
    border: 1px solid rgba(168,85,247,0.28);
    border-radius: 100px;
    padding: 0.38rem 1.1rem;
    font-size: 0.82rem;
    font-weight: 500;
    color: #d8b4fe;
}
.lx-dot {
    width: 7px; height: 7px;
    background: #a855f7;
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
    display: inline-block;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:0.45;transform:scale(0.75);} }

/* ── HERO ── */
.lx-hero {
    text-align: center;
    padding: 1rem 0 3.5rem;
}
.lx-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 5px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.3);
    margin-bottom: 1.3rem;
}
.lx-title {
    font-family: 'Clash Display', sans-serif;
    font-size: clamp(4.5rem, 11vw, 8.5rem);
    font-weight: 700;
    line-height: 0.92;
    letter-spacing: -4px;
    margin-bottom: 1.3rem;
}
.lx-title .t1 {
    display: block;
    background: linear-gradient(135deg, #ffffff 20%, rgba(255,255,255,0.55));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.lx-title .t2 {
    display: block;
    background: linear-gradient(90deg, #ff3cac, #ff6b35, #ffb347, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    background-size: 300% auto;
    animation: shimmer 5s linear infinite;
}
.lx-sub {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.38);
    max-width: 460px;
    margin: 0 auto;
    line-height: 1.75;
    font-weight: 300;
}

/* ── GLASS CARDS ── */
.lx-card {
    background: rgba(255,255,255,0.028);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 24px;
    padding: 1.8rem;
    margin-bottom: 1.4rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}
.lx-card::before {
    content: '';
    position: absolute;
    top: 0; left: 20%; right: 20%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,60,172,0.7), rgba(168,85,247,0.7), transparent);
    pointer-events: none;
}
.lx-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(168,85,247,0.04) 0%, transparent 50%, rgba(255,60,172,0.02) 100%);
    pointer-events: none;
}

/* ── SECTION LABELS ── */
.lx-sec {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #ff3cac;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.7rem;
}
.lx-sec::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(255,60,172,0.25), transparent);
}

/* ── STREAMLIT TABS ── */
div[data-baseweb="tab-list"] {
    background: rgba(0,0,0,0.45) !important;
    border-radius: 14px !important;
    padding: 5px !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    gap: 3px !important;
    margin-bottom: 1.3rem !important;
}
div[data-baseweb="tab"] {
    border-radius: 10px !important;
    color: rgba(255,255,255,0.38) !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.55rem 1.3rem !important;
    transition: all 0.2s !important;
}
div[aria-selected="true"] {
    background: linear-gradient(135deg, #a855f7, #ff3cac) !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(168,85,247,0.35) !important;
}
div[data-baseweb="tab-panel"] {
    background: transparent !important;
    padding: 0 !important;
}

/* ── INPUTS ── */
textarea, .stTextInput input {
    background: rgba(0,0,0,0.38) !important;
    border: 1.5px solid rgba(255,255,255,0.08) !important;
    border-radius: 16px !important;
    color: #f1f0ff !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.98rem !important;
    padding: 1rem 1.2rem !important;
    transition: border-color 0.25s, box-shadow 0.25s !important;
    line-height: 1.65 !important;
}
textarea:focus, .stTextInput input:focus {
    border-color: rgba(168,85,247,0.6) !important;
    box-shadow: 0 0 0 4px rgba(168,85,247,0.1), 0 0 30px rgba(168,85,247,0.12) !important;
    outline: none !important;
}
textarea::placeholder, .stTextInput input::placeholder {
    color: rgba(255,255,255,0.18) !important;
}

/* ── BUTTONS ── */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #a855f7, #ff3cac, #ff6b35) !important;
    background-size: 200% auto !important;
    border: none !important;
    border-radius: 14px !important;
    color: #fff !important;
    font-family: 'Clash Display', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.9rem 2rem !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    cursor: pointer !important;
    transition: all 0.3s !important;
    margin-top: 0.8rem !important;
}
.stButton > button:hover {
    background-position: right center !important;
    box-shadow: 0 10px 40px rgba(168,85,247,0.45) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── DOWNLOAD BUTTONS ── */
.stDownloadButton > button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: rgba(255,255,255,0.55) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.2rem !important;
    font-size: 0.85rem !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    border-color: #ff3cac !important;
    color: #ff3cac !important;
    background: rgba(255,60,172,0.07) !important;
}

/* ── KEYWORD CARDS ── */
.kw-card {
    background: rgba(0,0,0,0.28);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.55rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.25s;
    position: relative;
    overflow: hidden;
}
.kw-card:hover {
    border-color: rgba(255,255,255,0.14);
    transform: translateX(5px);
    background: rgba(255,255,255,0.035);
}
.kw-rank {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: rgba(255,255,255,0.2);
    min-width: 30px;
    font-weight: 300;
}
.kw-name {
    flex: 1;
    font-weight: 600;
    font-size: 1rem;
    color: #f1f0ff;
}
.kw-score-wrap {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    min-width: 150px;
}
.kw-bar-bg {
    flex: 1;
    height: 5px;
    background: rgba(255,255,255,0.07);
    border-radius: 100px;
    overflow: hidden;
}
.kw-bar-fill {
    height: 100%;
    border-radius: 100px;
}
.kw-score-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    min-width: 36px;
    text-align: right;
    font-weight: 500;
}

/* ── RANK COLORS ── */
.rank-1 .kw-bar-fill { background: linear-gradient(90deg,#ff3cac,#ff6b35); box-shadow: 0 0 8px rgba(255,60,172,0.5); }
.rank-2 .kw-bar-fill { background: linear-gradient(90deg,#ff6b35,#ffb347); box-shadow: 0 0 8px rgba(255,107,53,0.5); }
.rank-3 .kw-bar-fill { background: linear-gradient(90deg,#ffb347,#ffe600); box-shadow: 0 0 8px rgba(255,179,71,0.5); }
.rank-4 .kw-bar-fill,
.rank-5 .kw-bar-fill { background: linear-gradient(90deg,#06b6d4,#0ea5e9); box-shadow: 0 0 8px rgba(6,182,212,0.5); }
.rank-other .kw-bar-fill { background: linear-gradient(90deg,#a855f7,#7c3aed); box-shadow: 0 0 8px rgba(168,85,247,0.5); }

.rank-1 .kw-score-val   { color: #ff3cac; }
.rank-2 .kw-score-val   { color: #ff6b35; }
.rank-3 .kw-score-val   { color: #ffb347; }
.rank-4 .kw-score-val,
.rank-5 .kw-score-val   { color: #06b6d4; }
.rank-other .kw-score-val { color: #a855f7; }

/* ── CHAT BUBBLES ── */
.chat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    color: rgba(255,255,255,0.2);
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 0.28rem;
}
.chat-label.user-label { text-align: right; color: rgba(168,85,247,0.55); }

.chat-bubble {
    padding: 0.85rem 1.1rem;
    border-radius: 16px;
    margin-bottom: 0.75rem;
    font-size: 0.92rem;
    line-height: 1.65;
    max-width: 88%;
}
.chat-bubble.user {
    background: linear-gradient(135deg, #a855f7, #ff3cac);
    color: white;
    font-weight: 500;
    margin-left: auto;
    border-bottom-right-radius: 4px;
    box-shadow: 0 4px 20px rgba(168,85,247,0.28);
}
.chat-bubble.ai {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.82);
    border-bottom-left-radius: 4px;
}

/* ── CHAT FORM ── */
.stForm {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
.stForm > div {
    background: transparent !important;
}
div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* Form submit button (Send) */
div[data-testid="stForm"] .stButton > button {
    background: linear-gradient(135deg, #a855f7, #ff3cac) !important;
    padding: 0.75rem 1.2rem !important;
    font-size: 1.1rem !important;
    margin-top: 0 !important;
    border-radius: 12px !important;
}

/* ── SIDEBAR / RIGHT PANEL CARDS ── */
.lx-side-card {
    background: rgba(255,255,255,0.028);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 1.4rem;
    margin-bottom: 1.2rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}
.lx-side-card::before {
    content: '';
    position: absolute;
    top: 0; left: 15%; right: 15%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,60,172,0.6), rgba(168,85,247,0.6), transparent);
}

/* ── LEGEND ── */
.legend-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    font-size: 0.88rem;
    color: rgba(255,255,255,0.5);
    margin-bottom: 0.65rem;
}
.legend-dot {
    width: 32px;
    height: 6px;
    border-radius: 100px;
    flex-shrink: 0;
}

/* ── GUIDE ITEMS ── */
.guide-section-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 0.65rem;
    margin-top: 0.5rem;
}
.guide-yes-title { color: #34d399; }
.guide-no-title  { color: #ff3cac; }

.guide-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.42rem 0;
    font-size: 0.88rem;
    color: rgba(255,255,255,0.52);
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.guide-yes { color: #34d399; }
.guide-no  { color: #ff3cac; }

/* ── STATS ── */
.stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.7rem;
    margin-bottom: 0.9rem;
}
.stat-item {
    background: rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 0.9rem;
    text-align: center;
}
.stat-val {
    font-family: 'Clash Display', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.25rem;
}
.stat-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.28);
}
.stat-top-kw {
    background: rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 0.9rem 1rem;
}
.stat-top-kw .s-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.28);
    margin-bottom: 0.3rem;
}
.stat-top-kw .s-val {
    font-size: 1.05rem;
    font-weight: 700;
    background: linear-gradient(90deg, #ff3cac, #ffb347);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ── SPINNER ── */
.stSpinner > div {
    border-top-color: #ff3cac !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 10px; }

/* ── ALERTS ── */
.stAlert {
    background: rgba(255,60,172,0.08) !important;
    border: 1px solid rgba(255,60,172,0.25) !important;
    border-radius: 12px !important;
    color: rgba(255,200,220,0.9) !important;
}

/* ── COLUMNS GAP FIX ── */
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)


# ── HELPERS ──────────────────────────────────────────────────────────────────

def score_to_color_class(idx):
    if idx == 0:       return "rank-1"
    if idx == 1:       return "rank-2"
    if idx == 2:       return "rank-3"
    if idx in (3, 4):  return "rank-4"
    return "rank-other"

def render_kw_cards(kws):
    html = ""
    for i, k in enumerate(kws):
        rank_cls = score_to_color_class(i)
        pct = int(float(k.get("score", 0)) * 100)
        html += f"""
        <div class="kw-card {rank_cls}">
            <span class="kw-rank">#{i+1:02d}</span>
            <span class="kw-name">{k['keyword']}</span>
            <div class="kw-score-wrap">
                <div class="kw-bar-bg">
                    <div class="kw-bar-fill" style="width:{pct}%"></div>
                </div>
                <span class="kw-score-val">{float(k.get('score', 0)):.2f}</span>
            </div>
        </div>"""
    return html

def kws_to_csv(kws):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["rank", "keyword", "score"])
    writer.writeheader()
    for i, k in enumerate(kws, 1):
        writer.writerow({"rank": i, "keyword": k["keyword"], "score": k.get("score", "")})
    return buf.getvalue().encode()

def kws_to_plain(kws):
    return "\n".join([
        f"{i+1}. {k['keyword']} ({float(k.get('score', 0)):.2f})"
        for i, k in enumerate(kws)
    ])

def extract_keywords(text):
    prompt = f"""Extract top 10 important keywords from the following text.
Return ONLY a JSON array. No explanation. No markdown. Example format:
[{{"keyword":"example","score":0.95}}]

TEXT:
{text[:6000]}"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=800
    )
    cleaned = re.sub(r'```json|```', '', response.choices[0].message.content.strip())
    return json.loads(cleaned)

def explain_keywords(kws, user_question=None):
    kw_list = ", ".join([k["keyword"] for k in kws])
    if user_question:
        q = user_question
    else:
        q = f"Explain why these keywords are significant and what themes they reveal: {kw_list}"
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are LEXIS, an expert in text analysis and keyword intelligence. Be insightful, concise, and conversational."
            },
            {
                "role": "user",
                "content": f"The extracted keywords are: {kw_list}\n\n{q}"
            }
        ],
        temperature=0.6,
        max_tokens=600
    )
    return response.choices[0].message.content.strip()


# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "kws" not in st.session_state:
    st.session_state.kws = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ── NAV ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lx-nav">
    <div class="lx-logo">LEXIS AI</div>
    <div class="lx-badge">⚡ Keyword Intelligence Engine</div>
    <div class="lx-pill"><span class="lx-dot"></span> AI Online</div>
</div>
""", unsafe_allow_html=True)


# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lx-hero">
    <div class="lx-eyebrow">— Next-Gen Text Analysis —</div>
    <h1 class="lx-title">
        <span class="t1">KEYWORD</span>
        <span class="t2">INTELLIGENCE</span>
    </h1>
    <p class="lx-sub">Extract, rank, and understand the most powerful keywords from any text or URL — powered by AI.</p>
</div>
""", unsafe_allow_html=True)


# ── MAIN LAYOUT ───────────────────────────────────────────────────────────────
left, right = st.columns([2.5, 1.1], gap="large")


# ════════════════════════════════════════════════════════
# LEFT COLUMN
# ════════════════════════════════════════════════════════
with left:

    # ── INPUT CARD ──
    st.markdown('<div class="lx-card">', unsafe_allow_html=True)
    st.markdown('<div class="lx-sec">01 — Input Source</div>', unsafe_allow_html=True)

    tab_text, tab_url = st.tabs(["📄  Text Input", "🌐  URL Input"])

    with tab_text:
        text_input = st.text_area(
            "",
            height=200,
            placeholder="Paste your article, blog post, or any content here…",
            label_visibility="collapsed"
        )
        if st.button("⚡ Extract Keywords", key="btn_text"):
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
            "",
            placeholder="https://example.com/article",
            label_visibility="collapsed"
        )
        if st.button("⚡ Extract from URL", key="btn_url"):
            if url_input.startswith("http"):
                blocked_exts = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp')
                if url_input.lower().split('?')[0].endswith(blocked_exts):
                    st.session_state.kws = []
                    st.session_state.chat_history = []
                    st.error("🚫 PDF & image-only pages are not supported. Please paste the text content manually instead.")
                else:
                    try:
                        req = urllib.request.Request(url_input, headers={'User-Agent': 'Mozilla/5.0'})
                        with st.spinner("Fetching & analyzing…"):
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                content_type = resp.headers.get('Content-Type', '')
                                if 'text/html' not in content_type:
                                    st.session_state.kws = []
                                    st.session_state.chat_history = []
                                    st.error(f"🚫 Unsupported content type ({content_type.split(';')[0].strip()}). Only HTML pages are supported.")
                                    st.stop()
                                html = resp.read().decode('utf-8', errors='ignore')

                        plain = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL)
                        plain = re.sub(r'<script[^>]*>.*?</script>', ' ', plain, flags=re.DOTALL)
                        plain = re.sub(r'<[^>]+>', ' ', plain)
                        plain = re.sub(r'\s+', ' ', plain).strip()
                        plain_lower = plain.lower()

                        login_signals = [
                            'sign in to continue', 'log in to continue', 'please sign in',
                            'please log in', 'login required', 'signin required',
                            'create an account', 'forgot your password', 'enter your password',
                            'enter your email', 'username and password', 'sign in with google',
                            'continue with google', 'continue with facebook',
                            'you must be logged in', 'members only', 'register to access'
                        ]
                        if any(sig in plain_lower for sig in login_signals):
                            st.session_state.kws = []
                            st.session_state.chat_history = []
                            st.error("🚫 This page requires login. Only publicly accessible pages are supported.")

                        elif any(sig in plain_lower for sig in [
                            'subscribe to read', 'subscribe to continue', 'subscription required',
                            'this article is for subscribers', 'unlock this article',
                            'get full access', 'premium content', 'paid subscribers only',
                            'buy a subscription', 'already a subscriber'
                        ]):
                            st.session_state.kws = []
                            st.session_state.chat_history = []
                            st.error("🚫 This page is behind a paywall. Only free, publicly accessible articles are supported.")

                        elif any(sig in plain_lower for sig in [
                            'captcha', 'are you a robot', 'verify you are human',
                            'ddos protection', 'checking your browser', 'enable javascript',
                            'access denied', 'robot check', 'automated access'
                        ]):
                            st.session_state.kws = []
                            st.session_state.chat_history = []
                            st.error("🚫 This site is blocking automated access. Try copying the text manually instead.")

                        elif len(plain) < 200:
                            st.session_state.kws = []
                            st.session_state.chat_history = []
                            st.error("🚫 Not enough readable text found on this page.")

                        else:
                            st.session_state.kws = extract_keywords(plain)
                            st.session_state.chat_history = []

                    except HTTPError as e:
                        st.session_state.kws = []
                        st.session_state.chat_history = []
                        if e.code in (401, 403):
                            st.error(f"🚫 Access Denied (HTTP {e.code}) — This page requires login or blocks bots.")
                        elif e.code == 402:
                            st.error("🚫 Payment Required (HTTP 402) — This page is behind a paywall.")
                        else:
                            st.error(f"🚫 HTTP Error {e.code} — Unable to access this page.")
                    except URLError:
                        st.session_state.kws = []
                        st.session_state.chat_history = []
                        st.error("🚫 Unable to reach the website. Check the URL and try again.")
                    except Exception as e:
                        st.session_state.kws = []
                        st.session_state.chat_history = []
                        st.error(f"Unexpected error: {e}")
            else:
                st.warning("Please enter a valid URL starting with http(s)://")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── RESULTS ──
    if st.session_state.kws:

        st.markdown('<div class="lx-card">', unsafe_allow_html=True)
        st.markdown('<div class="lx-sec">02 — Keyword Results</div>', unsafe_allow_html=True)

        # Export buttons
        col_dl1, col_dl2, col_spacer = st.columns([1, 1, 3])
        with col_dl1:
            st.download_button(
                "⬇ CSV",
                data=kws_to_csv(st.session_state.kws),
                file_name="lexis_keywords.csv",
                mime="text/csv"
            )
        with col_dl2:
            st.download_button(
                "⬇ TXT",
                data=kws_to_plain(st.session_state.kws).encode(),
                file_name="lexis_keywords.txt",
                mime="text/plain"
            )

        st.markdown(render_kw_cards(st.session_state.kws), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── CHAT ──
        st.markdown('<div class="lx-card">', unsafe_allow_html=True)
        st.markdown('<div class="lx-sec">03 — Ask LEXIS AI</div>', unsafe_allow_html=True)

        # Initial auto-explanation
        if not st.session_state.chat_history:
            with st.spinner("LEXIS is analyzing your keywords…"):
                initial = explain_keywords(st.session_state.kws)
            st.session_state.chat_history.append({"role": "ai", "text": initial})

        # Render chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'''
<div class="chat-label user-label">You</div>
<div class="chat-bubble user">{msg["text"]}</div>
''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
<div class="chat-label">LEXIS</div>
<div class="chat-bubble ai">{msg["text"]}</div>
''', unsafe_allow_html=True)

        # Chat input form
        with st.form("chat_form", clear_on_submit=True):
            chat_cols = st.columns([5, 1])
            with chat_cols[0]:
                user_q = st.text_input(
                    "",
                    placeholder="Ask anything about these keywords…",
                    label_visibility="collapsed"
                )
            with chat_cols[1]:
                sent = st.form_submit_button("↑")

        if sent and user_q.strip():
            st.session_state.chat_history.append({"role": "user", "text": user_q})
            with st.spinner("Thinking…"):
                reply = explain_keywords(st.session_state.kws, user_question=user_q)
            st.session_state.chat_history.append({"role": "ai", "text": reply})
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# RIGHT COLUMN
# ════════════════════════════════════════════════════════
with right:

    # ── STATS ──
    if st.session_state.kws:
        scores   = [float(k.get("score", 0)) for k in st.session_state.kws]
        avg      = sum(scores) / len(scores) if scores else 0
        top_kw   = st.session_state.kws[0]["keyword"] if st.session_state.kws else "—"
        sc_range = max(scores) - min(scores) if scores else 0

        st.markdown(f"""
<div class="lx-side-card">
    <div class="lx-sec">Quick Stats</div>
    <div class="stat-grid">
        <div class="stat-item">
            <div class="stat-val" style="color:#ff3cac;">{max(scores):.2f}</div>
            <div class="stat-label">Top Score</div>
        </div>
        <div class="stat-item">
            <div class="stat-val" style="color:#ffb347;">{avg:.2f}</div>
            <div class="stat-label">Avg Score</div>
        </div>
        <div class="stat-item">
            <div class="stat-val" style="color:#06b6d4;">{len(st.session_state.kws)}</div>
            <div class="stat-label">Keywords</div>
        </div>
        <div class="stat-item">
            <div class="stat-val" style="background:linear-gradient(135deg,#a855f7,#ff3cac);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{sc_range:.2f}</div>
            <div class="stat-label">Range</div>
        </div>
    </div>
    <div class="stat-top-kw">
        <div class="s-label">Top Keyword</div>
        <div class="s-val">{top_kw}</div>
    </div>
</div>
""", unsafe_allow_html=True)

        # ── LEGEND ──
        st.markdown("""
<div class="lx-side-card">
    <div class="lx-sec">Score Legend</div>
    <div class="legend-row">
        <div class="legend-dot" style="background:linear-gradient(90deg,#ff3cac,#ff6b35);box-shadow:0 0 8px rgba(255,60,172,0.4);"></div>
        <span>#1 — Top Relevance</span>
    </div>
    <div class="legend-row">
        <div class="legend-dot" style="background:linear-gradient(90deg,#ff6b35,#ffb347);box-shadow:0 0 8px rgba(255,107,53,0.4);"></div>
        <span>#2 — High Impact</span>
    </div>
    <div class="legend-row">
        <div class="legend-dot" style="background:linear-gradient(90deg,#ffb347,#ffe600);box-shadow:0 0 8px rgba(255,179,71,0.4);"></div>
        <span>#3 — Strong</span>
    </div>
    <div class="legend-row">
        <div class="legend-dot" style="background:linear-gradient(90deg,#06b6d4,#0ea5e9);box-shadow:0 0 8px rgba(6,182,212,0.4);"></div>
        <span>#4–5 — Notable</span>
    </div>
    <div class="legend-row">
        <div class="legend-dot" style="background:linear-gradient(90deg,#a855f7,#7c3aed);box-shadow:0 0 8px rgba(168,85,247,0.4);"></div>
        <span>#6–10 — Supporting</span>
    </div>
</div>
""", unsafe_allow_html=True)

    # ── GUIDELINES ──
    st.markdown("""
<div class="lx-side-card">
    <div class="lx-sec">Usage Guidelines</div>

    <div class="guide-section-title guide-yes-title">✦ Works great with</div>
    <div class="guide-item"><span class="guide-yes">✓</span> Public blogs &amp; articles</div>
    <div class="guide-item"><span class="guide-yes">✓</span> Wikipedia pages</div>
    <div class="guide-item"><span class="guide-yes">✓</span> Company websites</div>
    <div class="guide-item"><span class="guide-yes">✓</span> Documentation portals</div>
    <div class="guide-item"><span class="guide-yes">✓</span> Pasted raw text</div>

    <div class="guide-section-title guide-no-title" style="margin-top:1rem;">✦ Doesn't support</div>
    <div class="guide-item"><span class="guide-no">✗</span> Login-required portals</div>
    <div class="guide-item"><span class="guide-no">✗</span> Paywalled content</div>
    <div class="guide-item"><span class="guide-no">✗</span> Bot-blocking sites</div>
    <div class="guide-item" style="border-bottom:none;"><span class="guide-no">✗</span> PDF / image-only pages</div>
</div>
""", unsafe_allow_html=True)
