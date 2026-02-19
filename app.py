import streamlit as st
from groq import Groq
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Keyword Finder",
    page_icon="🔍",
    layout="centered"
)

# ── Load API Key ──────────────────────────────────────────────────────
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=API_KEY)
except Exception:
    st.error("⚠️ API key not configured.")
    st.info("Go to: Streamlit Cloud → Your App → ⋮ → Settings → Secrets → paste:\n\n`GROQ_API_KEY = \"your-key-here\"`")
    st.stop()

# ── Constants ─────────────────────────────────────────────────────────
MAX_CHARS    = 5000
MAX_URL_LEN  = 2048   # URLs longer than this are rejected up front

# ── Restricted domains (cannot be scraped) ────────────────────────────
RESTRICTED_DOMAINS = {
    # Paywalled news
    "nytimes.com":        "New York Times — paywalled, requires subscription login.",
    "wsj.com":            "Wall Street Journal — paywalled, requires subscription login.",
    "ft.com":             "Financial Times — paywalled, requires subscription login.",
    "bloomberg.com":      "Bloomberg — paywalled, requires subscription login.",
    "economist.com":      "The Economist — paywalled, requires subscription login.",
    "washingtonpost.com": "Washington Post — paywalled, requires subscription login.",
    "theatlantic.com":    "The Atlantic — paywalled after a few free articles.",
    "newyorker.com":      "The New Yorker — paywalled after a few free articles.",
    "hbr.org":            "Harvard Business Review — paywalled, requires subscription.",
    "thetimes.co.uk":     "The Times UK — paywalled, requires subscription login.",

    # Login-required / anti-scrape
    "medium.com":         "Medium — login wall after a few free reads; automated access is blocked.",
    "substack.com":       "Substack — many newsletters are behind a subscriber login.",
    "quora.com":          "Quora — login wall blocks content for automated requests.",
    "linkedin.com":       "LinkedIn — requires login; automated access is blocked by policy.",
    "facebook.com":       "Facebook — requires login; content is not publicly accessible.",
    "instagram.com":      "Instagram — requires login; content is not publicly accessible.",
    "twitter.com":        "Twitter/X — API access required; direct scraping is blocked.",
    "x.com":              "Twitter/X — API access required; direct scraping is blocked.",
    "reddit.com":         "Reddit — heavy bot-detection; most content blocks automated requests.",
    "pinterest.com":      "Pinterest — requires login for full content access.",
    "tiktok.com":         "TikTok — video platform, no readable text to extract.",

    # Academic / document platforms
    "researchgate.net":   "ResearchGate — academic papers require login or are paywalled.",
    "academia.edu":       "Academia.edu — requires login for full paper access.",
    "jstor.org":          "JSTOR — academic journal access requires institutional login.",
    "sciencedirect.com":  "ScienceDirect — Elsevier paywalled journals.",
    "springer.com":       "Springer — paywalled academic publisher.",
    "nature.com":         "Nature — paywalled academic publisher.",
    "ieee.org":           "IEEE Xplore — paywalled academic papers.",
    "dl.acm.org":         "ACM Digital Library — paywalled academic papers.",

    # Document / file hosts
    "docs.google.com":    "Google Docs — requires Google login; not publicly accessible.",
    "drive.google.com":   "Google Drive — requires Google login; not publicly accessible.",
    "dropbox.com":        "Dropbox — shared files require authentication or special links.",
    "onedrive.live.com":  "OneDrive — requires Microsoft login.",
    "sharepoint.com":     "SharePoint — requires Microsoft/organisational login.",
    "notion.so":          "Notion — most pages require login or are private.",
    "slideshare.net":     "SlideShare — heavy bot-detection; presentation text hard to extract.",

    # Video / audio
    "youtube.com":        "YouTube — video platform; no readable article text to extract.",
    "youtu.be":           "YouTube — video platform; no readable article text to extract.",
    "vimeo.com":          "Vimeo — video platform; no readable article text to extract.",
    "spotify.com":        "Spotify — audio platform; no readable text content to extract.",
    "podcasts.apple.com": "Apple Podcasts — audio platform; no readable text content to extract.",

    # E-commerce (thin/dynamic content)
    "amazon.com":         "Amazon — product pages are heavily JavaScript-rendered and bot-protected.",
    "ebay.com":           "eBay — listing pages use dynamic rendering that blocks plain HTTP fetch.",
    "etsy.com":           "Etsy — shop pages are JavaScript-rendered and bot-protected.",
}

