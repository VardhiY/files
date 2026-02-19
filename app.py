import streamlit as st
from groq import Groq
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser

# ── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="LEXIS · AI Keyword Engine",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── API Key ───────────────────────────────────────────────────────────
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
    ("Forum posts", "Publicly accessible Discourse, phpBB threads"),
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

# ── CSS — Gold & Black Luxury Theme ──────────────────────────────────
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600;700&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:         #111009;
  --surface:    #1a1810;
  --surface2:   #201e14;
  --glass:      rgba(212,175,55,0.03);
  --border:     rgba(212,175,55,0.12);
  --border-hi:  rgba(212,175,55,0.28);
  --gold:       #d4af37;
  --gold-light: #f0d060;
  --gold-dim:   #8a7020;
  --gold-pale:  rgba(212,175,55,0.15);
  --white:      #f5f0e8;
  --muted:      #5a5440;
  --muted2:     #8a8060;
  --danger:     #c0392b;
  --warn:       #e67e22;
  --success:    #27ae60;
  --card-r:     14px;
}

html, body, [class*="css"] {
  font-family: 'Outfit', sans-serif;
  background: var(--bg) !important;
  color: var(--white) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
.stDeployButton, [data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="collapsedControl"] { display: none !important; }

.block-container {
  max-width: 1080px !important;
  padding: 0 2rem 5rem !important;
  margin: 0 auto !important;
}

/* ── Background — deep dark amber mesh ── */
.stApp::before {
  content: '';
  position: fixed; inset: 0; z-index: -2;
  background:
    radial-gradient(ellipse 70% 45% at 10% 8%,  rgba(212,175,55,0.10) 0%, transparent 65%),
    radial-gradient(ellipse 55% 40% at 88% 85%,  rgba(212,175,55,0.07) 0%, transparent 60%),
    radial-gradient(ellipse 40% 55% at 50% 45%,  rgba(160,120,20,0.05) 0%, transparent 60%),
    #111009;
  animation: ambientPulse 14s ease-in-out infinite alternate;
}
@keyframes ambientPulse {
  0%   { opacity: 1; }
  50%  { opacity: 0.65; }
  100% { opacity: 1; }
}

/* Fine dot texture */
.stApp::after {
  content: '';
  position: fixed; inset: 0; z-index: -1; pointer-events: none;
  background-image: radial-gradient(rgba(212,175,55,0.04) 1px, transparent 1px);
  background-size: 28px 28px;
}

/* ── Decorative gold top bar ── */
.stApp > div:first-child::before {
  content: '';
  display: block; width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent 0%, var(--gold) 40%, var(--gold-light) 60%, transparent 100%);
}

/* ── Hero ── */
.hero {
  text-align: center;
  padding: 3.5rem 0 2rem;
  position: relative;
}
.hero-eyebrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem; letter-spacing: 0.3em; text-transform: uppercase;
  color: var(--gold-dim); margin-bottom: 1.5rem;
  display: flex; align-items: center; justify-content: center; gap: 1rem;
}
.hero-eyebrow::before, .hero-eyebrow::after {
  content: ''; display: block; width: 60px; height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold-dim));
}
.hero-eyebrow::after { transform: scaleX(-1); }

.hero-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(4.5rem, 12vw, 9rem);
  font-weight: 700; letter-spacing: 0.12em; line-height: 0.9;
  background: linear-gradient(160deg, var(--gold-light) 0%, var(--gold) 45%, #a07820 80%, var(--gold) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  margin-bottom: 0.25rem;
  text-shadow: none;
  filter: drop-shadow(0 0 40px rgba(212,175,55,0.25));
}
.hero-rule {
  display: flex; align-items: center; justify-content: center; gap: 0.75rem;
  margin: 1rem auto;
}
.hero-rule-line { flex: 1; max-width: 120px; height: 1px; background: var(--border); }
.hero-rule-diamond {
  width: 6px; height: 6px; background: var(--gold);
  transform: rotate(45deg); flex-shrink: 0;
}
.hero-sub {
  font-family: 'Outfit', sans-serif; font-weight: 300;
  font-size: 0.95rem; color: var(--muted2); letter-spacing: 0.04em;
  max-width: 440px; margin: 0 auto; line-height: 1.7;
}
.hero-tag {
  display: inline-block; margin-top: 1.8rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.62rem; letter-spacing: 0.18em; text-transform: uppercase;
  background: var(--glass);
  border: 1px solid var(--border);
  color: var(--gold-dim); padding: 0.4rem 1.2rem; border-radius: 999px;
}

