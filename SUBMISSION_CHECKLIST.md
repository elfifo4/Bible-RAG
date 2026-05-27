# Final Submission Checklist - Bible-RAG

## 1. Documentation
- [ ] `report.pdf` (or `report.md`) covers all 10 required sections.
- [ ] `README.md` is professional and includes "Quick Start".
- [ ] `data/MANIFEST.md` accurately describes the Tanakh corpus.

## 2. Technical Stability
- [ ] `python3 build_index.py` runs and builds the FAISS index.
- [ ] `python3 run_dev.py` launches both API and UI successfully.
- [ ] API keys and secrets are stored in `.env` and NOT committed to Git.

## 3. Evaluation
- [ ] Baseline evaluation run: `python3 eval/run_eval.py --strategy all`.
- [ ] Ablation study run: `python3 eval/run_eval.py --ablation`.
- [ ] Error analysis run: `python3 eval/error_analysis.py`.
- [ ] All results are visible in the "Performance Metrics" dashboard.

## 4. Final Polish
- [ ] All "TODO" comments removed from source code.
- [ ] Terminal logs are clean and readable.
- [ ] UI is responsive and works correctly in Hebrew (RTL).
