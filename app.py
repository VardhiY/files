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

# ── PREMIUM AI CSS ──────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;800;900&family=Inter:wght@400;600;700&display=swap');

.stApp {
    background:
        radial-gradient(circle at 20% 20%, rgba(0,255,255,0.25), transparent 40%),
        radial-gradient(circle at 80% 80%, rgba(138,43,226,0.3), transparent 45%),
        linear-gradient(135deg, #0a0f1f 0%, #050816 50%, #000000 100%);
    background-attachment: fixed;
    color: white;
}

/* MAIN TITLE */
.main-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 4.5rem;
    font-weight: 900;
    text-align: center;
    background: linear-gradient(90deg,#00ffff,#8a2be2,#00ffff);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 4px;
    margin-bottom: 0.5rem;
    animation: shine 4s linear infinite;
}

@keyframes shine {
    to { background-position: 200% center; }
}

/* Decorative Line Under Title */
.title-line {
    width: 220px;
    height: 4px;
    margin: 0 auto 2rem auto;
    border-radius: 5px;
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    box-shadow: 0 0 20px rgba(0,255,255,0.8);
}

/* Subtitle */
.subtitle {
    text-align: center;
    font-size: 1.4rem;
    color: #b0c4ff;
    margin-bottom: 3rem;
    font-weight: 700;
}

/* NAVIGATION TEXT (VISIBLE FIXED VERSION) */
div[role="radiogroup"] label {
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 800 !important;
    font-size: 1.3rem !important;
    background: linear-gradient(90deg,#00ffff,#8a2be2,#00ffff);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: initial !important; /* FIX */
    color: #00ffff !important;
    animation: shine 4s linear infinite;
}

/* NAV CONTAINER */
div[role="radiogroup"] {
    display: flex;
    justify-content: center;
    gap: 4rem;
    margin-bottom: 2.5rem;
    position: relative;
}

/* Decorative Line Under NAV */
div[role="radiogroup"]::after {
    content: "";
    position: absolute;
    bottom: -12px;
    left: 50%;
    transform: translateX(-50%);
    width: 300px;
    height: 4px;
    border-radius: 5px;
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    box-shadow: 0 0 25px rgba(0,255,255,0.8);
}

/* SECTION HEADINGS */
.section-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.2rem;
    font-weight: 900;
    margin-top: 3rem;
    margin-bottom: 1rem;
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Decorative Line Under Section */
.section-line {
    width: 180px;
    height: 4px;
    margin-bottom: 2rem;
    border-radius: 5px;
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    box-shadow: 0 0 20px rgba(0,255,255,0.6);
}

/* TEXT AREA */
textarea {
    background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)) !important;
    border: 2px solid rgba(0,255,255,0.6) !important;
    border-radius: 22px !important;
    color: white !important;
    padding: 1.4rem !important;
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    box-shadow:
        inset 0 0 20px rgba(0,255,255,0.1),
        0 0 25px rgba(0,255,255,0.15);
}

textarea:focus {
    border: 2px solid #00ffff !important;
    box-shadow:
        inset 0 0 25px rgba(0,255,255,0.2),
        0 0 35px rgba(0,255,255,0.5);
}

/* BUTTON */
.stButton > button {
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    border-radius: 40px !important;
    padding: 1rem 3rem !important;
    font-weight: 800 !important;
    font-size: 1.1rem !important;
    border: none !important;
    color: black !important;
}

/* KEYWORD CHIPS */
.keyword-chip {
    display: inline-block;
    padding: 0.8rem 1.8rem;
    margin: 0.5rem;
    border-radius: 50px;
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    color: black;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────────
st.markdown('<div class="main-title">LEXIS AI</div>', unsafe_allow_html=True)
st.markdown('<div class="title-line"></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Next-Generation Intelligent Keyword Engine</div>', unsafe_allow_html=True)

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
    text_input = st.text_area("", height=250, placeholder="Paste your content here...")
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
    st.markdown('<div class="section-title">SUPPORTED</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
    st.write("Public blogs, Wikipedia, company pages.")

    st.markdown('<div class="section-title">NOT SUPPORTED</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
    st.write("PDF, images, paywalled content.")

# ── RESULTS ──────────────────────────────
if "kws" in st.session_state:
    st.markdown('<div class="section-title">EXTRACTED KEYWORDS</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-line"></div>', unsafe_allow_html=True)
    chips = ""
    for k in st.session_state.kws:
        chips += f'<span class="keyword-chip">{k["keyword"]}</span>'
    st.markdown(chips, unsafe_allow_html=True)