/* ── Stat strip ── */
.stat-strip {
  display: flex; margin: 2.5rem 0;
  border: 1px solid var(--border);
  border-radius: var(--card-r); overflow: hidden;
  background: var(--surface);
  position: relative;
}
.stat-strip::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
}
.stat-item {
  flex: 1; padding: 1.3rem 0; text-align: center;
  border-right: 1px solid var(--border);
  position: relative;
}
.stat-item:last-child { border-right: none; }
.stat-val {
  font-family: 'Cormorant Garamond', serif;
  font-size: 2.2rem; font-weight: 600;
  color: var(--gold); letter-spacing: 0.05em; line-height: 1;
}
.stat-lbl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.58rem; color: var(--muted); letter-spacing: 0.18em;
  text-transform: uppercase; margin-top: 0.3rem;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 4px !important; gap: 2px !important;
  margin-bottom: 1.5rem !important;
  position: relative;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted2) !important;
  border-radius: 9px !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.72rem !important; letter-spacing: 0.08em !important;
  padding: 0.55rem 1.3rem !important;
  transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%) !important;
  color: #0d0b05 !important; font-weight: 600 !important;
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
  color: var(--gold-dim) !important;
  background: var(--gold-pale) !important;
}

/* ── Inputs ── */
div[data-testid="stTextArea"] textarea {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--white) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.82rem !important; line-height: 1.75 !important;
  padding: 1rem 1.2rem !important;
  transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
  resize: none !important;
}
div[data-testid="stTextArea"] textarea:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 3px rgba(212,175,55,0.10) !important;
  outline: none !important;
}
div[data-testid="stTextInput"] input {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  color: var(--white) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.82rem !important;
  padding: 0.75rem 1.2rem !important;
  transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
}
div[data-testid="stTextInput"] input:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 3px rgba(212,175,55,0.10) !important;
  outline: none !important;
}
div[data-testid="stSelectbox"] > div > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  color: var(--white) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.78rem !important;
}

/* ── Primary button ── */
.stButton > button {
  background: linear-gradient(135deg, #b8960c 0%, var(--gold) 45%, var(--gold-light) 100%) !important;
  color: #0d0b05 !important;
  font-family: 'Cormorant Garamond', serif !important;
  font-size: 1.2rem !important; font-weight: 700 !important;
  letter-spacing: 0.15em !important;
  border: none !important; border-radius: 12px !important;
  padding: 0.8rem 2rem !important; width: 100% !important;
  cursor: pointer !important;
  transition: all 0.25s ease !important;
  box-shadow: 0 4px 20px rgba(212,175,55,0.15) !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 35px rgba(212,175,55,0.35) !important;
  filter: brightness(1.08) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Download button ── */
.stDownloadButton > button {
  background: var(--surface) !important;
  border: 1px solid var(--border-hi) !important;
  color: var(--gold-dim) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.74rem !important;
  border-radius: 10px !important; padding: 0.65rem 1rem !important;
  transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
  border-color: var(--gold) !important;
  color: var(--gold) !important;
  background: var(--gold-pale) !important;
  box-shadow: 0 4px 16px rgba(212,175,55,0.12) !important;
}

/* ── Char counter bar ── */
.counter-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-top: 0.45rem;
  font-family: 'JetBrains Mono', monospace; font-size: 0.68rem;
}
.counter-bar-bg {
  flex: 1; height: 2px; background: var(--border);
  border-radius: 99px; margin: 0 0.8rem; overflow: hidden;
}
.counter-bar-fill { height: 100%; border-radius: 99px; transition: width 0.3s ease, background 0.3s ease; }
.counter-num { color: var(--muted2); }
.counter-num.warn { color: var(--warn); }
.counter-num.over { color: var(--danger); }

/* ── Rules panel ── */
.rules-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--gold);
  border-radius: var(--card-r);
  padding: 1rem 1.25rem; margin-bottom: 1rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem; line-height: 2; color: var(--muted2);
}
.rules-panel b { color: var(--gold); font-weight: 500; }
.rules-panel .rules-title {
  font-size: 0.62rem; letter-spacing: 0.2em; text-transform: uppercase;
  color: var(--gold-dim); margin-bottom: 0.5rem; display: block;
}

/* ── Banners ── */
.warn-banner {
  background: rgba(230,126,34,0.07);
  border: 1px solid rgba(230,126,34,0.25);
  border-radius: 10px; padding: 0.65rem 1rem;
  font-size: 0.78rem; color: var(--warn); margin: 0.5rem 0;
  font-family: 'JetBrains Mono', monospace;
}
.limit-banner {
  background: rgba(192,57,43,0.07);
  border: 1px solid rgba(192,57,43,0.25);
  border-radius: 10px; padding: 0.65rem 1rem;
  font-size: 0.78rem; color: #e74c3c; margin: 0.5rem 0;
  font-family: 'JetBrains Mono', monospace;
}
.trunc-notice {
  background: rgba(212,175,55,0.06);
  border: 1px solid rgba(212,175,55,0.2);
  border-radius: 10px; padding: 0.65rem 1rem;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem; color: var(--gold-dim); margin-bottom: 1rem;
}

