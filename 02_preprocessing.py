"""
02_preprocessing.py
====================
الخطوة الثانية في البايبلاين. بتعمل حاجتين بالتوازي:

    أ) تنظيف النصوص السردية: تحويل كل مستند HTML خام لـ Markdown نضيف
       عن طريق Docling، مع حذف الضوضاء (صور، جداول فاضية) وتجاهل
       الجداول المالية المكسورة تمامًا (لأن أرقامها هتيجي من مصدر تاني).

    ب) فلترة الأرقام المالية: من ملف Company Facts الضخم (500+ Tag)،
       بنسحب بس المؤشرات المهمة (config.yaml -> key_financial_tags)
       ونحولها لسجلات نضيفة وبسيطة.

طريقة التشغيل:
    python 02_preprocessing.py

المدخلات:
    - data/manifest/documents_manifest.json  (من 01_documents.py)
    - data/raw/<TICKER>/*.html
    - data/facts/<TICKER>_company_facts.json

المخرجات:
    - data/processed/narrative/<TICKER>/<FORM>_<DATE>_<ACCESSION>.md
    - data/processed/facts/<TICKER>_key_facts.json
"""

import json
import re
from pathlib import Path

import yaml
from docling.document_converter import DocumentConverter


# ---------------------------------------------------------------
# تحميل الإعدادات والـ Manifest
# ---------------------------------------------------------------
def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_manifest(manifest_path: str) -> list:
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------
# أ) تنظيف النصوص السردية
# ---------------------------------------------------------------
# أنماط الضوضاء اللي بنشيلها من أي مستند: أسماء صور، تعليقات HTML، جداول فاضية
IMAGE_LINE_PATTERN = re.compile(r"^\s*[\w\-]+\.(jpg|jpeg|png|gif)\s*$", re.IGNORECASE)
HTML_COMMENT_PATTERN = re.compile(r"^\s*<!--.*-->\s*$")
EMPTY_TABLE_ROW_PATTERN = re.compile(r"^[\|\s\-:]+$")  # سطر جدول فاضي زي "| | | |" أو "|----|----|"


def remove_noise_lines(markdown_text: str) -> str:
    """بتشيل سطور الصور والتعليقات وصفوف الجداول الفاضية تمامًا."""
    cleaned_lines = []
    for line in markdown_text.split("\n"):
        if IMAGE_LINE_PATTERN.match(line):
            continue
        if HTML_COMMENT_PATTERN.match(line):
            continue
        if EMPTY_TABLE_ROW_PATTERN.match(line) and line.strip():
            # بيشيل أي سطر جدول مفيهوش غير Pipes/شرطات/فراغات (فاصل أو صف فاضي تمامًا)
            continue
        cleaned_lines.append(line)

    # نقلل الأسطر الفاضية المتكررة لسطر واحد بس
    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_financial_statement_blocks(markdown_text: str, markers: list) -> str:
    """
    بتشيل أي جدول مالي معروف (قائمة الدخل، الميزانية...) بالكامل من النص السردي،
    لأن أرقامه هتيجي من Company Facts API بدل ما تتستخرج من جدول مكسور.

    المنطق: لو لقينا سطر فيه واحد من الـ markers، بنشيل من السطر ده لحد أول
    عنوان تاني يبان إنه بداية قسم جديد (سطر قصير كله حروف كبيرة، أو Bullet جديد).
    """
    lines = markdown_text.split("\n")
    output_lines = []
    skipping = False
    lines_skipped_in_block = 0

    for line in lines:
        upper_line = line.upper()

        if not skipping and any(marker in upper_line for marker in markers):
            skipping = True
            lines_skipped_in_block = 0
            continue

        if skipping:
            lines_skipped_in_block += 1
            # نوقف التجاهل لما نلاقي عنوان قسم جديد واضح (بولت جديد يبدأ بنقطة، أو نص طويل عادي)
            is_new_section_heading = line.strip().startswith("•") or line.strip().startswith("* ")
            is_long_paragraph = len(line.strip()) > 200  # فقرة نصية طويلة معناها رجعنا لنص سردي عادي
            safety_limit_reached = lines_skipped_in_block > 400  # حد أمان عشان مانمسحش المستند كله بالغلط

            if is_new_section_heading or is_long_paragraph or safety_limit_reached:
                skipping = False
                if is_new_section_heading:
                    output_lines.append(line)
            continue

        output_lines.append(line)

    return "\n".join(output_lines)


