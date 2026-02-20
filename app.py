import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

# ── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title="LEXIS - AI Keyword Finder",
    page_icon="🔍",
    layout="centered"
)

# ── Load API Key ────────────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing in Streamlit secrets.")
    st.stop()

# ── Professional CSS ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');

.stApp {
    background: #0b0f1a;
    color: #e8eaf2;
    font-family: 'Inter', sans-serif;
}

.block-container {
    padding-top: 2rem;
}

/* Header */
.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 3.2rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(180deg,#f5d97b,#c9a227);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.subtitle {
    text-align: center;
    color: #9aa3b2;
    font-size: 0.95rem;
    margin-bottom: 2.5rem;
}

/* Inputs */
textarea, input {
    background-color: #121826 !important;
    border: 1px solid #2a3244 !important;
    border-radius: 12px !important;
    color: #e8eaf2 !important;
}

/* Buttons */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg,#c9a227,#f5d97b);
    color: #000 !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 0.75rem !important;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(201,162,39,0.3);
}

/* Radio Horizontal */
div[role="radiogroup"] {
    justify-content: center;
    gap: 2rem;
}

/* Keyword Chips */
.keyword-chip {
    display: inline-block;
    padding: 0.45rem 1rem;
    border-radius: 999px;
    font-size: 0.85rem;
    margin: 0.35rem;
    background: rgba(201,162,39,0.12);
    border: 1px solid rgba(201,162,39,0.5);
    color: #f5d97b;
    font-weight: 500;
    transition: all 0.2s ease;
}

.keyword-chip:hover {
    background: rgba(201,162,39,0.2);
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────
st.markdown('<div class="main-title">LEXIS</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-powered semantic keyword extraction for text and web content.</div>',
    unsafe_allow_html=True
)

# ── Keyword Extraction ─────────────────────────────────────
def extract_keywords(text):
    prompt = f"""
Extract top 10 important keywords from the text.
Return ONLY JSON format:
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

# ── URL Extractor ──────────────────────────────────────────
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script','style','nav','footer','header'}
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip > 0:
            self.skip -= 1

    def handle_data(self, data):
        if self.skip == 0:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)

    def get_text(self):
        return ' '.join(self.text_parts)

def fetch_url_content(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    parser = TextExtractor()
    parser.feed(html)
    return parser.get_text()

# ── Navigation ─────────────────────────────────────────────
mode = st.radio(
    "",
    ["📄 Text Input", "🌐 URL Input", "📘 URL Guidelines"],
    horizontal=True
)

# ── TEXT INPUT ─────────────────────────────────────────────
if mode == "📄 Text Input":
    text_input = st.text_area("", height=200, placeholder="Paste article, blog, or content here...")
    if st.button("Extract Keywords"):
        if text_input.strip():
            with st.spinner("Analyzing content..."):
                st.session_state.kws = extract_keywords(text_input)

# ── URL INPUT ──────────────────────────────────────────────
elif mode == "🌐 URL Input":
    url_input = st.text_input("", placeholder="https://example.com/article")
    if st.button("Extract from URL"):
        if url_input.startswith("http"):
            with st.spinner("Fetching and analyzing webpage..."):
                content = fetch_url_content(url_input)
                st.session_state.kws = extract_keywords(content)

# ── URL GUIDELINES ─────────────────────────────────────────
elif mode == "📘 URL Guidelines":

    st.markdown("## 📘 URL Guidelines")
    st.markdown("This tool extracts visible text from publicly accessible HTML pages only.")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✔ Supported")
        st.success("""
• Public blog posts  
• News articles (no paywall)  
• Wikipedia pages  
• Company & product pages  
• Documentation sites  
• Government & NGO pages  
        """)

    with col2:
        st.markdown("### ✖ Not Supported")
        st.error("""
• PDF files  
• Word / Excel / PowerPoint files  
• Image links (.jpg, .png, .svg)  
• Paywalled content  
        """)

    st.markdown("---")

    st.markdown("### 🔒 Restricted Pages")
    st.warning("""
• Login-required pages  
• Google Docs / Drive links  
• Private dashboards  
• Social media requiring authentication  
    """)

# ── Results ────────────────────────────────────────────────
if "kws" in st.session_state:
    st.markdown("---")
    st.markdown("### 🔎 Extracted Keywords")

    chips = ""
    for k in st.session_state.kws:
        chips += f'<span class="keyword-chip">{k["keyword"]}</span>'

    st.markdown(chips, unsafe_allow_html=True)
