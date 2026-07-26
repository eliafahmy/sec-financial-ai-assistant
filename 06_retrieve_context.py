"""
06_retrieve_context.py
========================
الخطوة السادسة: استرجاع أقرب الأجزاء (Chunks) لسؤال المستخدم من Qdrant،
مع طبقتين تحسين خفيفتين (بلا أي موديل إضافي تقيل):

  1) فلترة تلقائية حسب الشركة: لو السؤال بيذكر اسم شركة بوضوح (بالعربي
     أو الإنجليزي)، البحث بيتفلتر جوه Qdrant على الشركة دي بس.

  2) ترتيب إضافي بالتطابق اللفظي (Lexical Boost): أي Chunk فيه تطابق
     مباشر بين كلمات السؤال ونص الـ Chunk نفسه بياخد أولوية أعلى في
     الترتيب النهائي - ده بيصحح حالات زي "Net Income" اللي كانت بتتلخبط
     مع "Accumulated Other Comprehensive Income" بسبب التشابه اللفظي.

  النتيجة: بنسترجع عدد أكبر من النتائج (initial_top_k) ونودّي أفضلهم
  (final_top_n) لموديل التوليد في 07_prompting.py، مع تعليمات صريحة
  يختار الرقم الصح ويتجاهل الباقي.

الاستخدام (من غير تشغيل مباشر - بيتم استدعاؤه من streamlit_app.py):
    import importlib
    retrieve_module = importlib.import_module("06_retrieve_context")
    chunks = retrieve_module.retrieve_context("What was Apple's net income?")
"""

import os
import re

import yaml
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
from sentence_transformers import SentenceTransformer

# Cache بسيط عشان مانحملش الموديل أو نفتح اتصال جديد كل مرة (مهم للأداء
# جوه Streamlit اللي بيعيد تشغيل الكود مع كل تفاعل)
_config = None
_model = None
_client = None


