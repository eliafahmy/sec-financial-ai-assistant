"""
app_common.py
==============
وحدة مشتركة بين كل صفحات التطبيق: التصميم (CSS)، نصوص الترجمة، وإعداد
الحالة العامة للجلسة (بما فيها المحادثات المتعددة).
"""

import uuid

import streamlit as st

# ---------------------------------------------------------------
# نصوص الترجمة (واجهة فقط - الأسئلة المقترحة إنجليزي دايمًا بمعزل عن اللغة)
# ---------------------------------------------------------------
STRINGS = {
    "ar": {
        "app_title": "مساعد SEC المالي",
        "app_tagline": "اسأل عن تقارير آبل ومايكروسوفت المالية الرسمية",
        "nav_dashboard": "لوحة البيانات",
        "new_chat": "محادثة جديدة",
        "recent_chats": "المحادثات السابقة",
        "suggested_questions": "أسئلة مقترحة",
        "show_sources": "عرض المصادر",
        "source": "المصدر",
        "filed_on": "تاريخ التقديم",
        "section": "القسم",
        "empty_chat_title": "ابدأ بسؤال عن آبل أو مايكروسوفت",
        "empty_chat_subtitle": "الإجابات مبنية فقط على تقارير 10-K و10-Q الرسمية المقدمة لهيئة SEC",
        "greeting": "أهلًا! أقدر أساعدك ازاي النهاردة؟",
        "thinking": "جاري البحث في التقارير...",
        "footer_credit": "بُني بواسطة",
        "model_used": "الموديل",
        "sources_count": "مصدر",
    },
    "en": {
        "app_title": "SEC Financial Assistant",
        "app_tagline": "Ask about Apple's and Microsoft's official financial filings",
        "nav_dashboard": "Dashboard",
        "new_chat": "New chat",
        "recent_chats": "Recent chats",
        "suggested_questions": "Suggested questions",
        "show_sources": "Show sources",
        "source": "Source",
        "filed_on": "Filed on",
        "section": "Section",
        "empty_chat_title": "Ask something about Apple or Microsoft",
        "empty_chat_subtitle": "Answers are grounded only in official 10-K and 10-Q filings submitted to the SEC",
        "greeting": "Hi! How can I help you today?",
        "thinking": "Searching the filings...",
        "footer_credit": "Built by",
        "model_used": "Model",
        "sources_count": "sources",
    },
}

# الأسئلة المقترحة إنجليزي دايمًا (بغض النظر عن لغة الواجهة) - النظام
# نفسه بيفهم عربي وإنجليزي، ده بس بخصوص شكل الأزرار في الشريط الجانبي
SUGGESTED_QUESTIONS = [
    "What was Apple's net income last quarter?",
    "What was Microsoft's total revenue for fiscal year 2025?",
    "Compare Apple's and Microsoft's revenue",
    "What are Apple's main risk factors?",
]


def t(key: str) -> str:
    lang = st.session_state.get("lang", "ar")
    return STRINGS[lang].get(key, key)


# ---------------------------------------------------------------
# إعداد الحالة العامة للجلسة - بما فيها دعم محادثات متعددة (زي
# ChatGPT/Claude/Gemini): تقدر تبدأ محادثة جديدة، والقديمة تفضل
# محفوظة وتقدر ترجعلها من الشريط الجانبي.
# ---------------------------------------------------------------
def _new_conversation_id() -> str:
    return str(uuid.uuid4())


def init_session_state():
    if "lang" not in st.session_state:
        st.session_state.lang = "ar"
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "conversations" not in st.session_state:
        first_id = _new_conversation_id()
        st.session_state.conversations = {first_id: {"title": None, "history": []}}
        st.session_state.current_conv_id = first_id


def start_new_conversation():
    new_id = _new_conversation_id()
    st.session_state.conversations[new_id] = {"title": None, "history": []}
    st.session_state.current_conv_id = new_id


