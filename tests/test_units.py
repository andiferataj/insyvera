import io
from decimal import Decimal
import openpyxl
import pytest
from app.analytics import isolated
from app.ingestion import dataset, numeric, parse
from app.tools import calculator, public_url

def test_formulas_merged_cells_and_profiles():
    book=openpyxl.Workbook()
    sheet=book.active
    sheet.append(["Name","Amount","Amount"])
    sheet.append(["First",10,"=B2*2"])
    sheet.append(["First",10,None])
    sheet.merge_cells("A4:A5")
    stream=io.BytesIO()
    book.save(stream)
    result=parse(stream.getvalue(),"formulas.xlsx")
    table=result["datasets"][0]
    assert table["columns"]==["Name","Amount","Amount (2)"]
    assert table["formulas"][0]["cell"]=="C2"
    assert table["formulas"][0]["value"] is None
    assert any("cached" in w for w in result["warnings"])
    assert table["merged"]==["A4:A5"]

def test_exact_decimal_arithmetic_and_operation_restrictions():
    result=isolated({"operation":"aggregate","column":"value","rows":[{"value":"0.1"},{"value":"0.2"},{"value":None}]})
    assert Decimal(result["result"]["total"])==Decimal("0.3")
    assert result["result"]["excluded_rows"]==1
    for operation in ["exec","open","network","__import__","shell"]:
        with pytest.raises(ValueError):
            isolated({"operation":operation,"rows":[]})

def test_filter_join_and_correlation():
    joined=isolated({"operation":"join","key":"id","rows":[{"id":1,"x":10},{"id":None,"x":8}],
        "right_rows":[{"id":1,"y":20},{"id":None,"y":7}]})["result"]
    assert joined["rows"]==[{"id":1,"x":10,"y":20}]
    result=isolated({"operation":"correlation","column":"x","second_column":"y",
        "rows":[{"x":1,"y":2},{"x":2,"y":4},{"x":3,"y":6}]})
    assert result["result"]["pearson_r"]==pytest.approx(1)
    assert result["result"]["causality"] is False

def test_numeric_and_safety_edges():
    assert numeric("EUR 1,234.50")==1234.5
    assert numeric("2026-01-01") is None
    assert numeric("NaN") is None
    assert numeric(True) is None
    assert calculator("-(2+3)*4")==-20
    for target in ["http://example.com","https://user:pass@example.com","https://localhost:8080","file:///etc/passwd"]:
        with pytest.raises(ValueError):
            public_url(target)
    result=dataset("D",[["x","x"],[1,1],[1,1],[None,None]])
    assert result["profile"]["duplicate_rows"]==1

def test_checkpoint_recovery_without_repeating_planner(client, seeded, monkeypatch):
    import app.research as research
    from app.db import Run, Step, transaction
    from sqlalchemy import select
    original=research.search
    def unavailable(*args,**kwargs):
        raise ConnectionError("Temporary retrieval outage")
    with transaction() as db:
        run=Run(workspace_id=seeded,question="Filing deadline",mode="research",
            config={"provider":"extractive","model":"extractive"})
        db.add(run)
        db.flush()
        run_id=run.id
    monkeypatch.setattr(research,"search",unavailable)
    research.execute_run(run_id)
    with transaction() as db:
        assert db.get(Run,run_id).status=="failed"
    monkeypatch.setattr(research,"search",original)
    research.execute_run(run_id,resume=True)
    with transaction() as db:
        assert db.get(Run,run_id).status=="completed"
        steps=db.scalars(select(Step).where(Step.run_id==run_id,Step.node=="planner")).all()
        assert len(steps)==1

def test_cleaning_preview_trend_and_chart_replay(client, seeded):
    from app.analytics import isolated
    cleaned=isolated({"operation":"clean","rows":[{"x":"  A  ","n":None},{"x":"  A  ","n":None}],
        "options":{"trim_strings":True,"drop_duplicates":True,"fill_missing":{"n":0}}})["result"]
    assert cleaned["rows"]==[{"x":"A","n":0}]
    assert cleaned["removed_duplicates"]==1
    trend=isolated({"operation":"trend","column":"y","second_column":"x",
        "rows":[{"x":1,"y":2},{"x":2,"y":4},{"x":3,"y":6}]})["result"]
    assert trend["slope"]==pytest.approx(2)
    assert trend["r_squared"]==pytest.approx(1)
    base=f"/api/workspaces/{seeded}"
    dataset=next(d for d in client.get(base+"/datasets").json() if d["document_name"]=="christmas_gifts.xlsx")
    for kind in ["bar","line","histogram","scatter"]:
        created=client.post(base+"/charts",json={"version_id":dataset["version_id"],"kind":kind,
            "x":"Amount" if kind in {"histogram","scatter"} else "Recipient","y":"Budget" if kind=="scatter" else "Amount"})
        assert created.status_code==201,created.text
        artifact=created.json()
        assert artifact["chart"]["data"]
        replayed=client.post(base+"/analyses/"+artifact["id"]+"/replay")
        assert replayed.status_code==201
        assert replayed.json()["chart"]==artifact["chart"]

def test_local_backup_integrity_and_non_destructive_restore(client, seeded):
    import sqlite3
    from app.maintenance import backup, restore
    from app.config import settings
    target=settings.data_dir.parent/(settings.data_dir.name+"-backup.tar.gz")
    manifest=backup(target)
    assert manifest["files"]>7
    destination=settings.data_dir.parent/(settings.data_dir.name+"-restore")
    restored=restore(target,destination)
    assert restored["files"]==manifest["files"]
    with sqlite3.connect(destination/"insyvera.db") as db:
        assert db.execute("SELECT count(*) FROM documents").fetchone()[0]==7
    with pytest.raises(ValueError):
        restore(target,destination)

def test_currency_parsing_rejects_ambiguous_decimal_commas():
    from app.sandbox_runner import number
    from app.ingestion import numeric
    assert number("EUR 1,234.50")==Decimal("1234.50")
    assert number("1234.50 EUR")==Decimal("1234.50")
    assert number("1,23") is None
    assert numeric("1,23") is None
    assert number("(1,234.50)")==Decimal("-1234.50")
