"""
03_chunking.py
================
الخطوة الثالثة: تحويل النصوص السردية النظيفة + الأرقام المالية النظيفة
لـ Chunks موحدة جاهزة للـ Embedding، وكل Chunk معاه Metadata كاملة تسمح
بعرض مصدر دقيق وقابل للتحقق في إجابة الشات بوت.

استراتيجية المصدر (Citation Strategy):
    مستندات SEC هي HTML/iXBRL مش PDF، فمفهوم "رقم الصفحة" غير موثوق فيها.
    بدل ما نعرض رقم صفحة تقريبي ممكن يكون غلط، كل Chunk بياخد:
      1) section        -> اسم القسم (زي "Item 2. Management's Discussion...")
      2) source_url      -> رابط مباشر للمستند الأصلي على SEC
      3) period_label     -> (للأرقام المالية بس) الفترة الزمنية بوضوح
                            (3 أشهر / 6 أشهر / سنة كاملة) عشان الموديل
                            مايخلطش بين فترات مختلفة لنفس المؤشر
    حقل page_number اتسيب موجود (بقيمة None حاليًا) عشان لو لقينا مصدر
    أدق لاحقًا (زي PDF رسمي)، نقدر نملاه من غير ما نغيّر بنية البيانات.

المدخلات:
    - data/processed/narrative/<TICKER>/*.md
    - data/processed/facts/<TICKER>_key_facts.json
    - data/manifest/documents_manifest.json

المخرجات:
    - data/processed/chunks/all_chunks.json
"""

import json
import re
import uuid
from datetime import datetime
from pathlib import Path

import tiktoken
import yaml


# عناوين أقسام SEC القياسية (Item 1, Item 2, PART I...) بنستخدمها لتقسيم النص لأقسام
SECTION_HEADER_PATTERN = re.compile(
    r"^(?:•\s*)?(Item\s+\d+[A-Za-z]?\.|PART\s+[IVX]+\b)", re.IGNORECASE
)


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_manifest(manifest_path: str) -> list:
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_chunk_id(*parts) -> str:
    """بيبني معرّف فريد وثابت لكل Chunk (نفس المدخلات = نفس الـ ID دايمًا)."""
    raw = "_".join(str(p) for p in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, raw))


# ---------------------------------------------------------------
# أ) تقسيم النصوص السردية لأقسام ثم Chunks
# ---------------------------------------------------------------
def split_into_sections(markdown_text: str) -> list:
    """بتقسم النص لأقسام حسب عناوين SEC القياسية. كل قسم: (العنوان, النص)."""
    lines = markdown_text.split("\n")
    sections = []
    current_title = "مقدمة المستند / صفحة الغلاف"
    current_lines = []

    for line in lines:
        match = SECTION_HEADER_PATTERN.match(line.strip())
        if match:
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line.strip().lstrip("•").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    # نتجاهل الأقسام الفاضية أو القصيرة جدًا (مالهاش قيمة فعلية للاسترجاع)
    return [(title, text) for title, text in sections if len(text.strip()) > 50]


def chunk_text_by_tokens(text: str, encoding, chunk_size: int, overlap: int) -> list:
    """بتقسم نص طويل لـ Chunks بحجم Tokens ثابت مع Overlap بين كل Chunk واللي بعده."""
    tokens = encoding.encode(text)
    if len(tokens) <= chunk_size:
        return [text]

    pieces = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        pieces.append(encoding.decode(tokens[start:end]))
        if end == len(tokens):
            break
        start = end - overlap

    return pieces


def build_narrative_chunks(manifest_entry: dict, config: dict, encoding) -> list:
    """بتبني كل الـ Chunks (بمعتاداتها الكاملة) لمستند سردي واحد."""
    ticker = manifest_entry["ticker"]
    form = manifest_entry["form"]
    filing_date = manifest_entry["filing_date"]
    accession = manifest_entry["accession_number"]
    source_url = manifest_entry["source_url"]
    company_name = manifest_entry["company_name"]

    source_name = Path(manifest_entry["local_path"]).stem
    narrative_path = Path(config["processing"]["narrative_dir"]) / ticker / f"{source_name}.md"
    if not narrative_path.exists():
        return []

    text = narrative_path.read_text(encoding="utf-8")
    sections = split_into_sections(text)
    chunk_cfg = config["chunking"]

    chunks = []
    chunk_index = 0
    for section_title, section_text in sections:
        pieces = chunk_text_by_tokens(
            section_text, encoding, chunk_cfg["chunk_size_tokens"], chunk_cfg["chunk_overlap_tokens"]
        )
        for piece in pieces:
            if len(piece.strip()) < 30:
                continue
            chunks.append({
                "chunk_id": make_chunk_id(ticker, form, filing_date, accession, chunk_index),
                "chunk_type": "narrative",
                "text": piece.strip(),
                "company_name": company_name,
                "ticker": ticker,
                "form": form,
                "filing_date": filing_date,
                "accession_number": accession,
                "section": section_title,
                "source_url": source_url,
                "page_number": None,  # غير موثوق في HTML/iXBRL؛ الاعتماد على section + source_url بدلاً منه
            })
            chunk_index += 1

    return chunks


