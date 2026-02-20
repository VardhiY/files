import streamlit as st
from groq import Groq
import json
import re
import urllib.request

# ── PAGE CONFIG ─────────────────────────
st.set_page_config(
    page_title="LEXIS AI",
    page_icon="🤖",
    layout="wide"
)

# ── LOAD API KEY ───────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing.")
    st.stop()

# ── STYLING ─────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;600;700&display=swap');

.stApp {
    background:
        radial-gradient(circle at 20% 20%, rgba(0,255,255,0.25), transparent 40%),
        radial-gradient(circle at 80% 80%, rgba(138,43,226,0.3), transparent 45%),
        linear-gradient(135deg, #0a0f1f 0%, #050816 50%, #000000 100%);
    background-attachment: fixed;
    color: white;
}

.block-container {
    padding-top: 1.5rem;
}

/* Title */
.main-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 4rem;
    text-align: center;
    font-weight: 900;
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    text-align: center;
    font-size: 1.2rem;
    margin-bottom: 2rem;
    color: #b0c4ff;
}

/* Inputs */
textarea, input {
    background: rgba(255,255,255,0.08) !important;
    border: 2px solid rgba(0,255,255,0.6) !important;
    border-radius: 18px !important;
    color: white !important;
    padding: 1.4rem !important;
    font-size: 1.1rem !important;
}

/* Button */
.stButton > button {
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    border-radius: 40px !important;
    padding: 0.9rem 2.5rem !important;
    font-weight: 700 !important;
    border: none !important;
    color: black !important;
}

/* Keyword Chips */
.keyword-chip {
    display: inline-block;
    padding: 0.6rem 1.3rem;
    margin: 0.4rem;
    border-radius: 50px;
    background: linear-gradient(90deg,#00ffff,#8a2be2);
    color: black;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────
st.markdown('<div class="main-title">LEXIS AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Next-Generation Intelligent Keyword Engine</div>', unsafe_allow_html=True)

# ── TWO COLUMN LAYOUT ──────────────
left, right = st.columns([2.5, 1])

# ── LEFT COLUMN (WORK AREA ONLY) ───
with left:

    mode = st.radio("", ["📄 TEXT INPUT", "🌐 URL INPUT"], horizontal=True)

    if mode == "📄 TEXT INPUT":
        text_input = st.text_area("", height=320, placeholder="Paste your content here...")

        if st.button("EXTRACT KEYWORDS"):
            if text_input.strip():
                with st.spinner("AI analyzing..."):
                    prompt = f"""
Extract top 10 important keywords from the text.
Return ONLY JSON:
[{{"keyword":"...","score":0.00}},...]

TEXT:
{text_input[:6000]}
"""
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=800
                    )
                    cleaned = re.sub(r'```json|```', '', response.choices[0].message.content.strip())
                    st.session_state.kws = json.loads(cleaned)

    elif mode == "🌐 URL INPUT":
        url_input = st.text_input("", placeholder="https://example.com/article")

        if st.button("EXTRACT FROM URL"):
            if url_input.startswith("http"):
                req = urllib.request.Request(url_input, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')

                prompt = f"""
Extract top 10 important keywords from the text.
Return ONLY JSON:
[{{"keyword":"...","score":0.00}},...]

TEXT:
{html[:6000]}
"""
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=800
                )
                cleaned = re.sub(r'```json|```', '', response.choices[0].message.content.strip())
                st.session_state.kws = json.loads(cleaned)

    if "kws" in st.session_state:
        st.markdown("### 🚀 Extracted Keywords")
        chips = ""
        for k in st.session_state.kws:
            chips += f'<span class="keyword-chip">{k["keyword"]}</span>'
        st.markdown(chips, unsafe_allow_html=True)

# ── RIGHT COLUMN (GUIDELINES ONLY — NO INPUTS HERE) ───────
with right:

    st.markdown("""
    <div style="
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(0,255,255,0.3);
        padding: 1.8rem;
        border-radius: 20px;
        backdrop-filter: blur(10px);
    ">
    """, unsafe_allow_html=True)

    st.markdown("""
    <h2 style="
        font-family: 'Orbitron', sans-serif;
        font-size: 1.6rem;
        font-weight: 800;
        background: linear-gradient(90deg,#00ffff,#8a2be2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.2rem;
    ">
    📘 GUIDELINES
    </h2>
    """, unsafe_allow_html=True)

    st.write("✔ Public blogs")
    st.write("✔ Wikipedia pages")
    st.write("✔ Company sites")
    st.write("✔ Documentation sites")

    st.markdown("---")

    st.write("✖ PDF files")
    st.write("✖ Image links")
    st.write("✖ Paywalled content")
    st.write("✖ Login required pages")

    st.markdown("</div>", unsafe_allow_html=True)
