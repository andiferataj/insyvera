import time
from decimal import Decimal
from .analytics import infer_analyses
from .db import Evaluation, Run, transaction
from .research import contradictions, execute_run
from .retrieval import search

DEFAULT_CASES = [
    {"name": "Tax summary retrieval", "kind": "retrieval", "question": "Income taxable income tax summary",
     "expected_file": "tax_report_2026.pdf"},
    {"name": "Cited deadline extracts", "kind": "citation", "question": "Filing deadline"},
    {"name": "Gift totals", "kind": "numeric", "metric": "Gift spending", "expected": "570"},
    {"name": "Unanswerable credentials", "kind": "abstention", "question": "What is my secret bank password?"},
    {"name": "Conflicting deadlines", "kind": "contradiction", "question": "Filing deadline", "subject": "filing deadline"},
]

def evaluate(workspace, cases=None, provider="extractive", model="extractive"):
    cases = cases or DEFAULT_CASES
    started = time.monotonic()
    results = []
    for case in cases:
        kind = case["kind"]
        with transaction() as db:
            if kind == "retrieval":
                hits = search(db, workspace, case["question"], 5)
                rank = next((i+1 for i,h in enumerate(hits) if h["name"] == case["expected_file"]), None)
                results.append({"name": case["name"], "kind": kind, "passed": rank is not None,
                    "recall_at_5": int(rank is not None), "reciprocal_rank": 1/rank if rank else 0,
                    "retrieved": [h["name"] for h in hits]})
            elif kind == "numeric":
                calculated = infer_analyses(db, workspace)
                metric = next((m for m in calculated["metrics"] if m["label"] == case["metric"]), None)
                results.append({"name": case["name"], "kind": kind,
                    "passed": bool(metric and Decimal(metric["value"]) == Decimal(case["expected"])),
                    "actual": metric["value"] if metric else None, "expected": case["expected"]})
            elif kind == "contradiction":
                hits = search(db, workspace, case["question"], 20)
                conflicts = contradictions(hits)
                results.append({"name": case["name"], "kind": kind,
                    "passed": any(c["subject"] == case["subject"] for c in conflicts), "conflicts": conflicts})
            elif kind in {"abstention", "citation"}:
                run = Run(workspace_id=workspace, question=case["question"], mode="research",
                    config={"provider": provider, "model": model})
                db.add(run)
                db.flush()
                run_id = run.id
            else:
                raise ValueError("Unknown evaluation case kind.")
        if kind in {"abstention", "citation"}:
            execute_run(run_id)
            with transaction() as db:
                run = db.get(Run, run_id)
                if run.status != "completed":
                    results.append({"name": case["name"], "kind": kind, "passed": False, "error": run.error})
                else:
                    claims = run.result.get("claims", [])
                    valid = sum(c.get("citation_valid", False) for c in claims)
                    supported = sum(c["verification"] == "supported_extract" for c in claims)
                    passed = run.result["abstained"] if kind == "abstention" else bool(claims) and valid == len(claims)
                    results.append({"name": case["name"], "kind": kind, "passed": passed,
                        "citation_validity": valid/len(claims) if claims else None,
                        "extract_support": supported/len(claims) if claims else None, "run_id": run_id})
    metrics = {}
    for kind in ("retrieval", "numeric", "abstention", "citation", "contradiction"):
        group = [r for r in results if r["kind"] == kind]
        metrics[kind] = sum(r["passed"] for r in group)/len(group) if group else None
    retrieval = [r for r in results if r["kind"] == "retrieval"]
    scores = {"metrics": metrics, "mrr_at_5": sum(r["reciprocal_rank"] for r in retrieval)/len(retrieval) if retrieval else None,
        "passed": sum(r["passed"] for r in results), "total": len(results), "cases": results,
        "latency_ms": int((time.monotonic()-started)*1000), "estimated_cost_usd": None,
        "limitations": "Small synthetic benchmark. Numeric checks use exact expected values. Citation existence and extract matching are not semantic entailment scores."}
    with transaction() as db:
        result = Evaluation(workspace_id=workspace, config={"provider": provider, "model": model,
            "suite": "custom" if cases != DEFAULT_CASES else "synthetic-v1", "cases": cases}, scores=scores)
        db.add(result)
        db.flush()
        return {"id": result.id, "config": result.config, "scores": scores, "created_at": result.created_at.isoformat()}
