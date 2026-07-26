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


def detect_company_tickers(query: str, companies: list) -> list:
    """
    بتدور على كل أسماء الشركات المذكورة في السؤال (عربي/إنجليزي) وترجع
    قايمة بكل الـ Tickers المطابقة - ده بيدعم أسئلة المقارنة بين شركتين
    في نفس السؤال (مش بس أول شركة تتطابق).
    """
    query_normalized = normalize_arabic(query.lower())
    matched = []
    for company in companies:
        for alias in company.get("aliases", []):
            if normalize_arabic(alias.lower()) in query_normalized:
                matched.append(company["ticker"])
                break
    return matched


_ARABIC_HAMZA_PATTERN = re.compile(r"[أإآ]")
_ARABIC_DIACRITICS_PATTERN = re.compile(r"[\u0617-\u061A\u064B-\u0652]")


def normalize_arabic(text: str) -> str:
    """
    بتوحّد أشكال الألف المختلفة (أ/إ/آ -> ا) وتشيل التشكيل، عشان مقارنة
    المصطلحات العربية تشتغل مهما كانت طريقة كتابة المستخدم (بهمزة أو
    من غيرها، بـ"ال" التعريف أو من غيرها).
    """
    text = _ARABIC_HAMZA_PATTERN.sub("ا", text)
    text = _ARABIC_DIACRITICS_PATTERN.sub("", text)
    return text


# قاموس المصطلحات المالية العربية الشائعة -> الـ Tag/الـ Tags المطابقة
# (موديل الـ Embedding الصغير مش دايمًا بيفهم إن "صافي الربح" قريب من
# "Net Income" في الفضاء الرقمي، فبنضمن الربط ده يدويًا بدل ما نتوكل
# على فهمه الدلالي بس)
# ملحوظة: المصطلحات هنا من غير "ال" التعريف قصدًا (زي "ايرادات" مش
# "الإيرادات") عشان تتطابق سواء المستخدم كتبها بـ"ال" أو من غيرها.
ARABIC_FINANCIAL_TERMS = {
    "صافي الربح": ["NetIncomeLoss"],
    "صافي الدخل": ["NetIncomeLoss"],
    "صافي ربح": ["NetIncomeLoss"],
    "ارباح": ["NetIncomeLoss"],
    "ايرادات": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "مبيعات": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "اجمالي الربح": ["GrossProfit"],
    "مجمل الربح": ["GrossProfit"],
    "اصول": ["Assets"],
    "التزامات": ["Liabilities"],
    "خصوم": ["Liabilities"],
    "حقوق الملكية": ["StockholdersEquity"],
    "نقدية": ["CashAndCashEquivalentsAtCarryingValue"],
    "مخزون": ["InventoryNet"],
    "البحث والتطوير": ["ResearchAndDevelopmentExpense"],
    "ربحية السهم": ["EarningsPerShareBasic", "EarningsPerShareDiluted"],
    "التدفقات النقدية التشغيلية": ["NetCashProvidedByUsedInOperatingActivities"],
    "الانشطة التشغيلية": ["NetCashProvidedByUsedInOperatingActivities"],
    "ديون طويلة الاجل": ["LongTermDebt"],
}


def detect_tag_filter(query: str) -> list:
    """بتدور على مصطلح مالي عربي معروف في السؤال (بعد تطبيع الألف/التشكيل)، وترجع قايمة الـ Tags المطابقة."""
    normalized_query = normalize_arabic(query)
    matched_tags = []
    for term, tags in ARABIC_FINANCIAL_TERMS.items():
        if normalize_arabic(term) in normalized_query:
            matched_tags.extend(tags)
    return list(set(matched_tags)) or None


_STOPWORDS = {
    "what", "was", "is", "the", "of", "for", "in", "a", "an", "and",
    "reported", "how", "much", "did", "does", "company", "its",
}

