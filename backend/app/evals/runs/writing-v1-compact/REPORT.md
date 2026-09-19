# Writing model calibration benchmark

References are editorial estimates unless explicitly labelled human reviewed. This small set cannot establish population-level reliability or certify VSTEP accuracy.

| Model | Effort | N | MAE | ±0.5 | ±1 | Over >1 | Signed error | Valid | $ / task | $ / 100 | Pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.4-mini-2026-03-17 | low | 13 | 0.615 | 46% | 69% | 15% | 0.115 | 92% | 0.0165 | 1.65 | False |
| gpt-5.4-mini-2026-03-17 | medium | 13 | unknown | 0% | 0% | 0% | unknown | 0% | 0.0649 | 6.49 | False |
| gpt-5.4-mini-2026-03-17 | none | 13 | 0.602 | 54% | 69% | 15% | 0.080 | 85% | 0.0151 | 1.51 | False |
| gpt-5.6-luna | low | 13 | 0.490 | 54% | 85% | 15% | 0.260 | 100% | 0.0036 | 0.36 | False |
| gpt-5.6-luna | medium | 13 | 0.462 | 62% | 85% | 15% | 0.327 | 100% | 0.0050 | 0.50 | False |
| gpt-5.6-luna | none | 13 | 0.481 | 54% | 85% | 8% | 0.077 | 100% | 0.0033 | 0.33 | False |
| gpt-5.6-terra | low | 13 | 0.346 | 85% | 92% | 0% | 0.038 | 100% | 0.0352 | 3.52 | True |
| gpt-5.6-terra | medium | 13 | 0.346 | 85% | 92% | 0% | -0.058 | 100% | 0.0435 | 4.35 | True |
| gpt-5.6-terra | none | 13 | 0.356 | 85% | 92% | 0% | 0.087 | 100% | 0.0313 | 3.13 | True |

Cheapest passing candidate on this dataset: **gpt-5.6-terra / none**.

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
