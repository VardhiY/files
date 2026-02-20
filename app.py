import streamlit as st
from groq import Groq
import json
import re
import urllib.request

# ── CONFIG ─────────────────────────
st.set_page_config(
    page_title="LEXIS AI",
    page_icon="🤖",
    layout="wide"
)

# ── LOAD KEY ───────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("GROQ_API_KEY missing.")
    st.stop()

# ── CSS ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
}

/* Remove top spacing */
.block-container {
    padding-top: 1rem;
}

/* Title */
.main-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 4rem;
    text-align: center;
    font-weight: 900;
    background: linear-gradient(90deg,#00ffff,#ff00ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.subtitle {
    text-align: center;
    font-size: 1.2rem;
    margin-bottom: 2rem;
    color: #cfd8ff;
}

/* Big Inputs */
textarea, input {
    background: rgba(255,255,255,0.1) !important;
    border: 2px solid rgba(0,255,255,0.5) !important;
    border-radius: 15px !important;
    color: white !important;
    padding: 1.2rem !important;
    font-size: 1.1rem !important;
}

/* Button */
.stButton > button {
    background: linear-gradient(90deg,#00ffff,#ff00ff);
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
    background: linear-gradient(90deg,#00ffff,#ff00ff);
    color: black;
    font-weight: 700;
}

/* Guidelines Panel */
.guidelines {
    background: rgba(0,0,0,0.3);
    padding: 1.5rem;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.2);
}

.guidelines h2 {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.6rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ─────────────────────────
st.markdown('<div class="main-title">LEXIS AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Next-Generation Intelligent Keyword Engine</div>', unsafe_allow_html=True)

# ── TWO COLUMN DASHBOARD ───────────
left, right = st.columns([3,1])

# ── LEFT SIDE (CENTER WORK AREA) ───
with left:

    st.markdown("### Choose Mode")

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

    # Output
    if "kws" in st.session_state:
        st.markdown("### 🚀 Extracted Keywords")
        chips = ""
        for k in st.session_state.kws:
            chips += f'<span class="keyword-chip">{k["keyword"]}</span>'
        st.markdown(chips, unsafe_allow_html=True)

# ── RIGHT SIDE (PERMANENT GUIDELINES) ──────
with right:
    st.markdown('<div class="guidelines">', unsafe_allow_html=True)
    st.markdown("<h2>📘 Guidelines</h2>", unsafe_allow_html=True)
    st.write("✔ Public blogs")
    st.write("✔ Wikipedia pages")
    st.write("✔ Company sites")
    st.write("✔ Documentation sites")
    st.markdown("---")
    st.write("✖ PDF files")
    st.write("✖ Image links")
    st.write("✖ Paywalled content")
    st.write("✖ Login required pages")
    st.markdown('</div>', unsafe_allow_html=True)
