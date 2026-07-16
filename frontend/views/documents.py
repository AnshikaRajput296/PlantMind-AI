import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, api_get, page_header, chart_card_open, chart_card_close, API_BASE
import requests

inject_theme()
page_header("Document Intelligence",
            "Upload PDFs, Word documents, spreadsheets, or images. Entities are "
            "extracted automatically and the Knowledge Graph is updated in real time.")

chart_card_open("Upload Document")
uploaded = st.file_uploader(
    "Upload a document",
    type=["pdf", "docx", "xlsx", "csv", "png", "jpg", "jpeg", "txt", "json"],
    label_visibility="collapsed",
)
if uploaded and st.button("Ingest Document"):
    with st.spinner("Document Intelligence Agent processing (OCR, parsing, entity extraction)..."):
        files = {"file": (uploaded.name, uploaded.getvalue())}
        try:
            r = requests.post(f"{API_BASE}/documents/upload", files=files, timeout=120)
            r.raise_for_status()
            result = r.json()
            st.success(f"Ingested '{result['filename']}' as {result['category']} — "
                       f"{result['chunks_created']} chunks created, Knowledge Graph updated.")
            st.markdown("**Extracted Entities**")
            st.json(result["entities"])
        except Exception as e:
            st.error(f"Upload failed: {e}")
chart_card_close()

st.markdown('<div class="section-title">Document Library</div>', unsafe_allow_html=True)
docs = api_get("/documents") or []
if docs:
    for d in docs:
        with st.expander(f"{d['filename']} — {d['category']} ({d['doc_type']})"):
            st.caption(f"Uploaded: {d['uploaded_at']}")
            st.json(d["entities"])
else:
    st.info("No documents ingested yet.")