import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

# ── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Keyword Finder",
    page_icon="🔍",
    layout="centered"
)

# ── API Key ─────────────────────────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("API key missing.")
    st.stop()

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
.stApp { background: #0a0a0f; color: #e8e8f0; }

.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    text-align: center;
    background: linear-gradient(135deg, #e8e8f0 30%, #6c63ff 70%, #ff6584 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    text-align: center;
    color: #6b6b8a;
    font-size: 0.85rem;
    margin-bottom: 2rem;
}

/* Buttons */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #6c63ff, #9b59f7) !important;
    color: white !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 0.75rem !important;
    border: none !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #12121a;
    border-radius: 14px;
    padding: 5px;
    border: 1px solid #2a2a3d;
}
.stTabs [aria-selected="true"] {
    background: #6c63ff !important;
    color: white !important;
}

/* URL Guidelines Cards */
.guidelines-container {
    margin-top: 2rem;
}

.guideline-card {
    background: linear-gradient(145deg, #12121a, #0f0f16);
    border: 1px solid #2a2a3d;
    border-radius: 14px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    transition: 0.3s ease;
}

.guideline-card:hover {
    border: 1px solid #c9a227;
    box-shadow: 0 0 15px rgba(201,162,39,0.15);
}

.guideline-title {
    font-size: 0.9rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    color: #c9a227;
}

.guideline-text {
    font-size: 0.8rem;
    color: #a0a0c0;
}

.keyword-chip {
    display: inline-block;
    padding: 0.35rem 0.9rem;
    border-radius: 999px;
    font-size: 0.82rem;
    margin: 0.25rem;
    background: rgba(108,99,255,0.15);
    border: 1px solid rgba(108,99,255,0.4);
    color: #a099ff;
}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────
st.markdown('<div class="main-title">AI Keyword Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Extract high-relevance keywords from text or URLs instantly.</div>', unsafe_allow_html=True)

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

# ── Tabs (3 Tabs Now) ──────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📄 Text Input", "🌐 URL Input", "📘 URL Guidelines"])

# ── Text Tab ───────────────────────────────────────────────
with tab1:
    text_input = st.text_area("Text", height=200, label_visibility="collapsed")
    if st.button("🔍 Extract Keywords"):
        if text_input.strip():
            with st.spinner("Extracting..."):
                st.session_state.kws = extract_keywords(text_input)

# ── URL Tab ────────────────────────────────────────────────
with tab2:
    url_input = st.text_input("URL", label_visibility="collapsed")
    if st.button("🔍 Extract from URL"):
        if url_input.startswith("http"):
            with st.spinner("Fetching..."):
                content = fetch_url_content(url_input)
            with st.spinner("Extracting..."):
                st.session_state.kws = extract_keywords(content)

# ── URL Guidelines Tab ─────────────────────────────────────
with tab3:
    st.markdown("""
    <div class="guidelines-container">

        <div class="guideline-card">
            <div class="guideline-title">✔ Supported</div>
            <div class="guideline-text">
                Public blogs, news (no paywall), Wikipedia, company pages,
                documentation sites.
            </div>
        </div>

        <div class="guideline-card">
            <div class="guideline-title">✖ Not Supported</div>
            <div class="guideline-text">
                PDF, Word, Excel, PowerPoint files, image links (.jpg, .png),
                paywalled content.
            </div>
        </div>

        <div class="guideline-card">
            <div class="guideline-title">🔒 Restricted</div>
            <div class="guideline-text">
                Login-required pages, Google Docs, Drive links,
                private dashboards.
            </div>
        </div>

    </div>
    """, unsafe_allow_html=True)

# ── Results ─────────────────────────────────────────────────
if "kws" in st.session_state:
    st.markdown("---")
    for k in st.session_state.kws:
        st.markdown(
            f'<span class="keyword-chip">{k["keyword"]} ({float(k["score"]):.2f})</span>',
            unsafe_allow_html=True
        )
