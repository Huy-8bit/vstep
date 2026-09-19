# Writing model calibration benchmark

References are editorial estimates unless explicitly labelled human reviewed. This small set cannot establish population-level reliability or certify VSTEP accuracy.

| Model | Effort | N | MAE | ±0.5 | ±1 | Over >1 | Signed error | Valid | $ / task | $ / 100 | Pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.6-luna+conditional-gpt-5.6-terra | medium | 13 | 0.356 | 76.9% | 100.0% | 0.0% | 0.163 | 100.0% | 0.0234 | 2.34 | True |

Cheapest passing candidate on this dataset: **gpt-5.6-luna+conditional-gpt-5.6-terra / medium**.

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

Primary replay fixes all original primary outputs while measuring fresh conditional reviews. It is not a new end-to-end run. Full-route cost/tokens/latency include the original measured primary calls; only new review calls incur additional charges. The JSON records the source run ID, replayed calls, new_provider_requests and new_known_cost_usd. No sample subsets or reference labels are sent to reviewers.
