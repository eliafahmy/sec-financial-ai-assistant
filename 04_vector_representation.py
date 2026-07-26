"""
04_vector_representation.py
=============================
الخطوة الرابعة: تحويل كل Chunk نصي لتمثيل رقمي (Embedding) باستخدام
موديل multilingual-e5-small - مُشغّل محليًا.

ليه الموديل ده بالذات (مش bge-m3)؟
    Streamlit Community Cloud المجاني محدود بـ 1GB RAM فقط، وbge-m3
    (2+ جيجا) مش هيتحمل فيه. multilingual-e5-small (~470 ميجا) بيدّي
    تغطية عربي/إنجليزي كويسة، وبيشتغل مرتاح جوه حدود Streamlit المجانية
    وقت الاستعلام الحي، من غير أي اعتماد على API خارجي وحصص شهرية محدودة
    (Hugging Face Inference Providers المجاني بيدّي أقل من 0.10$ شهريًا
    فقط، اتضح إنه غير كافي حتى للاستخدام الخفيف).

ملحوظة تقنية: موديلات عائلة E5 بتحتاج بادئة قبل كل نص حسب نوعه
    ("passage: " للمستندات وقت الفهرسة، "query: " لسؤال المستخدم وقت
    الاسترجاع لاحقًا) - ده Convention رسمي للموديل بيحسّن جودة النتائج.

طريقة التشغيل:
    python 04_vector_representation.py

المدخلات:
    - data/processed/chunks/all_chunks.json

المخرجات:
    - data/processed/embeddings/embeddings.json
"""

import json
from pathlib import Path

import yaml
from sentence_transformers import SentenceTransformer


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()
    chunks_path = Path(config["chunking"]["output_path"])
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    embed_cfg = config["embedding"]
    model_name = embed_cfg["model_name"]
    batch_size = embed_cfg["batch_size"]
    passage_prefix = embed_cfg["passage_prefix"]

    print(f"[*] بنحمل موديل {model_name} محليًا...")
    model = SentenceTransformer(model_name)

    # بادئة "passage: " إلزامية لموديلات E5 عشان تفرّق بين نص مستند ونص سؤال
    texts = [passage_prefix + c["text"] for c in chunks]
    chunk_ids = [c["chunk_id"] for c in chunks]

    print(f"[*] بنعمل Embedding لـ {len(texts)} chunk (Batch size: {batch_size})...")
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,  # مهم عشان البحث بـ Cosine Similarity في Qdrant بعدين
    )

    results = [
        {"chunk_id": cid, "vector": vec.tolist()}
        for cid, vec in zip(chunk_ids, vectors)
    ]

    output_path = Path("data/processed/embeddings/embeddings.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f)

    print(f"\n[✓] إجمالي الـ Embeddings: {len(results)}")
    print(f"[✓] طول كل Vector: {len(results[0]['vector'])}")
    print(f"[✓] اتحفظوا في: {output_path}")


if __name__ == "__main__":
    main()
