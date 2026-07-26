"""
01_documents.py
================
الخطوة الأولى في البايبلاين: تحميل التقارير الخام (10-K / 10-Q) من SEC EDGAR
لكل شركة موجودة في config.yaml، والاحتفاظ بـ Manifest فيه كل الـ Metadata
اللازمة للخطوات الجاية (مصدر كل مستند، تاريخه، نوعه...).

طريقة التشغيل:
    python 01_documents.py

المخرجات:
    - data/raw/<TICKER>/<FORM>_<DATE>_<ACCESSION>.html   (المستند الخام)
    - data/manifest/documents_manifest.json               (فهرس كل المستندات)
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
import yaml


# ---------------------------------------------------------------
# تحميل الإعدادات
# ---------------------------------------------------------------
def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------
# طبقة الاتصال بـ SEC EDGAR
# ---------------------------------------------------------------
class SecEdgarClient:
    """
    عميل بسيط للتعامل مع SEC EDGAR API.
    كل الطلبات بتلتزم بقواعد SEC: User-Agent حقيقي + Rate Limiting.
    """

    def __init__(self, config: dict):
        self.cfg = config["sec_edgar"]
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.cfg["user_agent"],
            "Accept-Encoding": "gzip, deflate",
        })
        self._min_interval = 1.0 / self.cfg["requests_per_second"]
        self._last_request_time = 0.0

    def _throttled_get(self, url: str) -> requests.Response:
        """طلب GET مع احترام حد SEC للـ Rate limit."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        response = self.session.get(url, timeout=30)
        self._last_request_time = time.time()
        response.raise_for_status()
        return response

    def get_company_submissions(self, cik: str) -> dict:
        """
        بيجيب قايمة كل التقارير المتاحة لشركة معينة عن طريق الـ CIK.
        المصدر: https://data.sec.gov/submissions/CIK##########.json
        """
        cik_padded = cik.zfill(10)
        url = f"{self.cfg['submissions_base_url']}/CIK{cik_padded}.json"
        response = self._throttled_get(url)
        return response.json()

    def get_company_facts(self, cik: str) -> dict:
        """
        بيجيب كل الأرقام المالية المنظمة (Revenue, NetIncome, Assets...) لشركة معينة
        في صيغة JSON نظيفة 100%، من غير أي مشاكل جداول مدموجة أو تكرار.
        المصدر: https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
        """
        cik_padded = cik.zfill(10)
        url = f"{self.cfg['companyfacts_base_url']}/CIK{cik_padded}.json"
        response = self._throttled_get(url)
        return response.json()

    def download_document(self, url: str, destination: Path) -> bool:
        """
        بيحمل مستند واحد (HTML) ويحفظه محليًا.
        بيتخطى التحميل لو الملف موجود بالفعل (Idempotent / Caching).
        """
        if destination.exists():
            return False  # اتحمل قبل كده، مفيش داعي نعيد الطلب

        response = self._throttled_get(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return True


# ---------------------------------------------------------------
# منطق فلترة التقارير المطلوبة
# ---------------------------------------------------------------
def filter_recent_filings(submissions: dict, report_types: list, lookback_years: int) -> list:
    """
    بياخد استجابة submissions الكاملة من SEC ويرجّع بس التقارير
    اللي نوعها ضمن report_types وتاريخها جوه النطاق الزمني المطلوب.
    """
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])

    cutoff_date = datetime.now() - timedelta(days=365 * lookback_years)

    filtered = []
    for form, date_str, accession, primary_doc in zip(
        forms, dates, accession_numbers, primary_documents
    ):
        if form not in report_types:
            continue
        filing_date = datetime.strptime(date_str, "%Y-%m-%d")
        if filing_date < cutoff_date:
            continue
        filtered.append({
            "form": form,
            "filing_date": date_str,
            "accession_number": accession,
            "primary_document": primary_doc,
        })

    return filtered


def build_document_url(archives_base_url: str, cik: str, accession_number: str, primary_document: str) -> str:
    """بيبني رابط التحميل المباشر للمستند من SEC Archives."""
    cik_no_leading_zeros = str(int(cik))
    accession_no_dashes = accession_number.replace("-", "")
    return f"{archives_base_url}/{cik_no_leading_zeros}/{accession_no_dashes}/{primary_document}"


# ---------------------------------------------------------------
# التشغيل الرئيسي
# ---------------------------------------------------------------
def main():
    config = load_config()
    client = SecEdgarClient(config)

    raw_data_dir = Path(config["sec_edgar"]["raw_data_dir"])
    facts_dir = Path(config["sec_edgar"]["facts_dir"])
    manifest_path = Path(config["sec_edgar"]["manifest_path"])
    report_types = config["report_types"]
    lookback_years = config["lookback_years"]

    manifest = []

    for company in config["companies"]:
        ticker = company["ticker"]
        cik = company["cik"]
        print(f"[*] بجيب قايمة التقارير لـ {company['name']} ({ticker})...")

        # ---- جلب الأرقام المالية النظيفة (Company Facts) ----
        facts_path = facts_dir / f"{ticker}_company_facts.json"
        if facts_path.exists():
            print(f"    الأرقام المالية (Company Facts): موجودة بالفعل (Cache)")
        else:
            print(f"    [*] بجيب الأرقام المالية النظيفة (Company Facts)...")
            company_facts = client.get_company_facts(cik)
            facts_path.parent.mkdir(parents=True, exist_ok=True)
            with open(facts_path, "w", encoding="utf-8") as f:
                json.dump(company_facts, f, ensure_ascii=False, indent=2)
            print(f"    الأرقام المالية: اتحملت دلوقتي -> {facts_path}")

        submissions = client.get_company_submissions(cik)
        filings = filter_recent_filings(submissions, report_types, lookback_years)
        print(f"    لقيت {len(filings)} تقرير مطابق (10-K/10-Q آخر {lookback_years} سنة)")

        for filing in filings:
            doc_url = build_document_url(
                config["sec_edgar"]["archives_base_url"],
                cik,
                filing["accession_number"],
                filing["primary_document"],
            )

            local_filename = f"{filing['form']}_{filing['filing_date']}_{filing['accession_number']}.html"
            local_path = raw_data_dir / ticker / local_filename

            downloaded_now = client.download_document(doc_url, local_path)
            status = "اتحمل دلوقتي" if downloaded_now else "موجود بالفعل (Cache)"
            print(f"    - {filing['form']} ({filing['filing_date']}): {status}")

            manifest.append({
                "company_name": company["name"],
                "ticker": ticker,
                "cik": cik,
                "form": filing["form"],
                "filing_date": filing["filing_date"],
                "accession_number": filing["accession_number"],
                "source_url": doc_url,
                "local_path": str(local_path),
                "company_facts_path": str(facts_path),
            })

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n[✓] تم حفظ فهرس المستندات في: {manifest_path}")
    print(f"[✓] إجمالي المستندات: {len(manifest)}")


if __name__ == "__main__":
    main()