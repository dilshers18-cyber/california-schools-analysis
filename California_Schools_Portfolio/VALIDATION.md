# Validation record

Validated 2026-11-16.

- Ran `python main.py` successfully against the bundled analysis database.
- Generated all five CSVs, all five PNG charts, findings and quality metrics.
- Passed all five unittest checks: independent county aggregation and weighted means, FRPM bands and averages, opening-year counts, normalized join identifiers and ranges, and key source results.
- Compared rounded SQL outputs using a half-cent tolerance plus floating-point epsilon.
- Visually reviewed all five charts.
- Python version: 3.12.14
