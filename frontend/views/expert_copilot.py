import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, api_post, confidence_badge, page_header

inject_theme()
page_header("Expert Copilot",
            "Ask about assets, failures, maintenance history, or compliance. "
            "Every answer is produced by a transparent multi-agent pipeline.")

if "history" not in st.session_state:
    st.session_state.history = []
if "last_ctx" not in st.session_state:
    st.session_state.last_ctx = None

example_qs = [
    "Why did Pump P-101 fail repeatedly?",
    "What is the risk score and remaining useful life of P-101?",
    "Are there any compliance gaps for V-201?",
    "Show maintenance history for P-101",
]
cols = st.columns(len(example_qs))
clicked = None
for i, q in enumerate(example_qs):
    if cols[i].button(q, use_container_width=True):
        clicked = q

query = st.chat_input("Ask the Expert Copilot...") or clicked

for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])

if query:
    st.session_state.history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Orchestrating Planner, Knowledge Graph, Vector Search, "
                         "Maintenance, Root Cause, and Compliance agents..."):
            resp = api_post("/ask", {"query": query})

        if resp:
            st.session_state.last_ctx = resp
            st.markdown(resp["answer"])

            conf = resp.get("confidence") or {}
            if conf:
                st.markdown(
                    f"{confidence_badge(conf.get('hallucination_risk','medium'))} "
                    f"<span style='font-weight:600;font-size:13.5px'>Confidence: "
                    f"{conf.get('confidence',0)*100:.0f}%</span> &nbsp; "
                    f"<span style='color:var(--text-secondary);font-size:13px'>{conf.get('reason','')}</span>",
                    unsafe_allow_html=True,
                )

            sources = resp.get("sources", [])
            if sources:
                with st.expander(f"Source Citations ({len(sources)})"):
                    for s in sources:
                        st.markdown(f"- **{s['filename']}** ({s['category']}) — relevance {s['score']}")

            trace = resp.get("trace", [])
            if trace:
                with st.expander(f"Agent Reasoning Chain ({len(trace)} steps)"):
                    for step in trace:
                        st.markdown(f"""<div class="agent-step">
                            <div class="agent-name">{step['agent']}</div>
                            <div class="agent-msg">{step['message']}</div>
                        </div>""", unsafe_allow_html=True)

            colA, colB, colC = st.columns(3)
            with colA:
                if resp.get("rca"):
                    with st.expander("Root Cause Analysis"):
                        st.json(resp["rca"])
            with colB:
                if resp.get("prediction"):
                    with st.expander("Failure Prediction"):
                        st.json(resp["prediction"])
            with colC:
                if resp.get("compliance"):
                    with st.expander("Compliance Check"):
                        st.json(resp["compliance"])

            st.caption(f"LLM Provider: {resp.get('llm_provider')}  ·  Intent: {resp.get('intent')}")
            st.session_state.history.append({"role": "assistant", "content": resp["answer"]})

if st.session_state.last_ctx:
    st.divider()
    if st.button("Generate RCA / Audit PDF Report from last answer"):
        with st.spinner("Report Generator Agent compiling PDF..."):
            report = api_post("/report/generate", {
                "query": st.session_state.last_ctx["query"],
                "ctx_data": st.session_state.last_ctx["ctx_data_for_report"],
            })
        if report:
            st.success(f"Report generated: {report['filename']}")
            st.code(report["report_path"])