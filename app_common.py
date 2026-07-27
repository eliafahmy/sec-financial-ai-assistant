"""
app_common.py
==============
وحدة مشتركة: التصميم (CSS)، الترجمة، الحالة العامة، والشريط الجانبي.
"""

import textwrap
import uuid

import streamlit as st


def md_html(html: str):
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)


STRINGS = {
    "ar": {
        "app_title": "مساعد SEC المالي",
        "app_tagline": "اسأل عن تقارير آبل ومايكروسوفت المالية الرسمية",
        "nav_chat": "المحادثة",
        "nav_dashboard": "لوحة البيانات",
        "nav_about": "عن المشروع",
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
        "nav_chat": "Chat",
        "nav_dashboard": "Dashboard",
        "nav_about": "About",
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

SUGGESTED_QUESTIONS = [
    "What was Apple's net income last quarter?",
    "What was Microsoft's total revenue for fiscal year 2025?",
    "Compare Apple's and Microsoft's revenue",
    "What are Apple's main risk factors?",
]


def t(key: str) -> str:
    lang = st.session_state.get("lang", "ar")
    return STRINGS[lang].get(key, key)


def _new_conversation_id() -> str:
    return str(uuid.uuid4())


def init_session_state():
    if "lang" not in st.session_state:
        st.session_state.lang = "ar"
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
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


def icon(name: str, size: int = 16, color: str = "currentColor") -> str:
    paths = {
        "doc": '<path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M9 13h6M9 17h6"/>',
        "chat": '<path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>',
        "chart": '<path d="M3 3v18h18"/><path d="M18 17V9M13 17V5M8 17v-4"/>',
    }
    inner = paths.get(name, "")
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
    )


def get_logo_svg(size: int = 36) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" fill="none">'
        f'<rect width="40" height="40" rx="10" fill="#1E293B"/>'
        f'<path d="M40 0 L40 40 L14 40 Z" fill="#2563EB"/>'
        f'<rect x="9" y="21" width="4.5" height="10" rx="1" fill="#F1F5F9"/>'
        f'<rect x="17.5" y="15" width="4.5" height="16" rx="1" fill="#F1F5F9"/>'
        f'<rect x="26" y="9" width="4.5" height="22" rx="1" fill="#F8FAFC" opacity="0.95"/>'
        f'</svg>'
    )


