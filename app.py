import streamlit as st
from groq import Groq
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser

st.set_page_config(
    page_title="LEXIS · AI Keyword Engine",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

try:
    API_KEY = st.secrets["GROQ_API_KEY"]
    client  = Groq(api_key=API_KEY)
except Exception:
    st.error("⚠️ API key not configured.")
    st.stop()

MAX_CHARS   = 5000
MAX_URL_LEN = 2048

RESTRICTED_DOMAINS = {
    "nytimes.com":        "Paywalled — subscription required.",
    "wsj.com":            "Paywalled — subscription required.",
    "ft.com":             "Paywalled — subscription required.",
    "bloomberg.com":      "Paywalled — subscription required.",
    "economist.com":      "Paywalled — subscription required.",
    "washingtonpost.com": "Paywalled — subscription required.",
    "theatlantic.com":    "Paywalled after a few free articles.",
    "newyorker.com":      "Paywalled after a few free articles.",
    "hbr.org":            "Paywalled — subscription required.",
    "thetimes.co.uk":     "Paywalled — subscription required.",
    "medium.com":         "Login wall after a few free reads.",
    "substack.com":       "Many newsletters require subscriber login.",
    "quora.com":          "Login wall blocks automated access.",
    "linkedin.com":       "Requires login — scraping blocked by policy.",
    "facebook.com":       "Requires login — not publicly accessible.",
    "instagram.com":      "Requires login — not publicly accessible.",
    "twitter.com":        "API access required — scraping blocked.",
    "x.com":              "API access required — scraping blocked.",
    "reddit.com":         "Heavy bot-detection; most content blocked.",
    "pinterest.com":      "Requires login for full content.",
    "tiktok.com":         "Video platform — no readable text.",
    "researchgate.net":   "Academic papers require login or paywall.",
    "academia.edu":       "Requires login for full paper access.",
    "jstor.org":          "Institutional login required.",
    "sciencedirect.com":  "Elsevier — paywalled journals.",
    "springer.com":       "Paywalled academic publisher.",
    "nature.com":         "Paywalled academic publisher.",
    "ieee.org":           "Paywalled academic papers.",
    "dl.acm.org":         "Paywalled academic papers.",
    "docs.google.com":    "Requires Google login.",
    "drive.google.com":   "Requires Google login.",
    "dropbox.com":        "Requires authentication.",
    "onedrive.live.com":  "Requires Microsoft login.",
    "notion.so":          "Most pages are private.",
    "youtube.com":        "Video platform — no article text.",
    "youtu.be":           "Video platform — no article text.",
    "vimeo.com":          "Video platform — no article text.",
    "spotify.com":        "Audio platform — no readable text.",
    "amazon.com":         "JavaScript-rendered and bot-protected.",
    "ebay.com":           "Dynamic rendering blocks plain fetch.",
}

SUPPORTED_TYPES = [
    ("Public blog posts", "WordPress, Ghost, Blogger, personal sites"),
    ("News articles", "Publicly accessible, no paywall"),
    ("Wikipedia pages", "All language editions"),
    ("Company / product pages", "Marketing, landing, about pages"),
    ("Documentation sites", "ReadTheDocs, GitHub Pages, official docs"),
    ("Government & NGO pages", ".gov and .org public pages"),
    ("Stack Overflow threads", "Public Q&A pages"),
    ("Forum posts", "Discourse, phpBB, public threads"),
]

NOT_SUPPORTED_TYPES = [
    ("PDF files", ".pdf links or application/pdf responses"),
    ("Word / PowerPoint / Excel", "Direct .docx, .pptx, .xlsx file links"),
    ("Image files", ".jpg, .png, .svg, .gif, .webp"),
    ("Paywalled articles", "NYT, WSJ, Bloomberg, FT, Economist…"),
    ("Login-required pages", "LinkedIn, Facebook, Medium, Quora…"),
    ("Google Docs / Drive", "Requires Google account"),
    ("Academic papers", "JSTOR, Springer, IEEE (paywalled)"),
    ("Video / Audio", "YouTube, Vimeo, Spotify, Apple Podcasts"),
    ("JS-only pages", "Content loaded exclusively by JavaScript"),
]

# ─────────────────────────────────────────────────────────────────────
# CSS  —  Gold × Royal Blue, centered, premium dark
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;900&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:          #0e0e14;
  --surface:     #16161f;
  --surface2:    #1c1c28;
  --border:      rgba(212,175,55,0.13);
  --border-hi:   rgba(212,175,55,0.30);
  --border-blue: rgba(67,97,238,0.30);

  /* Gold palette */
  --gold:        #d4af37;
  --gold-light:  #ecd06f;
  --gold-dim:    #8a7228;
  --gold-pale:   rgba(212,175,55,0.08);

  /* Blue palette */
  --blue:        #4361ee;
  --blue-light:  #7b93f5;
  --blue-dim:    #2a3d99;
  --blue-pale:   rgba(67,97,238,0.08);

  --white:       #ede8f5;
  --muted:       #55546a;
  --muted2:      #888099;
  --danger:      #e63946;
  --warn:        #f4a261;
  --success:     #2ec4b6;
  --radius:      14px;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif !important;
  background: var(--bg) !important;
  color: var(--white) !important;
}

/* ── hide Streamlit chrome ── */
#MainMenu, footer, header,
.stDeployButton, [data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="collapsedControl"] { display: none !important; }

/* ── CENTERED layout — fix the left-drift ── */
.main .block-container {
  max-width: 820px !important;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  padding-bottom: 5rem !important;
  margin-left: auto !important;
  margin-right: auto !important;
}

