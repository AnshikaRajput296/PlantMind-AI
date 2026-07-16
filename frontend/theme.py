"""
Design System — PlantMind AI
------------------------------
Enterprise light theme (Linear / Notion / Azure Portal style). Single
source of truth for colors, typography, spacing, and reusable UI
components (KPI cards, chart cards, agent cards, header). Icons come from
Google's Material Symbols Outlined set (via st.Page `icon=` for nav, and
the `.icon` CSS class for inline use) — never emoji.
"""
from __future__ import annotations

import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def inject_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,300..500,0..1,0&display=swap');

    :root {
        --primary: #2563EB;
        --primary-hover: #1D4ED8;
        --primary-light: #EFF6FF;
        --background: #F5F7FA;
        --surface: #FFFFFF;
        --border: #E5E7EB;
        --hover: #F3F4F6;
        --text-primary: #111827;
        --text-secondary: #6B7280;
        --success: #10B981;
        --success-light: #ECFDF5;
        --warning: #F59E0B;
        --warning-light: #FFFBEB;
        --danger: #EF4444;
        --danger-light: #FEF2F2;
        --radius: 10px;
        --shadow: 0 1px 3px rgba(0,0,0,0.08);
        --space-1: 8px;
        --space-2: 16px;
        --space-3: 24px;
        --space-4: 32px;
    }

    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

    .icon {
        font-family: 'Material Symbols Outlined';
        font-weight: 400;
        font-style: normal;
        font-size: 20px;
        vertical-align: middle;
        line-height: 1;
        color: var(--text-secondary);
    }
    .icon-primary { color: var(--primary); }

    /* ================= App shell ================= */
    .stApp { background: var(--background); color: var(--text-primary); }
    .block-container { padding-top: var(--space-3); padding-bottom: var(--space-4); max-width: 1280px; }
    #MainMenu, footer, header[data-testid="stHeader"] { background: transparent; }

    /* ================= Sidebar ================= */
    section[data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
        min-width: 260px !important;
        width: 260px !important;
    }
    section[data-testid="stSidebar"] * { color: var(--text-primary); }
    section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {
        color: var(--text-secondary) !important;
    }

    [data-testid="stSidebarNav"] { padding-top: var(--space-1); }
    [data-testid="stSidebarNav"] ul { gap: 2px; }
    [data-testid="stSidebarNav"] a, [data-testid="stSidebarNavLink"] {
        border-radius: 8px;
        margin: 1px 12px;
        padding: 9px 12px !important;
        font-size: 15px;
        font-weight: 500;
        color: var(--text-secondary) !important;
        transition: background 0.15s ease;
        white-space: nowrap;
        overflow: visible !important;
        text-overflow: unset !important;
    }
    [data-testid="stSidebarNav"] a span, [data-testid="stSidebarNavLink"] span {
        overflow: visible !important;
        text-overflow: unset !important;
        white-space: nowrap !important;
    }
    [data-testid="stSidebarNav"] a:hover { background: var(--hover); color: var(--text-primary) !important; }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: var(--primary-light) !important;
        color: var(--primary) !important;
        font-weight: 600;
        border-left: 3px solid var(--primary);
        padding-left: 9px !important;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] svg { color: var(--primary) !important; }

    .sidebar-brand {
        display: flex; align-items: center; gap: 10px;
        padding: var(--space_1, 8px) 4px var(--space-2) 4px;
        margin-bottom: 4px;
        border-bottom: 1px solid var(--border);
    }
    .sidebar-brand-mark {
        width: 32px; height: 32px; border-radius: 8px; background: var(--primary);
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 700; font-size: 15px; flex-shrink: 0;
    }
    .sidebar-brand-text { line-height: 1.25; }
    .sidebar-brand-title { font-weight: 700; font-size: 15.5px; color: var(--text-primary); white-space: nowrap; }
    .sidebar-brand-subtitle { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }
    .sidebar-footer { font-size: 12.5px; color: var(--text-secondary); padding: 8px 4px; }

    /* ================= Typography ================= */
    h1, h2, h3, h4 { color: var(--text-primary) !important; font-weight: 700 !important; letter-spacing: -0.01em; }
    h1 { font-size: 26px !important; }
    h2, .section-title { font-size: 20px !important; margin-top: 4px !important; }
    h3 { font-size: 16px !important; }
    p, span, label, div { color: var(--text-primary); }
    .stCaption, small { color: var(--text-secondary) !important; font-size: 13px; }
    .body-text { font-size: 14px; color: var(--text-primary); }

    .page-title { font-size: 26px; font-weight: 700; color: var(--text-primary); margin-bottom: 2px; }
    .page-subtitle { font-size: 14px; color: var(--text-secondary); margin-bottom: var(--space-3); }

    /* ================= Top header ================= */
    .app-header {
        display: flex; align-items: center; justify-content: space-between;
        padding-bottom: var(--space-2); margin-bottom: var(--space-3);
        border-bottom: 1px solid var(--border);
    }
    .app-header-left .title { font-size: 22px; font-weight: 700; color: var(--text-primary); line-height: 1.3; }
    .app-header-left .subtitle { font-size: 13.5px; color: var(--text-secondary); }

    /* ================= Cards ================= */
    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        border-radius: var(--radius);
        padding: var(--space-3);
        margin-bottom: var(--space-2);
    }
    .card-title-row {
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: var(--space-2);
    }
    .card-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }

    /* Equal-height KPI cards */
    .kpi-card {
        background: var(--surface);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        border-radius: var(--radius);
        padding: var(--space-2) var(--space-3);
        height: 118px;
        display: flex; flex-direction: column; justify-content: space-between;
        margin-bottom: var(--space-2);
        transition: box-shadow 0.15s ease, transform 0.15s ease;
    }
    .kpi-card:hover { box-shadow: 0 4px 10px rgba(0,0,0,0.08); transform: translateY(-1px); }
    .kpi-icon-row { display: flex; align-items: center; justify-content: space-between; }
    .kpi-value { font-size: 30px; font-weight: 700; color: var(--text-primary); line-height: 1.1; }
    .kpi-label { font-size: 13px; color: var(--text-secondary); font-weight: 500; }

    /* Equal-height agent cards */
    .agent-card {
        background: var(--surface);
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        border-radius: var(--radius);
        padding: var(--space-2);
        height: 128px;
        display: flex; flex-direction: column; gap: 6px;
        margin-bottom: var(--space-2);
        transition: box-shadow 0.15s ease;
    }
    .agent-card:hover { box-shadow: 0 4px 10px rgba(0,0,0,0.08); }
    .agent-card-icon {
        width: 32px; height: 32px; border-radius: 8px; background: var(--primary-light);
        display: flex; align-items: center; justify-content: center; margin-bottom: 2px;
    }
    .agent-card-title { font-size: 14px; font-weight: 600; color: var(--text-primary); line-height: 1.3; }
    .agent-card-desc { font-size: 12.5px; color: var(--text-secondary); line-height: 1.4; }

    /* ================= Badges ================= */
    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 6px;
        font-size: 12px; font-weight: 600; letter-spacing: 0.01em;
        margin-right: 6px; border: 1px solid transparent;
    }
    .badge-low { background: var(--success-light); color: #047857; border-color: #A7F3D0; }
    .badge-medium { background: var(--warning-light); color: #B45309; border-color: #FDE68A; }
    .badge-high { background: var(--danger-light); color: #B91C1C; border-color: #FECACA; }

    /* ================= Agent reasoning trace ================= */
    .agent-step {
        border-left: 3px solid var(--primary);
        padding: 8px 0 8px 12px;
        margin-bottom: 6px;
        background: var(--primary-light);
        border-radius: 0 8px 8px 0;
    }
    .agent-name { color: var(--primary); font-weight: 600; font-size: 13px; }
    .agent-msg { color: var(--text-primary); font-size: 13.5px; }

    /* ================= Buttons ================= */
    .stButton>button {
        background: var(--primary);
        color: #FFFFFF; font-weight: 600; font-size: 14px; border: none; border-radius: 8px;
        padding: 8px 16px; box-shadow: none; transition: background 0.15s ease;
    }
    .stButton>button:hover { background: var(--primary-hover); color: #FFFFFF; }
    .stButton>button:focus { box-shadow: 0 0 0 3px var(--primary-light) !important; }

    button[kind="secondary"] {
        background: var(--surface) !important; color: var(--text-primary) !important;
        border: 1px solid var(--border) !important;
    }
    button[kind="secondary"]:hover { background: var(--hover) !important; }

    /* ================= Inputs ================= */
    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    .stDateInput input, .stSelectbox div[data-baseweb="select"] > div {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        font-size: 14px !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px var(--primary-light) !important;
    }

    /* ================= Misc ================= */
    hr { border-color: var(--border) !important; margin: var(--space-3) 0 !important; }

    div[data-testid="stMetric"] {
        background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
        padding: 14px 18px; box-shadow: var(--shadow);
    }
    div[data-testid="stMetricValue"] { color: var(--text-primary); font-weight: 700; font-size: 26px; }
    div[data-testid="stMetricLabel"] { color: var(--text-secondary); font-size: 13px; }

    details { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
    summary { font-size: 14px !important; font-weight: 500 !important; }

    [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: var(--radius); }

    .stTabs [data-baseweb="tab-list"] { gap: var(--space-1); border-bottom: 1px solid var(--border); }
    .stTabs [data-baseweb="tab"] { color: var(--text-secondary); font-weight: 500; }
    .stTabs [aria-selected="true"] { color: var(--primary) !important; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Reusable components
# ---------------------------------------------------------------------------
def sidebar_brand():
    st.sidebar.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-mark">P</div>
        <div class="sidebar-brand-text">
            <div class="sidebar-brand-title">PlantMind AI</div>
            <div class="sidebar-brand-subtitle">Knowledge Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def sidebar_footer(role: str = "Engineer", plant: str = "Plant A · Unit 2"):
    st.sidebar.markdown(f"""
    <div class="sidebar-footer">{role} &middot; {plant}</div>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", right_html: str = ""):
    st.markdown(f"""
    <div class="app-header">
        <div class="app-header-left">
            <div class="title">{title}</div>
            <div class="subtitle">{subtitle}</div>
        </div>
        <div class="app-header-right">{right_html}</div>
    </div>
    """, unsafe_allow_html=True)


def kpi_card(label: str, value, icon: str = "analytics"):
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-icon-row">
            <span class="icon">{icon}</span>
        </div>
        <div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
    </div>""", unsafe_allow_html=True)


def agent_card(title: str, desc: str, icon: str = "smart_toy"):
    st.markdown(f"""<div class="agent-card">
        <div class="agent-card-icon"><span class="icon icon-primary">{icon}</span></div>
        <div class="agent-card-title">{title}</div>
        <div class="agent-card-desc">{desc}</div>
    </div>""", unsafe_allow_html=True)


def chart_card_open(title: str):
    st.markdown(f"""<div class="card">
        <div class="card-title-row"><span class="card-title">{title}</span></div>""",
        unsafe_allow_html=True)


def chart_card_close():
    st.markdown("</div>", unsafe_allow_html=True)


PLOTLY_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#111827", size=13),
    margin=dict(l=10, r=10, t=10, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


def confidence_badge(risk: str) -> str:
    cls = {"low": "badge-low", "medium": "badge-medium", "high": "badge-high"}.get(risk, "badge-medium")
    return f'<span class="badge {cls}">{risk.upper()} RISK</span>'


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------
def api_get(path: str, **kwargs):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error on GET {path}: {e}")
        return None


def api_post(path: str, json_body: dict | None = None, files=None, timeout=60):
    try:
        r = requests.post(f"{API_BASE}{path}", json=json_body, files=files, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error on POST {path}: {e}")
        return None