/* ── Error card ── */
.error-card {
  background: rgba(192,57,43,0.05);
  border: 1px solid rgba(192,57,43,0.25);
  border-radius: var(--card-r); padding: 1.3rem 1.5rem;
  margin: 1rem 0; position: relative; overflow: hidden;
}
.error-card::before {
  content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px;
  background: linear-gradient(90deg, #c0392b, var(--gold));
}
.error-card .ec-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.3rem; font-weight: 700; letter-spacing: 0.05em;
  color: #e74c3c; margin-bottom: 0.6rem;
}
.error-card .ec-host {
  font-family: 'JetBrains Mono', monospace; font-size: 0.73rem;
  color: var(--muted2); background: var(--surface2);
  border: 1px solid var(--border); padding: 0.2rem 0.65rem;
  border-radius: 6px; display: inline-block; margin-bottom: 0.8rem;
}
.error-card .ec-reason { font-size: 0.85rem; color: var(--white); line-height: 1.6; margin-bottom: 0.8rem; }
.error-card .ec-tip {
  font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
  color: var(--muted2); border-top: 1px solid var(--border);
  padding-top: 0.75rem; line-height: 1.7;
}
.error-card .ec-tip b { color: var(--gold-dim); }

/* ── Results header ── */
.results-header {
  display: flex; align-items: baseline; justify-content: space-between;
  border-bottom: 1px solid var(--border); padding-bottom: 1.1rem; margin: 2rem 0 1.5rem;
  position: relative;
}
.results-header::after {
  content: ''; position: absolute; bottom: -1px; left: 0; width: 80px; height: 1px;
  background: var(--gold);
}
.results-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 2.2rem; font-weight: 600; letter-spacing: 0.08em; color: var(--white);
}
.results-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.67rem; color: var(--muted); text-align: right; line-height: 1.9;
}
.results-meta b { color: var(--gold-dim); }

/* ── Legend ── */
.legend-row { display: flex; gap: 0.6rem; margin-bottom: 1.3rem; flex-wrap: wrap; }
.legend-pill {
  font-family: 'JetBrains Mono', monospace; font-size: 0.62rem;
  letter-spacing: 0.1em; text-transform: uppercase;
  padding: 0.28rem 0.75rem; border-radius: 999px;
  display: flex; align-items: center; gap: 0.4rem;
}
.legend-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.legend-pill.hi {
  background: rgba(212,175,55,0.1); border: 1px solid rgba(212,175,55,0.35); color: var(--gold);
}
.legend-pill.hi .legend-dot { background: var(--gold); }
.legend-pill.md {
  background: rgba(240,208,96,0.07); border: 1px solid rgba(240,208,96,0.22); color: var(--gold-light);
}
.legend-pill.md .legend-dot { background: var(--gold-light); }
.legend-pill.lo {
  background: rgba(138,112,32,0.1); border: 1px solid rgba(138,112,32,0.3); color: var(--gold-dim);
}
.legend-pill.lo .legend-dot { background: var(--gold-dim); }

/* ── Keyword chips ── */
.chips-wrap { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0 2rem; }
.kchip {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.42rem 0.95rem; border-radius: 999px;
  font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
  cursor: default; transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kchip:hover { transform: translateY(-2px); }
.kchip.hi {
  background: rgba(212,175,55,0.12); border: 1px solid rgba(212,175,55,0.4); color: var(--gold);
}
.kchip.hi:hover { box-shadow: 0 4px 20px rgba(212,175,55,0.22); }
.kchip.md {
  background: rgba(240,208,96,0.08); border: 1px solid rgba(240,208,96,0.28); color: var(--gold-light);
}
.kchip.md:hover { box-shadow: 0 4px 20px rgba(240,208,96,0.15); }
.kchip.lo {
  background: rgba(138,112,32,0.1); border: 1px solid rgba(138,112,32,0.32); color: #a08040;
}
.kchip.lo:hover { box-shadow: 0 4px 16px rgba(138,112,32,0.18); }
.kchip-score {
  font-size: 0.62rem; opacity: 0.5;
  background: rgba(0,0,0,0.25); padding: 0.05rem 0.35rem; border-radius: 4px;
}

/* ── Score rows ── */
.score-section-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.4rem; font-weight: 600; letter-spacing: 0.08em;
  color: var(--muted2); margin-bottom: 0.75rem;
}
.score-row {
  display: grid; grid-template-columns: 28px 1fr auto;
  align-items: center; gap: 1rem;
  padding: 0.7rem 0; border-bottom: 1px solid var(--border);
}
.score-row:last-child { border-bottom: none; }
.score-idx { font-family: 'JetBrains Mono', monospace; font-size: 0.63rem; color: var(--muted); text-align: right; }
.score-kw  { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: var(--white); }
.score-bar-wrap { display: flex; align-items: center; gap: 0.6rem; min-width: 170px; }
.score-bar-bg   { flex: 1; height: 3px; background: var(--border); border-radius: 99px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 99px; transition: width 0.6s cubic-bezier(.23,1,.32,1); }
.score-val { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: var(--muted2); min-width: 38px; text-align: right; }

