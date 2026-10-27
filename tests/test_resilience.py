import threading
from dataclasses import replace
from decimal import Decimal
from unittest.mock import Mock
import pytest
from app.config import settings
from app.db import Run, transaction

def test_embedding_contract_rejects_bad_dimensions(monkeypatch):
    import app.retrieval as retrieval
    monkeypatch.setattr(retrieval,"settings",replace(settings,embedding_provider="ollama",dimensions=3))
    response=Mock()
    response.json.return_value={"embeddings":[[1.0,0.0,0.0]]}
    client=Mock()
    client.__enter__=Mock(return_value=client)
    client.__exit__=Mock(return_value=False)
    client.post.return_value=response
    monkeypatch.setattr(retrieval.httpx,"Client",Mock(return_value=client))
    assert retrieval.embed("A source passage")==[1,0,0]
    response.json.return_value={"embeddings":[[1.0,0.0]]}
    with pytest.raises(ValueError,match="dimensions"):
        retrieval.embed("A source passage")
    response.json.return_value={"embeddings":[[float("nan"),0,0]]}
    with pytest.raises(ValueError):
        retrieval.embed("A source passage")

def test_cancel_waits_for_active_node_then_resumes_once(client, seeded, monkeypatch):
    import app.research as research
    arrived=threading.Event()
    release=threading.Event()
    original=research.search
    calls=0
    def slow(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==1:
            arrived.set()
            assert release.wait(8)
        return original(*args,**kwargs)
    monkeypatch.setattr(research,"search",slow)
    with transaction() as db:
        run=Run(workspace_id=seeded,question="Filing deadline",mode="research",
            config={"provider":"extractive","model":"extractive"})
        db.add(run)
        db.flush()
        run_id=run.id
    thread=threading.Thread(target=research.execute_run,args=(run_id,))
    thread.start()
    assert arrived.wait(8)
    base=f"/api/workspaces/{seeded}/runs/{run_id}"
    try:
        assert client.post(base+"/cancel").status_code==200
        assert client.post(base+"/resume").status_code==409
    finally:
        release.set()
        thread.join(8)
    assert not thread.is_alive()
    assert client.get(base).json()["status"]=="cancelled"
    assert client.post(base+"/resume").status_code==200
    value=client.get(base).json()
    assert value["status"]=="completed",value
    assert sum(s["node"]=="planner" for s in value["steps"])==1
    research.execute_run(run_id)
    assert len(client.get(base).json()["steps"])==len(value["steps"])

def test_collections_and_source_comparison_are_permission_scoped(client, workspace):
    base=f"/api/workspaces/{workspace}"
    collection=client.post(base+"/collections",json={"name":"Research"}).json()
    first=client.post(base+"/documents",files={"file":("notes.txt",b"First finding.")}).json()
    document_id=first["id"]
    before=first["versions"][0]["id"]
    after=client.post(base+"/documents/"+document_id+"/versions",files={"file":("notes.txt",b"Second finding.")}).json()["versions"][0]["id"]
    assert client.patch(base+"/documents/"+document_id,json={"collection_id":collection["id"]}).status_code==200
    hits=client.get(base+"/search",params={"q":"finding","collection_id":collection["id"]}).json()
    assert len(hits)==1 and hits[0]["version_id"]==after
    compared=client.get(base+"/documents/"+document_id+"/compare",params={"before":before,"after":after})
    assert compared.status_code==200
    assert compared.json()["changed"]
    assert "-First finding." in compared.json()["diff"]
    assert "+Second finding." in compared.json()["diff"]
    wrong=client.patch(base+"/documents/"+document_id,json={"collection_id":"not-a-collection"})
    assert wrong.status_code==404

def test_analysis_replay_preserves_exact_total(client, seeded):
    base=f"/api/workspaces/{seeded}"
    dataset=next(d for d in client.get(base+"/datasets").json() if d["document_name"]=="christmas_gifts.xlsx")
    result=client.post(base+"/analyses",json={"version_id":dataset["version_id"],"operation":"aggregate","column":"Amount"}).json()
    replay=client.post(base+"/analyses/"+result["id"]+"/replay")
    assert replay.status_code==201
    assert replay.json()["id"]!=result["id"]
    assert Decimal(replay.json()["result"]["total"])==570
    assert replay.json()["provenance"]["operation_hash"]==result["provenance"]["operation_hash"]

def test_source_deletion_survives_object_store_outage(client, seeded, monkeypatch):
    from app.storage import storage
    from app.db import StorageDeletion, transaction
    from app.gc import retry_failed
    from sqlalchemy import select
    base=f"/api/workspaces/{seeded}"
    document=client.get(base+"/documents").json()[0]
    original=storage.delete
    def unavailable(key):
        raise ConnectionError("Synthetic storage outage")
    monkeypatch.setattr(storage,"delete",unavailable)
    response=client.delete(base+"/documents/"+document["id"])
    assert response.status_code==200
    assert client.get(base+"/documents/"+document["id"]).status_code==404
    with transaction() as db:
        assert db.scalars(select(StorageDeletion).where(StorageDeletion.status=="failed")).first()
    monkeypatch.setattr(storage,"delete",original)
    assert retry_failed()>=1
    with transaction() as db:
        assert not list(db.scalars(select(StorageDeletion).where(StorageDeletion.status!="completed")))
