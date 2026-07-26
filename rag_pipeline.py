"""
rag_pipeline.py
=================
وحدة مساعدة بسيطة بتربط صفحات Streamlit بملفات البايبلاين المرقمة
(06_retrieve_context.py و07_prompting.py) - أسماء الملفات دي مش
Identifiers صحيحة في بايثون (بتبدأ برقم)، فبنحمّلها عن طريق importlib.
"""

import importlib

import streamlit as st


@st.cache_resource(show_spinner=False)
def _load_pipeline_modules():
    retrieve_module = importlib.import_module("06_retrieve_context")
    prompting_module = importlib.import_module("07_prompting")
    return retrieve_module, prompting_module


def ask(question: str) -> dict:
    """
    بتاخد سؤال المستخدم، تسترجع أدق الأجزاء المرتبطة بيه من Qdrant،
    وتولّد إجابة نهائية عن طريق موديل لغوي مجاني. بترجع dict فيه
    الإجابة، اسم الموديل المستخدم، وقايمة المصادر.
    """
    retrieve_module, prompting_module = _load_pipeline_modules()

    # الـ API Key بيتحط في متغيرات البيئة من streamlit_app.py عن طريق
    # st.secrets قبل ما الدالة دي تتنادى
    chunks = retrieve_module.retrieve_context(question)
    result = prompting_module.generate_answer(question, chunks)
    return result


def load_key_facts(ticker: str) -> list:
    """بتحمل الأرقام المالية النظيفة لشركة معينة (للاستخدام في صفحة الداشبورد)."""
    import json
    from pathlib import Path

    retrieve_module, _ = _load_pipeline_modules()
    config = retrieve_module.load_config()
    facts_dir = Path(config["processing"]["facts_output_dir"])
    facts_path = facts_dir / f"{ticker}_key_facts.json"

    if not facts_path.exists():
        return []

    with open(facts_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_config() -> dict:
    retrieve_module, _ = _load_pipeline_modules()
    return retrieve_module.load_config()


def classify_period(start: str, end: str) -> str:
    """بنفس منطق 03_chunking.py - بتصنف الفترة الزمنية لسجل مالي معين."""
    from datetime import datetime

    if not start or not end:
        return "instant"

    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    days = (end_date - start_date).days

    if days <= 100:
        return "quarterly"
    elif days <= 200:
        return "half-year"
    elif days <= 290:
        return "nine-month"
    else:
        return "annual"
