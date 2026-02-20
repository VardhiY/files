import streamlit as st
from groq import Groq
import json
import re
import urllib.request
from html.parser import HTMLParser

st.set_page_config(page_title="LEXIS", page_icon="🔍", layout="wide")

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("⚠️ GROQ_API_KEY missing.")
    st.stop()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');

.stApp {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg,#ff7a18,#ff3d77,#4c6ef5);
    background-size: 400% 400%;
    animation: bgmove 12s ease infinite;
    color: white;
}

@keyframes bgmove {
    0% {background-position:0% 50%;}
    50% {background-position:100% 50%;}
    100% {background-position:0% 50%;}
}

.block-container {
    max-width: 1200px;
    margin: auto;
    padding-top: 60px;
}

/* Hero */
.hero-title {
    font-size: 5rem;
    font-weight: 900;
    letter-spacing: -2px;
    line-height: 1;
}

.hero-title span {
    color: rgba(255,255,255,0.6);
}

.subtitle {
    font-size: 1.2rem;
    margin-top: 20px;
    max-width: 600px;
    font-weight: 500;
    opacity: 0.9;
}

/* Tabs */
div[role="radiogroup"] {
    margin-top: 40px;
    gap: 18px;
}

div[role="radiogroup"] > label {
    background: rgba(255,255,255,0.15);
    padding: 12px 28px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 15px;
    transition: 0.3s ease;
}

div[role="radiogroup"] > label:hover {
    background: white;
    color: #ff3d77 !important;
    transform: translateY(-3px);
}

/* Inputs */
textarea, input {
    background: rgba(255,255,255,0.18) !important;
    border: none !important;
    border-radius: 22px !important;
    padding: 22px !important;
    font-size: 16px !important;
    font-weight: 500;
    backdrop-filter: blur(10px);
}

/* Button */
.stButton > button {
    background: white;
    color: #ff3d77 !important;
    border-radius: 25px !important;
    padding: 16px !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.3);
}

/* Keywords */
.keyword-chip {
    display: inline-block;
    padding: 14px 32px;
    border-radius: 999px;
    margin: 12px;
    font-size: 15px;
    font-weight: 600;
    background: rgba(255,255,255,0.2);
    transition: 0.3s ease;
}

.keyword-chip:hover {
    background: white;
    color: #4c6ef5 !important;
    transform: translateY(-5px);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">LEX<span>IS</span></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Creative AI-powered keyword extraction built for modern web experiences.</div>', unsafe_allow_html=True)

def extract_keywords(text):
    prompt = f"""
Extract top 10 important keywords from the text.
Return ONLY JSON:
[{{"keyword":"...","score":0.00}}]
TEXT:
{text[:6000]}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.2,
        max_tokens=800
    )
    cleaned = re.sub(r'```json|```','',response.choices[0].message.content.strip())
    return json.loads(cleaned)

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts=[]
        self.skip_tags={'script','style','nav','footer','header'}
        self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in self.skip_tags: self.skip+=1
    def handle_endtag(self,tag):
        if tag in self.skip_tags and self.skip>0: self.skip-=1
    def handle_data(self,data):
        if self.skip==0:
            stripped=data.strip()
            if stripped: self.text_parts.append(stripped)
    def get_text(self):
        return ' '.join(self.text_parts)

def fetch_url_content(url):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=15) as resp:
        html=resp.read().decode('utf-8',errors='ignore')
    parser=TextExtractor()
    parser.feed(html)
    return parser.get_text()

mode=st.radio("",["📄 Text Input","🌐 URL Input","📘 URL Guidelines"],horizontal=True)

if mode=="📄 Text Input":
    text_input=st.text_area("",height=220,placeholder="Paste your content here...")
    if st.button("Extract Keywords"):
        if text_input.strip():
            with st.spinner("Analyzing..."):
                st.session_state.kws=extract_keywords(text_input)

elif mode=="🌐 URL Input":
    url_input=st.text_input("",placeholder="https://example.com")
    if st.button("Extract from URL"):
        if url_input.startswith("http"):
            with st.spinner("Fetching..."):
                content=fetch_url_content(url_input)
                st.session_state.kws=extract_keywords(content)

elif mode=="📘 URL Guidelines":
    st.success("✔ Public blogs, news, Wikipedia, company pages.")
    st.error("✖ PDF, Word, Excel, images, paywalled content.")
    st.warning("🔒 Login-required pages & private dashboards.")

if "kws" in st.session_state:
    st.markdown("## Extracted Keywords")
    chips=""
    for k in st.session_state.kws:
        chips+=f'<span class="keyword-chip">{k["keyword"]}</span>'
    st.markdown(chips,unsafe_allow_html=True)