def get_css() -> str:
    theme = st.session_state.get("theme", "dark")

    if theme == "dark":
        bg = "#0F172A"
        bg_secondary = "#1E293B"
        text_primary = "#F1F5F9"
        text_secondary = "#94A3B8"
        border = "#334155"
        card_bg = "#1E293B"
        input_bg = "#1E293B"
        input_text = "#F1F5F9"
        placeholder_text = "#94A3B8"
        button_bg = "#1E293B"
        button_hover_bg = "#293548"
        assistant_bubble = "#1E293B"
        accent = "#3B82F6"
    else:
        bg = "#FFFFFF"
        bg_secondary = "#F8FAFC"
        text_primary = "#0F172A"
        text_secondary = "#475569"
        border = "#E2E8F0"
        card_bg = "#FFFFFF"
        input_bg = "#F8FAFC"
        input_text = "#0F172A"
        placeholder_text = "#64748B"
        button_bg = "#FFFFFF"
        button_hover_bg = "#F1F5F9"
        assistant_bubble = "#F8FAFC"
        accent = "#2563EB"

    return textwrap.dedent(f"""
    <style>
    :root {{
        --bg: {bg}; 
        --bg-secondary: {bg_secondary}; 
        --text-primary: {text_primary};
        --text-secondary: {text_secondary}; 
        --border: {border}; 
        --card-bg: {card_bg};
        --button-bg: {button_bg}; 
        --button-hover-bg: {button_hover_bg};
        --assistant-bubble: {assistant_bubble}; 
        --accent: {accent};
        --input-bg: {input_bg}; 
        --input-text: {input_text}; 
        --placeholder-text: {placeholder_text};
    }}
    
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background-color: var(--bg) !important;
        color: var(--text-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }}

    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] li,
    [data-testid="stAppViewContainer"] strong,
    [data-testid="stMarkdownContainer"] *,
    [data-testid="stChatMessageContent"] *,
    .stMarkdown, .stMarkdown p,
    h1, h2, h3, h4, h5, h6 {{ 
        color: var(--text-primary) !important; 
    }}

    .stCaption, [data-testid="stCaptionContainer"], small {{ 
        color: var(--text-secondary) !important; 
    }}
    
    section[data-testid="stSidebar"] {{ 
        background-color: var(--bg-secondary) !important; 
        border-right: 1px solid var(--border) !important; 
    }}
    section[data-testid="stSidebar"] * {{ 
        color: var(--text-primary) !important; 
    }}
    section[data-testid="stSidebar"] .stCaption {{ 
        color: var(--text-secondary) !important; 
    }}
    
    div[data-testid="stButton"] button {{
        background-color: var(--button-bg) !important; 
        color: var(--text-primary) !important;
        border: 1px solid var(--border) !important; 
        border-radius: 10px !important;
        font-weight: 500 !important; 
    }}
    div[data-testid="stButton"] button p {{ 
        color: var(--text-primary) !important; 
    }}
    div[data-testid="stButton"] button:hover {{ 
        background-color: var(--button-hover-bg) !important; 
        border-color: var(--accent) !important; 
    }}
    div[data-testid="stButton"] button:hover p {{ 
        color: var(--accent) !important; 
    }}
    
    div[data-testid="stSidebarNav"] li a,
    div[data-testid="stPageLink"] a {{
        background-color: var(--button-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
        margin-bottom: 6px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }}
    div[data-testid="stSidebarNav"] li a:hover,
    div[data-testid="stPageLink"] a:hover {{
        background-color: var(--button-hover-bg) !important;
        border-color: var(--accent) !important;
    }}
    div[data-testid="stSidebarNav"] li a span,
    div[data-testid="stPageLink"] p {{
        color: var(--text-primary) !important;
    }}

    div[data-testid="stChatMessage"] {{
        max-width: 88%; 
        background-color: var(--assistant-bubble) !important;
        border: 1px solid var(--border) !important; 
        border-radius: 14px;
    }}

    footer, 
    [data-testid="stBottom"], 
    [data-testid="stBottomBlockContainer"],
    div[data-testid="stBottom"] > div {{
        background-color: var(--bg) !important;
        background: var(--bg) !important;
    }}

    div[data-testid="stChatInput"] {{
        background-color: var(--input-bg) !important;
        border: 1px solid var(--border) !important;
        border-radius: 16px !important;
        max-width: 768px !important;
        margin: 0 auto !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
    }}
    div[data-testid="stChatInput"] textarea {{
        font-size: 15px !important;
        color: var(--input-text) !important;
        background-color: transparent !important;
        -webkit-text-fill-color: var(--input-text) !important;
    }}
    div[data-testid="stChatInput"] textarea::placeholder {{
        color: var(--placeholder-text) !important;
        -webkit-text-fill-color: var(--placeholder-text) !important;
    }}
    div[data-testid="stChatInput"] button {{
        background-color: var(--accent) !important;
        border-radius: 50% !important;
    }}
    div[data-testid="stChatInput"] button svg {{
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }}

    .app-brand {{ display: flex; align-items: center; gap: 10px; padding: 4px 0 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 10px; }}
    .app-brand-text {{ display: flex; flex-direction: column; line-height: 1.25; }}
    .app-brand-title {{ font-weight: 650; font-size: 15.5px; color: var(--text-primary); }}
    .app-brand-subtitle {{ font-size: 12px; color: var(--text-secondary); }}
    .nav-section {{ margin-bottom: 14px; }}
    .kpi-card {{
        background: var(--card-bg); border: 1px solid var(--border); border-left: 3px solid var(--accent);
        border-radius: 10px; padding: 16px 18px; margin-bottom: 10px;
    }}
    .kpi-label {{ font-size: 12px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 6px; }}
    .kpi-value {{ font-size: 24px; font-weight: 650; color: var(--text-primary); }}
    .kpi-meta {{ font-size: 11.5px; color: var(--text-secondary); margin-top: 4px; }}
    .company-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }}
    .company-badge {{ width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; color: white; }}
    .sidebar-footer {{ margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border); font-size: 12.5px; color: var(--text-secondary); text-align: center; }}
    .sidebar-footer a {{ color: var(--accent) !important; text-decoration: none; }}
    .answer-meta {{ font-size: 11.5px; color: var(--text-secondary); margin-top: 8px; display: flex; align-items: center; gap: 6px; }}
    .chat-greeting {{ font-size: 14px; color: var(--text-secondary); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }}
    .citation-card {{ background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; font-size: 12.5px; }}
    .citation-card .cc-top {{ display: flex; justify-content: space-between; align-items: center; color: var(--text-secondary); font-family: monospace; margin-bottom: 4px; }}
    .citation-card a {{ color: var(--accent) !important; text-decoration: none; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    @media (max-width: 640px) {{
        div[data-testid="stChatMessage"] {{ max-width: 96%; }}
        .kpi-value {{ font-size: 20px; }}
    }}
    </style>
    """)


def inject_css():
    st.markdown(get_css(), unsafe_allow_html=True)


def render_sidebar_brand():
    md_html(f"""
    <div class="app-brand">
    {get_logo_svg(36)}
    <div class="app-brand-text">
    <div class="app-brand-title">{t('app_title')}</div>
    <div class="app-brand-subtitle">{t('app_tagline')}</div>
    </div>
    </div>
    """)


def render_sidebar_footer():
    md_html(f"""
    <div class="sidebar-footer">
    {t('footer_credit')}<br>
    <strong>Elia Fahmy</strong><br>
    <a href="https://www.linkedin.com/in/elia-fahmy" target="_blank">LinkedIn ↗</a>
    </div>
    """)


def render_lang_theme_controls():
    col1, col2 = st.columns(2)
    with col1:
        lang_label = "EN" if st.session_state.lang == "ar" else "AR"
        if st.button(f"🌐 {lang_label}", use_container_width=True, key="lang_toggle"):
            st.session_state.lang = "en" if st.session_state.lang == "ar" else "ar"
            st.rerun()
    with col2:
        theme_icon_emoji = "☀️" if st.session_state.theme == "dark" else "🌙"
        if st.button(theme_icon_emoji, use_container_width=True, key="theme_toggle"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
