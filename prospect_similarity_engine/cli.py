"""Local-only CLI. Example: pse2 fixtures --out demo."""
import argparse
import json
import os
from pathlib import Path
import tempfile
from .core import InputError, analyze, compare, validate
from .fixtures import generate
from .report import banner, render

META = {"_comment", "synthetic", "as_of", "records"}

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise InputError(f"ParseError: {path}: line {exc.lineno}: {exc.msg}") from None
    except (OSError, UnicodeError) as exc:
        raise InputError(f"ReadError: {path}: line 1: {exc}") from None

def load_input(directory):
    path = Path(directory)
    if not path.is_dir():
        raise InputError(f"MissingInput: {path}: use pse2 fixtures --out <dir> or provide an existing directory")
    records, dates, sources = [], set(), []
    for file in sorted(path.iterdir()):
        if file.name == "expectations.json" or file.is_dir():
            continue
        if file.suffix.lower() != ".json":
            raise InputError(f"SchemaError: {file}: line 1: unsupported format; use JSON input")
        data = read_json(file)
        if not isinstance(data, dict) or set(data) - META or not isinstance(data.get("records"), list) or type(data.get("synthetic")) is not bool or "as_of" not in data:
            raise InputError(f"SchemaError: {file}: line 1: expected synthetic, as_of, records and optional _comment fields")
        if any(not isinstance(r, dict) or r.get("synthetic") != data["synthetic"] for r in data["records"]):
            raise InputError(f"SchemaError: {file}: line 1: synthetic declaration disagrees with records")
        try:
            validate(data["records"], data["as_of"])
        except InputError as exc:
            raise InputError(f"{file}: line 1: {exc}") from None
        records.extend(data["records"])
        dates.add(data["as_of"])
        sources.append({"file": file.name, "synthetic": data["synthetic"], "records": len(data["records"])})
    if len(dates) > 1:
        raise InputError("SchemaError: as_of differs across input files")
    return records, next(iter(dates), "2026-09-30"), sources

def atomic_write(path, content):
    target = Path(path)
    temporary = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=target.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, target)
    except OSError as exc:
        raise InputError(f"WriteError: {target}: {exc}") from None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()

def main(argv=None):
    parser = argparse.ArgumentParser(description="Compute company feature similarity locally. No predictions or external calls.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("fixtures", help="Generate labelled synthetic data", epilog="Example: pse2 fixtures --out demo")
    p.add_argument("--out", required=True)
    for command, help_text in (("run", "Compute and save similarities"), ("rank", "Rank qualifying prospects by shared fields"), ("explain", "Compare two company records field by field")):
        p = sub.add_parser(command, help=help_text, description=help_text, epilog=f"Example: pse2 {command} --input demo" + (" --company c010 --reference c000" if command == "explain" else ""))
        p.add_argument("--input", required=True)
        if command != "explain":
            p.add_argument("--threshold", type=int, default=3)
        if command == "run":
            p.add_argument("--output", default=".pse2/results.json")
        if command == "explain":
            p.add_argument("--company", required=True)
            p.add_argument("--reference", required=True)
    p = sub.add_parser("report", help="Render saved results with provenance", epilog="Example: pse2 report --format md")
    p.add_argument("--format", choices=("md", "json"), default="md")
    p.add_argument("--results", default=".pse2/results.json")
    p.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 SYNTHETIC records and hand-computed expectations.")
        elif args.command == "report":
            result = read_json(Path(args.results))
            try:
                output = render(result, args.format)
            except (KeyError, TypeError, ValueError):
                raise InputError(f"SchemaError: {args.results}: invalid results schema; run pse2 run --input <dir>") from None
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        else:
            rows, as_of, sources = load_input(args.input)
            result = analyze(rows, as_of, getattr(args, "threshold", 3))
            result["inputs"] = sources
            if args.command == "run":
                atomic_write(args.output, render(result, "json"))
                print(banner(result))
                print(f"Computed {result['totals']['matches']} matching prospects. Results: {args.output}")
            elif args.command == "rank":
                result["matches"].sort(key=lambda r: (-r["score"], r["id"]))
                print(render(result, "json"), end="")
            else:
                indexed = {r["id"]: r for r in rows}
                if args.company not in indexed or args.reference not in indexed:
                    raise InputError("SchemaError: company or reference id not found")
                print(json.dumps({"provenance_banner": banner(result), "company": args.company, "reference": args.reference, **compare(indexed[args.company], indexed[args.reference]), "honesty": result["honesty"]}, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except (InputError, OSError) as exc:
        print(str(exc), file=__import__("sys").stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
