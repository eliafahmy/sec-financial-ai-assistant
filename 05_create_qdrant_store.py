"""
05_create_qdrant_store.py
============================
الخطوة الخامسة: إنشاء Collection في Qdrant ورفع كل الـ Chunks مع
الـ Embeddings بتاعتهم والـ Metadata الكاملة، جاهزين للاسترجاع الفوري.

ملحوظة تسمية: التعليمات الرسمية للتسليم بتسمي الملف ده
"05_create_chroma_store.py" (بافتراض استخدام ChromaDB). إحنا استخدمنا
Qdrant بدلاً منه لأسباب تقنية (فلترة Metadata متقدمة بين شركتين)، وغيّرنا
اسم الملف ليعكس ده بوضوح. **لازم تتأكد من الدكتور إن التغيير ده مقبول
قبل التسليم النهائي.**

طريقة التشغيل:
    python 05_create_qdrant_store.py

متطلبات:
    - QDRANT_URL و QDRANT_API_KEY في متغيرات البيئة (Colab Secrets)

المدخلات:
    - data/processed/chunks/all_chunks.json
    - data/processed/embeddings/embeddings.json

المخرجات:
    - Collection في Qdrant Cloud اسمها sec_filings، فيها 1418 نقطة
      (كل نقطة = Chunk + Vector + Metadata كاملة)
"""

import json
import os
from pathlib import Path

import yaml
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, PointStruct, VectorParams


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def connect_to_qdrant() -> QdrantClient:
    url = os.environ.get("QDRANT_URL")
    api_key = os.environ.get("QDRANT_API_KEY")
    if not url or not api_key:
        raise ValueError(
            "محتاج تحط QDRANT_URL و QDRANT_API_KEY في متغيرات البيئة الأول."
        )
    return QdrantClient(url=url, api_key=api_key)


def ensure_collection(client: QdrantClient, collection_name: str, vector_size: int):
    """
    بتنشئ Collection جديدة لو مش موجودة. لو موجودة بالفعل من تشغيل سابق،
    بتسيبها زي ما هي (Idempotent) - عشان إعادة التشغيل متكررش البيانات.
    """
    existing_collections = [c.name for c in client.get_collections().collections]
    if collection_name in existing_collections:
        print(f"[*] Collection '{collection_name}' موجودة بالفعل، هنضيف/نحدّث النقط فيها")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(f"[✓] اتعملت Collection جديدة: '{collection_name}' (Vector size: {vector_size})")

    # لازم فهرس مخصص على حقل ticker عشان نقدر نفلتر البحث بيه (06_retrieve_context.py)
    client.create_payload_index(
        collection_name=collection_name,
        field_name="ticker",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print(f"[✓] اتعمل فهرس (Index) على حقل 'ticker' عشان الفلترة تشتغل")

    client.create_payload_index(
        collection_name=collection_name,
        field_name="tag",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print(f"[✓] اتعمل فهرس (Index) على حقل 'tag' عشان فلترة المصطلحات العربية تشتغل")


def build_points(chunks: list, embeddings_map: dict) -> list:
    """
    بتدمج كل Chunk مع الـ Vector بتاعه، وتبنيهم كـ Points جاهزة للرفع.
    كل الـ Metadata (الشركة، النوع، القسم، المصدر...) بتتحط في الـ Payload
    عشان نقدر نفلتر بيها وقت البحث.
    """
    points = []
    for i, chunk in enumerate(chunks):
        chunk_id = chunk["chunk_id"]
        vector = embeddings_map.get(chunk_id)
        if vector is None:
            print(f"[!] تحذير: مفيش Embedding لـ chunk {chunk_id}, هنتخطاه")
            continue

        points.append(
            PointStruct(
                id=i,  # Qdrant بيحتاج ID رقمي أو UUID؛ بنستخدم رقم متسلسل هنا
                vector=vector,
                payload=chunk,  # كل الـ Metadata + النص نفسه بيتحط كـ Payload
            )
        )
    return points


def main():
    config = load_config()

    chunks = load_json(config["chunking"]["output_path"])
    embeddings = load_json("data/processed/embeddings/embeddings.json")
    embeddings_map = {e["chunk_id"]: e["vector"] for e in embeddings}

    print(f"[*] عدد الـ Chunks: {len(chunks)}")
    print(f"[*] عدد الـ Embeddings: {len(embeddings)}")

    client = connect_to_qdrant()
    vector_size = config["embedding"]["vector_size"]
    collection_name = config["vector_store"]["collection_name"]

    ensure_collection(client, collection_name, vector_size)

    points = build_points(chunks, embeddings_map)
    print(f"[*] بنرفع {len(points)} نقطة لـ Qdrant...")

    # الرفع على دفعات عشان نتجنب مشاكل حجم الطلب الواحد لو كبير أوي
    batch_size = 100
    for start in range(0, len(points), batch_size):
        batch = points[start:start + batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        print(f"    اترفع {min(start + batch_size, len(points))}/{len(points)}")

    collection_info = client.get_collection(collection_name)
    print(f"\n[✓] تم الرفع بنجاح")
    print(f"[✓] إجمالي النقط في الـ Collection دلوقتي: {collection_info.points_count}")


if __name__ == "__main__":
    main()
