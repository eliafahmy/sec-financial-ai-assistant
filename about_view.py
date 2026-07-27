"""
about_view.py
==============
منطق صفحة "عن المشروع".
"""

import streamlit as st

from app_common import inject_css, render_sidebar_brand, render_sidebar_footer, render_lang_theme_controls


def render_about_page():
    inject_css()

    with st.sidebar:
        render_sidebar_brand()
        render_lang_theme_controls()
        render_sidebar_footer()

    lang = st.session_state.lang

    if lang == "ar":
        st.markdown("### عن المشروع")
        st.markdown(
            """
مساعد **SEC Financial AI Assistant** هو نظام RAG (Retrieval-Augmented Generation)
بيجاوب على أسئلتك عن التقارير المالية الرسمية لشركتي **Apple** و **Microsoft**،
بالاعتماد فقط على النص الفعلي لتقارير **10-K** (السنوية) و **10-Q** (الربعية)
المقدمة رسميًا لهيئة **SEC** الأمريكية - من غير اختلاق أي معلومة غير موجودة
في المصدر.

#### إزاي بيشتغل؟
1. **جلب البيانات** مباشرة من SEC EDGAR API (المستندات + الأرقام المالية الرسمية).
2. **تنظيف ومعالجة** النصوص، مع فصل الأرقام المالية من مصدر منظم (Company Facts)
   لضمان دقتها 100%.
3. **تقسيم وترميز** كل جزء لتمثيل رقمي (Embedding)، وتخزينه في قاعدة بيانات متجهات.
4. **الاسترجاع**: لما تسأل سؤال، النظام بيدور على أدق الأجزاء المرتبطة بيه.
5. **التوليد**: موديل لغوي بيجاوب بناءً على الأجزاء المسترجعة فقط، مع ذكر
   المصدر لأي رقم بيقوله.

#### حدود المشروع
- البيانات مقتصرة على **Apple** و **Microsoft** بس، آخر سنة من التقارير.
- الإجابات **مش نصيحة استثمارية**؛ دايمًا ارجع للمستند الأصلي المذكور كمصدر.
- المشروع تعليمي (مشروع تخرج)، مش أداة مالية احترافية معتمدة.

#### التقنيات المستخدمة
SEC EDGAR API · Docling · Sentence Transformers · Qdrant · OpenRouter · Streamlit
            """
        )
    else:
        st.markdown("### About this project")
        st.markdown(
            """
**SEC Financial AI Assistant** is a Retrieval-Augmented Generation (RAG) system
that answers questions about the official financial filings of **Apple** and
**Microsoft**, grounded only in the actual text of their **10-K** (annual) and
**10-Q** (quarterly) reports submitted to the U.S. **SEC** - with no invented
information beyond what's in the source.

#### How it works
1. **Ingestion** directly from the SEC EDGAR API (filings + official financial facts).
2. **Cleaning & processing** of the text, with financial figures sourced separately
   from a structured feed (Company Facts) to guarantee 100% accuracy.
3. **Chunking & embedding** each piece into a vector representation, stored in a
   vector database.
4. **Retrieval**: when you ask a question, the system finds the most relevant pieces.
5. **Generation**: a language model answers based only on the retrieved context,
   citing the source for every figure.

#### Scope & limitations
- Data is limited to **Apple** and **Microsoft** only, covering the last year of filings.
- Answers are **not investment advice** - always check the cited original document.
- This is an educational (graduation) project, not a certified financial tool.

#### Built with
SEC EDGAR API · Docling · Sentence Transformers · Qdrant · OpenRouter · Streamlit
            """
        )
