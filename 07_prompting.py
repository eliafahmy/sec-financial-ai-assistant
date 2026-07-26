"""
07_prompting.py
=================
الخطوة السابعة: بناء الـ Prompt وتوليد الإجابة النهائية من موديل لغوي
مجاني عن طريق OpenRouter، بناءً على الأجزاء المسترجعة من 06_retrieve_context.py.

قواعد التصميم (لمنع الهلوسة):
    1) الموديل يجاوب من النص المسترجع بس - ولو المعلومة مش موجودة يقول
       كده صراحة بدل ما يخترع رقم.
    2) نفس المؤشر المالي ممكن يظهر لفترات مختلفة (ربع سنوي/نصف سنوي/
       سنوي) في نفس النتائج - الموديل لازم يميّز بينهم بوضوح ويختار
       الأنسب للسؤال، مش يخلط بينهم.
    3) كل رقم لازم يتوثّق بمصدره (نوع التقرير + تاريخ التقديم).
    4) يجاوب بنفس لغة السؤال (عربي أو إنجليزي).

آلية اختيار الموديل:
    بنجيب قايمة الموديلات النصية المتاحة فعليًا كـ "مجانية" من OpenRouter
    وقت التشغيل نفسه (مش اسم ثابت في الكود)، ونجرب بالترتيب لحد ما واحد
    ينجح - لو موديل معين اتشال من القايمة المجانية، النظام يبدّل تلقائيًا
    لموديل تاني متاح من غير ما يقع.

متطلبات:
    - OPENROUTER_API_KEY في متغيرات البيئة محليًا، أو في Streamlit
      secrets وقت النشر (streamlit_app.py بيتحقق من الاتنين).
"""

import os

import requests
import yaml

# متغيرات على مستوى الموديول - قابلة للتعديل من الخارج (زي streamlit_app.py)
# لو الـ API Key مش موجود في متغيرات البيئة محليًا، ويتحط بعدين من
# Streamlit secrets وقت النشر.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = "openai/gpt-4o-mini"  # قيمة احتياطية أخيرة بس - النظام بيفضّل موديل مجاني ديناميكي
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# قايمة احتياطية لو تعذّر جلب قايمة الموديلات المجانية الحية من OpenRouter لأي سبب
FALLBACK_FREE_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "google/gemma-2-9b-it:free",
    "mistralai/mistral-7b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free",
]


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_free_models() -> list:
    """بتجيب قايمة الموديلات النصية المتاحة فعليًا كـ Free من OpenRouter وقت التشغيل نفسه."""
    response = requests.get(f"{OPENROUTER_BASE_URL}/models", timeout=30)
    response.raise_for_status()
    models = response.json().get("data", [])

    free_models = [
        m["id"] for m in models
        if m.get("pricing", {}).get("prompt") == "0"
        and m.get("pricing", {}).get("completion") == "0"
    ]
    return free_models


