"""
streamlit_app.py
==================
نقطة الدخول الرئيسية للتطبيق. الملف ده بس "موجّه" (Router) بيتحكم في
التنقل بين الصفحات - بأسماء وأيقونات مخصصة إحنا اللي بنحددها، مش
معتمدين على تسمية الملفات التلقائية من Streamlit.

المنطق الفعلي لكل صفحة موجود في ملف منفصل:
    chat_view.py       -> صفحة الشات
    dashboard_view.py  -> صفحة الداشبورد
    about_view.py       -> صفحة عن المشروع
"""

import streamlit as st

from app_common import init_session_state
from chat_view import render_chat_page
from dashboard_view import render_dashboard_page
from about_view import render_about_page

st.set_page_config(
    page_title="SEC Financial Assistant",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded",
)

init_session_state()

pages = [
    st.Page(render_chat_page, title="Chat", icon=":material/chat:", default=True, url_path="chat"),
    st.Page(render_dashboard_page, title="Dashboard", icon=":material/speed:", url_path="dashboard"),
    st.Page(render_about_page, title="About", icon=":material/info:", url_path="about"),
]

navigation = st.navigation(pages, position="sidebar")
navigation.run()
