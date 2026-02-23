import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from urllib.error import HTTPError, URLError
import csv
import io
import os

st.set_page_config(page_title="LEXIS AI", page_icon="⚡", layout="wide")

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except:
        pass
if not api_key:
    st.error("⚠️ GROQ_API_KEY missing.")
    st.stop()

client = Groq(api_key=api_key)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&family=Nunito:wght@400;600;700;800&display=swap');
*, *::before, *::after { box-sizing: border-box; }
.stApp {
    background: #0d0d0d;
    color: #f0f0f0;
    font-family: 'Nunito', sans-serif;
    font-size: 0.92rem;
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(-55deg, transparent, transparent 60px, rgba(255,60,120,0.03) 60px, rgba(255,60,120,0.03) 61px);
    pointer-events: none;
    z-index: 0;
}
.block-container { padding-top: 1.5rem; position: relative; z-index: 1; }
.hero-wrap { text-align: center; margin-bottom: 1.5rem; }
.main-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(1.6rem, 4vw, 3rem);
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1.2;
    display: inline-block;
    white-space: nowrap;
    padding-bottom: 0.15em;
    background: linear-gradient(90deg, #ff3c78, #ffb700, #00e5ff, #a259ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    background-size: 300% auto;
    animation: shimmer 4s linear infinite;
}
@keyframes shimmer { 0% { background-position: 0% center; } 100% { background-position: 300% center; } }
.subtitle { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #888; letter-spacing: 3px; text-transform: uppercase; margin-top: 0.3rem; }
div[data-baseweb="tab-list"] { background: #111 !important; border-radius: 10px !important; padding: 4px !important; border: 1px solid #2a2a2a !important; gap: 3px !important; }
div[data-baseweb="tab"] { border-radius: 8px !important; color: #888 !important; font-weight: 700 !important; font-family: 'Nunito', sans-serif !important; font-size: 0.85rem !important; padding: 0.35rem 1rem !important; }
div[aria-selected="true"] { background: linear-gradient(90deg,#ff3c78,#a259ff) !important; color: white !important; }
textarea, .stTextInput input {
    background: #1a1a1a !important;
    border: 1.5px solid #2e2e2e !important;
    border-radius: 10px !important;
    color: #f0f0f0 !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.7rem !important;
}
textarea:focus, .stTextInput input:focus { border-color: #ff3c78 !important; box-shadow: 0 0 0 2px rgba(255,60,120,0.15) !important; }
.stButton > button {
    background: linear-gradient(90deg, #ff3c78, #a259ff) !important;
    border: none !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 0.85rem !important;
    padding: 0.6rem 1.6rem !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    cursor: pointer;
    transition: transform 0.15s, box-shadow 0.15s;
}
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(255,60,120,0.4) !important; }
.stDownloadButton > button {
    background: #1f1f1f !important;
    border: 1.5px solid #2e2e2e !important;
    color: #ccc !important;
    font-family: 'Nunito', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    padding: 0.45rem 1rem !important;
    font-size: 0.8rem !important;
}
.stDownloadButton > button:hover { border-color: #ff3c78 !important; color: #ff3c78 !important; }
.kw-card {
    background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px;
    padding: 0.7rem 1.1rem; margin-bottom: 0.5rem;
    display: flex; align-items: center; gap: 0.8rem;
    transition: border-color 0.2s, transform 0.15s;
}
.kw-card:hover { border-color: #ff3c78; transform: translateX(3px); }
.kw-rank { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #555; min-width: 28px; }
.kw-name { flex: 1; font-weight: 700; font-size: 0.92rem; color: #f0f0f0; }
.kw-score-wrap { display: flex; align-items: center; gap: 0.6rem; min-width: 130px; }
.kw-bar-bg { flex: 1; height: 6px; background: #2a2a2a; border-radius: 100px; overflow: hidden; }
.kw-bar-fill { height: 100%; border-radius: 100px; }
.kw-score-val { font-family: 'DM Mono', monospace; font-size: 0.78rem; min-width: 36px; text-align: right; }
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
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0d0d0d; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 10px; }
hr { border-color: #1f1f1f !important; }
</style>
""", unsafe_allow_html=True)

def score_to_color_class(idx):
    if idx == 0: return "rank-1"
    if idx == 1: return "rank-2"
    if idx == 2: return "rank-3"
    if idx in (3, 4): return "rank-4"
    return "rank-other"

def render_kw_cards(kws):
    html = ""
    for i, k in enumerate(kws):
        rank_cls = score_to_color_class(i)
        pct = int(float(k.get("score", 0)) * 100)
        html += f"""<div class="kw-card {rank_cls}">
            <span class="kw-rank">#{i+1:02d}</span>
            <span class="kw-name">{k['keyword']}</span>
            <div class="kw-score-wrap">
                <div class="kw-bar-bg"><div class="kw-bar-fill" style="width:{pct}%"></div></div>
                <span class="kw-score-val">{float(k.get('score',0)):.2f}</span>
            </div></div>"""
    return html

def kws_to_csv(kws):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["rank","keyword","score"])
    writer.writeheader()
    for i, k in enumerate(kws, 1):
        writer.writerow({"rank": i, "keyword": k["keyword"], "score": k.get("score","")})
    return buf.getvalue().encode()

def kws_to_plain(kws):
    return "\n".join([f"{i+1}. {k['keyword']} ({float(k.get('score',0)):.2f})" for i, k in enumerate(kws)])

def extract_keywords(text):
    prompt = f"""Extract top 10 important keywords from the following text.
Return ONLY a JSON array. No explanation. No markdown. Example format:
[{{"keyword":"example","score":0.95}}]
TEXT:\n{text[:6000]}"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2, max_tokens=800
    )
    cleaned = re.sub(r'```json|```', '', response.choices[0].message.content.strip())
    return json.loads(cleaned)

def explain_keywords(kws, user_question=None):
    kw_list = ", ".join([k["keyword"] for k in kws])
    q = user_question or f"Explain why these keywords are significant and what themes they reveal: {kw_list}"
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":"You are LEXIS, an expert in text analysis and keyword intelligence. Be insightful, concise, and conversational."},
            {"role":"user","content":f"The extracted keywords are: {kw_list}\n\n{q}"}
        ],
        temperature=0.6, max_tokens=600
    )
    return response.choices[0].message.content.strip()

if "kws" not in st.session_state: st.session_state.kws = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []

st.markdown('<div class="hero-wrap"><div class="main-title">LEXIS AI</div><div class="subtitle">⚡ Next-Gen Intelligent Keyword Engine ⚡</div></div>', unsafe_allow_html=True)

left, right = st.columns([2.5, 1.1], gap="large")

with left:
    st.markdown('<p style="font-family:monospace;font-size:0.65rem;color:#ff3c78;letter-spacing:3px;text-transform:uppercase;font-weight:500;">01 — Input Source</p>', unsafe_allow_html=True)
    tab_text, tab_url = st.tabs(["📄  Text Input", "🌐  URL Input"])

    with tab_text:
        text_input = st.text_area("", height=180, placeholder="Paste your article, blog post, or any content here...", label_visibility="collapsed")
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
                blocked_exts = ('.pdf','.jpg','.jpeg','.png','.gif','.webp','.svg','.bmp')
                if url_input.lower().split('?')[0].endswith(blocked_exts):
                    st.session_state.kws = []; st.session_state.chat_history = []
                    st.error("🚫 PDF & image-only pages are not supported.")
                else:
                    try:
                        req = urllib.request.Request(url_input, headers={'User-Agent': 'Mozilla/5.0'})
                        with st.spinner("Fetching & analyzing..."):
                            with urllib.request.urlopen(req, timeout=15) as resp:
                                content_type = resp.headers.get('Content-Type', '')
                                if 'text/html' not in content_type:
                                    st.session_state.kws = []; st.session_state.chat_history = []
                                    st.error(f"🚫 Unsupported content type."); st.stop()
                                html = resp.read().decode('utf-8', errors='ignore')
                        plain = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL)
                        plain = re.sub(r'<script[^>]*>.*?</script>', ' ', plain, flags=re.DOTALL)
                        plain = re.sub(r'<[^>]+>', ' ', plain)
                        plain = re.sub(r'\s+', ' ', plain).strip()
                        plain_lower = plain.lower()
                        login_signals = ['sign in to continue','log in to continue','please sign in','please log in','login required','enter your password','members only']
                        if any(sig in plain_lower for sig in login_signals):
                            st.session_state.kws = []; st.session_state.chat_history = []
                            st.error("🚫 This page requires login.")
                        elif any(sig in plain_lower for sig in ['subscribe to read','paywall','premium content','paid subscribers only']):
                            st.session_state.kws = []; st.session_state.chat_history = []
                            st.error("🚫 This page is behind a paywall.")
                        elif any(sig in plain_lower for sig in ['captcha','are you a robot','checking your browser','access denied']):
                            st.session_state.kws = []; st.session_state.chat_history = []
                            st.error("🚫 This site is blocking automated access.")
                        elif len(plain) < 200:
                            st.session_state.kws = []; st.session_state.chat_history = []
                            st.error("🚫 Not enough readable text found.")
                        else:
                            st.session_state.kws = extract_keywords(plain)
                            st.session_state.chat_history = []
                    except HTTPError as e:
                        st.session_state.kws = []; st.session_state.chat_history = []
                        if e.code in (401, 403): st.error(f"🚫 Access Denied (HTTP {e.code})")
                        elif e.code == 402: st.error("🚫 Payment Required (HTTP 402)")
                        else: st.error(f"🚫 HTTP Error {e.code}")
                    except URLError:
                        st.session_state.kws = []; st.session_state.chat_history = []
                        st.error("🚫 Unable to reach the website.")
                    except Exception as e:
                        st.session_state.kws = []; st.session_state.chat_history = []
                        st.error(f"Unexpected error: {e}")
            else:
                st.warning("Please enter a valid URL starting with http(s)://")

    if st.session_state.kws:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p style="font-family:monospace;font-size:0.65rem;color:#ff3c78;letter-spacing:3px;text-transform:uppercase;font-weight:500;">02 — Keyword Results</p>', unsafe_allow_html=True)
        col_dl1, col_dl2, col_spacer = st.columns([1, 1, 3])
        with col_dl1:
            st.download_button("⬇ CSV", data=kws_to_csv(st.session_state.kws), file_name="lexis_keywords.csv", mime="text/csv")
        with col_dl2:
            st.download_button("⬇ TXT", data=kws_to_plain(st.session_state.kws).encode(), file_name="lexis_keywords.txt", mime="text/plain")
        st.markdown(render_kw_cards(st.session_state.kws), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p style="font-family:monospace;font-size:0.65rem;color:#ff3c78;letter-spacing:3px;text-transform:uppercase;font-weight:500;">03 — Ask LEXIS AI</p>', unsafe_allow_html=True)

        if not st.session_state.chat_history:
            with st.spinner("LEXIS is analyzing your keywords..."):
                initial = explain_keywords(st.session_state.kws)
            st.session_state.chat_history.append({"role":"ai","text":initial})

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'''<div style="text-align:right;margin-bottom:0.2rem;font-size:0.6rem;color:#555;letter-spacing:2px;text-transform:uppercase;font-family:monospace;">You</div>
<div style="background:linear-gradient(90deg,#ff3c78,#a259ff);color:white;font-weight:600;padding:0.7rem 1rem;border-radius:14px;border-bottom-right-radius:3px;margin-bottom:0.6rem;font-size:0.85rem;line-height:1.6;max-width:90%;margin-left:auto;">{msg["text"]}</div>''', unsafe_allow_html=True)
            else:
                st.markdown(f'''<div style="margin-bottom:0.2rem;font-size:0.6rem;color:#555;letter-spacing:2px;text-transform:uppercase;font-family:monospace;">LEXIS</div>
<div style="background:#1e1e1e;border:1px solid #2a2a2a;color:#ddd;padding:0.7rem 1rem;border-radius:14px;border-bottom-left-radius:3px;margin-bottom:0.6rem;font-size:0.85rem;line-height:1.6;max-width:90%;">{msg["text"]}</div>''', unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            chat_cols = st.columns([5, 1])
            with chat_cols[0]:
                user_q = st.text_input("", placeholder="Ask anything about these keywords...", label_visibility="collapsed")
            with chat_cols[1]:
                sent = st.form_submit_button("Send")
        if sent and user_q.strip():
            st.session_state.chat_history.append({"role":"user","text":user_q})
            with st.spinner("Thinking..."):
                reply = explain_keywords(st.session_state.kws, user_question=user_q)
            st.session_state.chat_history.append({"role":"ai","text":reply})
            st.rerun()

with right:
    if st.session_state.kws:
        st.markdown('<p style="font-family:monospace;font-size:0.72rem;color:#ff3c78;letter-spacing:3px;text-transform:uppercase;font-weight:500;">Score Legend</p>', unsafe_allow_html=True)
        st.markdown("""<div style="background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:0.9rem;">
            <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;"><div style="width:28px;height:6px;border-radius:4px;background:linear-gradient(90deg,#ff3c78,#ff7043)"></div><span style="font-size:0.82rem;color:#aaa;">#1 — Top Relevance</span></div>
            <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;"><div style="width:28px;height:6px;border-radius:4px;background:linear-gradient(90deg,#ffb700,#ffe600)"></div><span style="font-size:0.82rem;color:#aaa;">#3 — High Impact</span></div>
            <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.5rem;"><div style="width:28px;height:6px;border-radius:4px;background:linear-gradient(90deg,#00e5ff,#00bcd4)"></div><span style="font-size:0.82rem;color:#aaa;">#4–5 — Notable</span></div>
            <div style="display:flex;align-items:center;gap:0.6rem;"><div style="width:28px;height:6px;border-radius:4px;background:linear-gradient(90deg,#a259ff,#7c4dff)"></div><span style="font-size:0.82rem;color:#aaa;">#6–10 — Supporting</span></div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<p style="font-size:0.78rem;font-weight:700;color:#f0f0f0;">USAGE GUIDELINES</p>', unsafe_allow_html=True)
    st.markdown("""<div style="background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:1rem;position:relative;overflow:hidden;">
<div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#ff3c78,#ffb700,#00e5ff,#a259ff)"></div>
<p style="font-size:0.7rem;color:#00e5b0;letter-spacing:2px;text-transform:uppercase;margin:0 0 0.4rem 0;">✔ Works great with</p>
<p style="color:#ccc;font-size:0.82rem;margin:0.2rem 0;border-bottom:1px solid #1f1f1f;padding-bottom:0.3rem;">● Public blogs &amp; articles</p>
<p style="color:#ccc;font-size:0.82rem;margin:0.2rem 0;border-bottom:1px solid #1f1f1f;padding-bottom:0.3rem;">● Wikipedia pages</p>
<p style="color:#ccc;font-size:0.82rem;margin:0.2rem 0;border-bottom:1px solid #1f1f1f;padding-bottom:0.3rem;">● Company websites</p>
<p style="color:#ccc;font-size:0.82rem;margin:0.2rem 0;padding-bottom:0.3rem;">● Documentation portals</p>
<p style="font-size:0.7rem;color:#ff3c78;letter-spacing:2px;text-transform:uppercase;margin:0.8rem 0 0.4rem 0;">✖ Doesn't support</p>
<p style="color:#ccc;font-size:0.82rem;margin:0.2rem 0;border-bottom:1px solid #1f1f1f;padding-bottom:0.3rem;">● Login-required portals</p>
<p style="color:#ccc;font-size:0.82rem;margin:0.2rem 0;border-bottom:1px solid #1f1f1f;padding-bottom:0.3rem;">● Paywalled content</p>
<p style="color:#ccc;font-size:0.82rem;margin:0.2rem 0;border-bottom:1px solid #1f1f1f;padding-bottom:0.3rem;">● Bot-blocking sites</p>
<p style="color:#ccc;font-size:0.82rem;margin:0.2rem 0;">● PDF / image-only pages</p>
</div>""", unsafe_allow_html=True)

    if st.session_state.kws:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p style="font-family:monospace;font-size:0.72rem;color:#ff3c78;letter-spacing:3px;text-transform:uppercase;font-weight:500;">Quick Stats</p>', unsafe_allow_html=True)
        scores = [float(k.get("score", 0)) for k in st.session_state.kws]
        avg = sum(scores) / len(scores) if scores else 0
        top_kw = st.session_state.kws[0]["keyword"] if st.session_state.kws else "—"
        st.markdown(f"""<div style="background:#161616;border:1px solid #2a2a2a;border-radius:12px;padding:0.9rem;display:flex;flex-direction:column;gap:0.6rem;">
            <div><div style="font-size:0.65rem;color:#555;letter-spacing:2px;text-transform:uppercase;font-family:'DM Mono',monospace;">Top Keyword</div>
            <div style="font-size:1rem;font-weight:800;color:#ff3c78;margin-top:0.15rem">{top_kw}</div></div>
            <div><div style="font-size:0.65rem;color:#555;letter-spacing:2px;text-transform:uppercase;font-family:'DM Mono',monospace;">Avg Score</div>
            <div style="font-size:1rem;font-weight:800;color:#ffb700;margin-top:0.15rem">{avg:.2f}</div></div>
            <div><div style="font-size:0.65rem;color:#555;letter-spacing:2px;text-transform:uppercase;font-family:'DM Mono',monospace;">Total Keywords</div>
            <div style="font-size:1rem;font-weight:800;color:#00e5ff;margin-top:0.15rem">{len(st.session_state.kws)}</div></div>
        </div>""", unsafe_allow_html=True)
