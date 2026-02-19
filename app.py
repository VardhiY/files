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

# ── Load API Key from Streamlit Secrets ───────────────────────────────
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=API_KEY)
except Exception:
    st.error("⚠️ API key not configured.")
    st.info("Go to: Streamlit Cloud → Your App → ⋮ → Settings → Secrets → paste:\n\n`GROQ_API_KEY = \"your-key-here\"`")
    st.stop()

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
.stApp { background: #0a0a0f; color: #e8e8f0; }

.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem; font-weight: 800;
    background: linear-gradient(135deg, #e8e8f0 30%, #6c63ff 70%, #ff6584 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    text-align: center; margin-bottom: 0.2rem;
}
.subtitle {
    text-align: center; color: #6b6b8a;
    font-size: 0.85rem; letter-spacing: 0.05em; margin-bottom: 2rem;
}
.badge { display: flex; justify-content: center; margin-bottom: 1rem; }
.badge span {
    background: linear-gradient(135deg, #6c63ff, #ff6584);
    color: white; padding: 0.3rem 1rem; border-radius: 999px;
    font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
}
.keyword-chip-high {
    display: inline-block; background: rgba(108,99,255,0.15);
    border: 1px solid rgba(108,99,255,0.4); color: #a099ff;
    padding: 0.3rem 0.8rem; border-radius: 999px; font-size: 0.82rem; margin: 0.2rem;
}
.keyword-chip-mid {
    display: inline-block; background: rgba(67,233,123,0.12);
    border: 1px solid rgba(67,233,123,0.35); color: #43e97b;
    padding: 0.3rem 0.8rem; border-radius: 999px; font-size: 0.82rem; margin: 0.2rem;
}
.keyword-chip-low {
    display: inline-block; background: rgba(255,101,132,0.1);
    border: 1px solid rgba(255,101,132,0.3); color: #ff8fa3;
    padding: 0.3rem 0.8rem; border-radius: 999px; font-size: 0.82rem; margin: 0.2rem;
}
div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
    background: #0a0a0f !important; border: 1px solid #2a2a3d !important;
    color: #e8e8f0 !important; font-family: 'DM Mono', monospace !important;
    border-radius: 10px !important;
}
div[data-testid="stSelectbox"] > div {
    background: #0a0a0f !important; border: 1px solid #2a2a3d !important;
    color: #e8e8f0 !important; border-radius: 8px !important;
}
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #6c63ff, #9b59f7) !important;
    color: white !important; font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 1rem !important;
    border: none !important; border-radius: 12px !important;
    padding: 0.75rem !important;
}
.stButton > button:hover { box-shadow: 0 8px 30px rgba(108,99,255,0.4) !important; }
.stTabs [data-baseweb="tab-list"] {
    background: #12121a; border-radius: 14px;
    padding: 5px; gap: 4px; border: 1px solid #2a2a3d;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #6b6b8a;
    border-radius: 10px; font-family: 'DM Mono', monospace; font-size: 0.82rem;
}
.stTabs [aria-selected="true"] { background: #6c63ff !important; color: white !important; }
section[data-testid="stSidebar"] { background: #12121a !important; border-right: 1px solid #2a2a3d; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────
st.markdown('<div class="badge"><span>⚡ Powered by Groq AI · Semantic Engine</span></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">AI Keyword Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Extract high-relevance keywords from any text or URL — instantly.</div>', unsafe_allow_html=True)

# ── Settings Sidebar ──────────────────────────────────────────────────
st.sidebar.markdown("## ⚙️ Settings")
top_n     = st.sidebar.selectbox("Top N Keywords", [5, 10, 15, 20], index=1)
ngram_max = st.sidebar.selectbox(
    "Keyphrase Length", [1, 2, 3],
    format_func=lambda x: {1:"Single words", 2:"1–2 word phrases", 3:"1–3 word phrases"}[x],
    index=1
)
diversity = st.sidebar.selectbox(
    "Diversity Mode", ["none", "mmr", "maxsum"],
    format_func=lambda x: {"none":"None (raw scores)","mmr":"MMR (balanced)","maxsum":"Max Sum (diverse)"}[x],
    index=1
)
st.sidebar.markdown("---")
st.sidebar.markdown("<small style='color:#6b6b8a'>AI Keyword Finder · v1.0</small>", unsafe_allow_html=True)

# ── Groq Keyword Extraction ───────────────────────────────────────────
def extract_keywords(text, top_n, ngram_max, diversity):
    diversity_rule = {
        "mmr":    "Apply MMR diversity — avoid repeating similar root concepts.",
        "maxsum": "Maximize diversity — make keywords as distinct as possible.",
        "none":   "Return purely by relevance score, no diversity constraint."
    }[diversity]
    length_rule = {1:"1 word only", 2:"1 to 2 words max", 3:"1 to 3 words max"}[ngram_max]

    prompt = f"""You are a semantic keyword extraction engine (like KeyBERT). Extract the top {top_n} keywords from the text below.

Rules:
- Keyphrase length: {length_rule}
- {diversity_rule}
- Score each from 0.00 to 1.00 by semantic importance to the text.
- Return ONLY a valid JSON array. No markdown fences, no explanation, nothing else.
- Format: [{{"keyword":"...","score":0.00}},...] 

TEXT:
{text[:7000]}"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1000
    )
    raw     = response.choices[0].message.content.strip()
    cleaned = re.sub(r'```json|```', '', raw).strip()
    return json.loads(cleaned)

# ── URL Text Extractor (no API needed — plain HTTP fetch) ─────────────
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags  = {'script','style','nav','footer','header','aside','noscript','form'}
        self.skip       = 0

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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        raise ValueError(f"Could not reach the URL: {e}")

    parser = TextExtractor()
    parser.feed(html)
    text = parser.get_text()

    # Clean up excess whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    if len(text.split()) < 30:
        raise ValueError("Not enough readable text found at that URL.")
    return text

# ── Chip Helper ───────────────────────────────────────────────────────
def chip(keyword, score):
    s   = float(score)
    cls = "keyword-chip-high" if s >= 0.75 else "keyword-chip-mid" if s >= 0.55 else "keyword-chip-low"
    return f'<span class="{cls}">{keyword} <small style="opacity:0.65">{s:.2f}</small></span>'

# ── Input Tabs ────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📄 Text Input", "🌐 URL Input"])

with tab1:
    text_input = st.text_area(
        "text", height=200,
        placeholder="Enter any article, blog post, product description, or content here...",
        label_visibility="collapsed"
    )
    run_text = st.button("🔍 Extract Keywords", key="btn_text", use_container_width=True)

with tab2:
    url_input = st.text_input(
        "url", placeholder="https://example.com/article",
        label_visibility="collapsed"
    )
    st.caption("✅ Paste any public URL — article, blog, Wikipedia, product page.")
    run_url = st.button("🔍 Extract Keywords", key="btn_url", use_container_width=True)

# ── Run: Text ─────────────────────────────────────────────────────────
if run_text:
    if not text_input.strip():
        st.error("Please paste some text first.")
    elif len(text_input.split()) < 20:
        st.error("Please provide at least 20 words.")
    else:
        with st.spinner("🧠 Extracting keywords with AI..."):
            try:
                kws = extract_keywords(text_input, top_n, ngram_max, diversity)
                st.session_state.keywords   = kws
                st.session_state.word_count = len(text_input.split())
                st.session_state.source     = None
            except Exception as e:
                st.error(f"Extraction failed: {e}")

# ── Run: URL ──────────────────────────────────────────────────────────
if run_url:
    if not url_input.strip():
        st.error("Please enter a URL.")
    elif not url_input.startswith("http"):
        st.error("URL must start with https://")
    else:
        content = None
        with st.spinner("🌐 Fetching page content..."):
            try:
                content = fetch_url_content(url_input)
            except Exception as e:
                st.error(f"Could not fetch URL: {e}")

        if content:
            with st.spinner("🧠 Extracting keywords with AI..."):
                try:
                    kws = extract_keywords(content, top_n, ngram_max, diversity)
                    st.session_state.keywords   = kws
                    st.session_state.word_count = len(content.split())
                    try:
                        st.session_state.source = urllib.parse.urlparse(url_input).hostname
                    except:
                        st.session_state.source = url_input
                except Exception as e:
                    st.error(f"Extraction failed: {e}")

# ── Results ───────────────────────────────────────────────────────────
if "keywords" in st.session_state:
    kws    = st.session_state.keywords
    wc     = st.session_state.get("word_count", 0)
    source = st.session_state.get("source")

    st.markdown("---")

    meta = f"**{len(kws)} keywords** · {wc:,} words analyzed"
    if source:
        meta += f" · `{source}`"
    st.markdown(meta)

    # Legend
    c1, c2, c3 = st.columns(3)
    c1.markdown("🟣 High ≥ 0.75")
    c2.markdown("🟢 Mid 0.55–0.74")
    c3.markdown("🔴 Lower < 0.55")

    # Chips
    st.markdown(
        '<div style="margin:1rem 0">' + "".join(chip(k["keyword"], k["score"]) for k in kws) + '</div>',
        unsafe_allow_html=True
    )

    # Score bars
    st.markdown("#### 📊 Relevance Scores")
    for i, k in enumerate(kws):
        s = float(k["score"])
        r, kw, bar = st.columns([0.5, 3, 6])
        r.markdown(f"<span style='color:#6b6b8a;font-size:.8rem'>{i+1}</span>", unsafe_allow_html=True)
        kw.markdown(f"`{k['keyword']}`")
        bar.progress(s, text=f"{s:.3f}")

    # Export
    st.markdown("---")
    csv   = "Keyword,Score\n" + "\n".join(f'"{k["keyword"]}",{float(k["score"]):.3f}' for k in kws)
    plain = ", ".join(k["keyword"] for k in kws)

    col_a, col_b = st.columns(2)
    col_a.download_button("⬇️ Export CSV", csv, "keywords.csv", "text/csv", use_container_width=True)
    with col_b:
        if st.button("⎘ Copy Keywords", use_container_width=True):
            st.code(plain, language=None)