/* ── Background mesh ── */
.stApp {
  background:
    radial-gradient(ellipse 65% 40% at 15% 5%,  rgba(212,175,55,0.07) 0%, transparent 60%),
    radial-gradient(ellipse 55% 45% at 85% 90%,  rgba(67,97,238,0.08)  0%, transparent 60%),
    radial-gradient(ellipse 40% 50% at 50% 50%,  rgba(67,97,238,0.04)  0%, transparent 65%),
    #0e0e14 !important;
}

/* subtle dot grid */
.stApp::after {
  content: '';
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: radial-gradient(rgba(212,175,55,0.035) 1px, transparent 1px);
  background-size: 32px 32px;
}

/* top accent bar */
[data-testid="stAppViewContainer"] > section > div:first-child {
  position: relative;
}
[data-testid="stAppViewContainer"] > section > div:first-child::before {
  content: '';
  display: block; width: 100%; height: 2px;
  background: linear-gradient(90deg, var(--blue) 0%, var(--gold) 50%, var(--blue) 100%);
  position: fixed; top: 0; left: 0; z-index: 999;
}

/* ── Hero ── */
.hero {
  text-align: center;
  padding: 3.5rem 0 2.2rem;
}
.hero-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.63rem; letter-spacing: 0.28em; text-transform: uppercase;
  color: var(--blue-light); margin-bottom: 1.4rem;
  display: flex; align-items: center; justify-content: center; gap: 0.9rem;
}
.hero-eyebrow::before, .hero-eyebrow::after {
  content: ''; display: block; width: 50px; height: 1px;
  background: linear-gradient(90deg, transparent, var(--blue-dim));
}
.hero-eyebrow::after { transform: scaleX(-1); }

.hero-title {
  font-family: 'Playfair Display', serif;
  font-size: clamp(4rem, 11vw, 7.5rem);
  font-weight: 900; letter-spacing: 0.06em; line-height: 1;
  background: linear-gradient(135deg, var(--gold-light) 0%, var(--gold) 40%, var(--blue-light) 75%, var(--blue) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  filter: drop-shadow(0 0 48px rgba(212,175,55,0.18));
  margin-bottom: 0.3rem;
}
.hero-divider {
  display: flex; align-items: center; justify-content: center; gap: 0.7rem; margin: 1rem 0;
}
.hero-divider-line { flex: 1; max-width: 100px; height: 1px; background: var(--border); }
.hero-divider-gem  { width: 5px; height: 5px; background: var(--gold); transform: rotate(45deg); flex-shrink: 0; }
.hero-sub {
  font-size: 0.92rem; font-weight: 300; color: var(--muted2);
  max-width: 420px; margin: 0 auto; line-height: 1.75; letter-spacing: 0.02em;
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 0.5rem;
  margin-top: 1.6rem;
  font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
  letter-spacing: 0.16em; text-transform: uppercase;
  border: 1px solid var(--border); color: var(--gold-dim);
  padding: 0.38rem 1.1rem; border-radius: 999px;
  background: var(--gold-pale);
}
.hero-badge-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--blue); flex-shrink: 0;
  box-shadow: 0 0 6px var(--blue);
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(0.7); }
}

/* ── Stat strip ── */
.stat-strip {
  display: flex; margin: 2rem 0 2.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius); overflow: hidden;
  background: var(--surface); position: relative;
}
.stat-strip::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, var(--blue-dim), var(--gold), var(--blue-dim));
}
.stat-item {
  flex: 1; padding: 1.2rem 0; text-align: center;
  border-right: 1px solid var(--border);
}
.stat-item:last-child { border-right: none; }
.stat-val {
  font-family: 'Playfair Display', serif;
  font-size: 1.9rem; font-weight: 700; line-height: 1;
  background: linear-gradient(135deg, var(--gold) 0%, var(--blue-light) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.stat-lbl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.57rem; color: var(--muted);
  letter-spacing: 0.16em; text-transform: uppercase; margin-top: 0.3rem;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 4px !important; gap: 2px !important;
  margin-bottom: 1.4rem !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important; color: var(--muted2) !important;
  border-radius: 9px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.7rem !important; letter-spacing: 0.07em !important;
  padding: 0.5rem 1.1rem !important;
  transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--blue) 0%, var(--blue-dim) 100%) !important;
  color: #fff !important; font-weight: 600 !important;
  box-shadow: 0 2px 12px rgba(67,97,238,0.35) !important;
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
  color: var(--gold-light) !important; background: var(--gold-pale) !important;
}

/* ── Textarea & text input ── */
div[data-testid="stTextArea"] textarea {
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: 12px !important; color: var(--white) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.8rem !important; line-height: 1.75 !important;
  padding: 1rem 1.2rem !important; resize: none !important;
  transition: border-color 0.25s, box-shadow 0.25s !important;
}
div[data-testid="stTextArea"] textarea:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 3px rgba(67,97,238,0.12) !important; outline: none !important;
}
div[data-testid="stTextInput"] input {
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: 12px !important; color: var(--white) !important;
  font-family: 'JetBrains Mono', monospace !important; font-size: 0.8rem !important;
  padding: 0.75rem 1.2rem !important;
  transition: border-color 0.25s, box-shadow 0.25s !important;
}
div[data-testid="stTextInput"] input:focus {
  border-color: var(--blue) !important;
  box-shadow: 0 0 0 3px rgba(67,97,238,0.12) !important; outline: none !important;
}
div[data-testid="stSelectbox"] > div > div {
  background: var(--surface) !important; border: 1px solid var(--border) !important;
  border-radius: 10px !important; color: var(--white) !important;
  font-family: 'JetBrains Mono', monospace !important; font-size: 0.76rem !important;
}

