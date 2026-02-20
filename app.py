st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700&display=swap');

.stApp {
    background: radial-gradient(circle at 15% 20%, #141b2d 0%, #0b0f1a 60%);
    color: #e8eaf2;
    font-family: 'Inter', sans-serif;
}

.block-container {
    padding-top: 3rem;
    max-width: 1100px;
}

/* ───────── HEADER ───────── */
.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 4rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(180deg,#f5d97b,#c9a227);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.6rem;
    letter-spacing: -0.02em;
}

.subtitle {
    text-align: center;
    color: #aab2c5;
    font-size: 1.05rem;
    margin-bottom: 3rem;
    line-height: 1.6;
}

/* ───────── NAVIGATION ───────── */
div[role="radiogroup"] {
    justify-content: center;
    gap: 3rem;
    background: rgba(255,255,255,0.03);
    padding: 0.8rem 1.5rem;
    border-radius: 16px;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.05);
}

/* ───────── INPUT FIELDS ───────── */
textarea, input {
    background-color: #121826 !important;
    border: 1px solid #2a3244 !important;
    border-radius: 14px !important;
    color: #e8eaf2 !important;
    padding: 0.8rem !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease;
}

textarea:focus, input:focus {
    border-color: #c9a227 !important;
    box-shadow: 0 0 0 2px rgba(201,162,39,0.25);
}

/* ───────── BUTTONS ───────── */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg,#c9a227,#f5d97b);
    color: #000 !important;
    font-weight: 600 !important;
    border-radius: 14px !important;
    border: none !important;
    padding: 0.85rem !important;
    font-size: 1rem !important;
    transition: all 0.25s ease;
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 30px rgba(201,162,39,0.35);
}

/* ───────── CARDS (Guidelines Section) ───────── */
.stSuccess, .stError, .stWarning {
    border-radius: 18px !important;
    padding: 1.2rem !important;
    backdrop-filter: blur(6px);
}

/* ───────── RESULTS SECTION ───────── */
.keyword-chip {
    display: inline-block;
    padding: 0.55rem 1.2rem;
    border-radius: 999px;
    font-size: 0.9rem;
    margin: 0.45rem;
    background: rgba(201,162,39,0.12);
    border: 1px solid rgba(201,162,39,0.5);
    color: #f5d97b;
    font-weight: 500;
    transition: all 0.25s ease;
}

.keyword-chip:hover {
    background: rgba(201,162,39,0.25);
    transform: translateY(-3px);
    box-shadow: 0 6px 18px rgba(201,162,39,0.25);
}

/* ───────── SECTION TITLES ───────── */
h2, h3 {
    color: #ffffff;
    margin-top: 2rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)
