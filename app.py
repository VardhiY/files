import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

st.set_page_config(page_title="LEXIS", page_icon="🖤", layout="wide")

# ── Load API Key ────────────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing.")
    st.stop()

# ── Ultra Bold Gold UI ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Montserrat:wght@400;600;700;800&display=swap');

.stApp {
    background: #070708;
    color: #ffffff;
    font-family: 'Montserrat', sans-serif;
}

/* Layout */
.block-container {
    max-width: 1250px;
    margin: auto;
    padding-top: 90px;
}

/* Logo + Title */
.hero-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 18px;
}

.logo-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: radial-gradient(circle,#f5d97b,#c9a227);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 30px;
    color: black;
    font-weight: 800;
    box-shadow: 0 0 25px rgba(201,162,39,0.7);
}

.hero-title {
    font-family: 'Oswald', sans-serif;
    font-size: 5rem;
    letter-spacing: 4px;
    background: linear-gradient(90deg,#f5d97b,#c9a227,#f5d97b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-sub {
    text-align: center;
    font-size: 1.2rem;
    color: #d4af37;
    margin-top: 20px;
    margin-bottom: 70px;
    letter-spacing: 2px;
}

/* Navigation Pills */
div[role="radiogroup"] {
    justify-content: center;
    gap: 25px;
    margin-bottom: 60px;
}

div[role="radiogroup"] > label {
    background: #101014;
    padding: 16px 40px;
    border-radius: 999px;
    font-weight: 700;
    color: #f5d97b !important;
    border: 2px solid #c9a227;
    box-shadow: inset 0 0 8px rgba(201,162,39,0.4);
    transition: 0.3s ease;
}

div[role="radiogroup"] > label:hover {
    box-shadow: 0 0 20px #c9a227;
}

/* Section Card */
.section-card {
    background: #0f0f12;
    padding: 50px;
    border-radius: 28px;
    border: 2px solid #c9a227;
    margin-bottom: 60px;
    box-shadow:
        0 0 40px rgba(201,162,39,0.15),
        inset 0 0 30px rgba(201,162,39,0.1);
}

/* Inputs */
textarea, input {
    background: #0c0c10 !important;
    border: 2px solid #c9a227 !important;
    border-radius: 20px !important;
    padding: 22px !important;
    color: #ffffff !important;
    font-size: 16px !important;
}

/* Button */
.stButton > button {
    background: linear-gradient(90deg,#f5d97b,#c9a227);
    color: #000 !important;
    border-radius: 20px !important;
    padding: 18px !important;
    font-weight: 800 !important;
    letter-spacing: 1px;
    border: none !important;
    box-shadow: 0 0 20px rgba(201,162,39,0.6);
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 0 30px rgba(201,162,39,0.9);
}

/* Headings */
h3, h4 {
    color: #f5d97b !important;
    margin-bottom: 25px;
    font-weight: 700;
}

/* Keyword Chips */
.keyword-chip {
    display: inline-block;
    padding: 14px 30px;
    border-radius: 999px;
    margin: 15px;
    font-size: 15px;
    font-weight: 700;
    background: #111115;
    color: #f5d97b;
    border: 2px solid #c9a227;
    box-shadow: inset 0 0 10px rgba(201,162,39,0.3);
    transition: 0.3s ease;
}

.keyword-chip:hover {
    box-shadow: 0 0 25px #c9a227;
    transform: translateY(-3px);
}
</style>
""", unsafe_allow_html=True)

# ── Hero Section ─────────────────────────────────────────
st.markdown("""
<div class="hero-wrapper">
    <div class="logo-icon">L</div>
    <div class="hero-title">LEXIS</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-sub">ELITE AI KEYWORD ENGINE</div>', unsafe_allow_html=True)

# ── Keyword Extraction ─────────────────────────────
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

# ── URL Extractor ─────────────────────────────────
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts=[]
        self.skip_tags={'script','style','nav','footer','header'}
        self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in self.skip_tags: self.skip+=1
    def handle_endtag(self,tag):
        if tag in self.skip_tags and self.skip>0: self.skip-=1
    def handle_data(self,data):
        if self.skip==0:
            stripped=data.strip()
            if stripped: self.text_parts.append(stripped)
    def get_text(self):
        return ' '.join(self.text_parts)

def fetch_url_content(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=15) as resp:
        html=resp.read().decode('utf-8',errors='ignore')
    parser=TextExtractor()
    parser.feed(html)
    return parser.get_text()

# ── Navigation ─────────────────────────────────────
mode = st.radio("",["📄 TEXT INPUT","🌐 URL INPUT","📘 GUIDELINES"],horizontal=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)

if mode=="📄 TEXT INPUT":
    text_input=st.text_area("",height=240,placeholder="PASTE YOUR CONTENT HERE...")
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

st.markdown('</div>', unsafe_allow_html=True)

if "kws" in st.session_state:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### EXTRACTED KEYWORDS")
    chips=""
    for k in st.session_state.kws:
        chips+=f'<span class="keyword-chip">{k["keyword"]}</span>'
    st.markdown(chips,unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
