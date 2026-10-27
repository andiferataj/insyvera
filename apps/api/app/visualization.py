import hashlib
import json
from decimal import Decimal
from sqlalchemy import select
from .db import Analysis, Document, Version
from .ingestion import numeric

def chart_analysis(db, workspace, definition):
    import numpy as np
    row = db.execute(select(Document, Version).join(Version).where(
        Document.workspace_id == workspace, Version.id == definition["version_id"], Version.status == "ready")).first()
    if not row:
        raise ValueError("Ready source dataset not found.")
    document, version = row
    tables = version.parsed.get("datasets", [])
    index = definition.get("table_index", 0)
    if index >= len(tables):
        raise ValueError("Dataset index not found.")
    table = tables[index]
    x, y, kind = definition["x"], definition.get("y"), definition["kind"]
    if x not in table["columns"] or (y and y not in table["columns"]):
        raise ValueError("Chart column not found.")
    data = []
    records = []
    if kind == "histogram":
        pairs = [(i, numeric(r.get(x))) for i,r in enumerate(table["rows"])]
        pairs = [(i,v) for i,v in pairs if v is not None]
        if not pairs:
            raise ValueError("No numeric values for this histogram.")
        counts, edges = np.histogram([v for _,v in pairs], bins=definition.get("bins",12))
        labels = [f"{edges[i]:.3g} – {edges[i+1]:.3g}" for i in range(len(counts))]
        data = [{"type":"bar","x":labels,"y":counts.astype(int).tolist(),"marker":{"color":"#648c73"}}]
        records = [{"row":table["row_numbers"][i],x:v} for i,v in pairs]
    elif kind == "scatter":
        if not y:
            raise ValueError("Scatter charts require both numeric columns.")
        pairs = [(i,numeric(r.get(x)),numeric(r.get(y))) for i,r in enumerate(table["rows"])]
        pairs = [(i,a,b) for i,a,b in pairs if a is not None and b is not None]
        data = [{"type":"scatter","mode":"markers","x":[a for _,a,_ in pairs],"y":[b for _,_,b in pairs],
            "text":[f"Source row {table['row_numbers'][i]}" for i,_,_ in pairs],"marker":{"color":"#648c73","size":9}}]
        records = [{"row":table["row_numbers"][i],x:a,y:b} for i,a,b in pairs]
    else:
        if not y:
            raise ValueError("Bar and line charts require a numeric y column.")
        totals = {}
        for i,r in enumerate(table["rows"]):
            amount = numeric(r.get(y))
            if amount is not None:
                key = str(r.get(x) or "(missing)")
                totals[key] = totals.get(key, Decimal(0)) + Decimal(str(amount))
                records.append({"row":table["row_numbers"][i],x:key,y:str(amount)})
        labels = sorted(totals) if kind == "line" else list(totals)
        data = [{"type":"bar" if kind=="bar" else "scatter","mode":"lines+markers","x":labels,
            "y":[float(totals[k]) for k in labels],"marker":{"color":"#648c73"}}]
    if not records:
        raise ValueError("No complete records are available for the selected chart.")
    source = {"document_id":document.id,"version_id":version.id,"hash":version.hash,
        "name":document.name,"sheet":table["name"],"range":table["range"]}
    chart = {"title":document.name+" · "+kind,"data":data,"layout":{"xaxis":{"title":x},"yaxis":{"title":"Count" if kind=="histogram" else y}}}
    result = {"chart":chart,"result":{"rows":records,"included_rows":len(records),"excluded_rows":len(table["rows"])-len(records)},
        "source":source,"provenance":{"engine":"validated-chart-v1",
            "operation_hash":hashlib.sha256(json.dumps(definition,sort_keys=True).encode()).hexdigest(),
            "numpy":np.__version__,"assumption":"Line order uses sorted category labels. Use ISO dates for chronological order."}}
    item=Analysis(workspace_id=workspace,definition={"operation":"chart",**definition},result=result)
    db.add(item)
    db.flush()
    return {"id":item.id,**result}
