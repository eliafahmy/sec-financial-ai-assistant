"""
streamlit_app.py
==================
الصفحة الرئيسية للتطبيق - واجهة شات بوت لسؤال/إجابة عن التقارير المالية
الرسمية لآبل ومايكروسوفت، مبنية فوق بايبلاين RAG الكامل (01-07).
"""

import os

import streamlit as st

from app_common import (
    init_session_state, inject_css, render_sidebar_brand, render_sidebar_footer,
    render_lang_theme_controls, t, SUGGESTED_QUESTIONS, start_new_conversation,
    get_current_history, add_to_current_history,
)
import rag_pipeline

st.set_page_config(
    page_title="SEC Financial Assistant",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded",
)

init_session_state()
inject_css()

# ---------------------------------------------------------------
# ربط مفاتيح الـ API من Streamlit secrets وقت النشر
# ---------------------------------------------------------------
try:
    prompting_module = rag_pipeline._load_pipeline_modules()[1]
    if not prompting_module.OPENROUTER_API_KEY:
        prompting_module.OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY", "")
    if not os.environ.get("QDRANT_URL"):
        os.environ["QDRANT_URL"] = st.secrets.get("QDRANT_URL", "")
    if not os.environ.get("QDRANT_API_KEY"):
        os.environ["QDRANT_API_KEY"] = st.secrets.get("QDRANT_API_KEY", "")
except Exception:
    pass


def render_sources(sources: list):
    with st.expander(f"📎 {t('show_sources')} ({len(sources)})"):
        for i, src in enumerate(sources, 1):
            st.markdown(
                f"**{i}.** {src['company']} ({src['ticker']}) — {src['form']} · "
                f"{t('filed_on')}: {src['filing_date']}  \n"
                f"{t('section')}: {src.get('section', '—')}  \n"
                f"[{t('source')} ↗]({src['source_url']})"
            )


# ---------------------------------------------------------------
# الشريط الجانبي
# ---------------------------------------------------------------
with st.sidebar:
    render_sidebar_brand()

    if st.button("＋ " + t("new_chat"), use_container_width=True):
        start_new_conversation()
        st.rerun()

    st.markdown(f"**{t('suggested_questions')}**")
    for i, question_text in enumerate(SUGGESTED_QUESTIONS):
        if st.button(question_text, use_container_width=True, key=f"suggest_{i}"):
            st.session_state.pending_question = question_text
            st.rerun()

    # قايمة المحادثات السابقة - تقدر ترجع لأي واحدة منها
    other_conversations = [
        (cid, conv) for cid, conv in st.session_state.conversations.items()
        if cid != st.session_state.current_conv_id and conv["history"]
    ]
    if other_conversations:
        st.markdown("---")
        st.markdown(f"**{t('recent_chats')}**")
        for cid, conv in reversed(other_conversations):
            label = conv["title"] or "..."
            if st.button(f"💬 {label}", use_container_width=True, key=f"conv_{cid}"):
                st.session_state.current_conv_id = cid
                st.rerun()

    st.markdown("---")
    render_lang_theme_controls()
    render_sidebar_footer()


# ---------------------------------------------------------------
# منطقة الشات الرئيسية
# ---------------------------------------------------------------
st.markdown(f"### {t('app_title')}")
st.caption(t("app_tagline"))

history = get_current_history()

if not history:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 50px 20px; color: var(--text-secondary);">
            <div style="font-size: 40px; margin-bottom: 10px;">📊</div>
            <div style="font-size: 17px; font-weight: 600; color: var(--text-primary);">{t('empty_chat_title')}</div>
            <div style="font-size: 14px; margin-top: 6px;">{t('empty_chat_subtitle')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

for entry in history:
    with st.chat_message("user"):
        st.markdown(entry["question"])
    with st.chat_message("assistant"):
        st.markdown(entry["answer"])
        if entry.get("sources"):
            render_sources(entry["sources"])
        if entry.get("model_used"):
            st.markdown(
                f"<div class='answer-meta'>🔧 {t('model_used')}: {entry['model_used']} · "
                f"📄 {len(entry.get('sources', []))} {t('sources_count')}</div>",
                unsafe_allow_html=True,
            )

# رسالة ترحيب بسيطة فوق صندوق الكتابة - زي Claude/Gemini
st.markdown(f"<div class='chat-greeting'>💬 {t('greeting')}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------
# معالجة سؤال جديد
# ---------------------------------------------------------------
typed_question = st.chat_input("Ask about Apple's or Microsoft's financials...")
question = st.session_state.pending_question or typed_question
st.session_state.pending_question = None

if question:
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner(t("thinking")):
            try:
                result = rag_pipeline.ask(question)
                answer = result["answer"]
                sources = result.get("sources", [])
                model_used = result.get("model_used")
            except Exception as e:
                answer = f"⚠️ {e}"
                sources = []
                model_used = None
        st.markdown(answer)
        if sources:
            render_sources(sources)
        if model_used:
            st.markdown(
                f"<div class='answer-meta'>🔧 {t('model_used')}: {model_used} · "
                f"📄 {len(sources)} {t('sources_count')}</div>",
                unsafe_allow_html=True,
            )

    add_to_current_history(question, answer, sources, model_used)
    st.rerun()
