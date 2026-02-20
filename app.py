import streamlit as st
from groq import Groq
import json
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Keyword Finder",
    page_icon="🔍",
    layout="centered"
)

# ── Load API Key ─────────────────────────────────────────────────────
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=API_KEY)
except Exception:
    st.error("⚠️ API key not configured.")
    st.stop()

# ── Custom Professional CSS ──────────────────────────────────────────
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
    margin-bottom: 0.2rem;
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

.badge {
    display: flex;
    justify-content: center;
    margin-bottom: 1rem;
}

.badge span {
    background: linear-gradient(135deg, #6c63ff, #ff6584);
    color: white;
    padding: 0.3rem 1rem;
    border-radius: 999px;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
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
.stButton > button:hover {
    box-shadow: 0 8px 30px rgba(108,99,255,0.4);
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

/* URL Guidelines Professional */
.guidelines-wrapper {
    margin-top: 2rem;
    padding: 1.8rem;
    border-radius: 16px;
    background: linear-gradient(145deg, #11111a, #0d0d14);
    border: 1px solid #2a2a3d;
}

.guidelines-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
}

.guidelines-subtitle {
    color: #6b6b8a;
    font-size: 0.85rem;
    margin-bottom: 1.5rem;
}

.guidelines-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
}

.guideline-card {
    background: #141421;
    padding: 1rem;
    border-radius: 12px;
    border: 1px solid #232336;
}

.guideline-card h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.9rem;
    font-weight: 600;
}

.supported h4 { color: #43e97b; }
.not-supported h4 { color: #ff6584; }

.guideline-card ul {
    padding-left: 1rem;
    margin: 0;
    font-size: 0.8rem;
    color: #a0a0c0;
}

.guideline-card li { margin-bottom: 0.3rem; }

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

# ── Header ───────────────────────────────────────────────────────────
st.markdown('<div class="badge"><span>⚡ Powered by Groq AI</span></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">AI Keyword Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Extract high-relevance keywords from any text or URL — instantly.</div>', unsafe_allow_html=True)

# ── Keyword Extraction ───────────────────────────────────────────────
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

# ── URL Text Extractor ───────────────────────────────────────────────
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
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    parser = TextExtractor()
    parser.feed(html)
    return parser.get_text()

# ── Tabs ─────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📄 Text Input", "🌐 URL Input"])

with tab1:
    text_input = st.text_area("Text", height=200, label_visibility="collapsed")
    if st.button("🔍 Extract Keywords"):
        if text_input.strip():
            with st.spinner("Extracting..."):
                kws = extract_keywords(text_input)
                st.session_state.kws = kws

with tab2:
    url_input = st.text_input("URL", label_visibility="collapsed")
    st.caption("Paste any public article or webpage URL.")

    # Professional URL Guidelines
    st.markdown("""
    <div class="guidelines-wrapper">
        <div class="guidelines-title">URL Guidelines</div>
        <div class="guidelines-subtitle">
            Only publicly accessible HTML pages are supported.
        </div>

        <div class="guidelines-grid">
            <div class="guideline-card supported">
                <h4>✔ Supported</h4>
                <ul>
                    <li>Public blog posts</li>
                    <li>News articles (no paywall)</li>
                    <li>Wikipedia pages</li>
                    <li>Company pages</li>
                    <li>Documentation sites</li>
                </ul>
            </div>

            <div class="guideline-card not-supported">
                <h4>✖ Not Supported</h4>
                <ul>
                    <li>PDF files</li>
                    <li>Word / PPT / Excel files</li>
                    <li>Image links</li>
                    <li>Paywalled content</li>
                    <li>Login-required pages</li>
                </ul>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔍 Extract from URL"):
        if url_input.startswith("http"):
            with st.spinner("Fetching content..."):
                text = fetch_url_content(url_input)
            with st.spinner("Extracting keywords..."):
                kws = extract_keywords(text)
                st.session_state.kws = kws

# ── Results ──────────────────────────────────────────────────────────
if "kws" in st.session_state:
    st.markdown("---")
    for k in st.session_state.kws:
        st.markdown(
            f'<span class="keyword-chip">{k["keyword"]} ({float(k["score"]):.2f})</span>',
            unsafe_allow_html=True
        )
