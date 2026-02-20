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

# ── Black + Gold Luxury UI ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap');

.stApp {
    background: #0b0b0f;
    color: #f5f5f5;
    font-family: 'Montserrat', sans-serif;
}

/* Layout */
.block-container {
    max-width: 1200px;
    margin: auto;
    padding-top: 70px;
}

/* Header */
.hero-title {
    font-size: 4.5rem;
    font-weight: 800;
    letter-spacing: -2px;
    background: linear-gradient(90deg,#f5d97b,#c9a227,#f5d97b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-sub {
    font-size: 1.1rem;
    margin-top: 12px;
    margin-bottom: 45px;
    color: #c9a227;
    letter-spacing: 1px;
}

/* Navigation */
div[role="radiogroup"] {
    justify-content: center;
    gap: 20px;
    margin-bottom: 40px;
}

div[role="radiogroup"] > label {
    background: #111117;
    padding: 12px 30px;
    border-radius: 999px;
    font-weight: 600;
    color: #f5d97b !important;
    border: 1px solid #c9a227;
}

/* Section Card */
.section-card {
    background: #121218;
    padding: 40px;
    border-radius: 20px;
    border: 1px solid #2a2a35;
    margin-bottom: 40px;
}

/* Inputs */
textarea, input {
    background: #0f0f14 !important;
    border: 1px solid #c9a227 !important;
    border-radius: 14px !important;
    padding: 18px !important;
    color: #ffffff !important;
    font-size: 15px !important;
}

/* Button */
.stButton > button {
    background: linear-gradient(90deg,#f5d97b,#c9a227);
    color: #000 !important;
    border-radius: 14px !important;
    padding: 14px !important;
    font-weight: 700 !important;
    border: none !important;
}

/* Section Headings */
h3, h4 {
    color: #f5d97b !important;
}

/* Keywords */
.keyword-chip {
    display: inline-block;
    padding: 10px 22px;
    border-radius: 999px;
    margin: 10px;
    font-size: 14px;
    font-weight: 600;
    background: #111117;
    color: #f5d97b;
    border: 1px solid #c9a227;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────
st.markdown('<div class="hero-title">LEXIS</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">LUXURY AI KEYWORD EXTRACTION</div>', unsafe_allow_html=True)

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
mode = st.radio("",["📄 Text Input","🌐 URL Input","📘 URL Guidelines"],horizontal=True)

st.markdown('<div class="section-card">', unsafe_allow_html=True)

if mode=="📄 Text Input":
    text_input=st.text_area("",height=220,placeholder="Paste your content here...")
    if st.button("EXTRACT KEYWORDS"):
        if text_input.strip():
            with st.spinner("Analyzing..."):
                st.session_state.kws=extract_keywords(text_input)

elif mode=="🌐 URL Input":
    url_input=st.text_input("",placeholder="https://example.com/article")
    if st.button("EXTRACT FROM URL"):
        if url_input.startswith("http"):
            with st.spinner("Fetching..."):
                content=fetch_url_content(url_input)
                st.session_state.kws=extract_keywords(content)

elif mode=="📘 URL Guidelines":
    st.markdown("### ✔ Supported")
    st.write("Public blogs, news, Wikipedia, company pages.")
    st.markdown("### ✖ Not Supported")
    st.write("PDF, Word, Excel, images, paywalled content.")
    st.markdown("### 🔒 Restricted")
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
