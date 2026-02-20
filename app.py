import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

st.set_page_config(page_title="LEXIS", page_icon="💜", layout="wide")

# ── Load API Key ────────────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing.")
    st.stop()

# ── Purple + Pink UI ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700;800&display=swap');

.stApp {
    background: #160f2e;  /* Deep purple */
    font-family: 'Space Grotesk', sans-serif;
}

/* Layout */
.block-container {
    max-width: 1150px;
    margin: auto;
    padding-top: 70px;
}

/* Header */
.hero-title {
    font-size: 4.5rem;
    font-weight: 800;
    color: #ff4fd8;   /* Pink headline */
    letter-spacing: -1px;
}

.hero-sub {
    font-size: 1.1rem;
    color: #ff9cf3;   /* Soft pink subtitle */
    margin-bottom: 45px;
}

/* Navigation */
div[role="radiogroup"] {
    justify-content: center;
    gap: 18px;
    margin-bottom: 35px;
}

div[role="radiogroup"] > label {
    background: #2a1f4f;
    padding: 12px 28px;
    border-radius: 999px;
    font-weight: 600;
    color: #ff9cf3 !important;
    border: 1px solid #ff4fd8;
}

/* Section Card */
.section-card {
    background: #211542;
    padding: 35px;
    border-radius: 20px;
    border: 1px solid #3b2c6b;
    margin-bottom: 35px;
}

/* Inputs */
textarea, input {
    background: #2a1f4f !important;
    border: 1px solid #ff4fd8 !important;
    border-radius: 14px !important;
    padding: 16px !important;
    color: #ffffff !important;
    font-size: 15px !important;
}

/* Button */
.stButton > button {
    background: #ff4fd8;
    color: #160f2e !important;
    border-radius: 14px !important;
    padding: 12px !important;
    font-weight: 700 !important;
    border: none !important;
}

/* Section Headings */
h3, h4 {
    color: #ff4fd8 !important;
}

/* Keywords */
.keyword-chip {
    display: inline-block;
    padding: 10px 20px;
    border-radius: 999px;
    margin: 8px;
    font-size: 14px;
    font-weight: 600;
    background: #2a1f4f;
    color: #ff9cf3;
    border: 1px solid #ff4fd8;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────
st.markdown('<div class="hero-title">LEXIS</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">AI-powered keyword extraction for modern web content.</div>', unsafe_allow_html=True)

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
    if st.button("Extract Keywords"):
        if text_input.strip():
            with st.spinner("Analyzing..."):
                st.session_state.kws=extract_keywords(text_input)

elif mode=="🌐 URL Input":
    url_input=st.text_input("",placeholder="https://example.com/article")
    if st.button("Extract from URL"):
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
    st.markdown("### Extracted Keywords")
    chips=""
    for k in st.session_state.kws:
        chips+=f'<span class="keyword-chip">{k["keyword"]}</span>'
    st.markdown(chips,unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