/* ── Guide cards ── */
.guide-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.6rem; font-weight: 600; letter-spacing: 0.06em;
  color: var(--white); margin-bottom: 1rem;
}
.guide-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 0.8rem 1rem; margin-bottom: 0.5rem;
  transition: border-color 0.2s ease;
}
.guide-card:hover { border-color: var(--border-hi); }
.guide-card.yes { border-left: 3px solid var(--success); }
.guide-card.no  { border-left: 3px solid var(--danger); }
.guide-card .gc-label { font-size: 0.83rem; font-weight: 500; color: var(--white); margin-bottom: 0.2rem; }
.guide-card .gc-sub   { font-family: 'JetBrains Mono', monospace; font-size: 0.64rem; color: var(--muted); line-height: 1.5; }

/* ── Restricted chips ── */
.restricted-title {
  font-family: 'JetBrains Mono', monospace; font-size: 0.63rem;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted);
  margin: 1.2rem 0 0.45rem;
}
.restricted-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.rchip {
  font-family: 'JetBrains Mono', monospace; font-size: 0.67rem;
  background: rgba(212,175,55,0.05); border: 1px solid rgba(212,175,55,0.18);
  color: var(--gold-dim); padding: 0.22rem 0.6rem; border-radius: 6px; cursor: help;
  transition: border-color 0.15s ease;
}
.rchip:hover { border-color: var(--gold-dim); color: var(--gold); }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}
.sidebar-label {
  font-family: 'JetBrains Mono', monospace; font-size: 0.62rem;
  letter-spacing: 0.15em; text-transform: uppercase; color: var(--muted); margin-bottom: 0.3rem; display: block;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--gold) !important; }

/* ── Code block ── */
.stCodeBlock { border-radius: 10px !important; }
.stCodeBlock pre { background: var(--surface) !important; border: 1px solid var(--border) !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
  font-family: 'JetBrains Mono', monospace !important; font-size: 0.74rem !important;
  color: var(--muted2) !important; background: var(--surface) !important;
  border: 1px solid var(--border) !important; border-radius: 10px !important;
}

/* ── Progress bar override ── */
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--gold), var(--gold-light)) !important;
}
.stProgress > div > div { background: var(--border) !important; border-radius: 99px !important; }

