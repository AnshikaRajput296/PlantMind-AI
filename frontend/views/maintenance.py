import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, api_get, api_post, page_header, kpi_card, chart_card_open, chart_card_close, PLOTLY_LAYOUT

inject_theme()
page_header("Maintenance Intelligence",
            "Failure trends, downtime, and cost across all tracked equipment.")

work_orders = api_get("/work-orders") or []

if work_orders:
    df = pd.DataFrame(work_orders)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Work Orders", len(df), "assignment")
    with c2:
        kpi_card("Total Downtime (h)", f"{df['downtime_hours'].sum():.1f}", "schedule")
    with c3:
        kpi_card("Total Cost", f"₹{df['cost'].sum():,.0f}", "payments")
    with c4:
        kpi_card("Assets Tracked", df['equipment_tag'].nunique(), "precision_manufacturing")

    col1, col2 = st.columns(2)
    with col1:
        chart_card_open("Top Recurring Failure Modes")
        fm_counts = df[df['failure_mode'] != 'none']['failure_mode'].value_counts().reset_index()
        fm_counts.columns = ["failure_mode", "count"]
        fig = px.bar(fm_counts, x="failure_mode", y="count",
                     color_discrete_sequence=["#2563EB"])
        fig.update_layout(**PLOTLY_LAYOUT)
        fig.update_xaxes(gridcolor="#E5E7EB", title=None)
        fig.update_yaxes(gridcolor="#E5E7EB", title=None)
        st.plotly_chart(fig, use_container_width=True)
        chart_card_close()

    with col2:
        chart_card_open("Most Vulnerable Assets")
        eq_counts = df['equipment_tag'].value_counts().reset_index()
        eq_counts.columns = ["equipment_tag", "count"]
        fig2 = px.bar(eq_counts, x="equipment_tag", y="count",
                      color_discrete_sequence=["#F59E0B"])
        fig2.update_layout(**PLOTLY_LAYOUT)
        fig2.update_xaxes(gridcolor="#E5E7EB", title=None)
        fig2.update_yaxes(gridcolor="#E5E7EB", title=None)
        st.plotly_chart(fig2, use_container_width=True)
        chart_card_close()

    chart_card_open("Downtime Timeline")
    df_sorted = df.sort_values("date")
    fig3 = px.line(df_sorted, x="date", y="downtime_hours", color="equipment_tag", markers=True,
                    color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#7C3AED", "#0EA5E9"])
    fig3.update_layout(**PLOTLY_LAYOUT)
    fig3.update_xaxes(gridcolor="#E5E7EB", title=None)
    fig3.update_yaxes(gridcolor="#E5E7EB", title=None)
    st.plotly_chart(fig3, use_container_width=True)
    chart_card_close()

    chart_card_open("Full Work Order Log")
    st.dataframe(df, use_container_width=True, hide_index=True)
    chart_card_close()
else:
    st.info("No work orders yet. Run the seed script or add one below.")

st.markdown('<div class="section-title">Log New Work Order</div>', unsafe_allow_html=True)
chart_card_open("New Work Order")
with st.form("wo_form"):
    c1, c2, c3 = st.columns(3)
    equipment_tag = c1.text_input("Equipment Tag", value="P-101")
    date = c2.date_input("Date")
    technician = c3.text_input("Technician")
    description = st.text_area("Description")
    c4, c5, c6 = st.columns(3)
    failure_mode = c4.text_input("Failure Mode")
    downtime = c5.number_input("Downtime (hours)", min_value=0.0, value=0.0)
    cost = c6.number_input("Cost", min_value=0.0, value=0.0)
    submitted = st.form_submit_button("Submit Work Order")
    if submitted:
        result = api_post("/work-orders", {
            "equipment_tag": equipment_tag, "date": str(date), "technician": technician,
            "description": description, "failure_mode": failure_mode,
            "downtime_hours": downtime, "cost": cost,
        })
        if result:
            st.success("Work order logged and Knowledge Graph updated.")
            st.rerun()
chart_card_close()