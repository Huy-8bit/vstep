# Writing model calibration benchmark

References are editorial estimates unless explicitly labelled human reviewed. This small set cannot establish population-level reliability or certify VSTEP accuracy.

| Model | Effort | N | MAE | ±0.5 | ±1 | Over >1 | Signed error | Valid | $ / task | $ / 100 | Pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.6-luna | low | 13 | 0.469 | 46% | 54% | 8% | 0.250 | 62% | 0.0060 | 0.60 | False |
| gpt-5.6-luna | none | 13 | 0.575 | 46% | 69% | 0% | 0.000 | 77% | 0.0049 | 0.49 | False |
| gpt-5.6-luna | medium | 13 | 0.489 | 62% | 69% | 8% | 0.080 | 85% | 0.0060 | 0.60 | False |
| gpt-5.4-mini-2026-03-17 | low | 13 | 0.736 | 31% | 54% | 8% | -0.097 | 69% | 0.0246 | 2.46 | False |
| gpt-5.4-mini-2026-03-17 | none | 13 | 0.547 | 46% | 54% | 0% | 0.078 | 62% | 0.0205 | 2.05 | False |

Cheapest passing candidate on this dataset: **none**; do not claim a cheaper model has passed.

Product thresholds (not official exam requirements):
```json
{
  "overall_mae_max": 0.5,
  "criterion_mae_max": 0.75,
  "within_half_min": 0.7,
  "within_one_min": 0.9,
  "serious_overscore_max": 0.02,
  "structured_success_min": 0.99,
  "min_samples": 12
}
```

Band agreement is an internal comparison bucket; a single Writing task does not certify a proficiency level. Invalid-output rate counts each provider response; structured success counts validated final sample results including bounded retry cost. Failed samples remain in rate denominators. Full criterion errors, token/cache/reasoning usage, calls, latency, cost/1,000, source provenance and raw results are saved in the run JSON and database.
