import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from decimal import Decimal
from pathlib import Path
from sqlalchemy import func, select
from .config import settings
from .db import Analysis, Document, Version
from .ingestion import numeric

RUNNER = Path(__file__).with_name("sandbox_runner.py")

def isolated(definition):
    content = json.dumps(definition, allow_nan=False).encode()
    temp_root = settings.data_dir / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="analysis-", dir=temp_root) as directory:
        env = {"PATH": os.environ.get("PATH", ""), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "PYTHONIOENCODING": "utf-8"}
        process = subprocess.run([sys.executable, "-I", str(RUNNER)], input=content,
            capture_output=True, cwd=directory, timeout=15, env=env)
    result = json.loads(process.stdout)
    if process.returncode:
        raise ValueError(result.get("error", "Analysis worker failed."))
    return {**result, "provenance": {"operation": {k:v for k,v in definition.items() if k not in {"rows", "right_rows"}},
        "operation_hash": hashlib.sha256(content).hexdigest(), "executor_hash": hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
        "python": sys.version.split()[0], "stderr": process.stderr.decode(errors="replace")[:2000],
        "engine": "allowlisted-isolated-operations-v1", "timeout_seconds": 15}}

def latest_sources(db, workspace, ids=None):
    latest = select(Version.document_id, func.max(Version.number).label("n")).group_by(Version.document_id).subquery()
    q = select(Document, Version).join(Version, Version.document_id == Document.id).join(
        latest, (latest.c.document_id == Document.id) & (latest.c.n == Version.number)).where(
        Document.workspace_id == workspace, Version.status == "ready")
    if ids is not None:
        q = q.where(Document.id.in_(ids))
    return db.execute(q).all()

def run_analysis(db, workspace, version_id, table_index, operation, run_id=None, **parameters):
    item = db.execute(select(Document, Version).join(Version).where(Document.workspace_id == workspace,
        Version.id == version_id, Version.status == "ready")).first()
    if not item:
        raise ValueError("Ready dataset not found.")
    doc, version = item
    tables = version.parsed.get("datasets", [])
    if table_index < 0 or table_index >= len(tables):
        raise ValueError("Dataset index not found.")
    table = tables[table_index]
    definition = {"operation": operation, "rows": table["rows"], **parameters}
    result = isolated(definition)
    result["source"] = {"document_id": doc.id, "version_id": version.id, "hash": version.hash,
        "name": doc.name, "sheet": table["name"], "range": table["range"], "row_numbers": table["row_numbers"]}
    stored = {k:v for k,v in definition.items() if k not in {"rows", "right_rows"}}
    stored.update({"version_id": version.id, "table_index": table_index})
    if run_id:
        existing = db.scalars(select(Analysis).where(Analysis.workspace_id == workspace, Analysis.run_id == run_id)).all()
        for previous in existing:
            if previous.definition == stored:
                return {"id": previous.id, **previous.result}
    analysis = Analysis(workspace_id=workspace, run_id=run_id, definition=stored, result=result)
    db.add(analysis)
    db.flush()
    return {"id": analysis.id, **result}

