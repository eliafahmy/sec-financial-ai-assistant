"""
pages/1_📊_Dashboard.py
=========================
صفحة داشبورد بسيطة تعرض أهم المؤشرات المالية لآبل ومايكروسوفت،
مستخرجة مباشرة من بيانات SEC Company Facts النظيفة (بلا أي تدخل
يدوي في الأرقام).
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plotly.graph_objects as go
import streamlit as st

from app_common import init_session_state, inject_css, render_sidebar_brand, render_sidebar_footer, render_lang_theme_controls, t
import rag_pipeline

st.set_page_config(page_title="Dashboard - SEC Financial Assistant", page_icon="📊", layout="wide")

init_session_state()
inject_css()

with st.sidebar:
    render_sidebar_brand()
    render_lang_theme_controls()
    render_sidebar_footer()

st.markdown(f"### {t('nav_dashboard')}")

COMPANIES = [
    {"ticker": "AAPL", "name": "Apple Inc.", "color": "#1E293B"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "color": "#2563EB"},
]

REVENUE_TAGS = ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues"]


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
    """بترجع أحدث سجل (بأحدث تاريخ نهاية فترة) يطابق أحد الـ Tags ونوع الفترة المطلوب."""
    candidates = [
        r for r in records
        if r["tag"] in tags and rag_pipeline.classify_period(r.get("period_start"), r.get("period_end")) == period_type
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda r: r["period_end"])


def render_kpi_card(label: str, record, period_note: str = ""):
    if record is None:
        value_str = "—"
        meta = t("nav_dashboard")
    else:
        value_str = format_currency(record["value"])
        meta = f"{record['form']} · {record['period_end']}" + (f" ({period_note})" if period_note else "")

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value_str}</div>
            <div class="kpi-meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_revenue_chart(records: list, color: str):
    quarterly = [
        r for r in records
        if r["tag"] in REVENUE_TAGS
        and rag_pipeline.classify_period(r.get("period_start"), r.get("period_end")) == "quarterly"
    ]
    if not quarterly:
        st.info(t("nav_dashboard"))
        return

    quarterly = sorted(quarterly, key=lambda r: r["period_end"])
    # نشيل تكرار محتمل لنفس التاريخ (لو ظهر أكتر من مرة في تقارير مختلفة)
    seen = set()
    unique_quarterly = []
    for r in quarterly:
        if r["period_end"] not in seen:
            seen.add(r["period_end"])
            unique_quarterly.append(r)

    fig = go.Figure(
        data=[
            go.Bar(
                x=[r["period_end"] for r in unique_quarterly],
                y=[r["value"] / 1_000_000_000 for r in unique_quarterly],
                marker_color=color,
            )
        ]
    )
    fig.update_layout(
        height=260,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Billion USD",
        font=dict(family="-apple-system, Segoe UI, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)


tabs = st.tabs([c["name"] for c in COMPANIES])

for tab, company in zip(tabs, COMPANIES):
    with tab:
        records = rag_pipeline.load_key_facts(company["ticker"])

        st.markdown(
            f"""
            <div class="company-header">
                <div class="company-badge" style="background:{company['color']}">{company['ticker'][:2]}</div>
                <div style="font-size:19px; font-weight:650;">{company['name']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not records:
            st.warning("No data found. Run the ingestion pipeline first.")
            continue

        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card("Revenue", latest_record(records, REVENUE_TAGS, "quarterly"), "Q")
        with col2:
            render_kpi_card("Net Income", latest_record(records, ["NetIncomeLoss"], "quarterly"), "Q")
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
        st.markdown("**Quarterly Revenue Trend**")
        render_revenue_chart(records, company["color"])
