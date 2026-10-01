import json
from prospect_similarity_engine.core import analyze
from prospect_similarity_engine.fixtures import payload, expectations
from prospect_similarity_engine.report import render

def test_report_matches_ground_truth_exact():
    result = json.loads(render(analyze(payload()["records"]), "json"))
    assert result["totals"] == expectations()["totals"]

def test_report_zero_false_positives():
    result = analyze(payload()["records"])
    actual = {r["id"] for r in result["matches"]}
    assert actual == set(expectations()["match_ids"])

def test_report_carries_provenance_banner():
    for fmt in ("md", "json"):
        output = render(analyze(payload()["records"]), fmt)
        assert "DATA PROVENANCE" in output
        assert "200 synthetic" in output
        assert "0 user-supplied" in output

def test_hypothetical_figures_labelled():
    for fmt in ("md", "json"):
        output = render(analyze([]), fmt)
        assert "time saved and money saved are unmeasured" in output
        assert "Response probability" in output

def test_no_em_dashes_in_outputs():
    for fmt in ("md", "json"):
        assert chr(0x2014) not in render(analyze(payload()["records"]), fmt)
