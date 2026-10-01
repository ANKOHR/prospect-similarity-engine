"""Synthetic, planted examples; no random generator or estimated figures."""
import json
from pathlib import Path

def payload():
    records = []
    for n in range(200):
        row = {"id": f"c{n:03d}", "name": f"Synthetic company {n:03d}", "synthetic": True, "responded": n < 10, "industry": "software" if n < 50 else "manufacturing", "business_model": "subscription" if n < 50 else "wholesale", "country": "GB" if n < 30 else "DE", "employee_band": "11-50" if n < 50 else "201-500"}
        records.append(row)
    return {"_comment": "SYNTHETIC fixture data, not real companies", "synthetic": True, "as_of": "2026-09-30", "records": records}

def expectations():
    return {"_comment": "SYNTHETIC hand-computed ground truth: 10 responders, 20 four-field matches, 20 three-field matches, 150 two-or-fewer-field nonmatches", "synthetic": True, "totals": {"records": 200, "responders": 10, "prospects": 190, "matches": 40}, "match_ids": [f"c{n:03d}" for n in range(10, 50)], "score_counts": {"4": 20, "3": 20}}

def generate(out):
    target = Path(out)
    target.mkdir(parents=True, exist_ok=True)
    for name, value in (("companies.json", payload()), ("expectations.json", expectations())):
        (target / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
