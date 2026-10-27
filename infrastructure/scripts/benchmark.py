"""Measured local API throughput with synthetic uploads; no external load targets."""
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
import httpx

def main():
    base = "http://127.0.0.1:8100"
    assert urlsplit(base).hostname in {"127.0.0.1", "localhost"}
    with httpx.Client(base_url=base, timeout=60) as client:
        email = f"benchmark-{time.time_ns()}@example.test"
        result = client.post("/api/auth/register", json={"email":email,"password":"Synthetic-load-12345","name":"Benchmark"})
        result.raise_for_status()
        workspace = client.get("/api/workspaces").json()[0]["id"]
        client.post(f"/api/workspaces/{workspace}/demo").raise_for_status()
        def query(_):
            started=time.perf_counter()
            response=client.get(f"/api/workspaces/{workspace}/search", params={"q":"filing deadline income"})
            response.raise_for_status()
            return (time.perf_counter()-started)*1000
        with ThreadPoolExecutor(max_workers=4) as pool:
            values=list(pool.map(query,range(40)))
        report={"requests":len(values),"concurrency":4,"p50_ms":statistics.median(values),
            "p95_ms":sorted(values)[int(len(values)*.95)-1],"max_ms":max(values),
            "workload":"seven synthetic sources; lexical retrieval","limit":"Not a capacity or production SLA measurement."}
        print(json.dumps(report,indent=2))
if __name__=="__main__":
    main()
