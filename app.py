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

# ── MONOCHROME PREMIUM UI ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #6366f1;
    --primary-soft: #818cf8;
    --bg-dark: #0f172a;
    --glass: rgba(99,102,241,0.08);
}

.stApp {
    font-family: 'Outfit', sans-serif;
    background: var(--bg-dark);
    color: white;
}

/* Container */
.block-container {
    max-width: 1000px;
    margin: 4rem auto;
    padding: 3rem;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 28px;
    backdrop-filter: blur(20px);
    box-shadow: 0 30px 80px rgba(0,0,0,0.6);
}

/* Header */
.main-title {
    text-align: center;
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: 3px;
    color: var(--primary);
}

.subtitle {
    text-align: center;
    font-size: 1rem;
    opacity: 0.7;
    margin-bottom: 3rem;
}

/* Tabs */
div[role="radiogroup"] {
    justify-content: center;
    gap: 1.2rem;
}

div[role="radiogroup"] > label {
    background: rgba(255,255,255,0.05);
    padding: 0.6rem 1.4rem;
    border-radius: 999px;
    transition: 0.3s ease;
    font-weight: 500;
    letter-spacing: 0.5px;
}

div[role="radiogroup"] > label:hover {
    background: var(--primary);
    color: white !important;
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(99,102,241,0.4);
}

/* Inputs */
textarea, input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 18px !important;
    padding: 1rem !important;
    color: white !important;
    transition: 0.3s ease;
}

textarea:focus, input:focus {
    border: 1px solid var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.2);
}

/* Button */
.stButton > button {
    background: var(--primary);
    border-radius: 18px !important;
    border: none !important;
    padding: 1rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    letter-spacing: 1px;
    transition: 0.3s ease;
    box-shadow: 0 10px 25px rgba(99,102,241,0.3);
}

.stButton > button:hover {
    background: var(--primary-soft);
    transform: translateY(-3px);
    box-shadow: 0 15px 35px rgba(99,102,241,0.5);
}

/* Keywords */
.keyword-chip {
    display: inline-block;
    padding: 0.6rem 1.4rem;
    border-radius: 999px;
    margin: 0.5rem;
    font-size: 0.9rem;
    background: var(--glass);
    border: 1px solid rgba(99,102,241,0.3);
    transition: 0.3s ease;
    letter-spacing: 0.5px;
}

.keyword-chip:hover {
    background: var(--primary);
    transform: translateY(-4px);
    box-shadow: 0 10px 30px rgba(99,102,241,0.5);
}

/* Divider */
hr {
    border-color: rgba(255,255,255,0.08);
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────
st.markdown('<div class="main-title">LEXIS</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-powered semantic keyword extraction for text and web content.</div>', unsafe_allow_html=True)

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
mode = st.radio("", ["📄 Text Input", "🌐 URL Input", "📘 URL Guidelines"], horizontal=True)

if mode == "📄 Text Input":
    text_input = st.text_area("", height=220, placeholder="Paste content here...")
    if st.button("Extract Keywords"):
        if text_input.strip():
            with st.spinner("Analyzing..."):
                st.session_state.kws = extract_keywords(text_input)

elif mode == "🌐 URL Input":
    url_input = st.text_input("", placeholder="https://example.com")
    if st.button("Extract from URL"):
        if url_input.startswith("http"):
            with st.spinner("Fetching content..."):
                content = fetch_url_content(url_input)
                st.session_state.kws = extract_keywords(content)

elif mode == "📘 URL Guidelines":
    st.success("✔ Public blogs, news, Wikipedia, company pages.")
    st.error("✖ PDF, Word, Excel, images, paywalled content.")
    st.warning("🔒 Login-required pages & private dashboards.")

# ── Results ────────────────────────────────────────────────
if "kws" in st.session_state:
    st.markdown("---")
    st.markdown("### 🔎 Extracted Keywords")

    chips = ""
    for k in st.session_state.kws:
        chips += f'<span class="keyword-chip">{k["keyword"]}</span>'

    st.markdown(chips, unsafe_allow_html=True)
