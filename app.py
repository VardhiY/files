import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from urllib.error import HTTPError, URLError
import csv
import io

# ── PAGE CONFIG ─────────────────────────
st.set_page_config(
    page_title="LEXIS AI",
    page_icon="⚡",
    layout="wide"
)

# ── LOAD API KEY ───────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing.")
    st.stop()

# ── BOLD COLORFUL STYLING ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&family=Nunito:wght@400;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: #0d0d0d;
    color: #f0f0f0;
    font-family: 'Nunito', sans-serif;
}

/* ── Animated background stripes ── */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
        repeating-linear-gradient(
            -55deg,
            transparent,
            transparent 60px,
            rgba(255,60,120,0.03) 60px,
            rgba(255,60,120,0.03) 61px
        );
    pointer-events: none;
    z-index: 0;
}

.block-container {
    padding-top: 2rem;
    position: relative;
    z-index: 1;
}

/* ── Header ── */
.hero-wrap {
    text-align: center;
    margin-bottom: 2.5rem;
}
.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 5.5rem;
    font-weight: 800;
    letter-spacing: -3px;
    line-height: 1;
    display: inline-block;
    background: linear-gradient(90deg, #ff3c78, #ffb700, #00e5ff, #a259ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-size: 300% auto;
    animation: shimmer 4s linear infinite;
}
@keyframes shimmer {
    0%   { background-position: 0% center; }
    100% { background-position: 300% center; }
}
.subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 0.95rem;
    color: #888;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* ── Pill badge ── */
.badge {
    display: inline-block;
    padding: 0.3rem 1rem;
    border-radius: 100px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
    background: linear-gradient(90deg,#ff3c78,#ffb700);
    color: #000;
}

/* ── Panel cards ── */
.panel {
    background: #161616;
    border: 1px solid #2a2a2a;
    border-radius: 24px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.panel::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg,#ff3c78,#ffb700,#00e5ff,#a259ff);
}

/* ── Section label ── */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #ff3c78;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 1rem;
    font-weight: 500;
}

