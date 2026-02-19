import streamlit as st
import anthropic
import json
import re

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Keyword Finder",
    page_icon="🔍",
    layout="centered"
)

# ── Custom CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Mono', monospace; }

.stApp { background: #0a0a0f; color: #e8e8f0; }

.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #e8e8f0 30%, #6c63ff 70%, #ff6584 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 0.2rem;
}
.subtitle {
    text-align: center;
    color: #6b6b8a;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
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
.keyword-chip-high {
    display: inline-block;
    background: rgba(108,99,255,0.15);
    border: 1px solid rgba(108,99,255,0.4);
    color: #a099ff;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    font-size: 0.82rem;
    margin: 0.2rem;
}
.keyword-chip-mid {
    display: inline-block;
    background: rgba(67,233,123,0.12);
    border: 1px solid rgba(67,233,123,0.35);
    color: #43e97b;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    font-size: 0.82rem;
    margin: 0.2rem;
}
.keyword-chip-low {
    display: inline-block;
    background: rgba(255,101,132,0.1);
    border: 1px solid rgba(255,101,132,0.3);
    color: #ff8fa3;
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    font-size: 0.82rem;
    margin: 0.2rem;
}
.results-card {
    background: #12121a;
    border: 1px solid #2a2a3d;
    border-radius: 16px;
    padding: 1.5rem;
    margin-top: 1.5rem;
}
.section-label {
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    color: #6b6b8a;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
}
div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
    background: #0a0a0f !important;
    border: 1px solid #2a2a3d !important;
    color: #e8e8f0 !important;
    font-family: 'DM Mono', monospace !important;
    border-radius: 10px !important;
}
div[data-testid="stSelectbox"] > div {
    background: #0a0a0f !important;
    border: 1px solid #2a2a3d !important;
    color: #e8e8f0 !important;
    border-radius: 8px !important;
}
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #6c63ff, #9b59f7) !important;
    color: white !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    box-shadow: 0 8px 30px rgba(108,99,255,0.4) !important;
    transform: translateY(-1px) !important;
}
.stTabs [data-baseweb="tab-list"] {
    background: #12121a;
    border-radius: 14px;
    padding: 5px;
    gap: 4px;
    border: 1px solid #2a2a3d;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #6b6b8a;
    border-radius: 10px;
    font-family: 'DM Mono', monospace;
    font-size: 0.82rem;
}
.stTabs [aria-selected="true"] {
    background: #6c63ff !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────
st.markdown('<div class="badge"><span>⚡ Powered by Claude AI · KeyBERT Engine</span></div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">AI Keyword Finder</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Extract high-relevance keywords from any text or URL — instantly.</div>', unsafe_allow_html=True)

# ── API Key ──────────────────────────────────────────────────────────
api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
if not api_key:
    api_key = st.sidebar.text_input("🔑 Anthropic API Key", type="password", placeholder="sk-ant-...")
    if not api_key:
        st.sidebar.info("Get your key at console.anthropic.com")

# ── Settings Sidebar ─────────────────────────────────────────────────
st.sidebar.markdown("### ⚙️ Settings")
top_n = st.sidebar.selectbox("Top N Keywords", [5, 10, 15, 20], index=1)
ngram_max = st.sidebar.selectbox("Keyphrase Length", [1, 2, 3],
    format_func=lambda x: {1:"Single words", 2:"1–2 word phrases", 3:"1–3 word phrases"}[x], index=1)
diversity = st.sidebar.selectbox("Diversity Mode",
    ["none", "mmr", "maxsum"],
    format_func=lambda x: {"none":"None (raw scores)", "mmr":"MMR (balanced)", "maxsum":"Max Sum (diverse)"}[x],
    index=1)

# ── Claude API Helpers ───────────────────────────────────────────────
def get_client():
    if not api_key:
        st.error("⚠️ Please enter your Anthropic API key in the sidebar.")
        st.stop()
    return anthropic.Anthropic(api_key=api_key)

def extract_keywords(text, top_n, ngram_max, diversity):
    diversity_rule = {
        "mmr":    "Apply MMR diversity — avoid repeating similar root concepts.",
        "maxsum": "Maximize diversity — make keywords as distinct as possible.",
        "none":   "Return purely by relevance score, no diversity constraint."
    }[diversity]

    length_rule = {1: "1 word only", 2: "1 to 2 words max", 3: "1 to 3 words max"}[ngram_max]

    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""You are a semantic keyword extraction engine (like KeyBERT). Extract the top {top_n} keywords from the text below.

Rules:
- Keyphrase length: {length_rule}
- {diversity_rule}
- Score each from 0.00 to 1.00 by semantic importance to the text.
- Return ONLY a JSON array. No markdown, no explanation.
- Format: [{{"keyword":"...","score":0.00}},...] 

TEXT:
{text[:7000]}"""
        }]
    )

    raw = response.content[0].text
    cleaned = re.sub(r'```json|```', '', raw).strip()
    return json.loads(cleaned)

def fetch_url_content(url):
    client = get_client()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": f"""Use web search to visit this URL and extract its main content: {url}

Return ONLY the raw article/page body text (no HTML tags, no nav, no footer, no ads).
Return at least 150 words. If unable to access, start your reply with: FETCH_ERROR:"""
        }]
    )
    text = " ".join(b.text for b in response.content if b.type == "text")
    if text.strip().startswith("FETCH_ERROR:"):
        raise ValueError(text.replace("FETCH_ERROR:", "").strip())
    if len(text.split()) < 30:
        raise ValueError("Not enough content found at that URL.")
    return text

# ── Input Tabs ───────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📄 Text Input", "🌐 URL Input"])

with tab1:
    text_input = st.text_area(
        "Paste your text",
        height=200,
        placeholder="Enter any article, blog post, product description, or content here...",
        label_visibility="collapsed"
    )
    run_text = st.button("🔍 Extract Keywords", key="btn_text")

with tab2:
    url_input = st.text_input(
        "Enter a URL",
        placeholder="https://example.com/article",
        label_visibility="collapsed"
    )
    st.caption("✅ Paste any public URL — article, blog, Wikipedia, product page — keywords are extracted live.")
    run_url = st.button("🔍 Extract Keywords", key="btn_url")

# ── Keyword Chip Helper ───────────────────────────────────────────────
def chip(keyword, score):
    s = float(score)
    cls = "keyword-chip-high" if s >= 0.75 else "keyword-chip-mid" if s >= 0.55 else "keyword-chip-low"
    return f'<span class="{cls}">{keyword} <small style="opacity:0.7">{s:.2f}</small></span>'

# ── Run Text Mode ────────────────────────────────────────────────────
if run_text:
    if not text_input.strip():
        st.error("Please paste some text first.")
    elif len(text_input.split()) < 20:
        st.error("Please provide at least 20 words for meaningful extraction.")
    else:
        with st.spinner("Analyzing text and extracting keywords..."):
            try:
                keywords = extract_keywords(text_input, top_n, ngram_max, diversity)
                st.session_state["keywords"] = keywords
                st.session_state["word_count"] = len(text_input.split())
                st.session_state["source"] = None
            except Exception as e:
                st.error(f"Extraction failed: {e}")

# ── Run URL Mode ─────────────────────────────────────────────────────
if run_url:
    if not url_input.strip():
        st.error("Please enter a URL.")
    elif not url_input.startswith("http"):
        st.error("URL must start with https://")
    else:
        with st.spinner("Fetching URL content..."):
            try:
                content = fetch_url_content(url_input)
            except Exception as e:
                st.error(f"Could not fetch URL: {e}")
                content = None

        if content:
            with st.spinner("Extracting keywords with AI..."):
                try:
                    keywords = extract_keywords(content, top_n, ngram_max, diversity)
                    st.session_state["keywords"] = keywords
                    st.session_state["word_count"] = len(content.split())
                    try:
                        from urllib.parse import urlparse
                        st.session_state["source"] = urlparse(url_input).hostname
                    except:
                        st.session_state["source"] = url_input
                except Exception as e:
                    st.error(f"Extraction failed: {e}")

# ── Render Results ────────────────────────────────────────────────────
if "keywords" in st.session_state:
    keywords = st.session_state["keywords"]
    wc = st.session_state.get("word_count", 0)
    source = st.session_state.get("source")

    st.markdown("---")

    meta = f"**{len(keywords)} keywords** · {wc:,} words analyzed"
    if source:
        meta += f" · `{source}`"
    st.markdown(meta)

    # Legend
    col1, col2, col3 = st.columns(3)
    col1.markdown("🟣 High ≥ 0.75")
    col2.markdown("🟢 Mid 0.55–0.74")
    col3.markdown("🔴 Lower < 0.55")

    # Chips
    chips_html = "".join(chip(k["keyword"], k["score"]) for k in keywords)
    st.markdown(f'<div style="margin: 1rem 0">{chips_html}</div>', unsafe_allow_html=True)

    # Score table
    st.markdown("#### 📊 Relevance Scores")
    for i, k in enumerate(keywords):
        s = float(k["score"])
        col_rank, col_kw, col_bar = st.columns([0.5, 3, 6])
        col_rank.markdown(f"<span style='color:#6b6b8a'>{i+1}</span>", unsafe_allow_html=True)
        col_kw.markdown(f"`{k['keyword']}`")
        col_bar.progress(s, text=f"{s:.3f}")

    # Export
    st.markdown("---")
    csv = "Keyword,Score\n" + "\n".join(f'"{k["keyword"]}",{float(k["score"]):.3f}' for k in keywords)
    plain = ", ".join(k["keyword"] for k in keywords)

    col_a, col_b = st.columns(2)
    col_a.download_button("⬇️ Export CSV", csv, "keywords.csv", "text/csv", use_container_width=True)
    col_b.button("⎘ Copy Keywords", on_click=lambda: st.write(f"```\n{plain}\n```"), use_container_width=True)
    st.code(plain, language=None)
