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

# ── Ultra Aesthetic Animated UI ────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap');

.stApp {
    font-family: 'Outfit', sans-serif;
    background: linear-gradient(-45deg, #5f6bff, #b06ab3, #ff6a88, #ff8a00);
    background-size: 400% 400%;
    animation: gradientMove 12s ease infinite;
}

@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Glass Container */
.block-container {
    max-width: 1100px;
    margin: 4rem auto;
    padding: 3rem;
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(30px);
    border-radius: 30px;
    box-shadow: 0 40px 100px rgba(0,0,0,0.35);
    color: white !important;
}

/* Header */
.main-title {
    text-align: center;
    font-size: 3.5rem;
    font-weight: 800;
    letter-spacing: 2px;
    animation: floatText 4s ease-in-out infinite;
}

@keyframes floatText {
    0%,100% { transform: translateY(0px); }
    50% { transform: translateY(-6px); }
}

.subtitle {
    text-align: center;
    font-size: 1rem;
    opacity: 0.85;
    margin-bottom: 2.5rem;
}

/* Navigation */
div[role="radiogroup"] {
    justify-content: center;
    gap: 1.5rem;
}

div[role="radiogroup"] > label {
    background: rgba(255,255,255,0.15);
    padding: 0.6rem 1.3rem;
    border-radius: 999px;
    font-weight: 500;
    transition: all 0.3s ease;
    color: white !important;
}

div[role="radiogroup"] > label:hover {
    background: white;
    color: #5f6bff !important;
    transform: scale(1.05);
}

/* Inputs */
textarea, input {
    background: rgba(255,255,255,0.2) !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 1rem !important;
    color: white !important;
    backdrop-filter: blur(10px);
}

/* Button */
.stButton > button {
    background: linear-gradient(135deg,#ff8a00,#ff3cac);
    border-radius: 20px !important;
    border: none !important;
    padding: 1rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    color: white !important;
    transition: all 0.3s ease;
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
}

.stButton > button:hover {
    transform: translateY(-4px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.4);
}

/* Keyword Chips */
.keyword-chip {
    display: inline-block;
    padding: 0.5rem 1.2rem;
    border-radius: 999px;
    margin: 0.4rem;
    font-size: 0.9rem;
    font-weight: 500;
    background: rgba(255,255,255,0.25);
    backdrop-filter: blur(15px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
    transition: all 0.3s ease;
    animation: fadeInUp 0.6s ease forwards;
}

.keyword-chip:hover {
    transform: translateY(-5px) scale(1.07);
    background: white;
    color: #5f6bff !important;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

hr {
    border-color: rgba(255,255,255,0.2);
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
    st.markdown("### ✔ Supported")
    st.success("Public blogs, news, Wikipedia, company pages, documentation sites.")
    st.markdown("### ✖ Not Supported")
    st.error("PDF, Word, Excel, image links, paywalled content.")
    st.markdown("### 🔒 Restricted")
    st.warning("Login-required pages, Google Docs, private dashboards.")

# ── Results ────────────────────────────────────────────────
if "kws" in st.session_state:
    st.markdown("---")
    st.markdown("### 🔎 Extracted Keywords")
    chips = ""
    for k in st.session_state.kws:
        chips += f'<span class="keyword-chip">{k["keyword"]}</span>'
    st.markdown(chips, unsafe_allow_html=True)
