import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, api_get, page_header, chart_card_open, chart_card_close, PLOTLY_LAYOUT

inject_theme()
page_header("Analytics & Anomaly Detection",
            "Isolation Forest over downtime, cost, and maintenance frequency to flag "
            "abnormal patterns.")

result = api_get("/analytics/anomalies")

if result:
    anomalies = result.get("anomalies", [])
    if anomalies:
        df = pd.DataFrame(anomalies)
        chart_card_open(f"Anomalies Detected ({len(anomalies)})")
        fig = px.scatter(df, x="downtime_hours", y="cost", size="anomaly_score",
                          color="equipment_tag", hover_data=["date", "reason"],
                          color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#7C3AED", "#0EA5E9"])
        fig.update_layout(**PLOTLY_LAYOUT)
        fig.update_xaxes(gridcolor="#E5E7EB")
        fig.update_yaxes(gridcolor="#E5E7EB")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        chart_card_close()
    else:
        st.info(result.get("note", "No anomalies detected yet — need more work order data."))

    freq = result.get("highest_frequency_assets")
    if freq:
        chart_card_open("Assets with Highest Maintenance Frequency")
        freq_df = pd.DataFrame(list(freq.items()), columns=["equipment_tag", "frequency"])
        fig2 = px.bar(freq_df, x="equipment_tag", y="frequency",
                      color_discrete_sequence=["#EF4444"])
        fig2.update_layout(**PLOTLY_LAYOUT)
        fig2.update_xaxes(gridcolor="#E5E7EB", title=None)
        fig2.update_yaxes(gridcolor="#E5E7EB", title=None)
        st.plotly_chart(fig2, use_container_width=True)
        chart_card_close()

st.markdown('<div class="section-title">Platform-Wide Statistics</div>', unsafe_allow_html=True)
stats = api_get("/stats")
if stats:
    chart_card_open("Raw Statistics")
    st.json(stats)
    chart_card_close()