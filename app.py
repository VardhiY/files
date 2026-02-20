import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

# ── PAGE CONFIG ─────────────────────────────────────
st.set_page_config(
    page_title="LEXIS - AI Keyword Finder",
    page_icon="🔍",
    layout="wide"
)

# ── LOAD API KEY ────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing in Streamlit secrets.")
    st.stop()

# ── ENTERPRISE UI STYLING ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

.stApp {
    background:
        radial-gradient(circle at 15% 20%, rgba(40, 80, 255, 0.25), transparent 40%),
        radial-gradient(circle at 85% 80%, rgba(0, 200, 255, 0.15), transparent 45%),
        linear-gradient(135deg, #0b1020 0%, #090e1a 40%, #05070f 100%);
    background-attachment: fixed;
    font-family: 'Inter', sans-serif;
    color: white;
}

.block-container {
    padding-top: 3rem;
    max-width: 1100px;
}

/* HEADER */
.main-title {
    font-size: 3.5rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(90deg,#ffffff,#00e0ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.5rem;
}

.subtitle {
    text-align: center;
    color: #9aa3b2;
    font-size: 1.1rem;
    margin-bottom: 2.5rem;
}

/* RADIO NAV */
div[role="radiogroup"] {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 2rem;
}

/* INPUT BOXES */
textarea, input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(0,200,255,0.4) !important;
    border-radius: 14px !important;
    color: white !important;
    padding: 1rem !important;
}

textarea:focus, input:focus {
    border: 1px solid #00e0ff !important;
    box-shadow: 0 0 15px rgba(0,224,255,0.4);
}

/* BUTTON */
.stButton > button {
    background: linear-gradient(90deg,#00e0ff,#4facfe);
    border-radius: 30px !important;
    padding: 0.7rem 2rem !important;
    font-weight: 600 !important;
    border: none !important;
    color: black !important;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,224,255,0.4);
}

/* KEYWORD CHIPS */
.keyword-chip {
    display: inline-block;
    padding: 0.5rem 1.2rem;
    margin: 0.4rem;
    border-radius: 30px;
    background: rgba(0,224,255,0.1);
    border: 1px solid rgba(0,224,255,0.5);
    color: #00e0ff;
    font-weight: 500;
    transition: 0.2s ease;
}

.keyword-chip:hover {
    background: rgba(0,224,255,0.2);
    transform: scale(1.05);
}

/* GUIDELINE CARDS */
.card {
    background: rgba(255,255,255,0.04);
    padding: 1.5rem;
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────
st.markdown('<div class="main-title">LEXIS</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-powered semantic keyword extraction for text and web content.</div>', unsafe_allow_html=True)

# ── KEYWORD FUNCTION ─────────────────────────────────
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

# ── HTML PARSER FOR URL ─────────────────────────────
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

# ── NAVIGATION ───────────────────────────────────────
mode = st.radio(
    "",
    ["📄 Text Input", "🌐 URL Input", "📘 Guidelines"],
    horizontal=True
)

# ── TEXT MODE ────────────────────────────────────────
if mode == "📄 Text Input":
    text_input = st.text_area("", height=220, placeholder="Paste article, blog, or content here...")
    if st.button("Extract Keywords"):
        if text_input.strip():
            with st.spinner("Analyzing content..."):
                st.session_state.kws = extract_keywords(text_input)

# ── URL MODE ─────────────────────────────────────────
elif mode == "🌐 URL Input":
    url_input = st.text_input("", placeholder="https://example.com/article")
    if st.button("Extract from URL"):
        if url_input.startswith("http"):
            with st.spinner("Fetching webpage..."):
                content = fetch_url_content(url_input)
                st.session_state.kws = extract_keywords(content)

# ── GUIDELINES ───────────────────────────────────────
elif mode == "📘 Guidelines":
    st.markdown('<div class="card"><b>✔ Supported:</b><br>Public blogs, news (no paywall), Wikipedia, company pages, documentation sites.</div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><b>✖ Not Supported:</b><br>PDF, Word, Excel, PowerPoint, image links, paywalled content.</div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><b>🔒 Restricted:</b><br>Login-required pages, Google Docs/Drive, private dashboards.</div>', unsafe_allow_html=True)

# ── RESULTS ──────────────────────────────────────────
if "kws" in st.session_state:
    st.markdown("### 🔎 Extracted Keywords")
    chips = ""
    for k in st.session_state.kws:
        chips += f'<span class="keyword-chip">{k["keyword"]}</span>'
    st.markdown(chips, unsafe_allow_html=True)