/* ── Tabs ── */
div[data-baseweb="tab-list"] {
    background: #111 !important;
    border-radius: 14px !important;
    padding: 6px !important;
    border: 1px solid #2a2a2a !important;
    gap: 4px !important;
}
div[data-baseweb="tab"] {
    border-radius: 10px !important;
    color: #888 !important;
    font-weight: 700 !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.5rem 1.2rem !important;
}
div[aria-selected="true"] {
    background: linear-gradient(90deg,#ff3c78,#a259ff) !important;
    color: white !important;
}

/* ── Text areas / inputs ── */
textarea, .stTextInput input {
    background: #1a1a1a !important;
    border: 1.5px solid #2e2e2e !important;
    border-radius: 14px !important;
    color: #f0f0f0 !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 1rem !important;
    padding: 1rem !important;
    transition: border-color 0.2s;
}
textarea:focus, .stTextInput input:focus {
    border-color: #ff3c78 !important;
    box-shadow: 0 0 0 3px rgba(255,60,120,0.15) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(90deg, #ff3c78, #a259ff) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #fff !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    padding: 0.8rem 2.2rem !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(255,60,120,0.4) !important;
}

/* ── Download / secondary buttons ── */
.stDownloadButton > button {
    background: #1f1f1f !important;
    border: 1.5px solid #2e2e2e !important;
    color: #ccc !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.4rem !important;
    font-size: 0.85rem !important;
}
.stDownloadButton > button:hover {
    border-color: #ff3c78 !important;
    color: #ff3c78 !important;
}

/* ── Keyword table card ── */
.kw-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 16px;
    padding: 1rem 1.4rem;
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: border-color 0.2s, transform 0.15s;
}
.kw-card:hover {
    border-color: #ff3c78;
    transform: translateX(4px);
}
.kw-rank {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #555;
    min-width: 28px;
}
.kw-name {
    flex: 1;
    font-weight: 700;
    font-size: 1rem;
    color: #f0f0f0;
}
.kw-score-wrap {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    min-width: 160px;
}
.kw-bar-bg {
    flex: 1;
    height: 6px;
    background: #2a2a2a;
    border-radius: 100px;
    overflow: hidden;
}
.kw-bar-fill {
    height: 100%;
    border-radius: 100px;
}
.kw-score-val {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    min-width: 36px;
    text-align: right;
}

/* ── Color stops by rank ── */
.rank-1 .kw-bar-fill { background: linear-gradient(90deg,#ff3c78,#ff7043); }
.rank-2 .kw-bar-fill { background: linear-gradient(90deg,#ff7043,#ffb700); }
.rank-3 .kw-bar-fill { background: linear-gradient(90deg,#ffb700,#ffe600); }
.rank-4 .kw-bar-fill, .rank-5 .kw-bar-fill { background: linear-gradient(90deg,#00e5ff,#00bcd4); }
.rank-other .kw-bar-fill { background: linear-gradient(90deg,#a259ff,#7c4dff); }

.rank-1 .kw-score-val { color: #ff3c78; }
.rank-2 .kw-score-val { color: #ff7043; }
.rank-3 .kw-score-val { color: #ffb700; }
.rank-4 .kw-score-val, .rank-5 .kw-score-val { color: #00e5ff; }
.rank-other .kw-score-val { color: #a259ff; }

/* ── Chat messages ── */
.chat-bubble {
    padding: 1rem 1.3rem;
    border-radius: 18px;
    margin-bottom: 0.8rem;
    font-size: 0.95rem;
    line-height: 1.6;
    max-width: 90%;
}
.chat-bubble.user {
    background: linear-gradient(90deg,#ff3c78,#a259ff);
    color: white;
    font-weight: 600;
    margin-left: auto;
    border-bottom-right-radius: 4px;
}
.chat-bubble.ai {
    background: #1e1e1e;
    border: 1px solid #2a2a2a;
    color: #ddd;
    border-bottom-left-radius: 4px;
}
.chat-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #555;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

/* ── Guidelines ── */
.guide-item {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.5rem 0;
    font-size: 0.9rem;
    border-bottom: 1px solid #1f1f1f;
}
.guide-yes { color: #00e5b0; font-size: 1rem; }
.guide-no  { color: #ff3c78; font-size: 1rem; }

/* ── Spinner text ── */
.stSpinner { color: #ff3c78 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d0d0d; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 10px; }

/* ── Radio ── */
div[data-testid="stHorizontalBlock"] label {
    color: #888 !important;
    font-weight: 600 !important;
}

/* ── Divider ── */
hr { border-color: #1f1f1f !important; }

</style>
""", unsafe_allow_html=True)

# ── HELPERS ─────────────────────────────────────────────────────────────────

def score_to_color_class(idx):
    if idx == 0:   return "rank-1"
    if idx == 1:   return "rank-2"
    if idx == 2:   return "rank-3"
    if idx in (3, 4): return "rank-4"
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
                <span class="kw-score-val">{float(k.get('score',0)):.2f}</span>
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
    return "\n".join([f"{i+1}. {k['keyword']} ({float(k.get('score',0)):.2f})"
                      for i, k in enumerate(kws)])

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
            {"role": "system", "content": "You are LEXIS, an expert in text analysis and keyword intelligence. Be insightful, concise, and conversational."},
            {"role": "user",   "content": f"The extracted keywords are: {kw_list}\n\n{q}"}
        ],
        temperature=0.6,
        max_tokens=600
    )
    return response.choices[0].message.content.strip()

# ── SESSION STATE ────────────────────────────────────────────────────────────
if "kws" not in st.session_state:
    st.session_state.kws = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="main-title">LEXIS AI</div>
    <div class="subtitle">⚡ Next-Gen Intelligent Keyword Engine ⚡</div>
</div>
""", unsafe_allow_html=True)

# ── MAIN LAYOUT ──────────────────────────────────────────────────────────────
left, right = st.columns([2.5, 1.1], gap="large")

# ════════════════════════════════════════════════════════
# LEFT COLUMN
# ════════════════════════════════════════════════════════
with left:

    # ── INPUT TABS ──
    st.markdown('<div class="section-label">01 — Input Source</div>', unsafe_allow_html=True)
    tab_text, tab_url = st.tabs(["📄  Text Input", "🌐  URL Input"])

    with tab_text:
        text_input = st.text_area("", height=220, placeholder="Paste your article, blog post, or any content here...", label_visibility="collapsed")
        if st.button("⚡ Extract Keywords", key="btn_text"):
            if text_input.strip():
                with st.spinner("Analyzing with AI..."):
                    try:
                        st.session_state.kws = extract_keywords(text_input)
                        st.session_state.chat_history = []
                    except Exception as e:
                        st.error(f"Extraction failed: {e}")
            else:
                st.warning("Please paste some text first.")

    with tab_url:
        url_input = st.text_input("", placeholder="https://example.com/article", label_visibility="collapsed")
        if st.button("⚡ Extract from URL", key="btn_url"):
            if url_input.startswith("http"):
                try:
                    req = urllib.request.Request(url_input, headers={'User-Agent': 'Mozilla/5.0'})
                    with st.spinner("Fetching & analyzing..."):
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            html = resp.read().decode('utf-8', errors='ignore')
                        st.session_state.kws = extract_keywords(html)
                        st.session_state.chat_history = []
                except HTTPError as e:
                    st.error(f"🚫 Access Restricted (HTTP {e.code}) — This page may require login or block bots.")
                except URLError:
                    st.error("🚫 Unable to reach the website.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
            else:
                st.warning("Please enter a valid URL starting with http(s)://")

    # ── RESULTS ──
    if st.session_state.kws:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">02 — Keyword Results</div>', unsafe_allow_html=True)

        # Export buttons row
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

        # Keyword cards
        st.markdown(render_kw_cards(st.session_state.kws), unsafe_allow_html=True)

        # ── CHAT ──
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">03 — Ask LEXIS AI</div>', unsafe_allow_html=True)

        # Initial auto-explanation
        if not st.session_state.chat_history:
            with st.spinner("LEXIS is analyzing your keywords..."):
                initial = explain_keywords(st.session_state.kws)
            st.session_state.chat_history.append({
                "role": "ai",
                "text": initial
            })

        # Render chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-label" style="text-align:right">You</div><div class="chat-bubble user">{msg["text"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-label">LEXIS</div><div class="chat-bubble ai">{msg["text"]}</div>', unsafe_allow_html=True)

        # Chat input
        with st.form("chat_form", clear_on_submit=True):
            chat_cols = st.columns([5, 1])
            with chat_cols[0]:
                user_q = st.text_input("", placeholder="Ask anything about these keywords...", label_visibility="collapsed")
            with chat_cols[1]:
                sent = st.form_submit_button("Send")

        if sent and user_q.strip():
            st.session_state.chat_history.append({"role": "user", "text": user_q})
            with st.spinner("Thinking..."):
                reply = explain_keywords(st.session_state.kws, user_question=user_q)
            st.session_state.chat_history.append({"role": "ai", "text": reply})
            st.rerun()


# ════════════════════════════════════════════════════════
# RIGHT COLUMN
# ════════════════════════════════════════════════════════
with right:

    # ── SCORE LEGEND ──
    if st.session_state.kws:
        st.markdown('<div class="section-label">Score Legend</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#161616;border:1px solid #2a2a2a;border-radius:16px;padding:1.2rem;">
            <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.5rem;">
                <div style="width:32px;height:6px;border-radius:4px;background:linear-gradient(90deg,#ff3c78,#ff7043)"></div>
                <span style="font-size:0.82rem;color:#aaa;">#1 — Top Relevance</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.5rem;">
                <div style="width:32px;height:6px;border-radius:4px;background:linear-gradient(90deg,#ffb700,#ffe600)"></div>
                <span style="font-size:0.82rem;color:#aaa;">#3 — High Impact</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.5rem;">
                <div style="width:32px;height:6px;border-radius:4px;background:linear-gradient(90deg,#00e5ff,#00bcd4)"></div>
                <span style="font-size:0.82rem;color:#aaa;">#4–5 — Notable</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.7rem;">
                <div style="width:32px;height:6px;border-radius:4px;background:linear-gradient(90deg,#a259ff,#7c4dff)"></div>
                <span style="font-size:0.82rem;color:#aaa;">#6–10 — Supporting</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    # ── GUIDELINES ──
    st.markdown('<div class="section-label">Usage Guidelines</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#161616;border:1px solid #2a2a2a;border-radius:16px;padding:1.4rem;position:relative;overflow:hidden;">
        <div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#ff3c78,#ffb700,#00e5ff,#a259ff)"></div>

        <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#00e5b0;letter-spacing:2px;text-transform:uppercase;margin-bottom:0.8rem;">✔ Works great with</div>

        <div class="guide-item"><span class="guide-yes">●</span> Public blogs & articles</div>
        <div class="guide-item"><span class="guide-yes">●</span> Wikipedia pages</div>
        <div class="guide-item"><span class="guide-yes">●</span> Company websites</div>
        <div class="guide-item"><span class="guide-yes">●</span> Documentation portals</div>

        <div style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#ff3c78;letter-spacing:2px;text-transform:uppercase;margin-top:1.2rem;margin-bottom:0.8rem;">✖ Doesn't support</div>

        <div class="guide-item"><span class="guide-no">●</span> Login-required portals</div>
        <div class="guide-item"><span class="guide-no">●</span> Paywalled content</div>
        <div class="guide-item"><span class="guide-no">●</span> Bot-blocking sites</div>
        <div class="guide-item" style="border:none"><span class="guide-no">●</span> PDF / image-only pages</div>
    </div>
    """, unsafe_allow_html=True)

    # ── STATS ──
    if st.session_state.kws:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-label">Quick Stats</div>', unsafe_allow_html=True)
        scores = [float(k.get("score", 0)) for k in st.session_state.kws]
        avg = sum(scores) / len(scores) if scores else 0
        top_kw = st.session_state.kws[0]["keyword"] if st.session_state.kws else "—"
        st.markdown(f"""
        <div style="background:#161616;border:1px solid #2a2a2a;border-radius:16px;padding:1.2rem;display:flex;flex-direction:column;gap:0.8rem;">
            <div>
                <div style="font-size:0.7rem;color:#555;letter-spacing:2px;text-transform:uppercase;font-family:'DM Mono',monospace;">Top Keyword</div>
                <div style="font-size:1.1rem;font-weight:800;color:#ff3c78;margin-top:0.2rem">{top_kw}</div>
            </div>
            <div>
                <div style="font-size:0.7rem;color:#555;letter-spacing:2px;text-transform:uppercase;font-family:'DM Mono',monospace;">Avg Score</div>
                <div style="font-size:1.1rem;font-weight:800;color:#ffb700;margin-top:0.2rem">{avg:.2f}</div>
            </div>
            <div>
                <div style="font-size:0.7rem;color:#555;letter-spacing:2px;text-transform:uppercase;font-family:'DM Mono',monospace;">Total Keywords</div>
                <div style="font-size:1.1rem;font-weight:800;color:#00e5ff;margin-top:0.2rem">{len(st.session_state.kws)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
