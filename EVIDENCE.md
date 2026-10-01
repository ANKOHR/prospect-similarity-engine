# Local build evidence

Measured on 2026-10-01 using Python 3.12.10, CPU only, on this Windows machine.

- pytest: 22 tests passed.
- Full installed CLI demo (fixtures, run, report): 0.806693 seconds measured with time.perf_counter, below 5 seconds.
- Fixture totals: 200 records, 10 responders, 190 prospects, 40 matches.
- Independently specified planted ids exactly match all returned ids: 40 found, zero false positives, zero false negatives.
- Mutation of company c010 removes two shared fields: computed matches fall to 39. Ignored expectations can be corrupted without controlling computed output.
- Two runs and two report writes are byte-identical in tests.
- Empty input, malformed JSON, unsupported CSV/YAML, schema drift, duplicates, future dates, negative amounts in unsupported fields, Unicode, long strings, missing input and report write failure tested.

The shipped [demo report](evidence/demo-report.md) is entirely synthetic. It is local build evidence, not evidence of improved real outreach. No real trials, time savings, money savings or response probabilities are measured. The measured elapsed time includes process startup and capture of the full report. Performance on other datasets and machines is unmeasured.