def clean_document(html_path: str, markers: list) -> str:
    """بتحول مستند HTML خام لنص Markdown نضيف وجاهز للتقسيم."""
    converter = DocumentConverter()
    result = converter.convert(html_path)
    raw_markdown = result.document.export_to_markdown()

    text = remove_noise_lines(raw_markdown)
    text = remove_financial_statement_blocks(text, markers)
    return text


# ---------------------------------------------------------------
# ب) فلترة الأرقام المالية النظيفة
# ---------------------------------------------------------------
def extract_key_facts(company_facts: dict, ticker: str, key_tags: list,
                       report_types: list, lookback_years: int) -> list:
    """
    بتسحب من ملف Company Facts الضخم بس المؤشرات المهمة (key_tags)،
    وتفلترها حسب نوع التقرير والنطاق الزمني، وترجعها كسجلات نضيفة.
    """
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=365 * lookback_years)
    us_gaap_facts = company_facts.get("facts", {}).get("us-gaap", {})

    records = []
    seen = set()  # عشان منكررش نفس (tag, end_date, form) مرتين

    for tag in key_tags:
        if tag not in us_gaap_facts:
            continue  # الشركة دي ممكن ماتستخدمش الـ Tag ده، طبيعي

        tag_data = us_gaap_facts[tag]
        label = tag_data.get("label", tag)
        units = tag_data.get("units", {})

        for unit_name, entries in units.items():
            for entry in entries:
                form = entry.get("form")
                filed_str = entry.get("filed")
                if form not in report_types or not filed_str:
                    continue

                filed_date = datetime.strptime(filed_str, "%Y-%m-%d")
                if filed_date < cutoff_date:
                    continue

                dedup_key = (tag, entry.get("end"), form, entry.get("val"))
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)

                records.append({
                    "ticker": ticker,
                    "tag": tag,
                    "label": label,
                    "value": entry.get("val"),
                    "unit": unit_name,
                    "fiscal_year": entry.get("fy"),
                    "fiscal_period": entry.get("fp"),
                    "form": form,
                    "period_start": entry.get("start"),
                    "period_end": entry.get("end"),
                    "filed_date": filed_str,
                    "accession_number": entry.get("accn"),
                })

    return records


# ---------------------------------------------------------------
# التشغيل الرئيسي
# ---------------------------------------------------------------
def main():
    config = load_config()
    manifest = load_manifest(config["sec_edgar"]["manifest_path"])

    narrative_dir = Path(config["processing"]["narrative_dir"])
    facts_output_dir = Path(config["processing"]["facts_output_dir"])
    markers = config["processing"]["financial_statement_markers"]
    key_tags = config["processing"]["key_financial_tags"]
    report_types = config["report_types"]
    lookback_years = config["lookback_years"]

    # ---- أ) تنظيف النصوص السردية لكل مستند في الـ Manifest ----
    print("=== تنظيف النصوص السردية ===")
    for entry in manifest:
        ticker = entry["ticker"]
        source_name = Path(entry["local_path"]).stem
        output_path = narrative_dir / ticker / f"{source_name}.md"

        if output_path.exists():
            print(f"[-] {ticker}/{source_name}: منضف بالفعل (Cache)")
            continue

        print(f"[*] بننضف {ticker}/{source_name}...")
        cleaned_text = clean_document(entry["local_path"], markers)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(cleaned_text, encoding="utf-8")
        print(f"    تم -> {output_path} ({len(cleaned_text)} حرف)")

    # ---- ب) فلترة الأرقام المالية لكل شركة ----
    print("\n=== فلترة الأرقام المالية ===")
    tickers_seen = {entry["ticker"] for entry in manifest}

    for ticker in tickers_seen:
        facts_path = next(
            entry["company_facts_path"] for entry in manifest if entry["ticker"] == ticker
        )
        with open(facts_path, "r", encoding="utf-8") as f:
            company_facts = json.load(f)

        key_facts = extract_key_facts(company_facts, ticker, key_tags, report_types, lookback_years)

        output_path = facts_output_dir / f"{ticker}_key_facts.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(key_facts, f, ensure_ascii=False, indent=2)

        print(f"[✓] {ticker}: {len(key_facts)} رقم مالي نضيف -> {output_path}")

    print("\n[✓] انتهت مرحلة التنظيف بنجاح")


if __name__ == "__main__":
    main()