def build_prompt(question: str, chunks: list) -> list:
    """بتبني رسائل الـ Chat (System + User) بالسياق المسترجع، مع تعليمات صريحة لمنع الهلوسة."""
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        source_line = (
            f"[Source {i}] {chunk['company_name']} ({chunk['ticker']}) - "
            f"{chunk['form']} filed {chunk['filing_date']} - "
            f"Section: {chunk.get('section', 'N/A')}"
        )
        context_blocks.append(f"{source_line}\n{chunk['text']}")

    context_text = "\n\n".join(context_blocks)

    system_prompt = (
        "You are a financial assistant that answers questions about SEC filings "
        "(10-K and 10-Q reports) for Apple and Microsoft, using ONLY the context "
        "provided below.\n\n"
        "Rules you MUST follow strictly:\n"
        "1. Answer ONLY using information explicitly present in the context below. "
        "Never use outside knowledge, and never invent or estimate a number.\n"
        "2. If the answer is not present in the context, say so explicitly, in "
        "the same language as the question - do not guess or approximate.\n"
        "3. The same financial metric often appears for DIFFERENT time periods "
        "(quarterly, six-month, nine-month, or full fiscal year) in the context. "
        "Read each source's period carefully and pick the one that matches what "
        "the user is asking about. If the question doesn't specify a period, use "
        "the most recent one available and clearly state which period it covers.\n"
        "4. Always cite the source for any figure you mention: report type "
        "(10-K/10-Q) and filing date, e.g. '(10-Q filed 2026-05-01)'.\n"
        "5. Answer in the same language the user asked in (Arabic or English).\n"
        "6. Be concise and direct - a few sentences is usually enough."
    )

    user_prompt = f"Context:\n\n{context_text}\n\nQuestion: {question}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _call_openrouter(model_name: str, messages: list, api_key: str) -> str:
    response = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model_name, "messages": messages, "temperature": 0.1},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def generate_answer(question: str, chunks: list) -> dict:
    """
    الدالة الأساسية: بتولد الإجابة النهائية بناءً على الأجزاء المسترجعة.
    بتجرب الموديلات المجانية المتاحة بالترتيب لحد ما واحد ينجح، وبترجع
    الإجابة + اسم الموديل المستخدم + قايمة المصادر (لعرضها في الواجهة).
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("محتاج تحط OPENROUTER_API_KEY في متغيرات البيئة أو Streamlit secrets الأول.")

    if not chunks:
        return {
            "answer": "لا تتوفر معلومات كافية في المستندات المسترجعة للإجابة على هذا السؤال.",
            "model_used": None,
            "sources": [],
        }

    messages = build_prompt(question, chunks)

    try:
        candidate_models = get_free_models() or FALLBACK_FREE_MODELS
    except Exception:
        candidate_models = FALLBACK_FREE_MODELS

    last_error = None
    for model_name in candidate_models:
        try:
            answer_text = _call_openrouter(model_name, messages, OPENROUTER_API_KEY)
            return {
                "answer": answer_text,
                "model_used": model_name,
                "sources": [
                    {
                        "company": c["company_name"],
                        "ticker": c["ticker"],
                        "form": c["form"],
                        "filing_date": c["filing_date"],
                        "section": c.get("section"),
                        "source_url": c["source_url"],
                    }
                    for c in chunks
                ],
            }
        except Exception as e:
            last_error = e
            continue

    # آخر محاولة: الموديل الاحتياطي الثابت (لو متاح لسه)
    try:
        answer_text = _call_openrouter(OPENROUTER_MODEL, messages, OPENROUTER_API_KEY)
        return {
            "answer": answer_text,
            "model_used": OPENROUTER_MODEL,
            "sources": [
                {
                    "company": c["company_name"], "ticker": c["ticker"], "form": c["form"],
                    "filing_date": c["filing_date"], "section": c.get("section"),
                    "source_url": c["source_url"],
                }
                for c in chunks
            ],
        }
    except Exception as e:
        raise RuntimeError(f"فشلت كل الموديلات المتاحة (آخر خطأ: {e}). الخطأ قبله: {last_error}")


# ---------------------------------------------------------------
# اختبار يدوي مباشر - بيستدعي 06_retrieve_context.py تلقائيًا
# ---------------------------------------------------------------
def main():
    import importlib
    retrieve_module = importlib.import_module("06_retrieve_context")

    test_questions = [
        "What was Apple's net income?",
        "كام صافي ربح مايكروسوفت؟",
    ]

    for question in test_questions:
        print(f"\n{'=' * 60}\nالسؤال: {question}\n{'=' * 60}")
        chunks = retrieve_module.retrieve_context(question)
        result = generate_answer(question, chunks)
        print(f"الموديل المستخدم: {result['model_used']}")
        print(f"\nالإجابة:\n{result['answer']}")
        print(f"\nعدد المصادر: {len(result['sources'])}")


if __name__ == "__main__":
    main()
