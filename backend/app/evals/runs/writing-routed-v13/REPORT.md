# Writing model calibration benchmark

References are editorial estimates unless explicitly labelled human reviewed. This small set cannot establish population-level reliability or certify VSTEP accuracy.

| Model | Effort | N | MAE | ±0.5 | ±1 | Over >1 | Signed error | Valid | $ / task | $ / 100 | Pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.4-mini-2026-03-17+conditional-gpt-5.6-terra | low | 13 | 0.667 | 8% | 15% | 0% | -0.250 | 23% | 0.0067 | 0.67 | False |
| gpt-5.6-luna+conditional-gpt-5.6-terra | low | 13 | 0.562 | 8% | 15% | 0% | -0.562 | 15% | 0.0040 | 0.40 | False |

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
