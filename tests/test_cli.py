import json
import time
from pathlib import Path
from prospect_similarity_engine.cli import main, load_input
from prospect_similarity_engine.fixtures import generate
from prospect_similarity_engine.core import InputError
import pytest

def test_run_completes_on_fixture(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    start = time.perf_counter()
    assert main(["fixtures", "--out", "demo"]) == 0
    assert main(["run", "--input", "demo"]) == 0
    assert main(["report", "--format", "md"]) == 0
    assert time.perf_counter() - start < 5
    assert "matches: 40" in capsys.readouterr().out

def test_empty_input_renders_without_traceback(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    Path("empty").mkdir()
    assert main(["run", "--input", "empty"]) == 0
    assert main(["report"]) == 0
    assert "records: 0" in capsys.readouterr().out

def test_malformed_input_named_error(tmp_path, capsys):
    (tmp_path / "bad.json").write_text('{\n"records": broken}', encoding="utf-8")
    assert main(["run", "--input", str(tmp_path)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "bad.json" in error and "line 2" in error
    for suffix in ("csv", "yaml"):
        (tmp_path / "bad.json").unlink(missing_ok=True)
        path = tmp_path / ("bad." + suffix)
        path.write_text("broken", encoding="utf-8")
        assert main(["run", "--input", str(tmp_path)]) == 2
        error = capsys.readouterr().err
        assert path.name in error and "line 1" in error
        path.unlink()

def test_determinism_byte_identical(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generate("demo")
    main(["run", "--input", "demo"])
    first = Path(".pse2/results.json").read_bytes()
    main(["run", "--input", "demo"])
    assert first == Path(".pse2/results.json").read_bytes()
    main(["report", "--out", "one.md"])
    main(["report", "--out", "two.md"])
    assert Path("one.md").read_bytes() == Path("two.md").read_bytes()

def test_cli_smoke_all_subcommands(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    for command in ("fixtures", "run", "report", "rank", "explain"):
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0
    main(["fixtures", "--out", "demo"])
    main(["run", "--input", "demo"])
    for fmt in ("md", "json"):
        assert main(["report", "--format", fmt]) == 0
    assert main(["rank", "--input", "demo"]) == 0
    assert main(["explain", "--input", "demo", "--company", "c010", "--reference", "c000"]) == 0
    assert chr(0x2014) not in capsys.readouterr().out

def test_missing_input_and_write_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["run", "--input", "absent"]) == 2
    assert "MissingInput" in capsys.readouterr().err
    generate("demo")
    assert main(["run", "--input", "demo"]) == 0
    Path("blocked").write_text("keep", encoding="utf-8")
    assert main(["report", "--out", "blocked/report.md"]) == 2
    assert "WriteError" in capsys.readouterr().err
    assert Path("blocked").read_text() == "keep"
    assert not list(Path(".").glob("tmp*"))

def test_schema_drift_and_mixed_provenance(tmp_path):
    generate(tmp_path)
    data = json.loads((tmp_path / "companies.json").read_text())
    data["records"][0]["unexpected"] = 2
    (tmp_path / "companies.json").write_text(json.dumps(data))
    with pytest.raises(InputError, match="unexpected"):
        load_input(tmp_path)

def test_smallest_five_record_input(tmp_path):
    from prospect_similarity_engine.core import analyze
    data = json.loads(Path(__file__).parents[1].joinpath("examples/five/companies.json").read_text(encoding="utf-8"))
    result = analyze(data["records"], data["as_of"])
    assert result["totals"] == {"records": 5, "responders": 1, "prospects": 4, "matches": 2}


def test_cli_corruption_is_computed_not_expected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generate("demo")
    company_path = Path("demo/companies.json")
    data = json.loads(company_path.read_text())
    data["records"][10]["industry"] = "other"
    data["records"][10]["country"] = "other"
    company_path.write_text(json.dumps(data))
    Path("demo/expectations.json").write_text("deliberately invalid expectations")
    assert main(["run", "--input", "demo"]) == 0
    assert json.loads(Path(".pse2/results.json").read_text())["totals"]["matches"] == 39


def test_real_and_synthetic_provenance(tmp_path):
    from prospect_similarity_engine.core import analyze
    from prospect_similarity_engine.report import render
    generate(tmp_path)
    data = json.loads((tmp_path / "companies.json").read_text())
    real = data["records"].pop()
    real["synthetic"] = False
    (tmp_path / "companies.json").write_text(json.dumps(data))
    (tmp_path / "real.json").write_text(json.dumps({"synthetic": False, "as_of": data["as_of"], "records": [real]}))
    rows, cutoff, sources = load_input(tmp_path)
    result = analyze(rows, cutoff)
    result["inputs"] = sources
    assert result["provenance"]["synthetic_records"] == 199
    assert result["provenance"]["user_supplied_real_records"] == 1
    assert "1 user-supplied records declared real" in render(result)
