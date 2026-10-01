import copy
import pytest
from prospect_similarity_engine.core import InputError, analyze
from prospect_similarity_engine.fixtures import payload

def test_rejects_adversarial_values():
    original = payload()["records"]
    for field, value in (("amount", -1), ("name", "x" * 4097), ("responded", 1), ("response_date", "2099-01-01"), ("industry", "")):
        rows = copy.deepcopy(original)
        rows[0][field] = value
        with pytest.raises(InputError):
            analyze(rows)
    with pytest.raises(InputError, match="duplicate id"):
        analyze(original + [original[0]])

def test_handles_unicode_and_long_inputs():
    rows = payload()["records"]
    rows[10]["name"] = "会社 café " + "a" * 3000 + r" C:\客户\company"
    assert analyze(rows)["matches"][0]["name"] == rows[10]["name"]

def test_corrupted_fixture_changes_computed_figures():
    rows = payload()["records"]
    rows[10]["industry"] = "different"
    rows[10]["country"] = "different"
    assert analyze(rows)["totals"]["matches"] == 39

def test_case_normalization_and_tie_breaking():
    rows = payload()["records"][:11]
    rows[10]["industry"] = " SOFTWARE "
    result = analyze(list(reversed(rows)))
    assert result["matches"][0]["score"] == 4
    assert result["matches"][0]["reference_id"] == "c000"

def test_no_responders_and_threshold():
    rows = payload()["records"][10:20]
    assert analyze(rows)["totals"]["matches"] == 0
    for threshold in (0, 5, True):
        with pytest.raises(InputError):
            analyze(rows, threshold=threshold)
