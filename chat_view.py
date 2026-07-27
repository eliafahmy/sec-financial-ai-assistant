"""
chat_view.py
=============
منطق صفحة الشات - بشكل دالة قابلة للاستدعاء من نظام التنقل المخصص
في streamlit_app.py (st.navigation).
"""

import os

import streamlit as st

from app_common import (
    inject_css, render_sidebar_brand, render_sidebar_footer, render_lang_theme_controls,
    t, icon, md_html, SUGGESTED_QUESTIONS, start_new_conversation,
    get_current_history, add_to_current_history,
)
import rag_pipeline


def _ensure_secrets():
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
    with st.expander(f"{t('show_sources')} ({len(sources)})"):
        for i, src in enumerate(sources, 1):
            md_html(f"""
            <div class="citation-card">
            <div class="cc-top">
            <span>{src['ticker']} · {src['form']}</span>
            <a href="{src['source_url']}" target="_blank">{t('source')} ↗</a>
            </div>
            <div>{src['company']} — {t('filed_on')}: {src['filing_date']}</div>
            <div style="color:var(--text-secondary);">{t('section')}: {src.get('section', '—')}</div>
            </div>
            """)


def render_answer_meta(model_used: str, n_sources: int):
    if not model_used:
        return
    md_html(f"""
    <div class='answer-meta'>{icon('doc', 13)} {t('model_used')}: {model_used} ·
    {n_sources} {t('sources_count')}</div>
    """)


def render_chat_page():
    inject_css()
    _ensure_secrets()

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

    st.markdown(f"### {t('app_title')}")
    st.caption(t("app_tagline"))

    history = get_current_history()

    if not history:
        md_html("""
        <style>
        div[data-testid="stChatInput"] {
        position: relative !important; bottom: auto !important;
        margin-top: 24px;
        }
        </style>
        """)
        md_html(f"""
        <div style="text-align:center; padding: 40px 20px 10px 20px; color: var(--text-secondary);">
        <div style="margin-bottom: 14px;">{icon('chart', 34, 'var(--accent)')}</div>
        <div style="font-size: 17px; font-weight: 600; color: var(--text-primary);">{t('empty_chat_title')}</div>
        <div style="font-size: 14px; margin-top: 6px;">{t('empty_chat_subtitle')}</div>
        </div>
        """)
        typed_question = st.chat_input("Ask about Apple's or Microsoft's financials...")
    else:
        for entry in history:
            with st.chat_message("user"):
                st.markdown(entry["question"])
            with st.chat_message("assistant"):
                st.markdown(entry["answer"])
                if entry.get("sources"):
                    render_sources(entry["sources"])
                render_answer_meta(entry.get("model_used"), len(entry.get("sources", [])))

        md_html(f"<div class='chat-greeting'>{icon('chat', 15)} {t('greeting')}</div>")
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
            render_answer_meta(model_used, len(sources))

        add_to_current_history(question, answer, sources, model_used)
        st.rerun()
