import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

# ─────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────
st.set_page_config(page_title="LEXIS", page_icon="🖤", layout="wide")

# ─────────────────────────────────────────
# Load API Key
# ─────────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing in Streamlit secrets.")
    st.stop()

# ─────────────────────────────────────────
# Premium Black + Gold CSS (UPDATED BACKGROUND)
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@600;700&family=Montserrat:wght@400;600;700;800&display=swap');

/* 🌟 NEW LUXURY BACKGROUND */
.stApp {
    background:
        radial-gradient(circle at 20% 20%, rgba(201,162,39,0.08), transparent 40%),
        radial-gradient(circle at 80% 70%, rgba(201,162,39,0.06), transparent 40%),
        linear-gradient(135deg, #0a0a0f, #050507 60%);
    color: #ffffff;
    font-family: 'Montserrat', sans-serif;
}

.block-container {
    max-width: 1100px;
    margin: auto;
    padding-top: 40px;
}

.element-container {
    margin-bottom: 0rem !important;
}

/* HERO */
.hero-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 14px;
    margin-bottom: 5px;
}

.logo-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: radial-gradient(circle,#f5d97b,#c9a227);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: black;
    font-weight: 800;
    box-shadow: 0 0 15px rgba(201,162,39,0.6);
}

.hero-title {
    font-family: 'Oswald', sans-serif;
    font-size: 4rem;
    letter-spacing: 3px;
    background: linear-gradient(90deg,#f5d97b,#c9a227,#f5d97b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-sub {
    text-align: center;
    font-size: 0.9rem;
    color: #d4af37;
    margin-bottom: 20px;
    letter-spacing: 2px;
}

/* NAVIGATION */
div[role="radiogroup"] {
    justify-content: center !important;
    gap: 20px;
    margin-bottom: 25px;
}

div[role="radiogroup"] > label {
    background: #101014;
    padding: 10px 26px;
    border-radius: 999px;
    font-weight: 700;
    color: #f5d97b !important;
    border: 2px solid #c9a227;
}

/* INPUTS */
textarea, input {
    background: #0c0c10 !important;
    border: 2px solid #c9a227 !important;
    border-radius: 14px !important;
    padding: 14px !important;
    color: #ffffff !important;
}

/* BUTTON */
.stButton > button {
    background: linear-gradient(90deg,#f5d97b,#c9a227);
    color: #000 !important;
    border-radius: 14px !important;
    padding: 10px !important;
    font-weight: 800 !important;
    border: none !important;
}

/* RESULT TITLE */
.result-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #f5d97b;
    margin-top: 25px;
    margin-bottom: 10px;
}

/* KEYWORD CHIPS */
.keyword-chip {
    display: inline-block;
    padding: 8px 18px;
    border-radius: 999px;
    margin: 6px;
    font-size: 13px;
    font-weight: 700;
    background: #111115;
    color: #f5d97b;
    border: 2px solid #c9a227;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# Hero Section
# ─────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
    <div class="logo-icon">L</div>
    <div class="hero-title">LEXIS</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-sub">ELITE AI KEYWORD ENGINE</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# Keyword Extraction Function
# ─────────────────────────────────────────
def extract_keywords(text):
    prompt = f"""
Extract top 10 important keywords from the text.
Return ONLY JSON:
[{{"keyword":"...","score":0.00}}]

TEXT:
{text[:6000]}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2,
        max_tokens=800
    )
    cleaned = re.sub(r'```json|```','',response.choices[0].message.content.strip())
    return json.loads(cleaned)

# ─────────────────────────────────────────
# URL Extractor
# ─────────────────────────────────────────
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts=[]
        self.skip_tags={'script','style','nav','footer','header'}
        self.skip=0

    def handle_starttag(self,tag,attrs):
        if tag in self.skip_tags:
            self.skip+=1

    def handle_endtag(self,tag):
        if tag in self.skip_tags and self.skip>0:
            self.skip-=1

    def handle_data(self,data):
        if self.skip==0:
            stripped=data.strip()
            if stripped:
                self.text_parts.append(stripped)

    def get_text(self):
        return ' '.join(self.text_parts)

def fetch_url_content(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=15) as resp:
        html=resp.read().decode('utf-8',errors='ignore')
    parser=TextExtractor()
    parser.feed(html)
    return parser.get_text()

# ─────────────────────────────────────────
# Navigation
# ─────────────────────────────────────────
mode = st.radio("",["📄 TEXT INPUT","🌐 URL INPUT","📘 GUIDELINES"],horizontal=True)

# ─────────────────────────────────────────
# Sections
# ─────────────────────────────────────────
if mode=="📄 TEXT INPUT":
    text_input=st.text_area("",height=220,placeholder="PASTE YOUR CONTENT HERE...")
    if st.button("EXTRACT KEYWORDS"):
        if text_input.strip():
            with st.spinner("Analyzing..."):
                st.session_state.kws=extract_keywords(text_input)

elif mode=="🌐 URL INPUT":
    url_input=st.text_input("",placeholder="https://example.com/article")
    if st.button("EXTRACT FROM URL"):
        if url_input.startswith("http"):
            with st.spinner("Fetching..."):
                content=fetch_url_content(url_input)
                st.session_state.kws=extract_keywords(content)

elif mode=="📘 GUIDELINES":
    st.markdown("### ✔ SUPPORTED")
    st.write("Public blogs, news, Wikipedia, company pages.")
    st.markdown("### ✖ NOT SUPPORTED")
    st.write("PDF, Word, Excel, images, paywalled content.")
    st.markdown("### 🔒 RESTRICTED")
    st.write("Login-required pages and private dashboards.")

# ─────────────────────────────────────────
# Results
# ─────────────────────────────────────────
if "kws" in st.session_state:
    st.markdown('<div class="result-title">EXTRACTED KEYWORDS</div>', unsafe_allow_html=True)
    chips=""
    for k in st.session_state.kws:
        chips+=f'<span class="keyword-chip">{k["keyword"]}</span>'
    st.markdown(chips,unsafe_allow_html=True)
