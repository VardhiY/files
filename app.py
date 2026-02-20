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

# ── ULTRA PREMIUM UI ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #1e3a8a;
    --primary-soft: #3b82f6;
    --bg: #0b1120;
    --panel: #111827;
    --border: rgba(255,255,255,0.06);
}

.stApp {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background: var(--bg);
    color: #e5e7eb;
}

/* Remove Streamlit padding */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Main Floating Panel */
.main-panel {
    max-width: 1100px;
    margin: 80px auto;
    background: var(--panel);
    border-radius: 32px;
    padding: 60px;
    box-shadow:
        0 40px 100px rgba(0,0,0,0.6),
        inset 0 0 0 1px var(--border);
    animation: fadeIn 0.8s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px);}
    to { opacity: 1; transform: translateY(0);}
}

/* Header */
.main-title {
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: 1px;
    text-align: center;
    color: white;
}

.subtitle {
    text-align: center;
    opacity: 0.6;
    margin-top: 10px;
    margin-bottom: 50px;
}

/* Tabs */
div[role="radiogroup"] {
    justify-content: center;
    gap: 14px;
    margin-bottom: 40px;
}

div[role="radiogroup"] > label {
    background: #0f172a;
    border: 1px solid var(--border);
    padding: 10px 22px;
    border-radius: 14px;
    font-weight: 500;
    transition: all 0.25s ease;
}

div[role="radiogroup"] > label:hover {
    background: var(--primary);
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(30,58,138,0.4);
}

/* Inputs */
textarea, input {
    background: #0f172a !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    padding: 20px !important;
    font-size: 16px !important;
    transition: all 0.25s ease !important;
}

textarea:focus, input:focus {
    border: 1px solid var(--primary-soft) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.3);
}

/* Button */
.stButton > button {
    background: var(--primary);
    border-radius: 18px !important;
    padding: 16px !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    transition: 0.3s ease;
    box-shadow: 0 10px 25px rgba(30,58,138,0.4);
}

.stButton > button:hover {
    background: var(--primary-soft);
    transform: translateY(-3px);
    box-shadow: 0 20px 40px rgba(59,130,246,0.5);
}

/* Keywords */
.keyword-chip {
    display: inline-block;
    padding: 12px 24px;
    border-radius: 999px;
    margin: 8px;
    font-size: 14px;
    font-weight: 500;
    background: #0f172a;
    border: 1px solid var(--border);
    transition: 0.25s ease;
}

.keyword-chip:hover {
    background: var(--primary);
    transform: translateY(-4px);
    box-shadow: 0 12px 30px rgba(30,58,138,0.4);
}
</style>
""", unsafe_allow_html=True)

# Floating wrapper
st.markdown('<div class="main-panel">', unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title">LEXIS</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Advanced AI-powered semantic keyword extraction.</div>', unsafe_allow_html=True)

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

# URL extractor (unchanged)
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script','style','nav','footer','header'}
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags: self.skip += 1
    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip > 0: self.skip -= 1
    def handle_data(self, data):
        if self.skip == 0:
            stripped = data.strip()
            if stripped: self.text_parts.append(stripped)
    def get_text(self):
        return ' '.join(self.text_parts)

def fetch_url_content(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    parser = TextExtractor()
    parser.feed(html)
    return parser.get_text()

# Navigation
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

if "kws" in st.session_state:
    st.markdown("---")
    st.markdown("### Extracted Keywords")
    chips = ""
    for k in st.session_state.kws:
        chips += f'<span class="keyword-chip">{k["keyword"]}</span>'
    st.markdown(chips, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