# ---------------------------------------------------------------
# ب) تحويل الأرقام المالية لجمل نصية مع تصنيف الفترة الزمنية بدقة
# ---------------------------------------------------------------
def classify_period(start_str: str, end_str: str) -> str:
    """بتصنف الفترة الزمنية حسب عدد الأيام، عشان مايتلخبطش ربع سنة مع سنة كاملة."""
    if not start_str or not end_str:
        return "instant"  # أرقام لحظية (الأصول، الالتزامات) مالهاش فترة، بس تاريخ واحد

    start = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")
    days = (end - start).days

    if days <= 100:
        return "three-month (quarterly)"
    elif days <= 200:
        return "six-month (half-year)"
    elif days <= 290:
        return "nine-month"
    else:
        return "full fiscal year"


def fact_to_sentence(record: dict, company_name: str) -> tuple:
    """بتحول رقم مالي واحد لجملة نصية واضحة، تحدد الفترة الزمنية بدقة تمنع الهلوسة."""
    period_label = classify_period(record.get("period_start"), record.get("period_end"))
    value = record["value"]
    label = record["label"]
    unit = record.get("unit", "")

    if unit == "USD":
        value_str = f"${value:,}"
    else:
        value_str = f"{value:,} {unit}".strip()

    if period_label == "instant":
        sentence = (
            f"{company_name} ({record['ticker']}) reported {label} of {value_str} "
            f"as of {record['period_end']}, according to its {record['form']} filed on {record['filed_date']}."
        )
    else:
        sentence = (
            f"{company_name} ({record['ticker']}) reported {label} of {value_str} "
            f"for the {period_label} period ending {record['period_end']} "
            f"(from {record['period_start']} to {record['period_end']}), "
            f"according to its {record['form']} filed on {record['filed_date']}."
        )

    return sentence, period_label


def build_fact_chunks(ticker: str, company_name: str, facts_records: list, source_url_map: dict) -> list:
    """بتبني Chunk واحد لكل رقم مالي، بجملة نصية واضحة + Metadata كاملة."""
    chunks = []
    for i, record in enumerate(facts_records):
        sentence, period_label = fact_to_sentence(record, company_name)
        accession = record.get("accession_number")
        source_url = source_url_map.get(accession, "")

        chunks.append({
            "chunk_id": make_chunk_id(ticker, "FACT", record["tag"], record.get("period_end"), accession),
            "chunk_type": "financial_fact",
            "text": sentence,
            "company_name": company_name,
            "ticker": ticker,
            "form": record["form"],
            "filing_date": record["filed_date"],
            "accession_number": accession,
            "section": "Financial Facts (XBRL)",
            "source_url": source_url,
            "page_number": None,
            "tag": record["tag"],
            "label": record["label"],
            "period_label": period_label,
            "period_start": record.get("period_start"),
            "period_end": record.get("period_end"),
            "fiscal_year": record.get("fiscal_year"),
            "fiscal_period": record.get("fiscal_period"),
            "value": record["value"],
            "unit": record.get("unit"),
        })
    return chunks


# ---------------------------------------------------------------
# التشغيل الرئيسي
# ---------------------------------------------------------------
def main():
    config = load_config()
    manifest = load_manifest(config["sec_edgar"]["manifest_path"])
    encoding = tiktoken.get_encoding("cl100k_base")

    all_chunks = []

    print("=== تقسيم النصوص السردية ===")
    for entry in manifest:
        chunks = build_narrative_chunks(entry, config, encoding)
        all_chunks.extend(chunks)
        print(f"[*] {entry['ticker']}/{Path(entry['local_path']).stem}: {len(chunks)} chunk")

    print("\n=== تحويل الأرقام المالية لجمل نصية ===")
    company_name_map = {e["ticker"]: e["company_name"] for e in manifest}
    source_url_map = {e["accession_number"]: e["source_url"] for e in manifest}

    for ticker in {e["ticker"] for e in manifest}:
        facts_path = Path(config["processing"]["facts_output_dir"]) / f"{ticker}_key_facts.json"
        with open(facts_path, "r", encoding="utf-8") as f:
            facts_records = json.load(f)

        fact_chunks = build_fact_chunks(ticker, company_name_map[ticker], facts_records, source_url_map)
        all_chunks.extend(fact_chunks)
        print(f"[*] {ticker}: {len(fact_chunks)} chunk رقم مالي")

    output_path = Path(config["chunking"]["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    narrative_count = sum(1 for c in all_chunks if c["chunk_type"] == "narrative")
    fact_count = sum(1 for c in all_chunks if c["chunk_type"] == "financial_fact")

    print(f"\n[✓] إجمالي الـ Chunks: {len(all_chunks)} ({narrative_count} نصي + {fact_count} رقم مالي)")
    print(f"[✓] اتحفظوا في: {output_path}")


if __name__ == "__main__":
    main()
