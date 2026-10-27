# Synthetic evaluation suite v1

Five separately scored cases:
- Tax-summary retrieval: tax_report_2026.pdf must appear in top five; report reciprocal rank.
- Deadline citation: all returned extracts must have resolvable source IDs.
- Gift arithmetic: exactly 570 in the Gift spending metric.
- Missing answer: abstain on a request for an unknown bank password.
- Contradiction: flag differing filing deadline values across the PDF and DOCX.

The independent expected numeric values are in datasets/demo/expected.json. Default case definitions live in app/evaluation.py. They do not use a model as an arithmetic judge.

The benchmark is intentionally small. It does not establish broad retrieval recall, semantic entailment, universal hallucination resistance, model superiority, tax correctness, or production throughput. A null metric means not measured, not a perfect score.

Custom API cases and explicit provider/model IDs support additional experiments. Compare like-for-like suites and retain source versions when interpreting results.
