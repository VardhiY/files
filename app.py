mode = st.radio("",["📄 TEXT INPUT","🌐 URL INPUT","📘 GUIDELINES"],horizontal=True)

# TEXT INPUT
if mode=="📄 TEXT INPUT":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    text_input=st.text_area("",height=220,placeholder="PASTE YOUR CONTENT HERE...")
    if st.button("EXTRACT KEYWORDS"):
        if text_input.strip():
            with st.spinner("Analyzing..."):
                st.session_state.kws=extract_keywords(text_input)
    st.markdown('</div>', unsafe_allow_html=True)

# URL INPUT
elif mode=="🌐 URL INPUT":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    url_input=st.text_input("",placeholder="https://example.com/article")
    if st.button("EXTRACT FROM URL"):
        if url_input.startswith("http"):
            with st.spinner("Fetching..."):
                content=fetch_url_content(url_input)
                st.session_state.kws=extract_keywords(content)
    st.markdown('</div>', unsafe_allow_html=True)

# GUIDELINES
elif mode=="📘 GUIDELINES":
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### ✔ SUPPORTED")
    st.write("Public blogs, news, Wikipedia, company pages.")
    st.markdown("### ✖ NOT SUPPORTED")
    st.write("PDF, Word, Excel, images, paywalled content.")
    st.markdown("### 🔒 RESTRICTED")
    st.write("Login-required pages and private dashboards.")
    st.markdown('</div>', unsafe_allow_html=True)
