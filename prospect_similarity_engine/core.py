"""Pure similarity computations. Scores measure shared fields, never probability."""
from datetime import date

FEATURES = ("industry", "business_model", "country", "employee_band")
FIELDS = {"id", "name", "responded", "synthetic", "response_date", *FEATURES}

class InputError(ValueError):
    """Named input failure suitable for CLI display."""

def validate(records, as_of):
    try:
        cutoff = date.fromisoformat(as_of)
    except (TypeError, ValueError):
        raise InputError("SchemaError: as_of must be an ISO date") from None
    seen = set()
    for n, row in enumerate(records, 1):
        prefix = f"SchemaError: record {n}"
        if not isinstance(row, dict):
            raise InputError(f"{prefix}: expected object")
        unknown = set(row) - FIELDS
        if unknown:
            raise InputError(f"{prefix}: unknown field {sorted(unknown)[0]}")
        for field in ("id", "name", *FEATURES):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > 4096 or any(ord(c) < 32 for c in value) or chr(0x2014) in value:
                raise InputError(f"{prefix}: invalid field {field} (nonempty text, max 4096, no controls or em dash)")
        for field in ("responded", "synthetic"):
            if type(row.get(field)) is not bool:
                raise InputError(f"{prefix}: {field} must be boolean")
        if row["id"] in seen:
            raise InputError(f"{prefix}: duplicate id {row['id']}")
        seen.add(row["id"])
        if row.get("response_date") is not None:
            try:
                response = date.fromisoformat(row["response_date"])
            except (ValueError, TypeError):
                raise InputError(f"{prefix}: invalid response_date") from None
            if response > cutoff or not row["responded"]:
                raise InputError(f"{prefix}: response_date is future or company has not responded")
    return records

def compare(a, b):
    fields = [field for field in FEATURES if a[field].strip().casefold() == b[field].strip().casefold()]
    return {"score": len(fields), "matched_fields": fields}

def analyze(records, as_of="2026-09-30", threshold=3):
    if type(threshold) is not int or not 1 <= threshold <= 4:
        raise InputError("SchemaError: threshold must be integer from 1 to 4")
    validate(records, as_of)
    responders = sorted((r for r in records if r["responded"]), key=lambda r: r["id"])
    matches = []
    for row in sorted(records, key=lambda r: r["id"]):
        if row["responded"] or not responders:
            continue
        ranked = [(compare(row, r), r) for r in responders]
        best, reference = min(ranked, key=lambda x: (-x[0]["score"], x[1]["id"]))
        if best["score"] >= threshold:
            matches.append({"id": row["id"], "name": row["name"], "reference_id": reference["id"], **best})
    synthetic = sum(r["synthetic"] for r in records)
    return {"as_of": as_of, "threshold": threshold, "totals": {"records": len(records), "responders": len(responders), "prospects": len(records)-len(responders), "matches": len(matches)}, "provenance": {"synthetic_records": synthetic, "user_supplied_real_records": len(records)-synthetic, "real_data_claim": "Real status is declared by the input author, not independently verified."}, "matches": matches, "honesty": "Scores count matching fields out of 4. Response probability, time saved and money saved are unmeasured and are not reported."}
