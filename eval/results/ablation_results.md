# Ablation Study Results

## Retrieval Strategy (Top-K=5)

| Variant | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| hybrid | 0.100 | 0.120 | 0.160 | 0.116 |
| dense_only | 0.060 | 0.080 | 0.100 | 0.071 |
| lexical_only | 0.080 | 0.100 | 0.140 | 0.095 |

## Top-K Ablation (Strategy=Hybrid)

| Top-K | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---:|---:|---:|---:|
| 3 | 0.100 | 0.120 | 0.160 | 0.116 |
| 5 | 0.100 | 0.120 | 0.160 | 0.116 |
| 10 | 0.100 | 0.120 | 0.160 | 0.125 |
