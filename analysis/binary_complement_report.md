# KBS strict binary-complement replication

## Completeness

- Planned records: 558
- Complete records: 558
- Missing records: 0
- Incomplete observed records: 0
- Failed/missing slots in observed records: 0

## Primary estimates

- Stable-correct: +6.72 pp [+4.23, +9.29]
- Support-rescuable: +19.75 pp [+15.22, +24.39]
- R - C interaction: +13.03 pp [+7.58, +18.40]

## By endpoint

| Model | C n | C effect | R n | R effect | Interaction |
|---|---:|---:|---:|---:|---:|
| Qwen/Qwen3-VL-8B-Instruct | 80 | +22.50 pp [+15.62, +29.38] | 80 | +42.50 pp [+34.38, +50.62] | +20.00 pp [+9.15, +30.86] |
| Qwen/Qwen3.5-9B | 80 | +0.62 pp [-4.38, +5.62] | 58 | +4.31 pp [-2.59, +11.21] | +3.69 pp [-5.19, +12.49] |
| Pro/moonshotai/Kimi-K2.6 | 80 | -1.88 pp [-5.00, +0.00] | 28 | -3.57 pp [-14.29, +5.36] | -1.70 pp [-12.53, +8.04] |
| zai-org/GLM-4.5V | 80 | +5.62 pp [+1.88, +10.00] | 72 | +15.97 pp [+9.03, +23.61] | +10.35 pp [+2.26, +18.86] |

## By task

| Task | C n | C effect | R n | R effect | Interaction |
|---|---:|---:|---:|---:|---:|
| BoolQ | 160 | +7.19 pp [+3.27, +11.11] | 124 | +24.19 pp [+17.80, +30.65] | +17.01 pp [+9.37, +24.80] |
| StrategyQA | 160 | +6.25 pp [+3.01, +9.81] | 114 | +14.91 pp [+8.74, +21.19] | +8.66 pp [+1.40, +16.02] |

## Leave one endpoint out

| Omitted model | Interaction |
|---|---:|
| Qwen/Qwen3-VL-8B-Instruct | +6.77 pp [+1.37, +12.17] |
| Qwen/Qwen3.5-9B | +15.97 pp [+9.68, +22.26] |
| Pro/moonshotai/Kimi-K2.6 | +13.27 pp [+7.14, +19.56] |
| zai-org/GLM-4.5V | +14.30 pp [+7.93, +20.55] |
