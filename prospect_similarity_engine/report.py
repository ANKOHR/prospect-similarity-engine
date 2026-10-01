"""Deterministic reports with explicit provenance and unmeasured boundaries."""
import json

def banner(result):
    p = result["provenance"]
    return f"DATA PROVENANCE: {p['synthetic_records']} synthetic fixture records; {p['user_supplied_real_records']} user-supplied records declared real. Real status is not independently verified."

def render(result, format="md"):
    if format == "json":
        return json.dumps({"provenance_banner": banner(result), **result}, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    def safe(value):
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("|", "&#124;").replace("`", "&#96;")
    lines = ["# Prospect Similarity Engine", "", banner(result), "", result["honesty"], "", f"As of: {result['as_of']}. Threshold: {result['threshold']} of 4 fields.", ""]
    lines.extend(f"- {key}: {value}" for key, value in result["totals"].items())
    lines += ["", "| Prospect ID | Company | Reference responder | Matching fields | Score / 4 |", "| --- | --- | --- | --- | --- |"]
    for row in result["matches"]:
        lines.append(f"| {safe(row['id'])} | {safe(row['name'])} | {safe(row['reference_id'])} | {', '.join(row['matched_fields'])} | {row['score']} |")
    return "\n".join(lines) + "\n"
