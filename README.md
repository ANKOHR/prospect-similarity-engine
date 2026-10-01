# Prospect Similarity Engine

`pse2` finds companies in supplied local data that share explicit features with companies recorded as having responded. It computes similarities; it does not discover companies or predict responses. Python 3.10 or newer, CPU only, standard-library runtime, no network, models, GPU packages or server.

## Hypothesis and acceptance

A deterministic feature comparison can produce auditable targeting candidates. On the labelled 200-record synthetic fixture, all 40 planted candidates must be found with zero false positives; every count must reconcile; fixture generation, run and report must complete within 5 seconds. This validates implementation against planted rules, not targeting effectiveness in real outreach.

## Quickstart

```powershell
python -m pip install --disable-pip-version-check --no-index --no-deps --no-build-isolation -e .
pse2 fixtures --out demo
pse2 run --input demo
pse2 report --format md
python -m pytest -q
```

Installation uses local build tools already installed; runtime never calls the network. If Windows reports that the user Scripts directory is not on PATH, add the directory shown by pip to PATH to use `pse2`. Offline users can also use `python -m prospect_similarity_engine.cli` in place of `pse2`.

For the tiny hand-written five-record example:

```powershell
pse2 run --input examples/five
pse2 report --format json
```

It contains one responder, two qualifying prospects and two nonmatches. All example companies are synthetic.

## Input reference

An input directory contains UTF-8 JSON envelopes. Files are processed in filename order. Only JSON is supported: CSV, YAML and other files cause a named schema error. `expectations.json` is reserved for independent fixture ground truth and is never read by the engine. Do not use this filename for company data. Put reports outside the input directory.

```json
{
  "_comment": "SYNTHETIC example only",
  "synthetic": true,
  "as_of": "2026-09-30",
  "records": [{
    "id": "example-1",
    "name": "Synthetic Example",
    "industry": "software",
    "business_model": "subscription",
    "country": "GB",
    "employee_band": "11-50",
    "responded": true,
    "synthetic": true,
    "response_date": "2026-09-20"
  }]
}
```

Henry can enter his own data by hand using the same schema and `synthetic: false` in envelope and records. Real status is his declaration, not verified by this tool. Keep real trial inputs and results private and outside this repository. Mixed provenance is supported through separate files. All files must share an explicit `as_of` ISO date. An empty directory uses the documented fixed date 2026-09-30 and reports zeros.

Required record fields are id, name, industry, business_model, country, employee_band, responded and synthetic. Optional response_date must be an ISO date no later than as_of and requires responded=true. Responded means a response actually recorded by the user; the tool does not classify sentiment or qualification. Unknown fields, including monetary amounts, are rejected. Negative amounts cannot enter a computation. Empty or whitespace-only fields, control characters, em dash characters, strings over 4096 characters, non-boolean flags and duplicate ids are rejected. Unicode and Windows paths within string fields are accepted. Ids are case-sensitive and unique across all files. Matching trims whitespace and uses Unicode casefold. Names are display labels, never matching features. Keep employee bands and categories consistent; the tool does not infer category equivalence.

## Matching rule and traceability

Each prospect is compared with each responder on industry, business_model, country and employee_band, one point each. Default threshold is 3 of 4. Choose an integer threshold from 1 to 4 explicitly if needed. Responders are excluded from candidates. The highest-scoring responder is retained, with ties broken by lexicographically smallest id. Run reports are sorted by prospect id; rank sorts by descending score then id. No responders means zero candidates. Each candidate includes reference id and the exact matching fields. All counts reconcile: prospects = records - responders; matches <= prospects. Time complexity is O(prospects * responders), suitable for small local lists, without a large-scale performance claim.

Fixture arithmetic is independent of the engine: c000-c009 are 10 responders with identical four fields; c010-c029 are 20 four-field matches; c030-c049 are 20 three-field matches; c050-c199 are 150 nonmatches. Total 200, prospects 190, matches 40. Generation uses explicit ranges and no randomness, so no seed is needed. Editing a company's fields changes computed scores and counts. Editing expectations alone has no effect, intentionally.

## Subcommands

- `pse2 fixtures --out demo`: writes labelled synthetic companies and hand-computed expectations.
- `pse2 run --input demo --threshold 3 --output .pse2/results.json`: computes and atomically saves results.
- `pse2 report --format md --out report.md`: renders saved results. `--format json` provides machine-readable output; `--results <file>` chooses a saved result. Saved results are snapshots; rerun after editing inputs.
- `pse2 rank --input demo --threshold 3`: computes ranked qualifying prospects with provenance.
- `pse2 explain --input demo --company c030 --reference c000`: explains any supplied pair, even below threshold. It does not require the reference to be a responder; it is an explicit pair comparison.

Each subcommand supports `--help` and an example. Errors exit 2 and successful commands exit 0. Parse errors identify file and JSON line. Schema errors identify file, offending field and record index, with line 1 denoting the envelope rather than claiming an exact field line. Missing directories include a usage hint. Read failures are named. Report writes use a sibling temporary file and atomic replacement; write failure leaves no partial report and preserves any previous destination.

## Architecture

```text
labelled JSON files -> CLI parsing and validation -> pure core comparison
                                                     |
                                                     v
                                            deterministic results
                                                     |
                                                     v
                                      JSON or Markdown with provenance
fixtures -> companies + independent expectations -> pytest acceptance
```

## Honesty boundary and labelling

All outputs are computed from supplied fields. Shared-feature scores are not response probability, fit certification or discovered demand. Response probability, time saved and money saved are unmeasured and are not reported. No hypothetical performance or savings numbers are displayed. Synthetic JSON files include a `_comment` header field and `synthetic: true`; every synthetic record has its own flag. JSON cannot carry native comments, so `_comment` is the in-format header. Reports always state synthetic and declared-real counts and retain per-file provenance. Fixture results establish planted-rule correctness only. Runtime measurements are local measurements, recorded in EVIDENCE.md, without guarantees for other machines.

## Failure modes and limits

Malformed input, schema drift, missing paths and output write failures are named. Duplicate ids are never silently merged. Extreme strings are rejected explicitly. Future dates are evaluated against the input's as_of date, not the system clock, preserving reproducibility. False provenance declarations cannot be detected. Broad categories can produce misleading similarities. A responder with an unqualified or negative reply still counts if entered as responded=true. There is no semantic interpretation, enrichment, causal inference or deduplication by company name. This engine can only rank companies already provided.

## Evidence-based improvement and verdict

After two weeks of real use, Henry should hand-check a sample of returned prospects and record the checked count, errors, error rate, usage days and reason for each error in a private trial log. Primary metric: hand-checked candidate error rate = incorrect candidates / checked candidates. Empty samples are unmeasured, never 0% accuracy. If error rate exceeds 10%, fix the leading failure cause and recheck, or kill with the reason recorded. If unused, record that and kill. Do not treat fixture correctness as real-world accuracy.

The two-week real-use evidence window has not occurred. Operational verdict is explicitly pending, not invented. Record the final dated verdict and evidence after that window: expand for daily use or revenue, integrate for substantial sibling overlap, commercialise for a demonstrated buyer willing to pay as-is, maintain for useful portfolio evidence otherwise, kill if unused or unable to meet acceptance criteria. See VERDICT.md. This is the one improvement hook; no fabricated real trial is shipped.