/* ── Primary button ── */
.stButton > button {
  background: linear-gradient(135deg, var(--blue-dim) 0%, var(--blue) 50%, #5a75f0 100%) !important;
  color: #fff !important;
  font-family: 'Playfair Display', serif !important;
  font-size: 1.05rem !important; font-weight: 700 !important; letter-spacing: 0.1em !important;
  border: none !important; border-radius: 12px !important;
  padding: 0.8rem 2rem !important; width: 100% !important;
  box-shadow: 0 4px 20px rgba(67,97,238,0.25) !important;
  transition: all 0.25s ease !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 32px rgba(67,97,238,0.45) !important;
  filter: brightness(1.1) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Download button ── */
.stDownloadButton > button {
  background: var(--surface) !important;
  border: 1px solid var(--border-hi) !important; color: var(--gold-dim) !important;
  font-family: 'JetBrains Mono', monospace !important; font-size: 0.72rem !important;
  border-radius: 10px !important; padding: 0.6rem 1rem !important;
  transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
  border-color: var(--gold) !important; color: var(--gold) !important;
  background: var(--gold-pale) !important; box-shadow: 0 4px 14px rgba(212,175,55,0.12) !important;
}

/* ── Counter bar ── */
.counter-row {
  display: flex; align-items: center; gap: 0.7rem;
  margin-top: 0.45rem;
  font-family: 'JetBrains Mono', monospace; font-size: 0.67rem;
}
.counter-bar-bg {
  flex: 1; height: 2px; background: var(--border);
  border-radius: 99px; overflow: hidden;
}
.counter-bar-fill { height: 100%; border-radius: 99px; transition: width 0.3s ease, background 0.3s ease; }
.counter-num       { color: var(--muted2); white-space: nowrap; }
.counter-num.warn  { color: var(--warn); }
.counter-num.over  { color: var(--danger); }

/* ── Panels / banners ── */
.rules-panel {
  background: var(--surface); border: 1px solid var(--border);
  border-left: 3px solid var(--blue);
  border-radius: var(--radius); padding: 1rem 1.2rem; margin-bottom: 1rem;
  font-family: 'JetBrains Mono', monospace; font-size: 0.71rem;
  line-height: 2; color: var(--muted2);
}
.rules-panel b         { color: var(--gold); }
.rules-panel .rp-title {
  font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--blue-light); margin-bottom: 0.4rem; display: block;
}
.warn-banner {
  background: rgba(244,162,97,0.07); border: 1px solid rgba(244,162,97,0.25);
  border-radius: 10px; padding: 0.6rem 1rem; margin: 0.5rem 0;
  font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--warn);
}
.limit-banner {
  background: rgba(230,57,70,0.07); border: 1px solid rgba(230,57,70,0.25);
  border-radius: 10px; padding: 0.6rem 1rem; margin: 0.5rem 0;
  font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--danger);
}
.trunc-notice {
  background: rgba(67,97,238,0.07); border: 1px solid rgba(67,97,238,0.22);
  border-radius: 10px; padding: 0.6rem 1rem; margin-bottom: 1rem;
  font-family: 'JetBrains Mono', monospace; font-size: 0.71rem; color: var(--blue-light);
}

/* ── Error card ── */
.error-card {
  background: rgba(230,57,70,0.05); border: 1px solid rgba(230,57,70,0.22);
  border-radius: var(--radius); padding: 1.25rem 1.4rem; margin: 1rem 0; position: relative;
}
.error-card::before {
  content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
  background: linear-gradient(90deg, var(--danger), var(--gold));
}
.error-card .ec-title {
  font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700;
  color: var(--danger); margin-bottom: 0.5rem;
}
.error-card .ec-host {
  font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--muted2);
  background: var(--surface2); border: 1px solid var(--border);
  padding: 0.18rem 0.6rem; border-radius: 6px; display: inline-block; margin-bottom: 0.75rem;
}
.error-card .ec-reason { font-size: 0.84rem; color: var(--white); line-height: 1.6; margin-bottom: 0.75rem; }
.error-card .ec-tip {
  font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--muted2);
  border-top: 1px solid var(--border); padding-top: 0.7rem; line-height: 1.7;
}
.error-card .ec-tip b { color: var(--blue-light); }

/* ── Results ── */
.results-header {
  display: flex; align-items: baseline; justify-content: space-between;
  border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin: 2rem 0 1.4rem;
  position: relative;
}
.results-header::after {
  content: ''; position: absolute; bottom: -1px; left: 0; width: 60px; height: 1px;
  background: linear-gradient(90deg, var(--gold), var(--blue));
}
.results-title {
  font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700;
  letter-spacing: 0.04em; color: var(--white);
}
.results-meta {
  font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
  color: var(--muted); text-align: right; line-height: 1.9;
}
.results-meta .rm-gold { color: var(--gold-dim); }
.results-meta .rm-blue { color: var(--blue-light); }

/* ── Legend ── */
.legend-row { display: flex; gap: 0.55rem; margin-bottom: 1.2rem; flex-wrap: wrap; }
.legend-pill {
  font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  padding: 0.25rem 0.7rem; border-radius: 999px;
  display: flex; align-items: center; gap: 0.38rem;
}
.legend-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }

/* High → Gold */
.legend-pill.hi { background: rgba(212,175,55,0.10); border: 1px solid rgba(212,175,55,0.32); color: var(--gold); }
.legend-pill.hi .legend-dot { background: var(--gold); }
/* Mid → Blue */
.legend-pill.md { background: rgba(67,97,238,0.10); border: 1px solid rgba(67,97,238,0.32); color: var(--blue-light); }
.legend-pill.md .legend-dot { background: var(--blue-light); }
/* Low → muted */
.legend-pill.lo { background: rgba(136,128,153,0.10); border: 1px solid rgba(136,128,153,0.25); color: var(--muted2); }
.legend-pill.lo .legend-dot { background: var(--muted2); }