def get_current_history() -> list:
    return st.session_state.conversations[st.session_state.current_conv_id]["history"]


def add_to_current_history(question: str, answer: str, sources: list, model_used: str = None):
    conv = st.session_state.conversations[st.session_state.current_conv_id]
    conv["history"].append({
        "question": question, "answer": answer, "sources": sources, "model_used": model_used,
    })
    if conv["title"] is None:
        conv["title"] = question[:42] + ("…" if len(question) > 42 else "")


# ---------------------------------------------------------------
# التصميم (CSS)
# ---------------------------------------------------------------
def get_css() -> str:
    theme = st.session_state.get("theme", "light")

    if theme == "dark":
        bg = "#0B1220"
        bg_secondary = "#121A2C"
        text_primary = "#F2F5F9"
        text_secondary = "#94A3B8"
        border = "#26314A"
        card_bg = "#141C30"
        user_bubble = "#173357"
        assistant_bubble = "#141C30"
        accent = "#3B9EFF"
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

    accent_hover = accent
    apple_accent = text_primary
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

    /* فرض لون النص الأساسي على كل عناصر Markdown والشات - عشان الوضع
       الداكن يبقى مقروء دايمًا (مش معتمد على ألوان Streamlit الافتراضية) */
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stChatMessageContent"] p,
    h1, h2, h3, h4, h5, h6 {{
        color: var(--text-primary) !important;
    }}

    .stCaption, [data-testid="stCaptionContainer"], small {{
        color: var(--text-secondary) !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: var(--bg-secondary);
        border-right: 1px solid var(--border);
    }}
    section[data-testid="stSidebar"] * {{
        color: var(--text-primary) !important;
    }}
    section[data-testid="stSidebar"] .stCaption {{
        color: var(--text-secondary) !important;
    }}

    div[data-testid="stChatMessage"] {{
        max-width: 88%;
        background-color: var(--assistant-bubble);
        border-radius: 16px;
    }}

    div[data-testid="stChatInput"] textarea {{
        font-size: 16px !important;
        border-radius: 20px !important;
        color: var(--text-primary) !important;
        background-color: var(--card-bg) !important;
    }}

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
    .app-brand-text {{ display: flex; flex-direction: column; line-height: 1.25; }}
    .app-brand-title {{ font-weight: 650; font-size: 15.5px; color: var(--text-primary); }}
    .app-brand-subtitle {{ font-size: 12px; color: var(--text-secondary); }}

    .kpi-card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 10px;
    }}
    .kpi-label {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; }}
    .kpi-value {{ font-size: 26px; font-weight: 650; color: var(--text-primary); }}
    .kpi-meta {{ font-size: 11.5px; color: var(--text-secondary); margin-top: 4px; }}

    .company-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }}
    .company-badge {{
        width: 42px; height: 42px; border-radius: 11px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 15px; color: white;
    }}

    .sidebar-footer {{
        margin-top: 20px;
        padding-top: 14px;
        border-top: 1px solid var(--border);
        font-size: 12.5px;
        color: var(--text-secondary);
        text-align: center;
    }}
    .sidebar-footer a {{ color: var(--accent) !important; text-decoration: none; }}

    .answer-meta {{
        font-size: 11.5px;
        color: var(--text-secondary);
        margin-top: 6px;
    }}

    .chat-greeting {{
        font-size: 14px;
        color: var(--text-secondary);
        margin-bottom: 6px;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    @media (max-width: 640px) {{
        div[data-testid="stChatMessage"] {{ max-width: 96%; }}
        .kpi-value {{ font-size: 21px; }}
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
        f"""
        <div class="sidebar-footer">
            {t('footer_credit')}<br>
            <strong>Elia Fahmy</strong><br>
            <a href="https://www.linkedin.com/in/elia-fahmy" target="_blank">LinkedIn ↗</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_lang_theme_controls():
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
