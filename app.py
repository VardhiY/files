import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

# ── PAGE CONFIG ─────────────────────────────
st.set_page_config(
    page_title="LEXIS AI",
    page_icon="🤖",
    layout="wide"
)

# ── LOAD API KEY ────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing.")
    st.stop()

# ── FUTURISTIC AI CSS ───────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800&family=Inter:wght@400;600&display=swap');

.stApp {
    background:
        radial-gradient(circle at 20% 20%, rgba(0,255,255,0.25), transparent 40%),
        radial-gradient(circle at 80% 80%, rgba(138,43,226,0.3), transparent 45%),
        linear-gradient(135deg, #0a0f1f 0%, #050816 50%, #000000 100%);
    background-attachment: fixed;
    color: white;
}

/* HEADER */
.main-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 3.8rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 3px;
    margin-bottom: 0.5rem;
}

.subtitle {
    text-align: center;
    font-size: 1.1rem;
    color: #b0c4ff;
    margin-bottom: 2.5rem;
    font-weight: 600;
}

/* CENTER NAV */
div[role="radiogroup"] {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 2rem;
}

/* GLASS PANELS */
.glass {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0,255,255,0.2);
    padding: 1.5rem;
    border-radius: 18px;
    box-shadow: 0 0 20px rgba(0,255,255,0.1);
}

/* INPUTS */
textarea, input {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(0,255,255,0.4) !important;
    border-radius: 16px !important;
    color: white !important;
    padding: 1rem !important;
    font-weight: 500 !important;
}

textarea:focus, input:focus {
    border: 1px solid #00ffff !important;
    box-shadow: 0 0 18px rgba(0,255,255,0.6);
}

/* BUTTON */
.stButton > button {
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    border-radius: 40px !important;
    padding: 0.8rem 2.5rem !important;
    font-weight: 700 !important;
    border: none !important;
    color: black !important;
    transition: 0.3s ease;
    letter-spacing: 1px;
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 25px rgba(0,255,255,0.7);
}

/* KEYWORD CHIPS */
.keyword-chip {
    display: inline-block;
    padding: 0.6rem 1.4rem;
    margin: 0.4rem;
    border-radius: 40px;
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    color: black;
    font-weight: 700;
    transition: 0.2s ease;
}

.keyword-chip:hover {
    transform: scale(1.08);
}

/* REMOVE EXTRA GAPS */
.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────
st.markdown('<div class="main-title">LEXIS AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Next-Gen Intelligent Keyword Engine</div>', unsafe_allow_html=True)

# ── KEYWORD FUNCTION ─────────────────────
def extract_keywords(text):
    prompt = f"""
Extract top 10 important keywords from the text.
Return ONLY JSON:
[{{"keyword":"...","score":0.00}},...]

TEXT:
{text[:6000]}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=800
    )
    cleaned = re.sub(r'```json|```', '', response.choices[0].message.content.strip())
    return json.loads(cleaned)

# ── NAVIGATION ───────────────────────────
mode = st.radio("",["📄 TEXT INPUT","🌐 URL INPUT","📘 GUIDELINES"],horizontal=True)

# ── TEXT MODE ────────────────────────────
if mode == "📄 TEXT INPUT":
    text_input = st.text_area("", height=220, placeholder="Paste your content here...")
    if st.button("EXTRACT KEYWORDS"):
        if text_input.strip():
            with st.spinner("AI analyzing..."):
                st.session_state.kws = extract_keywords(text_input)

# ── URL MODE ─────────────────────────────
elif mode == "🌐 URL INPUT":
    url_input = st.text_input("", placeholder="https://example.com/article")
    if st.button("EXTRACT FROM URL"):
        if url_input.startswith("http"):
            req = urllib.request.Request(url_input, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
            st.session_state.kws = extract_keywords(html)

# ── GUIDELINES ───────────────────────────
elif mode == "📘 GUIDELINES":
    st.markdown('<div class="glass"><b>✔ Supported:</b><br>Public blogs, Wikipedia, company pages.</div>', unsafe_allow_html=True)
    st.markdown('<div class="glass"><b>✖ Not Supported:</b><br>PDF, images, paywalled content.</div>', unsafe_allow_html=True)

# ── RESULTS ──────────────────────────────
if "kws" in st.session_state:
    st.markdown("### 🚀 Extracted Keywords")
    chips = ""
    for k in st.session_state.kws:
        chips += f'<span class="keyword-chip">{k["keyword"]}</span>'
    st.markdown(chips, unsafe_allow_html=True)
