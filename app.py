import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

# ── Page Config ─────────────────────────────
st.set_page_config(
    page_title="LEXIS - AI Keyword Finder",
    page_icon="🔍",
    layout="wide"
)

# ── Load API Key ────────────────────────────
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing in Streamlit secrets.")
    st.stop()

# ── CREATIVE WEB DESIGN STYLE UI ───────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&family=Poppins:wght@400;500;600&display=swap');

.stApp {
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg,#ff6a88,#ff8a00,#6a5af9,#00c9ff);
    background-size: 400% 400%;
    animation: gradientMove 12s ease infinite;
    color: white;
}

@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Remove default spacing */
.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

/* Floating Card */
.main-card {
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(25px);
    border-radius: 30px;
    padding: 60px;
    box-shadow: 0 40px 100px rgba(0,0,0,0.3);
    animation: fadeIn 0.8s ease;
}

@keyframes fadeIn {
    from { opacity:0; transform:translateY(30px);}
    to { opacity:1; transform:translateY(0);}
}

/* Header */
.main-title {
    font-family: 'Montserrat', sans-serif;
    font-size: 4rem;
    font-weight: 800;
    letter-spacing: 2px;
}

.subtitle {
    font-size: 1.1rem;
    margin-top: 10px;
    opacity: 0.9;
}

/* Tabs */
div[role="radiogroup"] {
    margin-top: 40px;
    gap: 20px;
}

div[role="radiogroup"] > label {
    background: rgba(255,255,255,0.2);
    padding: 10px 25px;
    border-radius: 999px;
    font-weight: 500;
    transition: all 0.3s ease;
}

div[role="radiogroup"] > label:hover {
    background: white;
    color: #6a5af9 !important;
    transform: scale(1.05);
}

/* Inputs */
textarea, input {
    background: rgba(255,255,255,0.2) !important;
    border: none !important;
    border-radius: 20px !important;
    padding: 20px !important;
    font-size: 16px !important;
    color: white !important;
    backdrop-filter: blur(10px);
}

/* Button */
.stButton > button {
    background: linear-gradient(90deg,#6a5af9,#00c9ff);
    border-radius: 20px !important;
    border: none !important;
    padding: 15px !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

/* Keywords */
.keyword-chip {
    display: inline-block;
    padding: 12px 28px;
    border-radius: 999px;
    margin: 10px;
    font-size: 14px;
    font-weight: 500;
    background: rgba(255,255,255,0.25);
    transition: all 0.3s ease;
}

.keyword-chip:hover {
    background: white;
    color: #6a5af9 !important;
    transform: translateY(-4px);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-card">', unsafe_allow_html=True)

# Header
st.markdown('<div class="main-title">LEXIS</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Creative AI-powered keyword extraction for modern web content.</div>', unsafe_allow_html=True)

# ── Keyword Extraction Logic (UNCHANGED) ─────────────
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

# URL Extractor (unchanged)
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
    text_input = st.text_area("", height=220, placeholder="Paste article or content here...")
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