/* ── Selectbox dropdown ── */
[data-baseweb="popover"] { background: var(--surface2) !important; border: 1px solid var(--border) !important; }
[role="option"] { color: var(--white) !important; font-family: 'JetBrains Mono', monospace !important; font-size: 0.78rem !important; }
[role="option"]:hover { background: var(--gold-pale) !important; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">Semantic Extraction Engine</div>
  <div class="hero-title">LEXIS</div>
  <div class="hero-rule">
    <div class="hero-rule-line"></div>
    <div class="hero-rule-diamond"></div>
    <div class="hero-rule-line"></div>
  </div>
  <div class="hero-sub">Extract high-signal keywords from any text or URL using Groq-powered AI — in under a second.</div>
  <div class="hero-tag">◈ &nbsp; Powered by Groq · LLaMA 3.1 · v1.4</div>
</div>
""", unsafe_allow_html=True)

# ── Stat strip ────────────────────────────────────────────────────────
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

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ◈ Settings")
    st.markdown('<span class="sidebar-label">Top N Keywords</span>', unsafe_allow_html=True)
    top_n = st.selectbox("top_n", [5,10,15,20], index=1, label_visibility="collapsed")
    st.markdown('<span class="sidebar-label">Keyphrase Length</span>', unsafe_allow_html=True)
    ngram_max = st.selectbox("ngram", [1,2,3],
        format_func=lambda x:{1:"Single words",2:"1–2 word phrases",3:"1–3 word phrases"}[x],
        index=1, label_visibility="collapsed")
    st.markdown('<span class="sidebar-label">Diversity Mode</span>', unsafe_allow_html=True)
    diversity = st.selectbox("diversity", ["none","mmr","maxsum"],
        format_func=lambda x:{"none":"None — raw scores","mmr":"MMR — balanced","maxsum":"Max Sum — diverse"}[x],
        index=1, label_visibility="collapsed")
    st.markdown("---")
    st.markdown(f"<small style='color:var(--muted);font-family:JetBrains Mono,monospace;font-size:0.63rem'>Max chars: {MAX_CHARS:,}<br>Max URL: {MAX_URL_LEN} chars<br><br>LEXIS · AI Keyword Engine</small>", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────
class FetchError(Exception):
    def __init__(self, reason, tip):
        super().__init__(reason)
        self.reason = reason
        self.tip    = tip

def get_restricted_reason(url):
    try:
        hostname = urllib.parse.urlparse(url).hostname or ""
        hostname = hostname.lower().removeprefix("www.")
        for domain, reason in RESTRICTED_DOMAINS.items():
            if hostname == domain or hostname.endswith("." + domain):
                return domain, reason
    except Exception:
        pass
    return None

def detect_url_type(url):
    lower = url.lower().split("?")[0]
    if lower.endswith(".pdf"):                          return "pdf"
    if lower.endswith((".ppt",".pptx")):               return "ppt"
    if lower.endswith((".doc",".docx")):               return "doc"
    if lower.endswith((".xls",".xlsx")):               return "excel"
    if lower.endswith((".jpg",".jpeg",".png",
                        ".gif",".svg",".webp")):       return "image"
    return "html"

def char_counter_html(current, limit):
    pct   = min(current / limit, 1.0)
    w     = f"{pct*100:.1f}%"
    color = "#c0392b" if current > limit else "#e67e22" if pct >= 0.85 else "#d4af37"
    cls   = "over" if current > limit else "warn" if pct >= 0.85 else ""
    return f"""
    <div class="counter-row">
      <span class="counter-num {cls}">{current:,} chars</span>
      <div class="counter-bar-bg"><div class="counter-bar-fill" style="width:{w};background:{color}"></div></div>
      <span class="counter-num">{limit:,} max</span>
    </div>"""

def chip_html(keyword, score):
    s   = float(score)
    cls = "hi" if s >= 0.75 else "md" if s >= 0.55 else "lo"
    return f'<span class="kchip {cls}">{keyword}<span class="kchip-score">{s:.2f}</span></span>'

def score_bar_html(keyword, score, idx):
    s     = float(score)
    pct   = f"{s*100:.1f}%"
    color = "#d4af37" if s >= 0.75 else "#f0d060" if s >= 0.55 else "#8a7020"
    return f"""
    <div class="score-row">
      <span class="score-idx">{idx:02d}</span>
      <span class="score-kw">{keyword}</span>
      <div class="score-bar-wrap">
        <div class="score-bar-bg"><div class="score-bar-fill" style="width:{pct};background:{color}"></div></div>
        <span class="score-val">{s:.3f}</span>
      </div>
    </div>"""

def show_fetch_error(url, reason, tip):
    hostname = url
    try: hostname = urllib.parse.urlparse(url).hostname or url
    except: pass
    st.markdown(f"""
    <div class="error-card">
      <div class="ec-title">Extraction Failed</div>
      <div class="ec-host">{hostname}</div>
      <div class="ec-reason">{reason}</div>
      <div class="ec-tip">◈ <b>What to do:</b> {tip}</div>
    </div>""", unsafe_allow_html=True)


# ── Groq extraction ───────────────────────────────────────────────────
def extract_keywords(text, top_n, ngram_max, diversity):
    drule = {"mmr":"Apply MMR — avoid repeating similar root concepts.",
             "maxsum":"Maximize diversity — make keywords as distinct as possible.",
             "none":"Return purely by relevance, no diversity constraint."}[diversity]
    lrule = {1:"1 word only",2:"1 to 2 words max",3:"1 to 3 words max"}[ngram_max]
    prompt = f"""You are a semantic keyword extraction engine (like KeyBERT). Extract the top {top_n} keywords.
Rules:
- Keyphrase length: {lrule}
- {drule}
- Score each 0.00–1.00 by semantic importance.
- Return ONLY a valid JSON array, no markdown, no explanation.
- Format: [{{"keyword":"...","score":0.00}},...] 
TEXT:
{text[:MAX_CHARS]}"""
    resp    = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2, max_tokens=1000
    )
    raw     = resp.choices[0].message.content.strip()
    cleaned = re.sub(r'```json|```','',raw).strip()
    return json.loads(cleaned)


# ── HTML parser ───────────────────────────────────────────────────────
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts     = []
        self.skip_tags = {'script','style','nav','footer','header','aside','noscript','form'}
        self.skip      = 0
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
        raise FetchError(f"URL is too long ({len(url)} chars). Maximum is {MAX_URL_LEN} characters.",
                         "Shorten the URL or remove extra query parameters and try again.")
    r = get_restricted_reason(url)
    if r:
        domain, why = r
        raise FetchError(f"'{domain}' is a restricted website. {why}",
                         "Copy the article text manually from the page and paste into the Text Input tab.")
    url_type = detect_url_type(url)
    blocked  = {
        "pdf":   ("This is a PDF file. PDF content cannot be extracted directly.",
                  "Download the PDF, copy its text, and paste into the Text Input tab."),
        "ppt":   ("This is a PowerPoint file. Slide text cannot be extracted from a direct link.",
                  "Open the file, copy the slide text, and paste into the Text Input tab."),
        "doc":   ("This is a Word document. Direct .docx links cannot be read here.",
                  "Open the document, copy its text, and paste into the Text Input tab."),
        "excel": ("This is an Excel file. Spreadsheet data cannot be extracted from a direct link.",
                  "Copy the relevant cells as text and paste into the Text Input tab."),
        "image": ("This URL is an image file. Images contain no readable text.",
                  "If the image has text, transcribe it and paste into the Text Input tab."),
    }
    if url_type in blocked:
        raise FetchError(*blocked[url_type])
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'en-US,en;q=0.5',
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            ct = resp.headers.get("Content-Type","")
            if "application/pdf" in ct:
                raise FetchError("Server returned a PDF file. Cannot parse PDF text here.",
                                 "Download the PDF, copy the text, and paste into the Text Input tab.")
            if any(t in ct for t in ["application/octet-stream","application/zip","application/msword","application/vnd"]):
                raise FetchError(f"Server returned a binary/Office file ({ct.split(';')[0].strip()}).",
                                 "Open the file, copy the content, and paste into the Text Input tab.")
            html = resp.read().decode('utf-8', errors='ignore')
    except FetchError: raise
    except urllib.error.HTTPError as e:
        codes = {
            401:("Access denied — login or authentication required (HTTP 401).",
                 "Log in to the website, copy the article text, and paste into Text Input tab."),
            403:("Access forbidden — website is blocking automated requests (HTTP 403).",
                 "Open in browser, copy the text, and paste into Text Input tab."),
            404:("Page not found (HTTP 404). URL may be broken or content removed.",
                 "Double-check the URL is correct and the page still exists."),
            429:("Rate limited — too many requests (HTTP 429).",
                 "Wait a moment, try again, or paste the text manually."),
            500:("Server error (HTTP 500). Site may be temporarily down.", "Try again later."),
            503:("Service unavailable (HTTP 503). Site is temporarily down.", "Try again in a few minutes."),
        }
        reason, tip = codes.get(e.code,(f"HTTP error {e.code}.","Open in browser and copy-paste the text."))
        raise FetchError(reason, tip)
    except urllib.error.URLError as e:
        rs = str(e.reason).lower()
        if "timed out" in rs or "timeout" in rs:
            raise FetchError("Request timed out — website too slow or blocking bots.","Try again or paste text manually.")
        if "ssl" in rs or "certificate" in rs:
            raise FetchError("SSL certificate error.","Open in browser and copy-paste the content.")
        raise FetchError(f"Network error: {e.reason}","Check the URL is correct and publicly accessible.")
    except Exception as e:
        raise FetchError(f"Unexpected error: {str(e)}","Try copying the page text manually into the Text Input tab.")

    if html.startswith("%PDF-") or "\x00" in html[:200]:
        raise FetchError("Page is serving raw PDF/binary data.","Download the PDF, copy the text, and paste into Text Input tab.")

    parser = TextExtractor()
    parser.feed(html)
    text = re.sub(r'\s+',' ', parser.get_text()).strip()

    paywall_sigs = ["subscribe to read","sign in to read","create a free account to continue",
                    "this content is for subscribers","log in to access",
                    "subscribe now to continue","members only","premium content","unlock this article"]
    if any(s in text.lower() for s in paywall_sigs) and len(text.split()) < 80:
        raise FetchError("Page is behind a paywall or login wall. Only a preview was accessible.",
                         "Log in in your browser, copy the full text, and paste into Text Input tab.")
    if len(text.split()) < 30:
        raise FetchError("Not enough readable text found (<30 words). Page may be JS-rendered or blocking access.",
                         "Open in browser, copy the visible text, and paste into Text Input tab.")
    return text[:MAX_CHARS]


# ── Tabs ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["◈  Text Input", "◈  URL Input", "◈  URL Guidelines"])

with tab1:
    text_input = st.text_area("text", height=220,
        placeholder="Paste any article, blog post, product description, research summary, or content here…",
        label_visibility="collapsed")
    cc = len(text_input)
    # inline counter — avoid walrus syntax for Python compat
    pct_cc   = min(cc / MAX_CHARS, 1.0)
    color_cc = "#c0392b" if cc > MAX_CHARS else "#e67e22" if pct_cc >= 0.85 else "#d4af37"
    cls_cc   = "over" if cc > MAX_CHARS else "warn" if pct_cc >= 0.85 else ""
    st.markdown(f"""
    <div class="counter-row">
      <span class="counter-num {cls_cc}">{cc:,} chars</span>
      <div class="counter-bar-bg"><div class="counter-bar-fill" style="width:{pct_cc*100:.1f}%;background:{color_cc}"></div></div>
      <span class="counter-num">{MAX_CHARS:,} max</span>
    </div>""", unsafe_allow_html=True)
    if cc > MAX_CHARS:
        st.markdown(f'<div class="limit-banner">⚠ Input exceeds {MAX_CHARS:,} chars — only the first {MAX_CHARS:,} will be analysed.</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    run_text = st.button("◈  EXTRACT KEYWORDS", key="btn_text")

with tab2:
    st.markdown(f"""
    <div class="rules-panel">
      <span class="rules-title">◈ &nbsp; URL Input Rules</span>
      • Only <b>publicly accessible HTML pages</b> — no login required<br>
      • Max URL length: <b>{MAX_URL_LEN} characters</b><br>
      • No PDFs, Word docs, spreadsheets, or image files<br>
      • No paywalled or restricted sites (see URL Guidelines tab)<br>
      • First <b>{MAX_CHARS:,} characters</b> of extracted text will be analysed
    </div>""", unsafe_allow_html=True)

    url_input = st.text_input("url", placeholder="https://example.com/article-title", label_visibility="collapsed")

    if url_input:
        ul      = len(url_input)
        pct_ul  = min(ul / MAX_URL_LEN, 1.0)
        col_ul  = "#c0392b" if ul > MAX_URL_LEN else "#d4af37"
        cls_ul  = "over" if ul > MAX_URL_LEN else ""
        st.markdown(f"""
        <div class="counter-row" style="margin-top:0.4rem">
          <span class="counter-num {cls_ul}">URL: {ul} chars</span>
          <div class="counter-bar-bg"><div class="counter-bar-fill" style="width:{pct_ul*100:.1f}%;background:{col_ul}"></div></div>
          <span class="counter-num">{MAX_URL_LEN} max</span>
        </div>""", unsafe_allow_html=True)
        restr = get_restricted_reason(url_input)
        if restr:
            d, w = restr
            st.markdown(f'<div class="warn-banner">⚠ &nbsp;<b>{d}</b> is a restricted site — {w}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    run_url = st.button("◈  EXTRACT FROM URL", key="btn_url")

with tab3:
    st.markdown("""
    <div style="padding:0.5rem 0 1.5rem">
      <div style="font-family:'Cormorant Garamond',serif;font-size:2.2rem;font-weight:600;letter-spacing:0.08em;margin-bottom:0.5rem">URL Guidelines</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:var(--muted2);line-height:1.8">
        This tool fetches raw HTML and extracts visible text. It works on standard public web pages only.<br>
        Content behind logins, paywalls, or served as binary files cannot be extracted automatically.
      </div>
    </div>""", unsafe_allow_html=True)

    col_yes, col_no = st.columns(2, gap="medium")
    with col_yes:
        st.markdown('<div class="guide-title" style="color:var(--success)">✓ &nbsp;Supported</div>', unsafe_allow_html=True)
        for label, sub in SUPPORTED_TYPES:
            st.markdown(f'<div class="guide-card yes"><div class="gc-label">{label}</div><div class="gc-sub">{sub}</div></div>', unsafe_allow_html=True)
    with col_no:
        st.markdown('<div class="guide-title" style="color:var(--danger)">✕ &nbsp;Not Supported</div>', unsafe_allow_html=True)
        for label, sub in NOT_SUPPORTED_TYPES:
            st.markdown(f'<div class="guide-card no"><div class="gc-label">{label}</div><div class="gc-sub">{sub}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="guide-title">🚫 &nbsp;Restricted Websites</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.7rem;color:var(--muted2);margin-bottom:0.5rem">Hover over a domain to see why it is blocked.</div>', unsafe_allow_html=True)

    domain_groups = {
        "Paywalled News": ["nytimes.com","wsj.com","ft.com","bloomberg.com","economist.com","washingtonpost.com","theatlantic.com","newyorker.com","hbr.org","thetimes.co.uk"],
        "Login-Required Platforms": ["medium.com","substack.com","quora.com","linkedin.com","facebook.com","instagram.com","twitter.com","x.com","reddit.com","pinterest.com","tiktok.com"],
        "Academic / Paywalled Journals": ["researchgate.net","academia.edu","jstor.org","sciencedirect.com","springer.com","nature.com","ieee.org","dl.acm.org"],
        "Cloud / Document Storage": ["docs.google.com","drive.google.com","dropbox.com","onedrive.live.com","notion.so"],
        "Video / Audio Platforms": ["youtube.com","youtu.be","vimeo.com","spotify.com"],
        "E-Commerce": ["amazon.com","ebay.com"],
    }
    for group, domains in domain_groups.items():
        st.markdown(f'<div class="restricted-title">◈ &nbsp;{group}</div>', unsafe_allow_html=True)
        chips = "".join(
            f'<span class="rchip" title="{RESTRICTED_DOMAINS.get(d,"")}">{d}</span>'
            for d in domains
        )
        st.markdown(f'<div class="restricted-chips">{chips}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="rules-panel">
      <span class="rules-title">◈ &nbsp; Universal Workaround</span>
      For <b>any</b> restricted or unsupported URL — open the page in your browser,
      select all text <b>(Ctrl+A / Cmd+A)</b>, copy it, and paste it directly into the
      <b>Text Input</b> tab. Works for paywalled articles, PDFs opened in a browser,
      Google Docs, and virtually any page.
    </div>""", unsafe_allow_html=True)