def load_config(config_path: str = "config.yaml") -> dict:
    global _config
    if _config is None:
        with open(config_path, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        config = load_config()
        _model = SentenceTransformer(config["embedding"]["model_name"])
    return _model


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        url = os.environ.get("QDRANT_URL")
        api_key = os.environ.get("QDRANT_API_KEY")
        if not url or not api_key:
            raise ValueError("محتاج QDRANT_URL و QDRANT_API_KEY في متغيرات البيئة.")
        _client = QdrantClient(url=url, api_key=api_key)
    return _client


def detect_company_ticker(query: str, companies: list) -> str:
    """بتدور على اسم شركة واضح في السؤال (عربي/إنجليزي) وترجع الـ ticker، أو None."""
    query_lower = query.lower()
    for company in companies:
        for alias in company.get("aliases", []):
            if alias.lower() in query_lower:
                return company["ticker"]
    return None


# قاموس المصطلحات المالية العربية الشائعة -> الـ Tag/الـ Tags المطابقة
# (موديل الـ Embedding الصغير مش دايمًا بيفهم إن "صافي الربح" قريب من
# "Net Income" في الفضاء الرقمي، فبنضمن الربط ده يدويًا بدل ما نتوكل
# على فهمه الدلالي بس)
ARABIC_FINANCIAL_TERMS = {
    "صافي الربح": ["NetIncomeLoss"],
    "صافي الدخل": ["NetIncomeLoss"],
    "صافي ربح": ["NetIncomeLoss"],
    "الأرباح": ["NetIncomeLoss"],
    "الإيرادات": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "المبيعات": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "إجمالي الربح": ["GrossProfit"],
    "مجمل الربح": ["GrossProfit"],
    "الأصول": ["Assets"],
    "الالتزامات": ["Liabilities"],
    "الخصوم": ["Liabilities"],
    "حقوق الملكية": ["StockholdersEquity"],
    "النقدية": ["CashAndCashEquivalentsAtCarryingValue"],
    "المخزون": ["InventoryNet"],
    "البحث والتطوير": ["ResearchAndDevelopmentExpense"],
    "ربحية السهم": ["EarningsPerShareBasic", "EarningsPerShareDiluted"],
    "التدفقات النقدية التشغيلية": ["NetCashProvidedByUsedInOperatingActivities"],
    "الديون طويلة الأجل": ["LongTermDebt"],
}


def detect_tag_filter(query: str) -> list:
    """بتدور على مصطلح مالي عربي معروف في السؤال، وترجع قايمة الـ Tags المطابقة له."""
    matched_tags = []
    for term, tags in ARABIC_FINANCIAL_TERMS.items():
        if term in query:
            matched_tags.extend(tags)
    return list(set(matched_tags)) or None


_STOPWORDS = {
    "what", "was", "is", "the", "of", "for", "in", "a", "an", "and",
    "reported", "how", "much", "did", "does", "company", "its",
}


def _extract_words(text: str) -> list:
    return re.findall(r"[a-zA-Z]+", text.lower())


def lexical_overlap_score(query: str, payload: dict) -> float:
    """
    بتحسب درجة تطابق لفظي بين السؤال والمؤشر المالي (label) أو القسم
    (section) - مش النص الكامل، عشان منتلخبطش بكلمات مشتركة عامة
    (زي "reported", "according", "filed") موجودة في كل الـ Chunks بالتساوي.

    بتدّي وزن أعلى بكتير لو الكلمات اتطابقت كـ "عبارة متجاورة" (Bigram)
    زي "net income" - ده بيفرّق بدقة بين مؤشرات زي "Net Income" و
    "Accumulated Other Comprehensive Income ... Net of Tax" اللي
    بتشترك في نفس الكلمات المنفردة لكن مش بنفس الترتيب المتجاور.
    """
    reference_text = payload.get("label") or payload.get("section") or ""

    query_words = _extract_words(query)
    reference_words = _extract_words(reference_text)

    query_unigrams = set(query_words) - _STOPWORDS
    reference_unigrams = set(reference_words) - _STOPWORDS
    unigram_overlap = len(query_unigrams & reference_unigrams)

    query_bigrams = set(zip(query_words, query_words[1:]))
    reference_bigrams = set(zip(reference_words, reference_words[1:]))
    bigram_overlap = len(query_bigrams & reference_bigrams)

    # العبارة المتجاورة (Bigram) وزنها أعلى بكتير من كلمة منفردة عشان
    # تحسم التمييز بين مؤشرات بتشترك في نفس الكلمات لكن بترتيب مختلف
    return unigram_overlap * 1.0 + bigram_overlap * 5.0


def retrieve_context(query: str, top_n: int = None) -> list:
    """
    بترجع أفضل الأجزاء (Chunks) المتعلقة بسؤال المستخدم، بعد فلترة
    الشركة (لو مذكورة) وترتيب إضافي بالتطابق اللفظي.
    """
    config = load_config()
    retrieval_cfg = config["retrieval"]
    top_n = top_n or retrieval_cfg["final_top_n"]

    model = get_model()
    client = get_client()

    query_prefix = config["embedding"]["query_prefix"]
    query_vector = model.encode(query_prefix + query, normalize_embeddings=True).tolist()

    ticker = detect_company_ticker(query, config["companies"])
    tags = detect_tag_filter(query)

    filter_conditions = []
    if ticker:
        filter_conditions.append(FieldCondition(key="ticker", match=MatchValue(value=ticker)))
    if tags:
        filter_conditions.append(FieldCondition(key="tag", match=MatchAny(any=tags)))

    query_filter = Filter(must=filter_conditions) if filter_conditions else None

    results = client.query_points(
        collection_name=config["vector_store"]["collection_name"],
        query=query_vector,
        query_filter=query_filter,
        limit=retrieval_cfg["initial_top_k"],
    ).points

    boosted = []
    for point in results:
        boost = lexical_overlap_score(query, point.payload)
        final_score = point.score + boost * retrieval_cfg["lexical_boost_weight"]
        boosted.append((final_score, point))

    boosted.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [point.payload for _, point in boosted[:top_n]]

    return top_chunks


if __name__ == "__main__":
    test_queries = [
        "What was Apple's net income?",
        "كام صافي ربح مايكروسوفت؟",
    ]
    for q in test_queries:
        print(f"\n=== السؤال: {q} ===")
        chunks = retrieve_context(q)
        for i, chunk in enumerate(chunks, 1):
            tag = chunk.get("tag", chunk["chunk_type"])
            print(f"{i}. [{tag}] {chunk['text'][:150]}")