/* ── Keyword chips ── */
.chips-wrap { display: flex; flex-wrap: wrap; gap: 0.45rem; margin: 0.9rem 0 1.8rem; }
.kchip {
  display: inline-flex; align-items: center; gap: 0.45rem;
  padding: 0.38rem 0.9rem; border-radius: 999px;
  font-family: 'JetBrains Mono', monospace; font-size: 0.76rem;
  transition: transform 0.15s ease, box-shadow 0.15s ease; cursor: default;
}
.kchip:hover { transform: translateY(-2px); }
.kchip.hi {
  background: rgba(212,175,55,0.10); border: 1px solid rgba(212,175,55,0.38); color: var(--gold);
}
.kchip.hi:hover { box-shadow: 0 4px 18px rgba(212,175,55,0.22); }
.kchip.md {
  background: rgba(67,97,238,0.10); border: 1px solid rgba(67,97,238,0.35); color: var(--blue-light);
}
.kchip.md:hover { box-shadow: 0 4px 18px rgba(67,97,238,0.25); }
.kchip.lo {
  background: rgba(136,128,153,0.08); border: 1px solid rgba(136,128,153,0.25); color: var(--muted2);
}
.kchip.lo:hover { box-shadow: 0 4px 14px rgba(136,128,153,0.15); }
.kchip-score {
  font-size: 0.6rem; opacity: 0.45;
  background: rgba(0,0,0,0.22); padding: 0.03rem 0.32rem; border-radius: 4px;
}

/* ── Score rows ── */
.score-section-title {
  font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 600;
  letter-spacing: 0.04em; color: var(--muted2); margin-bottom: 0.7rem;
}
.score-row {
  display: grid; grid-template-columns: 26px 1fr 180px;
  align-items: center; gap: 1rem;
  padding: 0.65rem 0; border-bottom: 1px solid var(--border);
}
.score-row:last-child { border-bottom: none; }
.score-idx { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: var(--muted); text-align: right; }
.score-kw  { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--white); }
.score-bar-wrap { display: flex; align-items: center; gap: 0.55rem; }
.score-bar-bg   { flex: 1; height: 3px; background: var(--border); border-radius: 99px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 99px; transition: width 0.6s cubic-bezier(.23,1,.32,1); }
.score-val { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: var(--muted); min-width: 36px; text-align: right; }

/* ── Guidelines cards ── */
.guide-title {
  font-family: 'Playfair Display', serif; font-size: 1.45rem; font-weight: 700;
  letter-spacing: 0.03em; color: var(--white); margin-bottom: 0.9rem;
}
.guide-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 0.75rem 1rem; margin-bottom: 0.45rem;
  transition: border-color 0.2s;
}
.guide-card:hover { border-color: var(--border-hi); }
.guide-card.yes { border-left: 3px solid var(--success); }
.guide-card.no  { border-left: 3px solid var(--danger); }
.guide-card .gc-label { font-size: 0.82rem; font-weight: 500; color: var(--white); margin-bottom: 0.18rem; }
.guide-card .gc-sub   { font-family: 'JetBrains Mono', monospace; font-size: 0.63rem; color: var(--muted); line-height: 1.5; }

/* ── Restricted domain chips ── */
.restricted-title {
  font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted);
  margin: 1.1rem 0 0.4rem;
}
.restricted-chips { display: flex; flex-wrap: wrap; gap: 0.32rem; }
.rchip {
  font-family: 'JetBrains Mono', monospace; font-size: 0.65rem;
  background: var(--blue-pale); border: 1px solid var(--border-blue);
  color: var(--blue-light); padding: 0.2rem 0.55rem; border-radius: 6px; cursor: help;
  transition: border-color 0.15s, color 0.15s;
}
.rchip:hover { border-color: var(--blue-light); color: #fff; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: var(--surface) !important; border-right: 1px solid var(--border) !important;
}
.sb-label {
  font-family: 'JetBrains Mono', monospace; font-size: 0.6rem;
  letter-spacing: 0.15em; text-transform: uppercase; color: var(--muted);
  margin-bottom: 0.25rem; display: block;
}

