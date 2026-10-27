"""Standalone operation worker. No generated code, eval, imports, paths or URLs accepted from requests."""
import hashlib
import json
import statistics
import sys
from decimal import Decimal

def number(value):
    import re
    try:
        if isinstance(value, bool) or value is None:
            return None
        text = str(value).strip()
        text = re.sub(r"^(EUR|USD|GBP|€|£|\$)\s*", "", text, flags=re.I)
        text = re.sub(r"\s*(EUR|USD|GBP)$", "", text, flags=re.I)
        negative = text.startswith("(") and text.endswith(")")
        if negative:
            text = text[1:-1]
        if "," in text and not re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", text):
            return None
        text = text.replace(",", "")
        if not re.fullmatch(r"-?\d+(\.\d+)?", text):
            return None
        n = Decimal(text) * (-1 if negative else 1)
        return n if n.is_finite() else None
    except Exception:
        return None

def execute(payload):
    operation = payload["operation"]
    if operation not in {"aggregate", "statistics", "filter", "join", "correlation", "clean", "trend"}:
        raise ValueError("Only aggregate, statistics, filter, join and correlation operations are allowed.")
    rows = payload.get("rows", [])
    if len(rows) > 100000 or any(not isinstance(r, dict) for r in rows):
        raise ValueError("Invalid or excessive rows.")
    column = payload.get("column")
    if operation == "clean":
        options = payload.get("options", {})
        if set(options) - {"trim_strings", "drop_duplicates", "fill_missing", "numeric_columns"}:
            raise ValueError("Unknown cleaning option.")
        changed, seen, removed = [], set(), 0
        for original in rows:
            row = dict(original)
            if options.get("trim_strings"):
                row = {k:v.strip() if isinstance(v,str) else v for k,v in row.items()}
            for k,v in options.get("fill_missing", {}).items():
                if row.get(k) is None or row.get(k) == "":
                    row[k] = v
            for key in options.get("numeric_columns", []):
                value = number(row.get(key))
                row[key] = str(value) if value is not None else None
            signature = json.dumps(row, sort_keys=True)
            if options.get("drop_duplicates") and signature in seen:
                removed += 1
                continue
            seen.add(signature)
            changed.append(row)
        return {"rows":changed,"removed_duplicates":removed,"input_rows":len(rows),
            "assumptions":options,"originals_modified":False}
    if operation == "trend":
        from datetime import datetime
        pairs = []
        for row in rows:
            y = number(row.get(column))
            raw = row.get(payload.get("second_column"))
            x = number(raw)
            if x is None and isinstance(raw,str):
                try:
                    x = Decimal(datetime.fromisoformat(raw).date().toordinal())
                except ValueError:
                    continue
            if x is not None and y is not None:
                pairs.append((float(x),float(y)))
        if len(pairs)<3:
            raise ValueError("A trend requires at least three complete observations.")
        x,y = zip(*pairs)
        line = statistics.linear_regression(x,y)
        return {"slope":line.slope,"intercept":line.intercept,"r_squared":statistics.correlation(x,y)**2,
            "observations":len(pairs),"limitation":"Observed linear association; not a forecast or causal relationship."}
    if operation == "filter":
        rule = payload.get("rule", {})
        if rule.get("operator") not in {"eq", "ne", "gt", "lt", "not_null"}:
            raise ValueError("Unsupported filter.")
        def keep(row):
            value = row.get(column)
            comparison = rule.get("value")
            op = rule["operator"]
            if op == "not_null":
                return value is not None and value != ""
            if op in {"eq", "ne"}:
                return (str(value) == str(comparison)) == (op == "eq")
            a, b = number(value), number(comparison)
            return a is not None and b is not None and (a > b if op == "gt" else a < b)
        return {"rows": [r for r in rows if keep(r)], "input_rows": len(rows)}
    if operation == "join":
        right = payload.get("right_rows", [])
        key = payload.get("key")
        if not key or len(right) > 100000:
            raise ValueError("A join key and bounded right dataset are required.")
        index = {}
        for r in right:
            if r.get(key) is not None:
                index.setdefault(str(r[key]), []).append(r)
        result = []
        for row in rows:
            if row.get(key) is None:
                continue
            for other in index.get(str(row[key]), []):
                result.append({**row, **{k if k == key or k not in row else "right_" + k: v for k,v in other.items()}})
                if len(result) > 100000:
                    raise ValueError("Join exceeds row limit.")
        return {"rows": result, "join": "inner", "key": key}
    values = [number(r.get(column)) for r in rows]
    good = [v for v in values if v is not None]
    if not good:
        raise ValueError("Selected column has no numeric values.")
    if operation == "correlation":
        second = payload.get("second_column")
        pairs = [(float(a), float(b)) for r in rows if (a := number(r.get(column))) is not None
                 and (b := number(r.get(second))) is not None]
        if len(pairs) < 3:
            raise ValueError("Correlation needs at least three complete pairs.")
        x, y = zip(*pairs)
        return {"pearson_r": statistics.correlation(x,y), "pairs": len(pairs), "causality": False}
    if operation == "statistics":
        floats = [float(v) for v in good]
        return {"count": len(good), "missing_or_non_numeric": len(rows) - len(good),
            "sum": str(sum(good)), "mean": str(sum(good) / len(good)),
            "median": statistics.median(floats), "min": str(min(good)), "max": str(max(good)),
            "std": statistics.pstdev(floats)}
    group = payload.get("group_by")
    groups = {}
    for row, value in zip(rows, values):
        if value is not None:
            label = str(row.get(group) or "(missing)") if group else "Total"
            groups[label] = groups.get(label, Decimal(0)) + value
    return {"column": column, "group_by": group, "total": str(sum(good)),
        "excluded_rows": len(rows) - len(good), "groups": [{"label": k, "value": str(v)} for k,v in groups.items()]}

if __name__ == "__main__":
    try:
        if sys.platform != "win32":
            import resource
            resource.setrlimit(resource.RLIMIT_CPU, (10,10))
            resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024,512*1024*1024))
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024*1024,1024*1024))
            resource.setrlimit(resource.RLIMIT_NOFILE, (32,32))
        data = sys.stdin.buffer.read(20*1024*1024 + 1)
        if len(data) > 20*1024*1024:
            raise ValueError("Input limit exceeded.")
        result = execute(json.loads(data))
        print(json.dumps({"result": result, "input_hash": hashlib.sha256(data).hexdigest()}, allow_nan=False))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)
