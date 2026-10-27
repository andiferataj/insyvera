import os
import tempfile
from pathlib import Path
import pytest

scratch = Path(__file__).resolve().parents[1] / ".local" / "tests"
scratch.mkdir(parents=True, exist_ok=True)
test_root = Path(tempfile.mkdtemp(prefix="run-", dir=scratch))
os.environ["DATA_DIR"] = str(test_root)
os.environ["DATABASE_URL"] = "sqlite:///" + (test_root / "test.db").as_posix()
os.environ["TASK_ALWAYS_EAGER"] = "true"
os.environ["MODEL_PROVIDER"] = "extractive"
os.environ["EMBEDDING_PROVIDER"] = "lexical"
os.environ["REDIS_URL"] = ""
os.environ["STORAGE_BACKEND"] = "local"
from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine
from app.security import limiter

@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    limiter.entries.clear()
    with TestClient(app) as client:
        yield client

@pytest.fixture
def workspace(client):
    response = client.post("/api/auth/register", json={"email":"andi@example.test","name":"Andi","password":"correct-horse-123"})
    assert response.status_code == 201, response.text
    return client.get("/api/workspaces").json()[0]["id"]

@pytest.fixture
def seeded(client, workspace):
    result = client.post(f"/api/workspaces/{workspace}/demo")
    assert result.status_code == 200, result.text
    return workspace
