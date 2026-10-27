# Allowlisted analysis executor

The API accepts operation definitions, never Python source. The actual runner uses Python isolated mode, bounded JSON input/output, wall/CPU/memory limits (CPU/memory limits apply on Linux), a temporary working directory, no inherited application credentials, and no dynamic code evaluation.

The application worker executes only this reviewed local program. It is not an arbitrary-code sandbox. Network isolation is structural because no supported operation imports or invokes network code; the subprocess itself is not an operating-system network jail.

For an additional container boundary, build this image and run:
```powershell
docker build -f apps/sandbox/Dockerfile -t insyvera-sandbox .
'{"operation":"aggregate","column":"x","rows":[{"x":"0.1"},{"x":"0.2"}]}' | docker run --rm -i --network none --read-only --cap-drop ALL --security-opt no-new-privileges --memory 512m --cpus 1 --pids-limit 32 insyvera-sandbox
```
No Docker socket is mounted in the API or worker. Arbitrary generated Python is intentionally unsupported.
