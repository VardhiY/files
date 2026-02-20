import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

st.set_page_config(page_title="LEXIS", page_icon="🔮", layout="wide")

# ── Load API Key ────────────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing.")
    st.stop()

# ── Elegant Muted Purple UI ─────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Manrope:wght@400;500;600&display=swap');

.stApp {
    background: #1e1b2e;   /* Soft deep violet */
    color: #f3f4f6;
    font-family: 'Manrope', sans-serif;
}

.block-container {
    max-width: 1050px;
    margin: auto;
    padding-top: 60px;
}

/* Header */
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 3.8rem;
    font-weight: 700;
    letter-spacing: -1px;
    color: #e9d5ff;
}

.hero-sub {
    font-size: 1.05rem;
    margin-top: 8px;
    margin-bottom: 40px;
    color: #c4b5fd;
}

/* Navigation */
div[role="radiogroup"] {
    justify-content: center;
    gap: 16px;
    margin-bottom: 30px;
}

div[role="radiogroup"] > label {
    background: #2a2542;
    padding: 10px 22px;
    border-radius: 999px;
    font-weight: 500;
    font-size: 14px;
    color: #e9d5ff !important;
}

/* Section Card */
.section-card {
    background: #2a2542;
    padding: 30px;
    border-radius: 16px;
    margin-bottom: 30px;
    border: 1px solid #3f3a60;
}

/* Inputs */
textarea, input {
    background: #1f1a34 !important;
    border: 1px solid #3f3a60 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    color: #ffffff !important;
    font-size: 14px !important;
}

/* Button */
.stButton > button {
    background: #7c3aed;
    color: white !important;
    border-radius: 12px !important;
    padding: 12px !important;
    font-weight: 600 !important;
    border: none !important;
}

/* Keywords */
.keyword-chip {
    display: inline-block;
    padding: 8px 18px;
    border-radius: 999px;
    margin: 8px;
    font-size: 13px;
    font-weight: 500;
    background: #3f3a60;
    color: #e9d5ff;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────
st.markdown('<div class="hero-title">LEXIS</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Refined AI-powered keyword extraction for modern web content.</div>', unsafe_allow_html=True)

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
