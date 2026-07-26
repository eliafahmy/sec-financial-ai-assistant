"""
app_common.py
==============
وحدة مشتركة بين كل صفحات التطبيق (streamlit_app.py وpages/*): التصميم
(CSS)، نصوص الترجمة (عربي/إنجليزي)، وإعداد الحالة العامة للجلسة.

اتجاه التصميم: واجهة نظيفة واحترافية بروح Apple/Microsoft - خطوط
النظام الأصلية (SF Pro لأبل، Segoe UI لمايكروسوفت)، ألوان محايدة
هادئة مع لمسة أزرق واحدة كعنصر مميز، بطاقات بحواف دائرية ناعمة،
وبلا أي زخرفة زايدة عن الحاجة.
"""

import streamlit as st

# ---------------------------------------------------------------
# نصوص الترجمة
# ---------------------------------------------------------------
STRINGS = {
    "ar": {
        "app_title": "مساعد SEC المالي",
        "app_tagline": "اسأل عن تقارير آبل ومايكروسوفت المالية الرسمية",
        "nav_chat": "المحادثة",
        "nav_dashboard": "لوحة البيانات",
        "nav_about": "عن المشروع",
        "new_chat": "محادثة جديدة",
        "suggested_questions": "أسئلة مقترحة",
        "language": "اللغة",
        "theme": "المظهر",
        "theme_light": "فاتح",
        "theme_dark": "داكن",
        "show_sources": "عرض المصادر",
        "hide_sources": "إخفاء المصادر",
        "source": "المصدر",
        "filed_on": "تاريخ التقديم",
        "section": "القسم",
        "empty_chat_title": "ابدأ بسؤال عن آبل أو مايكروسوفت",
        "empty_chat_subtitle": "الإجابات مبنية فقط على تقارير 10-K و10-Q الرسمية المقدمة لهيئة SEC",
        "thinking": "جاري البحث في التقارير...",
        "footer_credit": "بُني بواسطة",
        "q1": "كام صافي ربح آبل في آخر ربع سنة؟",
        "q2": "What was Microsoft's total revenue for fiscal year 2025?",
        "q3": "قارن بين إيرادات آبل ومايكروسوفت",
        "q4": "What are Apple's main risk factors?",
    },
    "en": {
        "app_title": "SEC Financial Assistant",
        "app_tagline": "Ask about Apple's and Microsoft's official financial filings",
        "nav_chat": "Chat",
        "nav_dashboard": "Dashboard",
        "nav_about": "About",
        "new_chat": "New chat",
        "suggested_questions": "Suggested questions",
        "language": "Language",
        "theme": "Theme",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "show_sources": "Show sources",
        "hide_sources": "Hide sources",
        "source": "Source",
        "filed_on": "Filed on",
        "section": "Section",
        "empty_chat_title": "Ask something about Apple or Microsoft",
        "empty_chat_subtitle": "Answers are grounded only in official 10-K and 10-Q filings submitted to the SEC",
        "thinking": "Searching the filings...",
        "footer_credit": "Built by",
        "q1": "What was Apple's net income last quarter?",
        "q2": "ايه إجمالي إيرادات مايكروسوفت في السنة المالية 2025؟",
        "q3": "Compare Apple's and Microsoft's revenue",
        "q4": "ايه أهم عوامل المخاطرة لآبل؟",
    },
}


def t(key: str) -> str:
    """بترجع النص المترجم حسب لغة الواجهة الحالية."""
    lang = st.session_state.get("lang", "ar")
    return STRINGS[lang].get(key, key)