def infer_analyses(db, workspace, ids=None, run_id=None):
    summaries, charts, metrics, pdf_metrics, warnings = [], [], [], [], []
    for doc, version in latest_sources(db, workspace, ids):
        for ti, table in enumerate(version.parsed.get("datasets", [])):
            columns = table["columns"]
            lookup = {c.lower(): c for c in columns}
            amount = next((lookup[c] for c in ("amount", "price", "cost", "spending", "total") if c in lookup), None)
            if not amount:
                continue
            currencies = {str(r.get(lookup["currency"])) for r in table["rows"] if r.get(lookup.get("currency"))} if "currency" in lookup else set()
            periods = {str(r.get(lookup["period"])) for r in table["rows"] if r.get(lookup.get("period"))} if "period" in lookup else set()
            if len(currencies) > 1 or len(periods) > 1:
                warnings.append(f"{doc.name}: mixed currencies or periods; select and filter an aligned dataset before totaling.")
                continue
            group = next((lookup[c] for c in ("recipient", "category", "type") if c in lookup), None)
            result = run_analysis(db, workspace, version.id, ti, "aggregate", run_id, column=amount, group_by=group)
            summaries.append(result)
            groups = result["result"]["groups"]
            charts.append({"title": f"{doc.name} · {table['name']}", "analysis_id": result["id"],
                "data": [{"type": "bar", "x": [g["label"] for g in groups], "y": [float(g["value"]) for g in groups],
                    "marker": {"color": "#648c73"}, "hovertemplate": "%{x}<br>%{y:,.2f}<extra></extra>"}],
                "layout": {"xaxis": {"title": group or amount}, "yaxis": {"title": amount}}})
            context = {"currency": next(iter(currencies), None), "period": next(iter(periods), None),
                "document_id": doc.id, "version_id": version.id, "name": doc.name, "sheet": table["name"],
                "range": table["range"], "analysis_id": result["id"]}
            if "type" in lookup:
                amounts = {}
                for row in table["rows"]:
                    value = numeric(row.get(amount))
                    if value is not None:
                        kind = str(row.get(lookup["type"], "")).lower()
                        amounts[kind] = amounts.get(kind, Decimal(0)) + Decimal(str(value))
                income = sum((v for k,v in amounts.items() if k in {"income", "revenue"}), Decimal(0))
                expense = sum((v for k,v in amounts.items() if k in {"expense", "expenses", "deduction"}), Decimal(0))
                if income or expense:
                    metrics += [{"label": "Income", "value": str(income), **context},
                        {"label": "Expenses", "value": str(expense), **context},
                        {"label": "Taxable income", "value": str(income-expense), **context}]
                    warnings.append("Taxable income here means income minus recorded expenses; eligibility of deductions is not established.")
            if "budget" in lookup:
                budget = run_analysis(db, workspace, version.id, ti, "aggregate", run_id, column=lookup["budget"], group_by=group)
                summaries.append(budget)
                metrics += [{"label": "Gift spending", "value": result["result"]["total"], **context},
                    {"label": "Gift budget", "value": budget["result"]["total"], **context},
                    {"label": "Over budget", "value": str(Decimal(result["result"]["total"])-Decimal(budget["result"]["total"])), **context}]
        if doc.type == "pdf":
            text = "\n".join(u["text"] for u in version.parsed.get("units", []))
            period = re.search(r"Period\s*:\s*(\d{4})", text, re.I)
            currency = re.search(r"Currency\s*:\s*([A-Z]{3})", text)
            for unit in version.parsed.get("units", []):
                for match in re.finditer(r"(?im)^(Income|Expenses|Taxable income)\s*:\s*(?:EUR|USD|GBP|€|\$)?\s*([\d,]+(?:\.\d+)?)", unit["text"]):
                    pdf_metrics.append({"label": match[1].capitalize(), "value": str(Decimal(match[2].replace(",",""))),
                        "document_id": doc.id, "version_id": version.id, "name": doc.name, **unit["location"],
                        "period": period[1] if period else None, "currency": currency[1] if currency else None})
    reconciliation = []
    for recorded in metrics:
        for reported in pdf_metrics:
            if recorded["label"].lower() == reported["label"].lower():
                aligned = bool(recorded["period"] and recorded["currency"] and
                    recorded["period"] == reported["period"] and recorded["currency"] == reported["currency"])
                reconciliation.append({"metric": recorded["label"], "recorded": recorded["value"],
                    "reported": reported["value"], "difference": str(Decimal(reported["value"]) - Decimal(recorded["value"])) if aligned else None,
                    "aligned": aligned, "status": "match" if aligned and Decimal(recorded["value"]) == Decimal(reported["value"]) else
                    "discrepancy" if aligned else "unaligned", "sources": [recorded, reported]})
    return {"analyses": summaries, "charts": charts, "metrics": metrics, "reconciliation": reconciliation,
        "warnings": sorted(set(warnings + ["Calculations exclude missing/non-numeric cells and do not imply available cash."]))}