/* ── Misc overrides ── */
.stSpinner > div  { border-top-color: var(--gold) !important; }
.stCodeBlock pre  { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; }
[data-baseweb="popover"] { background: var(--surface2) !important; border: 1px solid var(--border) !important; }
[role="option"]   { color: var(--white) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.76rem !important; }
[role="option"]:hover { background: var(--blue-pale) !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <div class="hero-eyebrow">AI · Semantic Extraction Engine</div>
  <div class="hero-title">LEXIS</div>
  <div class="hero-divider">
    <div class="hero-divider-line"></div>
    <div class="hero-divider-gem"></div>
    <div class="hero-divider-line"></div>
  </div>
  <div class="hero-sub">Extract high-signal keywords from any text or URL using Groq-powered AI — instantly.</div>
  <div class="hero-badge">
    <span class="hero-badge-dot"></span>
    Powered by Groq · LLaMA 3.1 · v1.5
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# STAT STRIP
# ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="stat-strip">
  <div class="stat-item">
    <div class="stat-val">{MAX_CHARS:,}</div>
    <div class="stat-lbl">Max Chars</div>
  </div>
  <div class="stat-item">
    <div class="stat-val">{MAX_URL_LEN}</div>
    <div class="stat-lbl">Max URL Len</div>
  </div>
  <div class="stat-item">
    <div class="stat-val">20</div>
    <div class="stat-lbl">Max Keywords</div>
  </div>
  <div class="stat-item">
    <div class="stat-val">&lt;1s</div>
    <div class="stat-lbl">Avg Response</div>
  </div>
  <div class="stat-item">
    <div class="stat-val">{len(RESTRICTED_DOMAINS)}+</div>
    <div class="stat-lbl">Blocked Sites</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ◈ &nbsp;Settings")
    st.markdown('<span class="sb-label">How Many Keywords?</span>', unsafe_allow_html=True)
    top_n = st.selectbox("top_n", [5, 10, 15, 20], index=1, label_visibility="collapsed",
                         help="Choose how many keywords to extract. Default is 10.")
    st.caption(f"Will extract exactly {top_n} keywords.")
    st.markdown('<span class="sb-label">Keyphrase Length</span>', unsafe_allow_html=True)
    ngram_max = st.selectbox("ngram", [1,2,3],
        format_func=lambda x:{1:"Single words",2:"1–2 word phrases",3:"1–3 word phrases"}[x],
        index=1, label_visibility="collapsed")
    st.markdown('<span class="sb-label">Diversity Mode</span>', unsafe_allow_html=True)
    diversity = st.selectbox("div", ["none","mmr","maxsum"],
        format_func=lambda x:{"none":"None — raw scores","mmr":"MMR — balanced","maxsum":"Max Sum — diverse"}[x],
        index=1, label_visibility="collapsed")
    st.markdown("---")
    st.info(f"Extracting **{top_n} keywords** per run. Change above to get more or fewer.")
    st.markdown(f"<small style='font-family:JetBrains Mono,monospace;font-size:0.62rem;color:var(--muted)'>Max chars: {MAX_CHARS:,}<br>Max URL: {MAX_URL_LEN}<br><br>LEXIS · AI Keyword Engine</small>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────
class FetchError(Exception):
    def __init__(self, reason, tip):
        super().__init__(reason)
        self.reason = reason
        self.tip    = tip

def get_restricted_reason(url):
    try:
        h = urllib.parse.urlparse(url).hostname or ""
        h = h.lower().removeprefix("www.")
        for domain, reason in RESTRICTED_DOMAINS.items():
            if h == domain or h.endswith("." + domain):
                return domain, reason
    except Exception:
        pass
    return None

def detect_url_type(url):
    l = url.lower().split("?")[0]
    if l.endswith(".pdf"):                        return "pdf"
    if l.endswith((".ppt",".pptx")):             return "ppt"
    if l.endswith((".doc",".docx")):             return "doc"
    if l.endswith((".xls",".xlsx")):             return "excel"
    if l.endswith((".jpg",".jpeg",".png",
                    ".gif",".svg",".webp")):     return "image"
    return "html"

def counter_html(current, limit):
    pct   = min(current / limit, 1.0)
    color = "#e63946" if current > limit else "#f4a261" if pct >= 0.85 else "#d4af37"
    cls   = "over" if current > limit else "warn" if pct >= 0.85 else ""
    return f"""<div class="counter-row">
      <span class="counter-num {cls}">{current:,} chars</span>
      <div class="counter-bar-bg">
        <div class="counter-bar-fill" style="width:{pct*100:.1f}%;background:{color}"></div>
      </div>
      <span class="counter-num">{limit:,} max</span>
    </div>"""

def chip_html(kw, score):
    s   = float(score)
    cls = "hi" if s >= 0.75 else "md" if s >= 0.55 else "lo"
    return f'<span class="kchip {cls}">{kw}<span class="kchip-score">{s:.2f}</span></span>'

def score_row_html(kw, score, idx):
    s = float(score)
    # High=gold, Mid=blue, Low=muted
    color = "#d4af37" if s >= 0.75 else "#7b93f5" if s >= 0.55 else "#55546a"
    return f"""<div class="score-row">
      <span class="score-idx">{idx:02d}</span>
      <span class="score-kw">{kw}</span>
      <div class="score-bar-wrap">
        <div class="score-bar-bg">
          <div class="score-bar-fill" style="width:{s*100:.1f}%;background:{color}"></div>
        </div>
        <span class="score-val">{s:.3f}</span>
      </div>
    </div>"""

def show_fetch_error(url, reason, tip):
    h = url
    try: h = urllib.parse.urlparse(url).hostname or url
    except: pass
    st.markdown(f"""<div class="error-card">
      <div class="ec-title">Extraction Failed</div>
      <div class="ec-host">{h}</div>
      <div class="ec-reason">{reason}</div>
      <div class="ec-tip">◈ &nbsp;<b>What to do:</b> {tip}</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# GROQ EXTRACTION
# ─────────────────────────────────────────────────────────────────────
def extract_keywords(text, top_n, ngram_max, diversity):
    drule = {"mmr":"Apply MMR diversity — avoid repeating similar root concepts.",
             "maxsum":"Maximize diversity — make keywords as distinct as possible.",
             "none":"Return purely by relevance score, no diversity constraint."}[diversity]
    lrule = {1:"single words only (1 word each)",
             2:"1 to 2 words per keyphrase",
             3:"1 to 3 words per keyphrase"}[ngram_max]
    prompt = (
        f"You are a semantic keyword extraction engine (like KeyBERT).\n\n"
        f"TASK: Extract EXACTLY {top_n} keywords from the text below. "
        f"You MUST return exactly {top_n} items — no more, no fewer.\n\n"
        f"RULES:\n"
        f"- Keyphrase length: {lrule}\n"
        f"- {drule}\n"
        f"- Score each keyword 0.00 to 1.00 based on semantic importance\n"
        f"- Do NOT repeat similar keywords\n"
        f"- CRITICAL: Return ONLY a raw JSON array. No markdown, no backticks, no explanation\n"
        f"- The array MUST have EXACTLY {top_n} objects\n\n"
        f"OUTPUT FORMAT:\n"
        f'[{{"keyword":"example","score":0.85}},{{"keyword":"another","score":0.72}}]\n\n'
        f"TEXT TO ANALYSE:\n{text[:MAX_CHARS]}"
    )
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.1,
        max_tokens=2000
    )
    raw     = resp.choices[0].message.content.strip()
    cleaned = re.sub(r'```json|```', '', raw).strip()
    match   = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    return json.loads(cleaned)[:top_n]


# ─────────────────────────────────────────────────────────────────────
# HTML PARSER
# ─────────────────────────────────────────────────────────────────────
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_tags = {'script','style','nav','footer','header','aside','noscript','form'}
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags: self.skip += 1
    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip > 0: self.skip -= 1
    def handle_data(self, data):
        if self.skip == 0:
            s = data.strip()
            if s: self.parts.append(s)
    def get_text(self): return ' '.join(self.parts)


def fetch_url_content(url):
    if len(url) > MAX_URL_LEN:
        raise FetchError(f"URL is too long ({len(url)} chars). Max allowed: {MAX_URL_LEN}.",
                         "Remove extra query parameters and try again.")
    r = get_restricted_reason(url)
    if r:
        d, w = r
        raise FetchError(f"'{d}' is a restricted website. {w}",
                         "Copy the article text manually and paste into the Text Input tab.")
    ut = detect_url_type(url)
    blocked = {
        "pdf":  ("This is a PDF file — cannot extract PDF text directly.",
                 "Download the PDF, copy its text, paste into Text Input tab."),
        "ppt":  ("PowerPoint file — slide text cannot be extracted from a direct link.",
                 "Open the file, copy slide text, paste into Text Input tab."),
        "doc":  ("Word document — .docx links cannot be read here.",
                 "Open the doc, copy its text, paste into Text Input tab."),
        "excel":("Excel file — spreadsheet data cannot be extracted from a direct link.",
                 "Copy the cells as text and paste into Text Input tab."),
        "image":("Image file — no readable text in an image.",
                 "Transcribe any text from the image and paste into Text Input tab."),
    }
    if ut in blocked:
        raise FetchError(*blocked[ut])
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120',
        'Accept':'text/html,application/xhtml+xml,*/*;q=0.8',
        'Accept-Language':'en-US,en;q=0.5',
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            ct = resp.headers.get("Content-Type","")
            if "application/pdf" in ct:
                raise FetchError("Server returned a PDF (application/pdf) — cannot parse here.",
                                 "Download the PDF, copy its text, paste into Text Input tab.")
            if any(t in ct for t in ["application/octet-stream","application/zip","application/msword","application/vnd"]):
                raise FetchError(f"Server returned a binary/Office file ({ct.split(';')[0].strip()}).",
                                 "Open the file, copy the content, paste into Text Input tab.")
            html = resp.read().decode('utf-8', errors='ignore')
    except FetchError: raise
    except urllib.error.HTTPError as e:
        codes = {
            401:("Login required (HTTP 401).","Log in in your browser, copy the text, paste into Text Input."),
            403:("Blocked — site refuses automated access (HTTP 403).","Open in browser, copy text, paste into Text Input."),
            404:("Page not found (HTTP 404).","Check the URL still exists."),
            429:("Rate limited (HTTP 429).","Wait a moment and try again."),
            500:("Server error (HTTP 500).","Try again later."),
            503:("Service unavailable (HTTP 503).","Try again in a few minutes."),
        }
        reason, tip = codes.get(e.code,(f"HTTP error {e.code}.","Open in browser and copy-paste the text."))
        raise FetchError(reason, tip)
    except urllib.error.URLError as e:
        rs = str(e.reason).lower()
        if "timed out" in rs or "timeout" in rs:
            raise FetchError("Request timed out.","Try again or paste the text manually.")
        if "ssl" in rs or "certificate" in rs:
            raise FetchError("SSL certificate error.","Open in browser and copy-paste the content.")
        raise FetchError(f"Network error: {e.reason}","Check the URL is correct and publicly accessible.")
    except Exception as e:
        raise FetchError(f"Unexpected error: {e}","Try copying the page text manually into Text Input tab.")

    if html.startswith("%PDF-") or "\x00" in html[:200]:
        raise FetchError("Raw PDF/binary data — no HTML found.","Download the PDF, copy text, paste into Text Input tab.")

    parser = TextExtractor()
    parser.feed(html)
    text = re.sub(r'\s+',' ', parser.get_text()).strip()

    paywall = ["subscribe to read","sign in to read","this content is for subscribers",
               "log in to access","members only","premium content","unlock this article"]
    if any(s in text.lower() for s in paywall) and len(text.split()) < 80:
        raise FetchError("Paywall or login wall detected — only a preview was accessible.",
                         "Log in in your browser, copy the full text, paste into Text Input tab.")
    if len(text.split()) < 30:
        raise FetchError("Too little text found (<30 words). Page may be JS-rendered or blocking access.",
                         "Open in browser, copy visible text, paste into Text Input tab.")
    return text[:MAX_CHARS]


# ─────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["◈  Text Input", "◈  URL Input", "◈  URL Guidelines"])

# ── Tab 1 ─────────────────────────────────────────────────────────────
with tab1:
    text_input = st.text_area("text_in", height=210,
        placeholder="Paste any article, blog post, product description, or content here…",
        label_visibility="collapsed")
    cur = len(text_input)
    pct = min(cur / MAX_CHARS, 1.0)
    col = "#e63946" if cur > MAX_CHARS else "#f4a261" if pct >= 0.85 else "#d4af37"
    cls = "over" if cur > MAX_CHARS else "warn" if pct >= 0.85 else ""
    st.markdown(f"""<div class="counter-row">
      <span class="counter-num {cls}">{cur:,} chars</span>
      <div class="counter-bar-bg"><div class="counter-bar-fill" style="width:{pct*100:.1f}%;background:{col}"></div></div>
      <span class="counter-num">{MAX_CHARS:,} max</span>
    </div>""", unsafe_allow_html=True)
    if cur > MAX_CHARS:
        st.markdown(f'<div class="limit-banner">⚠ Exceeds {MAX_CHARS:,} chars — only the first {MAX_CHARS:,} will be analysed.</div>', unsafe_allow_html=True)
    st.markdown(f'''<div style="font-family:JetBrains Mono,monospace;font-size:0.7rem;
    color:var(--blue-light);margin-top:0.6rem;padding:0.5rem 0.9rem;
    background:rgba(67,97,238,0.07);border:1px solid rgba(67,97,238,0.2);
    border-radius:8px;display:inline-block">
    ◈ &nbsp;Will extract <b style="color:var(--gold)">{top_n} keywords</b>
    &nbsp;— change in sidebar ☰</div>''', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    run_text = st.button("◈  Extract Keywords", key="btn_text")

# ── Tab 2 ─────────────────────────────────────────────────────────────
with tab2:
    st.markdown(f"""<div class="rules-panel">
      <span class="rp-title">◈ &nbsp; URL input rules</span>
      • Only <b>public HTML pages</b> — no login required<br>
      • Max URL length: <b>{MAX_URL_LEN} characters</b><br>
      • No PDFs, Office files, or images<br>
      • No paywalled or restricted sites (see URL Guidelines tab)<br>
      • First <b>{MAX_CHARS:,} characters</b> of extracted text will be analysed
    </div>""", unsafe_allow_html=True)
    url_input = st.text_input("url_in", placeholder="https://example.com/your-article",
                              label_visibility="collapsed")
    if url_input:
        ul  = len(url_input)
        upc = min(ul / MAX_URL_LEN, 1.0)
        uc  = "#e63946" if ul > MAX_URL_LEN else "#d4af37"
        ucl = "over" if ul > MAX_URL_LEN else ""
        st.markdown(f"""<div class="counter-row" style="margin-top:0.4rem">
          <span class="counter-num {ucl}">URL: {ul} chars</span>
          <div class="counter-bar-bg"><div class="counter-bar-fill" style="width:{upc*100:.1f}%;background:{uc}"></div></div>
          <span class="counter-num">{MAX_URL_LEN} max</span>
        </div>""", unsafe_allow_html=True)
        restr = get_restricted_reason(url_input)
        if restr:
            d, w = restr
            st.markdown(f'<div class="warn-banner">⚠ &nbsp;<b>{d}</b> is restricted — {w}</div>', unsafe_allow_html=True)
    st.markdown(f'''<div style="font-family:JetBrains Mono,monospace;font-size:0.7rem;
    color:var(--blue-light);margin-top:0.6rem;padding:0.5rem 0.9rem;
    background:rgba(67,97,238,0.07);border:1px solid rgba(67,97,238,0.2);
    border-radius:8px;display:inline-block">
    ◈ &nbsp;Will extract <b style="color:var(--gold)">{top_n} keywords</b>
    &nbsp;— change in sidebar ☰</div>''', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    run_url = st.button("◈  Extract from URL", key="btn_url")

# ── Tab 3 ─────────────────────────────────────────────────────────────
with tab3:
    st.markdown("""<div style="padding:0.4rem 0 1.5rem">
      <div style="font-family:'Playfair Display',serif;font-size:1.9rem;font-weight:700;margin-bottom:0.5rem">URL Guidelines</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:var(--muted2);line-height:1.85">
        This tool fetches raw HTML and extracts visible text from public web pages only.<br>
        Content behind logins, paywalls, or served as binary files cannot be extracted.
      </div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown('<div class="guide-title" style="color:#2ec4b6">✓ &nbsp;Supported</div>', unsafe_allow_html=True)
        for label, sub in SUPPORTED_TYPES:
            st.markdown(f'<div class="guide-card yes"><div class="gc-label">{label}</div><div class="gc-sub">{sub}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="guide-title" style="color:#e63946">✕ &nbsp;Not Supported</div>', unsafe_allow_html=True)
        for label, sub in NOT_SUPPORTED_TYPES:
            st.markdown(f'<div class="guide-card no"><div class="gc-label">{label}</div><div class="gc-sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="guide-title">🚫 &nbsp;Restricted Websites</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.68rem;color:var(--muted2);margin-bottom:0.25rem">Hover a domain chip to see the block reason.</div>', unsafe_allow_html=True)

    groups = {
        "Paywalled News":           ["nytimes.com","wsj.com","ft.com","bloomberg.com","economist.com","washingtonpost.com","theatlantic.com","newyorker.com","hbr.org","thetimes.co.uk"],
        "Login-Required Platforms": ["medium.com","substack.com","quora.com","linkedin.com","facebook.com","instagram.com","twitter.com","x.com","reddit.com","pinterest.com","tiktok.com"],
        "Academic / Paywalled":     ["researchgate.net","academia.edu","jstor.org","sciencedirect.com","springer.com","nature.com","ieee.org","dl.acm.org"],
        "Cloud / Storage":          ["docs.google.com","drive.google.com","dropbox.com","onedrive.live.com","notion.so"],
        "Video / Audio":            ["youtube.com","youtu.be","vimeo.com","spotify.com"],
        "E-Commerce":               ["amazon.com","ebay.com"],
    }
    for group, domains in groups.items():
        st.markdown(f'<div class="restricted-title">◈ &nbsp;{group}</div>', unsafe_allow_html=True)
        chips = "".join(f'<span class="rchip" title="{RESTRICTED_DOMAINS.get(d,"")}">{d}</span>' for d in domains)
        st.markdown(f'<div class="restricted-chips">{chips}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""<div class="rules-panel">
      <span class="rp-title">◈ &nbsp; Universal Workaround</span>
      For <b>any</b> restricted or unsupported URL — open the page in your browser,
      select all text <b>(Ctrl+A / Cmd+A)</b>, copy it, and paste it directly into the
      <b>Text Input</b> tab. Works for paywalled articles, PDFs opened in browser,
      Google Docs, and virtually any page.
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# RUN: TEXT
# ─────────────────────────────────────────────────────────────────────
if run_text:
    st.session_state.pop("fetch_error", None)
    if not text_input.strip():
        st.error("Please paste some text first.")
    elif len(text_input.split()) < 20:
        st.error("Please provide at least 20 words.")
    else:
        proc = text_input[:MAX_CHARS]
        with st.spinner("Analysing…"):
            try:
                kws = extract_keywords(proc, top_n, ngram_max, diversity)
                st.session_state.update(keywords=kws, word_count=len(proc.split()),
                                        char_count=len(proc), truncated=len(text_input)>MAX_CHARS, source=None)
            except Exception as e:
                st.error(f"Extraction failed: {e}")

# ─────────────────────────────────────────────────────────────────────
# RUN: URL
# ─────────────────────────────────────────────────────────────────────
if run_url:
    st.session_state.pop("fetch_error", None)
    st.session_state.pop("keywords", None)
    if not url_input.strip():
        st.error("Please enter a URL.")
    elif not url_input.startswith("http"):
        st.error("URL must start with https://")
    else:
        content = None
        with st.spinner("Fetching page…"):
            try:
                content = fetch_url_content(url_input)
            except FetchError as fe:
                st.session_state.fetch_error = {"url":url_input,"reason":fe.reason,"tip":fe.tip}
            except Exception as e:
                st.session_state.fetch_error = {"url":url_input,"reason":str(e),"tip":"Try pasting the text manually into the Text Input tab."}
        if content:
            with st.spinner("Extracting keywords…"):
                try:
                    kws = extract_keywords(content, top_n, ngram_max, diversity)
                    try: src = urllib.parse.urlparse(url_input).hostname
                    except: src = url_input
                    st.session_state.update(keywords=kws, word_count=len(content.split()),
                                            char_count=len(content), truncated=False, source=src)
                except Exception as e:
                    st.error(f"Extraction failed: {e}")

# ─────────────────────────────────────────────────────────────────────
# ERROR CARD
# ─────────────────────────────────────────────────────────────────────
if st.session_state.get("fetch_error"):
    err = st.session_state.fetch_error
    show_fetch_error(err["url"], err["reason"], err["tip"])

# ─────────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────────
if "keywords" in st.session_state:
    kws   = st.session_state.keywords
    wc    = st.session_state.get("word_count", 0)
    cc    = st.session_state.get("char_count", 0)
    src   = st.session_state.get("source")
    trunc = st.session_state.get("truncated", False)

    if trunc:
        st.markdown(f'<div class="trunc-notice">◈ &nbsp;Input trimmed to first {MAX_CHARS:,} characters for analysis.</div>', unsafe_allow_html=True)

    src_html = f'<span class="rm-gold">{src}</span> &nbsp;·&nbsp; ' if src else ""
    st.markdown(f"""<div class="results-header">
      <div class="results-title">Results</div>
      <div class="results-meta">
        {src_html}<span class="rm-blue">{len(kws)}</span> keywords extracted<br>
        <span class="rm-gold">{wc:,}</span> words &nbsp;·&nbsp; <span class="rm-gold">{cc:,}</span> chars analysed
      </div>
    </div>""", unsafe_allow_html=True)

    # Legend — Gold=High, Blue=Mid, Muted=Low
    st.markdown("""<div class="legend-row">
      <span class="legend-pill hi"><span class="legend-dot"></span>Gold · High ≥ 0.75</span>
      <span class="legend-pill md"><span class="legend-dot"></span>Blue · Mid 0.55–0.74</span>
      <span class="legend-pill lo"><span class="legend-dot"></span>Muted · Lower &lt; 0.55</span>
    </div>""", unsafe_allow_html=True)

    # Chips
    st.markdown(
        '<div class="chips-wrap">' +
        "".join(chip_html(k["keyword"], k["score"]) for k in kws) +
        '</div>', unsafe_allow_html=True)

    # Score bars
    st.markdown('<div class="score-section-title">Relevance Scores</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="margin-bottom:1.5rem">' +
        "".join(score_row_html(k["keyword"], k["score"], i+1) for i, k in enumerate(kws)) +
        '</div>', unsafe_allow_html=True)

    # Export
    csv   = "Keyword,Score\n" + "\n".join(f'"{k["keyword"]}",{float(k["score"]):.3f}' for k in kws)
    plain = ", ".join(k["keyword"] for k in kws)

    ca, cb = st.columns(2)
    ca.download_button("⬇  Export CSV", csv, "keywords.csv", "text/csv", use_container_width=True)
    with cb:
        if st.button("⎘  Copy as Plain Text", use_container_width=True):
            st.code(plain, language=None)