# ---------------------------------------------------------------
# إعداد الحالة العامة للجلسة (مرة واحدة بس)
# ---------------------------------------------------------------
def init_session_state():
    defaults = {
        "lang": "ar",
        "theme": "light",
        "chat_history": [],
        "pending_question": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------
# التصميم (CSS) - نظام ألوان واحد لكل الوضعين (فاتح/داكن)
# ---------------------------------------------------------------
def get_css() -> str:
    theme = st.session_state.get("theme", "light")

    if theme == "dark":
        bg = "#1C1C1E"
        bg_secondary = "#2C2C2E"
        text_primary = "#F5F5F7"
        text_secondary = "#98989D"
        border = "#38383A"
        card_bg = "#2C2C2E"
        user_bubble = "#0A3D67"
        assistant_bubble = "#2C2C2E"
    else:
        bg = "#FFFFFF"
        bg_secondary = "#F5F5F7"
        text_primary = "#1D1D1F"
        text_secondary = "#6E6E73"
        border = "#D2D2D7"
        card_bg = "#FFFFFF"
        user_bubble = "#E8F0FE"
        assistant_bubble = "#F5F5F7"

    accent = "#0071E3"
    accent_hover = "#0077ED"
    apple_accent = "#1D1D1F" if theme == "light" else "#F5F5F7"
    msft_accent = "#0078D4"

    return f"""
    <style>
    :root {{
        --bg: {bg};
        --bg-secondary: {bg_secondary};
        --text-primary: {text_primary};
        --text-secondary: {text_secondary};
        --border: {border};
        --card-bg: {card_bg};
        --user-bubble: {user_bubble};
        --assistant-bubble: {assistant_bubble};
        --accent: {accent};
        --accent-hover: {accent_hover};
        --apple-accent: {apple_accent};
        --msft-accent: {msft_accent};
    }}

    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
            "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }}

    .stApp {{
        background-color: var(--bg);
        color: var(--text-primary);
    }}

    section[data-testid="stSidebar"] {{
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border);
    }}

    section[data-testid="stSidebar"] * {{
        color: var(--text-primary);
    }}

    /* عنوان التطبيق في الشريط الجانبي */
    .app-brand {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 0 18px 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 16px;
    }}
    .app-brand-mark {{
        width: 34px;
        height: 34px;
        border-radius: 9px;
        background: linear-gradient(135deg, var(--apple-accent) 0%, var(--msft-accent) 100%);
        flex-shrink: 0;
    }}
    .app-brand-text {{
        display: flex;
        flex-direction: column;
        line-height: 1.25;
    }}
    .app-brand-title {{
        font-weight: 650;
        font-size: 15.5px;
        color: var(--text-primary);
    }}
    .app-brand-subtitle {{
        font-size: 12px;
        color: var(--text-secondary);
    }}

    /* فقاعات الشات */
    div[data-testid="stChatMessage"] {{
        max-width: 88%;
    }}

    /* صندوق الكتابة - حجم أكبر شبيه بـ ChatGPT / Claude */
    div[data-testid="stChatInput"] textarea {{
        font-size: 16px !important;
        border-radius: 20px !important;
    }}

    /* بطاقات KPI في الداشبورد */
    .kpi-card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 10px;
    }}
    .kpi-label {{
        font-size: 13px;
        color: var(--text-secondary);
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 26px;
        font-weight: 650;
        color: var(--text-primary);
    }}
    .kpi-meta {{
        font-size: 11.5px;
        color: var(--text-secondary);
        margin-top: 4px;
    }}

    .company-header {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
    }}
    .company-badge {{
        width: 42px;
        height: 42px;
        border-radius: 11px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 15px;
        color: white;
    }}

    /* توقيع أسفل الشريط الجانبي */
    .sidebar-footer {{
        margin-top: 24px;
        padding-top: 14px;
        border-top: 1px solid var(--border);
        font-size: 12.5px;
        color: var(--text-secondary);
        text-align: center;
    }}

    /* إخفاء بعض عناصر Streamlit الافتراضية اللي مش محتاجينها */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    /* استجابة للشاشات الصغيرة */
    @media (max-width: 640px) {{
        div[data-testid="stChatMessage"] {{
            max-width: 96%;
        }}
        .kpi-value {{
            font-size: 21px;
        }}
    }}
    </style>
    """


def inject_css():
    st.markdown(get_css(), unsafe_allow_html=True)


def render_sidebar_brand():
    st.markdown(
        f"""
        <div class="app-brand">
            <div class="app-brand-mark"></div>
            <div class="app-brand-text">
                <div class="app-brand-title">{t('app_title')}</div>
                <div class="app-brand-subtitle">{t('app_tagline')}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer():
    st.markdown(
        f"""<div class="sidebar-footer">{t('footer_credit')}<br><strong>Elia Fahmy</strong></div>""",
        unsafe_allow_html=True,
    )


def render_lang_theme_controls():
    """أزرار تبديل اللغة والمظهر - بتتكرر في كل صفحة."""
    col1, col2 = st.columns(2)
    with col1:
        lang_label = "EN" if st.session_state.lang == "ar" else "AR"
        if st.button(f"🌐 {lang_label}", use_container_width=True, key="lang_toggle"):
            st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
            st.rerun()
    with col2:
        theme_icon = "🌙" if st.session_state.theme == "light" else "☀️"
        if st.button(theme_icon, use_container_width=True, key="theme_toggle"):
            st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
            st.rerun()
