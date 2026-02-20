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
    layout="wide"
)

# ── Load API Key ────────────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing in Streamlit secrets.")
    st.stop()

# ── Advanced Mobile-App Style UI ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

.stApp {
    background: linear-gradient(135deg, #5f6bff, #b06ab3);
    font-family: 'Poppins', sans-serif;
}

/* Main White Container */
.block-container {
    max-width: 950px;
    margin: 3rem auto;
    padding: 2.5rem 3rem;
    background: #ffffff;
    border-radius: 28px;
    box-shadow: 0 40px 80px rgba(0,0,0,0.25);
}

/* Header */
.main-title {
    font-size: 3rem;
    font-weight: 700;
    text-align: center;
    color: #5f6bff;
    margin-bottom: 0.3rem;
}

.subtitle {
    text-align: center;
    color: #666;
    font-size: 1rem;
    margin-bottom: 2.5rem;
}

/* Navigation Pills */
div[role="radiogroup"] {
    justify-content: center;
    gap: 1.5rem;
}

div[role="radiogroup"] > label {
    background: #f3f4ff;
    padding: 0.6rem 1.2rem;
    border-radius: 999px;
    font-weight: 500;
    transition: 0.2s;
}

div[role="radiogroup"] > label:hover {
    background: #5f6bff;
    color: white;
}

/* Inputs */
textarea, input {
    background: #f6f7ff !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.9rem !important;
    font-size: 0.95rem !important;
    box-shadow: inset 0 2px 6px rgba(0,0,0,0.05);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg,#ff8a00,#e52e71);
    color: white !important;
    border-radius: 16px !important;
    border: none !important;
    padding: 0.9rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    box-shadow: 0 8px 20px rgba(229,46,113,0.3);
    transition: 0.2s;
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 25px rgba(229,46,113,0.4);
}

/* Keyword Chips */
.keyword-chip {
    display: inline-block;
    padding: 0.5rem 1.2rem;
    border-radius: 999px;
    font-size: 0.9rem;
    margin: 0.4rem;
    background: linear-gradient(135deg,#5f6bff,#b06ab3);
    color: white;
    font-weight: 500;
    box-shadow: 0 6px 15px rgba(95,107,255,0.3);
    transition: 0.2s;
}

.keyword-chip:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 20px rgba(95,107,255,0.4);
}

/* Alert Boxes */
.stSuccess, .stError, .stWarning {
    border-radius: 18px !important;
    padding: 1.2rem !important;
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
    text_input = st.text_area("", height=220, placeholder="Paste article, blog, or content here...")
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
        st.success("""
• Public blog posts  
• News articles (no paywall)  
• Wikipedia pages  
• Company & product pages  
• Documentation sites  
• Government & NGO pages  
        """)

    with col2:
        st.error("""
• PDF files  
• Word / Excel / PowerPoint files  
• Image links (.jpg, .png, .svg)  
• Paywalled content  
        """)

    st.warning("""
🔒 Restricted Pages:
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
