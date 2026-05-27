# Ablation Study Results

## Retrieval Strategy (Top-K=5)

| Variant | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| hybrid | 0.100 | 0.120 | 0.140 | 0.112 |
| dense_only | 0.060 | 0.080 | 0.080 | 0.067 |
| lexical_only | 0.080 | 0.100 | 0.140 | 0.095 |

## Top-K Ablation (Strategy=Hybrid)

| Top-K | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| 3 | 0.100 | 0.120 | 0.140 | 0.112 |
| 5 | 0.100 | 0.120 | 0.140 | 0.112 |
| 10 | 0.100 | 0.120 | 0.140 | 0.116 |
