import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, api_post, api_get, page_header, chart_card_open, chart_card_close

inject_theme()
page_header("Compliance & Audit Assistant",
            "Cross-checks the document corpus against ISO 9001, ISO 45001, ISO 14001, "
            "Factory Act, OISD, and PESO frameworks.")

frameworks = ["ISO 9001", "ISO 45001", "ISO 14001", "Factory Act", "OISD", "PESO"]
cols = st.columns(len(frameworks))
for i, fw in enumerate(frameworks):
    with cols[i]:
        st.markdown(f"""<div class="card" style="text-align:center;padding:14px;">
            <span style="font-weight:600;font-size:13.5px;">{fw}</span>
        </div>""", unsafe_allow_html=True)

chart_card_open("Run Compliance Check")
equipment = st.text_input("Equipment / topic to audit", value="V-201 pressure vessel corrosion")
if st.button("Run Compliance Agent"):
    with st.spinner("Compliance Agent analyzing corpus..."):
        resp = api_post("/ask", {"query": f"Are there any compliance gaps for {equipment}?"})
    if resp and resp.get("compliance"):
        comp = resp["compliance"]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Frameworks Referenced**")
            for f in comp.get("frameworks_referenced", []) or ["None found"]:
                st.success(f)
        with c2:
            st.markdown("**Potential Gaps**")
            for f in comp.get("potential_gaps", []) or ["None"]:
                st.warning(f)
        st.caption(comp.get("note", ""))
        st.markdown("**AI Summary**")
        st.write(resp["answer"])
chart_card_close()

st.markdown('<div class="section-title">Documents by Compliance Category</div>', unsafe_allow_html=True)
docs = api_get("/documents") or []
compliance_docs = [d for d in docs if d["category"] == "Compliance Document"]
chart_card_open("Compliance Documents")
if compliance_docs:
    for d in compliance_docs:
        st.markdown(f"- **{d['filename']}** — uploaded {d['uploaded_at']}")
else:
    st.caption("No dedicated compliance documents ingested yet. Upload some in the Documents page.")
chart_card_close()