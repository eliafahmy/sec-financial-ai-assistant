"""
dashboard_view.py
===================
منطق صفحة الداشبورد - أرقام مالية رئيسية + رسمين بيانيين (الإيرادات
وصافي الربح) لكل شركة، مستخرجة من بيانات SEC Company Facts النظيفة.
"""

import plotly.graph_objects as go
import streamlit as st

from app_common import (
    inject_css, render_sidebar_brand, render_sidebar_footer,
    render_lang_theme_controls, t, md_html,
)
import rag_pipeline

COMPANIES = [
    {"ticker": "AAPL", "name": "Apple Inc.", "color": "#1E293B"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "color": "#2563EB"},
]

REVENUE_TAGS = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"]
NET_INCOME_TAGS = ["NetIncomeLoss"]


def format_currency(value: float) -> str:
    abs_value = abs(value)
    sign = "-" if value < 0 else ""
    if abs_value >= 1_000_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000_000:.2f}T"
    if abs_value >= 1_000_000_000:
        return f"{sign}${abs_value / 1_000_000_000:.2f}B"
    if abs_value >= 1_000_000:
        return f"{sign}${abs_value / 1_000_000:.1f}M"
    return f"{sign}${abs_value:,.0f}"


def latest_record(records: list, tags: list, period_type: str):
    candidates = [
        r for r in records
        if r["tag"] in tags and rag_pipeline.classify_period(r.get("period_start"), r.get("period_end")) == period_type
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda r: r["period_end"])


def render_kpi_card(label: str, record, period_note: str = ""):
    if record is None:
        value_str, meta = "—", "—"
    else:
        value_str = format_currency(record["value"])
        meta = f"{record['form']} · {record['period_end']}" + (f" ({period_note})" if period_note else "")

    md_html(f"""
    <div class="kpi-card">
    <div class="kpi-label">{label}</div>
    <div class="kpi-value">{value_str}</div>
    <div class="kpi-meta">{meta}</div>
    </div>
    """)


def _quarterly_series(records: list, tags: list) -> list:
    quarterly = [
        r for r in records
        if r["tag"] in tags
        and rag_pipeline.classify_period(r.get("period_start"), r.get("period_end")) == "quarterly"
    ]
    quarterly = sorted(quarterly, key=lambda r: r["period_end"])
    seen, unique = set(), []
    for r in quarterly:
        if r["period_end"] not in seen:
            seen.add(r["period_end"])
            unique.append(r)
    return unique


def render_bar_chart(series: list, color: str, y_title: str):
    if not series:
        st.info("No data available yet for this chart.")
        return

    fig = go.Figure(
        data=[go.Bar(
            x=[r["period_end"] for r in series],
            y=[r["value"] / 1_000_000_000 for r in series],
            marker_color=color,
        )]
    )
    fig.update_xaxes(type="category")  # عشان المسافات بين الأرباع تبقى متساوية حتى لو فيه أرباع ناقصة
    fig.update_layout(
        height=240,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title=y_title,
        font=dict(family="-apple-system, Segoe UI, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_dashboard_page():
    inject_css()

    with st.sidebar:
        render_sidebar_brand()
        render_lang_theme_controls()
        render_sidebar_footer()

    st.markdown(f"### {t('nav_dashboard')}")

    tabs = st.tabs([c["name"] for c in COMPANIES])

    for tab, company in zip(tabs, COMPANIES):
        with tab:
            records = rag_pipeline.load_key_facts(company["ticker"])

            md_html(f"""
            <div class="company-header">
            <div class="company-badge" style="background:{company['color']}">{company['ticker'][:2]}</div>
            <div style="font-size:19px; font-weight:650;">{company['name']}</div>
            </div>
            """)

            if not records:
                st.warning("No data found. Make sure data/processed/facts/*.json is included in the repo.")
                continue

            col1, col2, col3 = st.columns(3)
            with col1:
                render_kpi_card("Revenue", latest_record(records, REVENUE_TAGS, "quarterly"), "Q")
            with col2:
                render_kpi_card("Net Income", latest_record(records, NET_INCOME_TAGS, "quarterly"), "Q")
            with col3:
                render_kpi_card("Gross Profit", latest_record(records, ["GrossProfit"], "quarterly"), "Q")

            col4, col5, col6 = st.columns(3)
            with col4:
                render_kpi_card("Total Assets", latest_record(records, ["Assets"], "instant"))
            with col5:
                render_kpi_card("Total Liabilities", latest_record(records, ["Liabilities"], "instant"))
            with col6:
                render_kpi_card("Cash & Equivalents", latest_record(records, ["CashAndCashEquivalentsAtCarryingValue"], "instant"))

            st.markdown("<br>", unsafe_allow_html=True)
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                st.markdown("**Quarterly Revenue**")
                render_bar_chart(_quarterly_series(records, REVENUE_TAGS), company["color"], "Billion USD")
            with chart_col2:
                st.markdown("**Quarterly Net Income**")
                render_bar_chart(_quarterly_series(records, NET_INCOME_TAGS), company["color"], "Billion USD")