# ── Supported URL types ───────────────────────────────────────────────
SUPPORTED_TYPES = [
    ("✅ Public blog posts", "e.g. WordPress, Blogger, Ghost, personal sites"),
    ("✅ News articles", "publicly accessible pages without a paywall"),
    ("✅ Wikipedia pages", "all language editions supported"),
    ("✅ Company / product pages", "marketing pages, landing pages, about pages"),
    ("✅ Documentation sites", "ReadTheDocs, GitHub Pages, official docs"),
    ("✅ Government & NGO pages", ".gov, .org public pages"),
    ("✅ Stack Overflow threads", "public Q&A pages"),
    ("✅ Forum posts", "publicly accessible threads on Discourse, phpBB, etc."),
]

NOT_SUPPORTED_TYPES = [
    ("❌ PDF files", ".pdf links or pages serving application/pdf"),
    ("❌ Word / PowerPoint / Excel", ".docx, .pptx, .xlsx direct file links"),
    ("❌ Image files", ".jpg, .png, .svg, .gif, .webp"),
    ("❌ Paywalled articles", "NYT, WSJ, Bloomberg, FT, The Economist, etc."),
    ("❌ Login-required pages", "LinkedIn, Facebook, Instagram, Medium, Quora"),
    ("❌ Google Docs / Drive", "requires Google account authentication"),
    ("❌ Academic papers", "JSTOR, Springer, IEEE, ScienceDirect (paywalled)"),
    ("❌ Video / Audio platforms", "YouTube, Vimeo, Spotify, Apple Podcasts"),
    ("❌ JavaScript-only pages", "pages that load content only via JS frameworks"),
    ("❌ Dark web / private URLs", "non-public or locally hosted pages"),
]

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
.char-counter { text-align: right; font-size: 0.75rem; margin-top: 0.25rem; }
.char-counter.ok   { color: #6b6b8a; }
.char-counter.warn { color: #f39c12; }
.char-counter.over { color: #ff6584; }
.limit-banner {
    background: rgba(255,101,132,0.1); border: 1px solid rgba(255,101,132,0.35);
    color: #ff8fa3; border-radius: 10px; padding: 0.6rem 1rem;
    font-size: 0.82rem; margin-bottom: 0.75rem;
}
.error-box {
    background: rgba(255,101,132,0.08); border: 1px solid rgba(255,101,132,0.4);
    border-radius: 12px; padding: 1rem 1.2rem; margin: 0.75rem 0;
}
.error-box .error-title { color: #ff6584; font-size: 0.95rem; font-weight: bold; margin-bottom: 0.4rem; }
.error-box .error-reason { color: #e8e8f0; font-size: 0.83rem; margin-bottom: 0.5rem; }
.error-box .error-tip {
    color: #6b6b8a; font-size: 0.78rem;
    border-top: 1px solid #2a2a3d; padding-top: 0.5rem; margin-top: 0.5rem;
}
.info-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin: 0.5rem 0 1rem;
}
.info-card {
    background: #12121a; border: 1px solid #2a2a3d;
    border-radius: 10px; padding: 0.7rem 0.9rem;
}
.info-card .ic-label { font-size: 0.78rem; color: #e8e8f0; }
.info-card .ic-sub   { font-size: 0.68rem; color: #6b6b8a; margin-top: 0.1rem; }
.url-rules-box {
    background: #12121a; border: 1px solid #2a2a3d;
    border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.75rem;
    font-size: 0.78rem; color: #6b6b8a; line-height: 1.7;
}
.url-rules-box b { color: #a099ff; }
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
    border: none !important; border-radius: 12px !important; padding: 0.75rem !important;
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

# ── Header ────────────────────────────────────────────────────────────
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
st.sidebar.markdown(f"<small style='color:#6b6b8a'>Max input: {MAX_CHARS:,} characters<br>Max URL length: {MAX_URL_LEN} characters</small>", unsafe_allow_html=True)
st.sidebar.markdown("<small style='color:#6b6b8a'>AI Keyword Finder · v1.3</small>", unsafe_allow_html=True)


# ── Structured Error ──────────────────────────────────────────────────
class FetchError(Exception):
    def __init__(self, reason: str, tip: str):
        super().__init__(reason)
        self.reason = reason
        self.tip    = tip


def show_fetch_error(url: str, reason: str, tip: str):
    hostname = url
    try:
        hostname = urllib.parse.urlparse(url).hostname or url
    except Exception:
        pass
    st.markdown(
        f"""<div class="error-box">
            <div class="error-title">❌ Could not extract content from <code>{hostname}</code></div>
            <div class="error-reason">📌 Reason: {reason}</div>
            <div class="error-tip">💡 Tip: {tip}</div>
        </div>""",
        unsafe_allow_html=True
    )


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
{text[:MAX_CHARS]}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1000
    )
    raw     = response.choices[0].message.content.strip()
    cleaned = re.sub(r'```json|```', '', raw).strip()
    return json.loads(cleaned)


# ── HTML Parser ───────────────────────────────────────────────────────
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags  = {'script','style','nav','footer','header','aside','noscript','form'}
        self.skip       = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags: self.skip += 1

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip > 0: self.skip -= 1

    def handle_data(self, data):
        if self.skip == 0:
            s = data.strip()
            if s: self.text_parts.append(s)

    def get_text(self):
        return ' '.join(self.text_parts)


def detect_url_type(url: str) -> str:
    lower = url.lower().split("?")[0]
    if lower.endswith(".pdf"):                              return "pdf"
    if lower.endswith((".ppt", ".pptx")):                  return "ppt"
    if lower.endswith((".doc", ".docx")):                  return "doc"
    if lower.endswith((".xls", ".xlsx")):                  return "excel"
    if lower.endswith((".jpg",".jpeg",".png",
                        ".gif",".svg",".webp")):           return "image"
    return "html"


def get_restricted_reason(url: str):
    """Return (domain, reason) if the URL matches a restricted domain, else None."""
    try:
        hostname = urllib.parse.urlparse(url).hostname or ""
        hostname = hostname.lower().removeprefix("www.")
        for domain, reason in RESTRICTED_DOMAINS.items():
            if hostname == domain or hostname.endswith("." + domain):
                return domain, reason
    except Exception:
        pass
    return None


def fetch_url_content(url: str) -> str:

    # ── URL length check ──────────────────────────────────────────────
    if len(url) > MAX_URL_LEN:
        raise FetchError(
            f"The URL is too long ({len(url)} characters). Maximum allowed is {MAX_URL_LEN} characters.",
            "Shorten the URL or remove unnecessary query parameters and try again."
        )

    # ── Restricted domain check ───────────────────────────────────────
    restricted = get_restricted_reason(url)
    if restricted:
        domain, why = restricted
        raise FetchError(
            f"'{domain}' is a restricted website. {why}",
            "Copy the article text from the page manually and paste it into the Text Input tab."
        )

    # ── File type check ───────────────────────────────────────────────
    url_type = detect_url_type(url)
    blocked = {
        "pdf":   ("This is a PDF file. PDF content cannot be extracted directly.",
                  "Download the PDF, copy its text, and paste it into the Text Input tab."),
        "ppt":   ("This is a PowerPoint file (.ppt/.pptx). Slide content cannot be extracted from a direct file link.",
                  "Open the file, copy the slide text, and paste it into the Text Input tab."),
        "doc":   ("This is a Word document (.doc/.docx). Direct file links cannot be read here.",
                  "Open the document, copy its text, and paste it into the Text Input tab."),
        "excel": ("This is an Excel file (.xls/.xlsx). Spreadsheet data cannot be extracted from a direct link.",
                  "Copy the relevant cells as text and paste them into the Text Input tab."),
        "image": ("This URL points to an image file. Images contain no readable text.",
                  "If the image has text, transcribe it manually and paste it into the Text Input tab."),
    }
    if url_type in blocked:
        raise FetchError(*blocked[url_type])

    # ── HTTP fetch ────────────────────────────────────────────────────
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "application/pdf" in content_type:
                raise FetchError(
                    "The server returned a PDF file (Content-Type: application/pdf). PDF text cannot be parsed here.",
                    "Download the PDF, copy its text, and paste it into the Text Input tab."
                )
            if any(t in content_type for t in [
                "application/octet-stream", "application/zip",
                "application/msword", "application/vnd"
            ]):
                raise FetchError(
                    f"The server returned a binary/Office file ({content_type.split(';')[0].strip()}). This cannot be read as text.",
                    "Open the file on your device, copy the text, and paste it into the Text Input tab."
                )
            html = resp.read().decode('utf-8', errors='ignore')

    except FetchError:
        raise

    except urllib.error.HTTPError as e:
        http_errors = {
            401: ("Access denied — the page requires login or authentication (HTTP 401).",
                  "Log in to the website in your browser, copy the article text, and paste it into the Text Input tab."),
            403: ("Access forbidden — the website is blocking automated requests (HTTP 403).",
                  "Open the page in your browser, copy the text, and paste it into the Text Input tab."),
            404: ("Page not found (HTTP 404). The URL may be broken or the content removed.",
                  "Double-check the URL is correct and the page still exists."),
            429: ("Too many requests — the website is rate-limiting (HTTP 429).",
                  "Wait a moment and try again, or copy-paste the text manually."),
            500: ("The website returned a server error (HTTP 500).",
                  "The site may be temporarily down. Try again later."),
            503: ("The website is temporarily unavailable (HTTP 503).",
                  "Try again in a few minutes."),
        }
        reason, tip = http_errors.get(e.code, (
            f"The website returned HTTP error {e.code}.",
            "Try opening the URL in your browser and copy-pasting the text."
        ))
        raise FetchError(reason, tip)

    except urllib.error.URLError as e:
        rs = str(e.reason).lower()
        if "timed out" in rs or "timeout" in rs:
            raise FetchError(
                "The request timed out — the website took too long to respond.",
                "The site may be slow or blocking bots. Try again or paste the text manually."
            )
        if "ssl" in rs or "certificate" in rs:
            raise FetchError(
                "An SSL/TLS certificate error occurred. The site's security certificate may be invalid.",
                "Try opening the page in your browser and copy-pasting the content."
            )
        raise FetchError(
            f"Could not reach the URL — network error: {e.reason}",
            "Check that the URL is correct and publicly accessible (not behind a VPN or firewall)."
        )

    except Exception as e:
        raise FetchError(
            f"An unexpected error occurred while fetching the page: {str(e)}",
            "Try copying the page text manually and pasting it into the Text Input tab."
        )

    # ── Raw PDF binary check ──────────────────────────────────────────
    if html.startswith("%PDF-") or "\x00" in html[:200]:
        raise FetchError(
            "The page is serving raw PDF or binary data — no readable HTML text was found.",
            "Download the PDF, copy its text, and paste it into the Text Input tab."
        )

    # ── Parse HTML ────────────────────────────────────────────────────
    parser = TextExtractor()
    parser.feed(html)
    text = parser.get_text()
    text = re.sub(r'\s+', ' ', text).strip()

    # ── Paywall detection ─────────────────────────────────────────────
    paywall_signals = [
        "subscribe to read", "sign in to read", "create a free account to continue",
        "this content is for subscribers", "log in to access",
        "subscribe now to continue reading", "members only",
        "premium content", "unlock this article"
    ]
    if any(sig in text.lower() for sig in paywall_signals) and len(text.split()) < 80:
        raise FetchError(
            "This page appears to be behind a paywall or login wall. Only a short preview was accessible.",
            "If you have a subscription, log in in your browser, copy the full text, and paste it into the Text Input tab."
        )

    # ── Too little text ───────────────────────────────────────────────
    if len(text.split()) < 30:
        raise FetchError(
            "Not enough readable text was found on this page (fewer than 30 words extracted). "
            "The page may be JavaScript-rendered, mostly images, or blocking automated access.",
            "Open the page in your browser, copy the visible text, and paste it into the Text Input tab."
        )

    return text[:MAX_CHARS]


# ── Helpers ───────────────────────────────────────────────────────────
def chip(keyword, score):
    s   = float(score)
    cls = "keyword-chip-high" if s >= 0.75 else "keyword-chip-mid" if s >= 0.55 else "keyword-chip-low"
    return f'<span class="{cls}">{keyword} <small style="opacity:0.65">{s:.2f}</small></span>'

def char_counter_html(current, limit):
    pct = current / limit
    css_class = "over" if current > limit else "warn" if pct >= 0.85 else "ok"
    return f'<div class="char-counter {css_class}">{current:,} / {limit:,} characters</div>'


# ── Input Tabs ────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📄 Text Input", "🌐 URL Input", "ℹ️ URL Guidelines"])

with tab1:
    text_input = st.text_area(
        "text", height=200,
        placeholder="Enter any article, blog post, product description, or content here...",
        label_visibility="collapsed"
    )
    char_count = len(text_input)
    st.markdown(char_counter_html(char_count, MAX_CHARS), unsafe_allow_html=True)
    if char_count > MAX_CHARS:
        st.markdown(
            f'<div class="limit-banner">⚠️ Input exceeds {MAX_CHARS:,} characters. '
            f'Only the first {MAX_CHARS:,} characters will be analysed.</div>',
            unsafe_allow_html=True
        )
    run_text = st.button("🔍 Extract Keywords", key="btn_text", use_container_width=True)

with tab2:
    # ── Quick rules reminder ──────────────────────────────────────────
    st.markdown(
        f"""<div class="url-rules-box">
        <b>URL Rules</b><br>
        • Max URL length: <b>{MAX_URL_LEN} characters</b><br>
        • Only <b>publicly accessible</b> web pages (no login required)<br>
        • Only <b>HTML pages</b> — no PDFs, Word docs, spreadsheets, or images<br>
        • No paywalled or restricted sites (see <b>ℹ️ URL Guidelines</b> tab for full list)<br>
        • First <b>{MAX_CHARS:,} characters</b> of page text will be analysed
        </div>""",
        unsafe_allow_html=True
    )
    url_input = st.text_input(
        "url", placeholder="https://example.com/article",
        label_visibility="collapsed"
    )
    if url_input:
        url_len = len(url_input)
        url_len_class = "over" if url_len > MAX_URL_LEN else "ok"
        st.markdown(
            f'<div class="char-counter {url_len_class}">URL length: {url_len} / {MAX_URL_LEN} characters</div>',
            unsafe_allow_html=True
        )
        # Warn about restricted domain before they even click extract
        restricted = get_restricted_reason(url_input)
        if restricted:
            domain, why = restricted
            st.markdown(
                f'<div class="limit-banner">⚠️ <b>{domain}</b> is a restricted site — {why}</div>',
                unsafe_allow_html=True
            )

    run_url = st.button("🔍 Extract Keywords", key="btn_url", use_container_width=True)

with tab3:
    st.markdown("### 🌐 What URLs can be extracted?")
    st.markdown(
        "This tool fetches the **raw HTML** of a page and extracts visible text. "
        f"Only the first **{MAX_CHARS:,} characters** of extracted text are sent for analysis. "
        f"URLs must be **under {MAX_URL_LEN} characters** long."
    )

    col_yes, col_no = st.columns(2)
    with col_yes:
        st.markdown("#### ✅ Supported")
        cards_yes = "".join(
            f'<div class="info-card"><div class="ic-label">{label}</div><div class="ic-sub">{sub}</div></div>'
            for label, sub in SUPPORTED_TYPES
        )
        st.markdown(f'<div style="display:flex;flex-direction:column;gap:0.5rem">{cards_yes}</div>', unsafe_allow_html=True)

    with col_no:
        st.markdown("#### ❌ Not Supported")
        cards_no = "".join(
            f'<div class="info-card"><div class="ic-label">{label}</div><div class="ic-sub">{sub}</div></div>'
            for label, sub in NOT_SUPPORTED_TYPES
        )
        st.markdown(f'<div style="display:flex;flex-direction:column;gap:0.5rem">{cards_no}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 🚫 Restricted Websites")
    st.caption("These sites are blocked because they use paywalls, login walls, bot protection, or are non-text platforms.")

    # Group restricted domains into categories for display
    groups = {
        "📰 Paywalled News": ["nytimes.com","wsj.com","ft.com","bloomberg.com","economist.com",
                               "washingtonpost.com","theatlantic.com","newyorker.com","hbr.org","thetimes.co.uk"],
        "🔐 Login-Required": ["medium.com","substack.com","quora.com","linkedin.com","facebook.com",
                               "instagram.com","twitter.com","x.com","reddit.com","pinterest.com","tiktok.com"],
        "🎓 Academic / Paywalled Journals": ["researchgate.net","academia.edu","jstor.org",
                                              "sciencedirect.com","springer.com","nature.com","ieee.org","dl.acm.org"],
        "📁 Document / Cloud Storage": ["docs.google.com","drive.google.com","dropbox.com",
                                         "onedrive.live.com","sharepoint.com","notion.so","slideshare.net"],
        "🎬 Video / Audio Platforms": ["youtube.com","youtu.be","vimeo.com","spotify.com","podcasts.apple.com"],
        "🛒 E-Commerce": ["amazon.com","ebay.com","etsy.com"],
    }

    for group_label, domains in groups.items():
        with st.expander(group_label):
            for d in domains:
                reason = RESTRICTED_DOMAINS.get(d, "")
                st.markdown(f"**`{d}`** — {reason}")

    st.markdown("---")
    st.info(
        "💡 **Workaround for any restricted page:** Open the page in your browser, "
        "select all the text (Ctrl+A / Cmd+A), copy it, and paste it directly into the **📄 Text Input** tab."
    )


# ── Run: Text ─────────────────────────────────────────────────────────
if run_text:
    st.session_state.pop("fetch_error", None)
    if not text_input.strip():
        st.error("Please paste some text first.")
    elif len(text_input.split()) < 20:
        st.error("Please provide at least 20 words.")
    else:
        processed = text_input[:MAX_CHARS]
        with st.spinner("🧠 Extracting keywords with AI..."):
            try:
                kws = extract_keywords(processed, top_n, ngram_max, diversity)
                st.session_state.keywords   = kws
                st.session_state.word_count = len(processed.split())
                st.session_state.char_count = len(processed)
                st.session_state.truncated  = len(text_input) > MAX_CHARS
                st.session_state.source     = None
            except Exception as e:
                st.error(f"Extraction failed: {e}")


# ── Run: URL ──────────────────────────────────────────────────────────
if run_url:
    st.session_state.pop("fetch_error", None)
    st.session_state.pop("keywords", None)

    if not url_input.strip():
        st.error("Please enter a URL.")
    elif not url_input.startswith("http"):
        st.error("URL must start with https://")
    else:
        content = None
        with st.spinner("🌐 Fetching page content..."):
            try:
                content = fetch_url_content(url_input)
            except FetchError as fe:
                st.session_state.fetch_error = {"url": url_input, "reason": fe.reason, "tip": fe.tip}
            except Exception as e:
                st.session_state.fetch_error = {
                    "url": url_input,
                    "reason": f"An unexpected error occurred: {str(e)}",
                    "tip": "Try copying the page text manually and pasting it into the Text Input tab."
                }

        if content:
            with st.spinner("🧠 Extracting keywords with AI..."):
                try:
                    kws = extract_keywords(content, top_n, ngram_max, diversity)
                    st.session_state.keywords   = kws
                    st.session_state.word_count = len(content.split())
                    st.session_state.char_count = len(content)
                    st.session_state.truncated  = False
                    try:
                        st.session_state.source = urllib.parse.urlparse(url_input).hostname
                    except Exception:
                        st.session_state.source = url_input
                except Exception as e:
                    st.error(f"Extraction failed: {e}")


# ── Show Fetch Error ──────────────────────────────────────────────────
if st.session_state.get("fetch_error"):
    err = st.session_state.fetch_error
    show_fetch_error(err["url"], err["reason"], err["tip"])


# ── Results ───────────────────────────────────────────────────────────
if "keywords" in st.session_state:
    kws       = st.session_state.keywords
    wc        = st.session_state.get("word_count", 0)
    cc        = st.session_state.get("char_count", 0)
    source    = st.session_state.get("source")
    truncated = st.session_state.get("truncated", False)

    st.markdown("---")
    if truncated:
        st.info(f"ℹ️ Input was trimmed to the first {MAX_CHARS:,} characters for analysis.")

    meta = f"**{len(kws)} keywords** · {wc:,} words · {cc:,} chars analysed"
    if source:
        meta += f" · `{source}`"
    st.markdown(meta)

    c1, c2, c3 = st.columns(3)
    c1.markdown("🟣 High ≥ 0.75")
    c2.markdown("🟢 Mid 0.55–0.74")
    c3.markdown("🔴 Lower < 0.55")

    st.markdown(
        '<div style="margin:1rem 0">' +
        "".join(chip(k["keyword"], k["score"]) for k in kws) +
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("#### 📊 Relevance Scores")
    for i, k in enumerate(kws):
        s = float(k["score"])
        r, kw, bar = st.columns([0.5, 3, 6])
        r.markdown(f"<span style='color:#6b6b8a;font-size:.8rem'>{i+1}</span>", unsafe_allow_html=True)
        kw.markdown(f"`{k['keyword']}`")
        bar.progress(s, text=f"{s:.3f}")

    st.markdown("---")
    csv   = "Keyword,Score\n" + "\n".join(f'"{k["keyword"]}",{float(k["score"]):.3f}' for k in kws)
    plain = ", ".join(k["keyword"] for k in kws)

    col_a, col_b = st.columns(2)
    col_a.download_button("⬇️ Export CSV", csv, "keywords.csv", "text/csv", use_container_width=True)
    with col_b:
        if st.button("⎘ Copy Keywords", use_container_width=True):
            st.code(plain, language=None)