# نمط لاستخراج اسم المؤشر المالي (Label) من الجملة النصية نفسها - محتاجينه
# لأن حقل "label" مش متخزّن فعليًا في الـ Chunks (Payload)؛ بس الـ section
# للأرقام المالية كلها ثابت وواحد ("Financial Facts (XBRL)") فمش بيميّز
# حاجة، فبنستخرج الاسم الحقيقي من النص نفسه بدل ما نعتمد عليه
_LABEL_FROM_TEXT_PATTERN = re.compile(r"reported (.+?) of \$")


def _extract_words(text: str) -> list:
    return re.findall(r"[a-zA-Z]+", text.lower())


def _get_reference_text(payload: dict) -> str:
    """بترجع أدق نص ممكن نقارن بيه (اسم المؤشر المالي أو القسم)."""
    if payload.get("chunk_type") == "financial_fact":
        match = _LABEL_FROM_TEXT_PATTERN.search(payload.get("text", ""))
        if match:
            return match.group(1)
    return payload.get("section") or ""


def lexical_overlap_score(query: str, payload: dict) -> float:
    """
    بتحسب درجة تطابق لفظي بين السؤال واسم المؤشر المالي (مستخرج من النص)
    أو القسم - مش النص الكامل، عشان منتلخبطش بكلمات مشتركة عامة
    (زي "reported", "according", "filed") موجودة في كل الـ Chunks بالتساوي.

    بتدّي وزن أعلى بكتير لو الكلمات اتطابقت كـ "عبارة متجاورة" (Bigram)
    زي "net income" - ده بيفرّق بدقة بين مؤشرات زي "Net Income" و
    "Accumulated Other Comprehensive Income ... Net of Tax" اللي
    بتشترك في نفس الكلمات المنفردة لكن مش بنفس الترتيب المتجاور.
    """
    reference_text = _get_reference_text(payload)

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


def _search_and_rerank(query: str, query_vector: list, config: dict, client,
                        ticker: str, tags: list, limit: int) -> list:
    """بتنفذ بحث + ترتيب لفظي لشركة واحدة بس (تُستخدم داخليًا)."""
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
        limit=limit,
    ).points

    boosted = []
    for point in results:
        boost = lexical_overlap_score(query, point.payload)
        final_score = point.score + boost * config["retrieval"]["lexical_boost_weight"]
        boosted.append((final_score, point))

    boosted.sort(key=lambda x: x[0], reverse=True)
    return boosted


def retrieve_context(query: str, top_n: int = None) -> list:
    """
    بترجع أفضل الأجزاء (Chunks) المتعلقة بسؤال المستخدم، بعد فلترة
    الشركة (لو مذكورة) وترتيب إضافي بالتطابق اللفظي.

    لو السؤال بيذكر أكتر من شركة (زي أسئلة المقارنة)، البحث بيتنفذ
    لكل شركة على حدة بشكل متوازن، عشان نضمن إن الاتنين ممثلين في
    النتائج النهائية بدل ما شركة واحدة تسيطر على كل الأماكن.
    """
    config = load_config()
    retrieval_cfg = config["retrieval"]
    top_n = top_n or retrieval_cfg["final_top_n"]

    model = get_model()
    client = get_client()

    query_prefix = config["embedding"]["query_prefix"]
    query_vector = model.encode(query_prefix + query, normalize_embeddings=True).tolist()

    tickers = detect_company_tickers(query, config["companies"])
    tags = detect_tag_filter(query)

    if len(tickers) >= 2:
        # سؤال مقارنة: بحث متوازن منفصل لكل شركة عشان نضمن تمثيل الاتنين
        per_company_n = max(top_n // len(tickers), 3)
        merged = []
        for ticker in tickers:
            boosted = _search_and_rerank(
                query, query_vector, config, client, ticker, tags,
                limit=retrieval_cfg["initial_top_k"],
            )
            merged.extend(boosted[:per_company_n])
        top_chunks = [point.payload for _, point in merged]
        return top_chunks

    ticker = tickers[0] if tickers else None
    boosted = _search_and_rerank(
        query, query_vector, config, client, ticker, tags,
        limit=retrieval_cfg["initial_top_k"],
    )
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
