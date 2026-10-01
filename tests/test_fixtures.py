import json
from collections import Counter
from prospect_similarity_engine.fixtures import generate, payload, expectations
from prospect_similarity_engine.core import analyze

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.iterdir():
        value = json.loads(path.read_text(encoding="utf-8"))
        assert value["synthetic"] is True
        assert "SYNTHETIC" in value["_comment"]
    assert all(row["synthetic"] for row in payload()["records"])

def test_fixture_ground_truth_matches_hand_computed():
    result = analyze(payload()["records"])
    expected = expectations()
    assert result["totals"] == expected["totals"]
    assert [r["id"] for r in result["matches"]] == expected["match_ids"]
    assert Counter(str(r["score"]) for r in result["matches"]) == expected["score_counts"]
