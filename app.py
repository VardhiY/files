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
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

/* ══════════════════════════════
   BASE
══════════════════════════════ */
.stApp {
    background: #f0f4f8 !important;
    color: #1a2332 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 15px !important;
}

.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 1000px 700px at 20% 0%,   rgba(186,230,255,0.55) 0%, transparent 60%),
        radial-gradient(ellipse  800px 600px at 85% 10%,  rgba(199,210,254,0.45) 0%, transparent 60%),
        radial-gradient(ellipse  700px 600px at 10% 90%,  rgba(167,243,208,0.30) 0%, transparent 60%),
        radial-gradient(ellipse  900px 500px at 90% 95%,  rgba(196,181,253,0.25) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
}

.block-container {
    padding-top: 0 !important;
    padding-bottom: 3rem !important;
    max-width: 1260px !important;
    position: relative;
    z-index: 1;
}

#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }

/* ══════════════════════════════
   NAV
══════════════════════════════ */
.lx-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.1rem 0;
    border-bottom: 1px solid rgba(0,0,0,0.06);
    margin-bottom: 0;
    background: rgba(255,255,255,0.7);
    backdrop-filter: blur(12px);
}
.lx-logo-wrap { display: flex; align-items: center; gap: 0.5rem; }
.lx-logo-icon {
    width: 30px; height: 30px;
    background: linear-gradient(135deg, #3b82f6, #06b6d4);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    box-shadow: 0 3px 10px rgba(59,130,246,0.3);
}
.lx-logo-text {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #1a2332;
}
.lx-nav-badge {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #64748b;
    border: 1px solid #e2e8f0;
    background: rgba(255,255,255,0.8);
    padding: 0.28rem 0.9rem;
    border-radius: 100px;
}
.lx-status {
    display: flex; align-items: center; gap: 0.4rem;
    font-size: 0.78rem; font-weight: 500; color: #64748b;
}
.lx-status-dot {
    width: 7px; height: 7px; background: #22c55e;
    border-radius: 50%; box-shadow: 0 0 6px rgba(34,197,94,0.6);
    animation: sDot 2.5s ease-in-out infinite;
}
@keyframes sDot { 0%,100%{opacity:1;} 50%{opacity:0.4;} }

/* ══════════════════════════════
   HERO
══════════════════════════════ */
.lx-hero { text-align: center; padding: 3rem 0 2.5rem; }
.lx-hero-tag {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: rgba(255,255,255,0.85); border: 1px solid #e2e8f0;
    border-radius: 100px; padding: 0.3rem 0.9rem;
    font-size: 0.78rem; font-weight: 600; color: #475569;
    margin-bottom: 1.3rem; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.lx-hero-tag::before {
    content: ''; width: 6px; height: 6px;
    background: linear-gradient(135deg, #3b82f6, #06b6d4);
    border-radius: 50%; flex-shrink: 0;
}
.lx-h1 {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    font-weight: 800; line-height: 1.12; letter-spacing: -1px;
    color: #0f172a; margin-bottom: 0;
}
.lx-h1-accent {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    font-weight: 800; line-height: 1.12; letter-spacing: -1px;
    background: linear-gradient(90deg, #3b82f6, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; display: block; margin-bottom: 1rem;
}
.lx-hero-sub {
    font-size: 1rem; color: #64748b;
    max-width: 420px; margin: 0 auto; line-height: 1.7;
}

/* ══════════════════════════════
   MAIN CARD
══════════════════════════════ */
.lx-card {
    background: rgba(255,255,255,0.82);
    border: 1px solid rgba(255,255,255,0.9);
    border-radius: 16px; padding: 1.5rem 1.5rem 1rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06), 0 1px 4px rgba(0,0,0,0.04);
    backdrop-filter: blur(12px);
}

/* ══════════════════════════════
   TABS
══════════════════════════════ */
div[data-baseweb="tab-list"] {
    background: #f1f5f9 !important; border-radius: 10px !important;
    padding: 4px !important; border: 1px solid #e2e8f0 !important;
    gap: 2px !important; margin-bottom: 1rem !important; width: fit-content !important;
}
div[data-baseweb="tab"] {
    border-radius: 7px !important; color: #94a3b8 !important;
    font-weight: 600 !important; font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important; padding: 0.42rem 1.1rem !important; transition: all 0.18s !important;
}
div[aria-selected="true"] {
    background: linear-gradient(135deg, #3b82f6, #06b6d4) !important;
    color: white !important; box-shadow: 0 2px 8px rgba(59,130,246,0.3) !important;
}
div[data-baseweb="tab-panel"] { background: transparent !important; padding: 0 !important; }

/* ══════════════════════════════
   INPUTS
══════════════════════════════ */
textarea, .stTextInput input {
    background: #ffffff !important; border: 1.5px solid #e2e8f0 !important;
    border-radius: 10px !important; color: #1a2332 !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 0.97rem !important;
    padding: 0.85rem 1rem !important; line-height: 1.6 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) inset !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
textarea:focus, .stTextInput input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important; outline: none !important;
}
textarea::placeholder, .stTextInput input::placeholder { color: #94a3b8 !important; }

/* ══════════════════════════════
   PRIMARY BUTTON
══════════════════════════════ */
.stButton > button {
    width: 100% !important;
    background: linear-gradient(90deg, #3b82f6, #06b6d4) !important;
    border: none !important; border-radius: 10px !important; color: #fff !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 700 !important;
    font-size: 1rem !important; padding: 0.8rem 1.5rem !important;
    margin-top: 0.65rem !important; cursor: pointer !important; transition: all 0.2s !important;
    box-shadow: 0 3px 12px rgba(59,130,246,0.28) !important;
}
.stButton > button:hover {
    opacity: 0.92 !important; transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(59,130,246,0.38) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ══════════════════════════════
   DOWNLOAD BUTTONS
══════════════════════════════ */
.stDownloadButton > button {
    background: #ffffff !important; border: 1.5px solid #e2e8f0 !important;
    color: #475569 !important; font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; border-radius: 8px !important;
    padding: 0.45rem 0.9rem !important; font-size: 0.82rem !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important; transition: all 0.18s !important;
}
.stDownloadButton > button:hover {
    border-color: #3b82f6 !important; color: #3b82f6 !important; background: #eff6ff !important;
}

/* ══════════════════════════════
   KEYWORD ROWS — with accuracy
══════════════════════════════ */
.kw-row {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.62rem 0.9rem; border-radius: 9px; margin-bottom: 0.32rem;
    background: #ffffff; border: 1px solid #f1f5f9;
    transition: all 0.18s; cursor: default;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.kw-row:hover {
    border-color: #bfdbfe; background: #eff6ff;
    transform: translateX(3px); box-shadow: 0 2px 8px rgba(59,130,246,0.1);
}
.kw-num { font-family:'DM Mono',monospace; font-size:0.68rem; color:#94a3b8; min-width:24px; }
.kw-word { flex:1; font-size:0.95rem; font-weight:600; color:#1e293b; }
.kw-bar-wrap { display:flex; align-items:center; gap:0.5rem; min-width:110px; }
.kw-bar-bg { flex:1; height:4px; background:#e2e8f0; border-radius:100px; overflow:hidden; }
.kw-bar-fill { height:100%; border-radius:100px; }
.kw-sc { font-family:'DM Mono',monospace; font-size:0.72rem; min-width:28px; text-align:right; font-weight:500; }

/* accuracy pill */
.kw-acc {
    font-family: 'DM Mono', monospace;
    font-size: 0.66rem;
    font-weight: 600;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    min-width: 48px;
    text-align: center;
    white-space: nowrap;
}
.kw-acc.high  { background:#dcfce7; color:#15803d; border:1px solid #bbf7d0; }
.kw-acc.mid   { background:#dbeafe; color:#1d4ed8; border:1px solid #bfdbfe; }
.kw-acc.low   { background:#f1f5f9; color:#64748b; border:1px solid #e2e8f0; }

/* rank bar colours */
.r0 .kw-bar-fill{background:linear-gradient(90deg,#2563eb,#06b6d4);} .r0 .kw-sc{color:#2563eb;}
.r1 .kw-bar-fill{background:linear-gradient(90deg,#3b82f6,#0ea5e9);} .r1 .kw-sc{color:#3b82f6;}
.r2 .kw-bar-fill{background:linear-gradient(90deg,#0ea5e9,#06b6d4);} .r2 .kw-sc{color:#0ea5e9;}
.r3 .kw-bar-fill{background:linear-gradient(90deg,#06b6d4,#22d3ee);} .r3 .kw-sc{color:#06b6d4;}
.r4 .kw-bar-fill{background:linear-gradient(90deg,#22d3ee,#67e8f9);} .r4 .kw-sc{color:#0891b2;}
.r5 .kw-bar-fill,.r6 .kw-bar-fill,.r7 .kw-bar-fill,
.r8 .kw-bar-fill,.r9 .kw-bar-fill{background:#cbd5e1;}
.r5 .kw-sc,.r6 .kw-sc,.r7 .kw-sc,.r8 .kw-sc,.r9 .kw-sc{color:#94a3b8;}

/* ── accuracy summary bar ── */
.acc-summary {
    display: flex; align-items: center; gap: 1.2rem;
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 0.65rem 1rem;
    margin-bottom: 0.85rem;
}
.acc-stat { text-align: center; }
.acc-stat-val {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.15rem; font-weight: 800; line-height: 1;
    margin-bottom: 0.1rem;
}
.acc-stat-lbl {
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem; letter-spacing: 0.1em;
    text-transform: uppercase; color: #94a3b8;
}
.acc-divider { width: 1px; height: 30px; background: #e2e8f0; flex-shrink: 0; }

/* ══════════════════════════════
   CHAT
══════════════════════════════ */
.chat-from {
    font-family: 'DM Mono', monospace; font-size: 0.62rem;
    letter-spacing: 0.15em; text-transform: uppercase; color: #94a3b8; margin-bottom: 0.2rem;
}
.chat-from.you { text-align:right; color:#3b82f6; }
.chat-msg {
    padding: 0.75rem 1rem; border-radius: 12px;
    font-size: 0.93rem; line-height: 1.65; max-width: 85%; margin-bottom: 0.55rem;
}
.chat-msg.you {
    background: linear-gradient(135deg, #2563eb, #0891b2); color:#fff;
    margin-left:auto; border-bottom-right-radius:3px;
    box-shadow: 0 3px 10px rgba(37,99,235,0.2);
}
.chat-msg.ai {
    background:#ffffff; border:1px solid #e2e8f0; color:#334155;
    border-bottom-left-radius:3px; box-shadow:0 1px 4px rgba(0,0,0,0.05);
}

div[data-testid="stForm"] {
    background:transparent !important; border:none !important;
    box-shadow:none !important; padding:0 !important;
}
div[data-testid="stForm"] .stButton > button {
    background:#f1f5f9 !important; border:1.5px solid #e2e8f0 !important;
    color:#475569 !important; box-shadow:none !important; margin-top:0 !important;
    font-size:1rem !important; padding:0.72rem 1rem !important;
    border-radius:9px !important; font-family:'DM Sans',sans-serif !important;
}
div[data-testid="stForm"] .stButton > button:hover {
    background:#eff6ff !important; border-color:#3b82f6 !important;
    color:#3b82f6 !important; transform:none !important; box-shadow:none !important;
}

/* ══════════════════════════════
   SIDEBAR CARDS
══════════════════════════════ */
.sc {
    background: rgba(255,255,255,0.85); border: 1px solid rgba(255,255,255,0.9);
    border-radius: 14px; padding: 1.1rem 1.15rem; margin-bottom: 0.85rem;
    box-shadow: 0 3px 16px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
    backdrop-filter: blur(10px);
}
.sc-ttl {
    font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.75rem;
    font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
    color: #475569; margin-bottom: 0.85rem; display:flex; align-items:center; gap:0.45rem;
}
.sc-ttl::after { content:''; flex:1; height:1px; background:#e2e8f0; }

.sg { display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-bottom:0.6rem; }
.si { background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:0.7rem 0.8rem; text-align:center; }
.sv { font-family:'Plus Jakarta Sans',sans-serif; font-size:1.5rem; font-weight:800; line-height:1; margin-bottom:0.2rem; }
.sl { font-size:0.6rem; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; color:#94a3b8; }
.tkb { background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:0.7rem 0.9rem; }
.tkl { font-size:0.6rem; font-weight:600; letter-spacing:0.1em; text-transform:uppercase; color:#94a3b8; margin-bottom:0.22rem; }
.tkv { font-size:1.02rem; font-weight:700; color:#2563eb; }

.lr { display:flex; align-items:center; gap:0.7rem; margin-bottom:0.5rem; font-size:0.85rem; color:#475569; font-family:'DM Sans',sans-serif; }
.ld { width:8px; height:8px; border-radius:50%; flex-shrink:0; }

.lx-sec-label {
    font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.68rem;
    font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;
    color: #64748b; margin-bottom: 0.75rem; display:flex; align-items:center; gap:0.5rem;
}
.lx-sec-label::after { content:''; flex:1; height:1px; background:#e2e8f0; }

.stAlert { background:#eff6ff !important; border:1px solid #bfdbfe !important; border-radius:10px !important; color:#1e40af !important; }
.stSpinner > div { border-top-color: #3b82f6 !important; }
div[data-testid="stHorizontalBlock"] > div[data-testid="column"] { background:transparent !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ──────────────────────────────────────────────────────────────────
def score_to_accuracy(score):
    """Convert 0-1 score to accuracy percentage with label"""
    pct = round(score * 100, 1)
    if score >= 0.75:
        cls = "high"
    elif score >= 0.45:
        cls = "mid"
    else:
        cls = "low"
    return pct, cls

def render_kw_cards(kws):
    html = ""
    for i, k in enumerate(kws):
        rc    = f"r{min(i,9)}"
        score = float(k.get("score", 0))
        pct   = int(score * 100)
        acc_pct, acc_cls = score_to_accuracy(score)
        html += f"""
<div class="kw-row {rc}">
  <span class="kw-num">#{i+1:02d}</span>
  <span class="kw-word">{k['keyword']}</span>
  <div class="kw-bar-wrap">
    <div class="kw-bar-bg"><div class="kw-bar-fill" style="width:{pct}%"></div></div>
    <span class="kw-sc">{score:.2f}</span>
  </div>
  <span class="kw-acc {acc_cls}">{acc_pct}%</span>
</div>"""
    return html

def render_accuracy_summary(kws):
    """Render accuracy metrics summary bar above results"""
    scores   = [float(k.get("score", 0)) for k in kws]
    avg_acc  = round(sum(scores) / len(scores) * 100, 1)
    high_ct  = sum(1 for s in scores if s >= 0.75)
    top_acc  = round(max(scores) * 100, 1)
    # confidence formula: ratio of high-accuracy keywords
    conf_pct = round((high_ct / len(scores)) * 100, 1)

    return f"""
<div class="acc-summary">
  <div class="acc-stat">
    <div class="acc-stat-val" style="color:#2563eb;">{top_acc}%</div>
    <div class="acc-stat-lbl">Peak Accuracy</div>
  </div>
  <div class="acc-divider"></div>
  <div class="acc-stat">
    <div class="acc-stat-val" style="color:#0891b2;">{avg_acc}%</div>
    <div class="acc-stat-lbl">Avg Accuracy</div>
  </div>
  <div class="acc-divider"></div>
  <div class="acc-stat">
    <div class="acc-stat-val" style="color:#16a34a;">{high_ct}/{len(scores)}</div>
    <div class="acc-stat-lbl">High Confidence</div>
  </div>
  <div class="acc-divider"></div>
  <div class="acc-stat">
    <div class="acc-stat-val" style="color:#7c3aed;">{conf_pct}%</div>
    <div class="acc-stat-lbl">Confidence Rate</div>
  </div>
</div>"""

def kws_to_csv(kws):
    buf = io.StringIO()
    w   = csv.DictWriter(buf, fieldnames=["rank","keyword","score","accuracy_%"])
    w.writeheader()
    for i, k in enumerate(kws, 1):
        sc  = float(k.get("score","0"))
        acc = round(sc * 100, 1)
        w.writerow({"rank":i, "keyword":k["keyword"], "score":f"{sc:.4f}", "accuracy_%":f"{acc}%"})
    return buf.getvalue().encode()

def kws_to_plain(kws):
    return "\n".join(
        f"{i+1}. {k['keyword']}  score={float(k.get('score',0)):.4f}  accuracy={round(float(k.get('score',0))*100,1)}%"
        for i, k in enumerate(kws)
    )

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
    <div class="lx-logo-text">LEXIS AI</div>
  </div>
  <div class="lx-nav-badge">Keyword Intelligence Engine</div>
  <div class="lx-status"><div class="lx-status-dot"></div>AI Online</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="lx-hero">
  <div class="lx-hero-tag">AI-Powered Analysis</div>
  <h1 class="lx-h1">Extract Keywords</h1>
  <span class="lx-h1-accent">with Intelligence</span>
  <p class="lx-hero-sub">Paste any text or URL — LEXIS AI extracts the most relevant keywords, scores them, and provides intelligent analysis.</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════
left, right = st.columns([2.3, 1.1], gap="large")


# ══════════════════════════════════════════════════════════
# LEFT COLUMN
# ══════════════════════════════════════════════════════════
with left:

    # ── INPUT CARD ──
    st.markdown('<div class="lx-card">', unsafe_allow_html=True)

    tab_text, tab_url = st.tabs(["📄  Text Input", "🔍  URL Input"])

    with tab_text:
        text_input = st.text_area(
            "", height=160,
            placeholder="Paste your text here...",
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
                    st.session_state.kws=[]; st.session_state.chat_history=[]
                    st.error("🚫 PDF & image-only pages are not supported.")
                else:
                    try:
                        req = urllib.request.Request(url_input, headers={'User-Agent':'Mozilla/5.0'})
                        with st.spinner("Fetching page…"):
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                ct = resp.headers.get('Content-Type','')
                                if 'text/html' not in ct:
                                    st.session_state.kws=[]; st.session_state.chat_history=[]
                                    st.error(f"🚫 Unsupported content type ({ct.split(';')[0].strip()}).")
                                    st.stop()
                                html_content = resp.read().decode('utf-8', errors='ignore')
                        plain = re.sub(r'<style[^>]*>.*?</style>',' ',html_content,flags=re.DOTALL)
                        plain = re.sub(r'<script[^>]*>.*?</script>',' ',plain,flags=re.DOTALL)
                        plain = re.sub(r'<[^>]+>',' ',plain)
                        plain = re.sub(r'\s+',' ',plain).strip()
                        pl    = plain.lower()
                        if any(s in pl for s in ['sign in to continue','log in to continue','please sign in',
                            'please log in','login required','you must be logged in','members only']):
                            st.session_state.kws=[]; st.session_state.chat_history=[]
                            st.error("🚫 This page requires login.")
                        elif any(s in pl for s in ['subscribe to read','subscription required',
                            'this article is for subscribers','unlock this article','paid subscribers only']):
                            st.session_state.kws=[]; st.session_state.chat_history=[]
                            st.error("🚫 This page is behind a paywall.")
                        elif any(s in pl for s in ['captcha','are you a robot','verify you are human',
                            'ddos protection','access denied','robot check']):
                            st.session_state.kws=[]; st.session_state.chat_history=[]
                            st.error("🚫 This site blocks automated access.")
                        elif len(plain) < 200:
                            st.session_state.kws=[]; st.session_state.chat_history=[]
                            st.error("🚫 Not enough readable text found.")
                        else:
                            with st.spinner("Analyzing content…"):
                                st.session_state.kws = extract_keywords(plain)
                                st.session_state.chat_history = []
                    except HTTPError as e:
                        st.session_state.kws=[]; st.session_state.chat_history=[]
                        if e.code in (401,403): st.error(f"🚫 Access Denied (HTTP {e.code}).")
                        elif e.code == 402:     st.error("🚫 Paywalled content.")
                        else:                   st.error(f"🚫 HTTP Error {e.code}.")
                    except URLError:
                        st.session_state.kws=[]; st.session_state.chat_history=[]
                        st.error("🚫 Unable to reach this URL.")
                    except Exception as e:
                        st.session_state.kws=[]; st.session_state.chat_history=[]
                        st.error(f"Unexpected error: {e}")
            else:
                st.warning("Enter a valid URL starting with http(s)://")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── RESULTS ──
    if st.session_state.kws:

        st.markdown('<div class="lx-card">', unsafe_allow_html=True)
        st.markdown('<div class="lx-sec-label">Keyword Results</div>', unsafe_allow_html=True)

        # ── ACCURACY SUMMARY BAR ──
        st.markdown(render_accuracy_summary(st.session_state.kws), unsafe_allow_html=True)

        # ── DOWNLOAD BUTTONS ──
        col_dl1, col_dl2, col_sp = st.columns([1,1,4])
        with col_dl1:
            st.download_button("⬇ CSV", data=kws_to_csv(st.session_state.kws),
                               file_name="lexis_keywords.csv", mime="text/csv")
        with col_dl2:
            st.download_button("⬇ TXT", data=kws_to_plain(st.session_state.kws).encode(),
                               file_name="lexis_keywords.txt", mime="text/plain")

        # ── COLUMN HEADERS ──
        st.markdown("""
<div style="display:flex;align-items:center;gap:0.75rem;padding:0.3rem 0.9rem;margin-bottom:0.2rem;">
  <span style="min-width:24px;font-family:'DM Mono',monospace;font-size:0.6rem;color:#cbd5e1;text-transform:uppercase;letter-spacing:0.08em;">#</span>
  <span style="flex:1;font-family:'DM Mono',monospace;font-size:0.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;">Keyword</span>
  <span style="min-width:110px;font-family:'DM Mono',monospace;font-size:0.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;text-align:right;">Score</span>
  <span style="min-width:48px;font-family:'DM Mono',monospace;font-size:0.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;text-align:center;">Accuracy</span>
</div>""", unsafe_allow_html=True)

        st.markdown(render_kw_cards(st.session_state.kws), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ── CHAT ──
        st.markdown('<div class="lx-card" style="margin-top:0.5rem;">', unsafe_allow_html=True)
        st.markdown('<div class="lx-sec-label">Ask LEXIS AI</div>', unsafe_allow_html=True)

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

        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# RIGHT COLUMN  — How It Works FIRST, then stats, then legend
# ══════════════════════════════════════════════════════════
with right:

    # ══ 1. HOW IT WORKS — ALWAYS ON TOP ══
    st.markdown("""
<div style="background:rgba(255,255,255,0.85);border:1px solid rgba(255,255,255,0.9);border-radius:14px;padding:1.1rem 1.15rem;margin-bottom:0.85rem;box-shadow:0 3px 16px rgba(0,0,0,0.06),0 1px 3px rgba(0,0,0,0.04);backdrop-filter:blur(10px);">

  <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.75rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#475569;margin-bottom:0.9rem;display:flex;align-items:center;gap:0.45rem;">
    How It Works
    <span style="flex:1;height:1px;background:#e2e8f0;display:inline-block;"></span>
  </div>

  <!-- SUPPORTED -->
  <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#16a34a;margin-bottom:0.45rem;">
    ✓ &nbsp;Supported
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem;padding:0.32rem 0;border-bottom:1px solid #f8fafc;">
    <span style="width:17px;height:17px;border-radius:4px;background:#dcfce7;border:1px solid #bbf7d0;display:inline-flex;align-items:center;justify-content:center;font-size:0.62rem;color:#16a34a;flex-shrink:0;">✓</span>
    <span style="font-size:0.85rem;color:#475569;font-family:'DM Sans',sans-serif;">Public blogs &amp; articles</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem;padding:0.32rem 0;border-bottom:1px solid #f8fafc;">
    <span style="width:17px;height:17px;border-radius:4px;background:#dcfce7;border:1px solid #bbf7d0;display:inline-flex;align-items:center;justify-content:center;font-size:0.62rem;color:#16a34a;flex-shrink:0;">✓</span>
    <span style="font-size:0.85rem;color:#475569;font-family:'DM Sans',sans-serif;">Wikipedia pages</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem;padding:0.32rem 0;border-bottom:1px solid #f8fafc;">
    <span style="width:17px;height:17px;border-radius:4px;background:#dcfce7;border:1px solid #bbf7d0;display:inline-flex;align-items:center;justify-content:center;font-size:0.62rem;color:#16a34a;flex-shrink:0;">✓</span>
    <span style="font-size:0.85rem;color:#475569;font-family:'DM Sans',sans-serif;">Company &amp; docs sites</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem;padding:0.32rem 0;border-bottom:1px solid #e2e8f0;">
    <span style="width:17px;height:17px;border-radius:4px;background:#dcfce7;border:1px solid #bbf7d0;display:inline-flex;align-items:center;justify-content:center;font-size:0.62rem;color:#16a34a;flex-shrink:0;">✓</span>
    <span style="font-size:0.85rem;color:#475569;font-family:'DM Sans',sans-serif;">Pasted raw text</span>
  </div>

  <!-- NOT SUPPORTED -->
  <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#dc2626;margin-top:0.8rem;margin-bottom:0.45rem;">
    ✕ &nbsp;Not Supported
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem;padding:0.32rem 0;border-bottom:1px solid #f8fafc;">
    <span style="width:17px;height:17px;border-radius:4px;background:#fee2e2;border:1px solid #fecaca;display:inline-flex;align-items:center;justify-content:center;font-size:0.62rem;color:#dc2626;flex-shrink:0;">✕</span>
    <span style="font-size:0.85rem;color:#475569;font-family:'DM Sans',sans-serif;">Login-gated pages</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem;padding:0.32rem 0;border-bottom:1px solid #f8fafc;">
    <span style="width:17px;height:17px;border-radius:4px;background:#fee2e2;border:1px solid #fecaca;display:inline-flex;align-items:center;justify-content:center;font-size:0.62rem;color:#dc2626;flex-shrink:0;">✕</span>
    <span style="font-size:0.85rem;color:#475569;font-family:'DM Sans',sans-serif;">Paywalled content</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem;padding:0.32rem 0;border-bottom:1px solid #f8fafc;">
    <span style="width:17px;height:17px;border-radius:4px;background:#fee2e2;border:1px solid #fecaca;display:inline-flex;align-items:center;justify-content:center;font-size:0.62rem;color:#dc2626;flex-shrink:0;">✕</span>
    <span style="font-size:0.85rem;color:#475569;font-family:'DM Sans',sans-serif;">Bot-blocking / CAPTCHA</span>
  </div>
  <div style="display:flex;align-items:center;gap:0.5rem;padding:0.32rem 0;">
    <span style="width:17px;height:17px;border-radius:4px;background:#fee2e2;border:1px solid #fecaca;display:inline-flex;align-items:center;justify-content:center;font-size:0.62rem;color:#dc2626;flex-shrink:0;">✕</span>
    <span style="font-size:0.85rem;color:#475569;font-family:'DM Sans',sans-serif;">PDF / image-only pages</span>
  </div>

</div>
""", unsafe_allow_html=True)

    # ══ 2. QUICK STATS ══
    scores   = [float(k.get("score",0)) for k in st.session_state.kws] if st.session_state.kws else [0.0]
    avg      = sum(scores)/len(scores) if st.session_state.kws else 0.0
    top_kw   = st.session_state.kws[0]["keyword"] if st.session_state.kws else "—"
    sc_range = (max(scores)-min(scores)) if st.session_state.kws else 0.0
    count    = len(st.session_state.kws)

    st.markdown(f"""
<div class="sc">
  <div class="sc-ttl">Quick Stats</div>
  <div class="sg">
    <div class="si">
      <div class="sl">Top Score</div>
      <div class="sv" style="color:#2563eb;">{max(scores):.2f}</div>
    </div>
    <div class="si">
      <div class="sl">Average</div>
      <div class="sv" style="color:#0891b2;">{avg:.2f}</div>
    </div>
    <div class="si">
      <div class="sl">Count</div>
      <div class="sv" style="color:#0369a1;">{count}</div>
    </div>
    <div class="si">
      <div class="sl">Range</div>
      <div class="sv" style="color:#0e7490;">{sc_range:.2f}</div>
    </div>
  </div>
  <div class="tkb">
    <div class="tkl">Top Keyword</div>
    <div class="tkv">{top_kw}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ══ 3. SCORE LEGEND ══
    st.markdown("""
<div class="sc">
  <div class="sc-ttl">Score Legend</div>
  <div class="lr"><div class="ld" style="background:linear-gradient(135deg,#2563eb,#06b6d4);"></div><span>0.90 – 1.00</span></div>
  <div class="lr"><div class="ld" style="background:#3b82f6;"></div><span>0.70 – 0.89</span></div>
  <div class="lr"><div class="ld" style="background:#0ea5e9;"></div><span>0.50 – 0.69</span></div>
  <div class="lr"><div class="ld" style="background:#22d3ee;"></div><span>0.30 – 0.49</span></div>
  <div class="lr" style="margin-bottom:0;"><div class="ld" style="background:#cbd5e1;"></div><span>0.00 – 0.29</span></div>
</div>
""", unsafe_allow_html=True)