# ── Run: Text ─────────────────────────────────────────────────────────
if run_text:
    st.session_state.pop("fetch_error", None)
    if not text_input.strip():
        st.error("Please paste some text first.")
    elif len(text_input.split()) < 20:
        st.error("Please provide at least 20 words.")
    else:
        processed = text_input[:MAX_CHARS]
        with st.spinner("Analysing text…"):
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
                    st.session_state.keywords   = kws
                    st.session_state.word_count = len(content.split())
                    st.session_state.char_count = len(content)
                    st.session_state.truncated  = False
                    try: st.session_state.source = urllib.parse.urlparse(url_input).hostname
                    except: st.session_state.source = url_input
                except Exception as e:
                    st.error(f"Extraction failed: {e}")

# ── Error card ────────────────────────────────────────────────────────
if st.session_state.get("fetch_error"):
    err = st.session_state.fetch_error
    show_fetch_error(err["url"], err["reason"], err["tip"])

# ── Results ───────────────────────────────────────────────────────────
if "keywords" in st.session_state:
    kws   = st.session_state.keywords
    wc    = st.session_state.get("word_count", 0)
    cc    = st.session_state.get("char_count", 0)
    src   = st.session_state.get("source")
    trunc = st.session_state.get("truncated", False)

    if trunc:
        st.markdown(f'<div class="trunc-notice">◈ &nbsp;Input trimmed to first {MAX_CHARS:,} characters for analysis.</div>', unsafe_allow_html=True)

    src_line = f"<b>{src}</b> &nbsp;·&nbsp; " if src else ""
    st.markdown(f"""
    <div class="results-header">
      <div class="results-title">Results</div>
      <div class="results-meta">
        {src_line}<b>{len(kws)}</b> keywords extracted<br>
        <b>{wc:,}</b> words &nbsp;·&nbsp; <b>{cc:,}</b> chars analysed
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="legend-row">
      <span class="legend-pill hi"><span class="legend-dot"></span>High ≥ 0.75</span>
      <span class="legend-pill md"><span class="legend-dot"></span>Mid 0.55–0.74</span>
      <span class="legend-pill lo"><span class="legend-dot"></span>Lower &lt; 0.55</span>
    </div>""", unsafe_allow_html=True)

    st.markdown(
        '<div class="chips-wrap">' +
        "".join(chip_html(k["keyword"], k["score"]) for k in kws) +
        '</div>', unsafe_allow_html=True)

    st.markdown('<div class="score-section-title">Relevance Scores</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="margin-bottom:1.5rem">' +
        "".join(score_bar_html(k["keyword"], k["score"], i+1) for i, k in enumerate(kws)) +
        '</div>', unsafe_allow_html=True)

    csv   = "Keyword,Score\n" + "\n".join(f'"{k["keyword"]}",{float(k["score"]):.3f}' for k in kws)
    plain = ", ".join(k["keyword"] for k in kws)

    col_a, col_b = st.columns(2)
    col_a.download_button("⬇  Export CSV", csv, "keywords.csv", "text/csv", use_container_width=True)
    with col_b:
        if st.button("⎘  Copy as Plain Text", use_container_width=True):
            st.code(plain, language=None)
