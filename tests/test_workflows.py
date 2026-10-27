import io
from decimal import Decimal
import pymupdf
from docx import Document as WordDocument

def test_all_formats_versions_and_deduplication(client, seeded):
    base = f"/api/workspaces/{seeded}"
    docs = client.get(base+"/documents").json()
    assert {d["type"] for d in docs} == {"xlsx","pdf","docx","csv","md","txt"}
    assert len(docs) == 7
    assert all(d["versions"][0]["status"] == "ready" for d in docs), docs
    data = client.get(base+"/datasets").json()
    gifts = next(d for d in data if d["document_name"] == "christmas_gifts.xlsx")
    assert gifts["profile"]["missing_cells"] == 3
    assert gifts["profile"]["row_count"] == 7
    assert client.post(base+"/demo").json()["created"] == 0
    original = next(d for d in docs if d["type"] == "txt")
    content = client.get(base+"/versions/"+original["versions"][0]["id"]+"/content").content
    repeated = client.post(base+"/documents", files={"file":(original["name"],content)})
    assert repeated.json()["id"] == original["id"]
    new = client.post(base+"/documents/"+original["id"]+"/versions",files={"file":("readme.txt",b"Version two with new evidence.")})
    assert new.status_code == 201
    preview = client.get(base+"/documents/"+original["id"]).json()
    assert [v["number"] for v in preview["versions"]] == [2,1]
    assert client.get(base+"/versions/"+original["versions"][0]["id"]+"/content").content == content

def test_canonical_investigation_and_exports(client, seeded):
    base=f"/api/workspaces/{seeded}"
    created=client.post(base+"/runs",json={"question":"Compare my tax records, identify mismatches, and analyze Christmas gift spending.","mode":"investigation"})
    assert created.status_code==201,created.text
    run=client.get(base+"/runs/"+created.json()["id"]).json()
    assert run["status"]=="completed",run
    result=run["result"]
    assert result["verification"]["unsupported"]==0
    assert result["verification"]["verified"]==len(result["claims"])
    metrics={m["label"]:Decimal(m["value"]) for m in result["analytics"]["metrics"]}
    assert metrics["Income"]==84000 and metrics["Expenses"]==18000
    assert metrics["Taxable income"]==66000
    assert metrics["Gift spending"]==570 and metrics["Gift budget"]==500 and metrics["Over budget"]==70
    reconciliation={r["metric"]:r for r in result["analytics"]["reconciliation"]}
    assert Decimal(reconciliation["Income"]["difference"])==500
    assert Decimal(reconciliation["Taxable income"]["difference"])==500
    assert reconciliation["Expenses"]["status"]=="match"
    assert any(c["subject"]=="filing deadline" for c in result["contradictions"])
    assert len(run["steps"])==6
    assert all(c["kind"]=="calculation" or client.get(base+"/sources/"+c["source_ids"][0]).status_code==200 for c in result["claims"])
    assert result["analytics"]["charts"]
    report=client.post(base+"/reports",json={"title":"Canonical report","run_id":run["id"]}).json()
    rid=report["id"]
    content=report["versions"][0]["content"]
    assert "reproduc" in content.lower() and "500" in content
    pdf=client.get(base+"/reports/"+rid+"/export?format=pdf")
    assert pdf.content.startswith(b"%PDF")
    with pymupdf.open(stream=pdf.content,filetype="pdf") as parsed:
        assert "Canonical report" in parsed[0].get_text()
    docx=client.get(base+"/reports/"+rid+"/export?format=docx").content
    assert len(WordDocument(io.BytesIO(docx)).paragraphs)>10
    update=client.patch(base+"/reports/"+rid,json={"title":"Edited","content":content+"\nReviewed.","expected_version":1})
    assert update.status_code==200
    assert len(update.json()["versions"])==2
    stale=client.patch(base+"/reports/"+rid,json={"title":"Stale","content":"old","expected_version":1})
    assert stale.status_code==409
    assert "Reviewed." not in client.get(base+"/reports/"+rid+"/export?version=1").text

def test_missing_answers_and_scoped_retrieval(client, seeded):
    base=f"/api/workspaces/{seeded}"
    created=client.post(base+"/runs",json={"question":"What is my secret bank password?","mode":"research"}).json()
    run=client.get(base+"/runs/"+created["id"]).json()
    # A source saying credentials are absent must not be mistaken for the missing credential.
    assert run["result"]["abstained"] or all("do not contain" in c["text"] for c in run["result"]["claims"])
    hits=client.get(base+"/search",params={"q":"filing deadline"}).json()
    assert any(h["type"]=="pdf" for h in hits)
    assert any(h["type"]=="docx" for h in hits)
    one=hits[0]
    filtered=client.get(base+"/search",params={"q":"filing deadline","document_id":one["document_id"]}).json()
    assert all(h["document_id"]==one["document_id"] for h in filtered)

def test_analysis_operations_and_provenance(client, seeded):
    base=f"/api/workspaces/{seeded}"
    table=next(d for d in client.get(base+"/datasets").json() if d["document_name"]=="christmas_gifts.xlsx")
    result=client.post(base+"/analyses",json={"version_id":table["version_id"],"operation":"aggregate","column":"Amount","group_by":"Recipient"})
    assert result.status_code==201,result.text
    analysis=result.json()
    assert Decimal(analysis["result"]["total"])==570
    assert analysis["result"]["excluded_rows"]==1
    assert len(analysis["provenance"]["operation_hash"])==64
    assert len(analysis["source"]["hash"])==64
    assert len(analysis["source"]["row_numbers"])==7
    assert b"Mira,150" in client.get(base+"/analyses/"+analysis["id"]+"/export").content
    filtered=client.post(base+"/analyses",json={"version_id":table["version_id"],"operation":"filter","column":"Amount","rule":{"operator":"gt","value":100}})
    assert len(filtered.json()["result"]["rows"])==2
    stats=client.post(base+"/analyses",json={"version_id":table["version_id"],"operation":"statistics","column":"Amount"})
    assert stats.json()["result"]["count"]==6

def test_deletion_flags_archived_evidence(client, seeded):
    base=f"/api/workspaces/{seeded}"
    created=client.post(base+"/runs",json={"question":"Filing deadline","mode":"research"}).json()
    run=client.get(base+"/runs/"+created["id"]).json()
    source=run["result"]["sources"][0]
    assert client.delete(base+"/documents/"+source["document_id"]).status_code==200
    assert client.get(base+"/sources/"+source["id"]).status_code==404
    updated=client.get(base+"/runs/"+created["id"]).json()
    assert source["id"] in updated["result"]["unavailable_source_ids"]

def test_repeatable_evaluation(client, seeded):
    base=f"/api/workspaces/{seeded}"
    result=client.post(base+"/evaluations",json={})
    assert result.status_code==201,result.text
    scores=result.json()["scores"]
    assert scores["passed"]==scores["total"],scores
    assert scores["metrics"]["citation"] == 1
    assert scores["mrr_at_5"]>0
