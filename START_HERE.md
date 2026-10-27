# Start here — Insyvera

The local application is built. Open **http://127.0.0.1:5180** while the local services are running.

If they are stopped:

```powershell
cd C:\Users\PC\Projects\insyvera
.\infrastructure\scripts\start-dev.ps1
```

Create your own account, then choose **Explore demo sources**.

Try **Research → Deep investigation**:
> Compare my tax records, identify mismatches, and analyze Christmas gift spending.

You should see the EUR 500 tax mismatch, EUR 570 gift spending, EUR 70 budget overrun, charts, source/cell links, and a potential deadline conflict. Create a report, edit it, save a version, and export it.

**Verified:** 23 backend tests, 2 browser journeys, 5 evaluation cases, production build, lint, Compose configuration, and 0 frontend audit findings.

**Still to verify together:** the full Docker stack, real AI models/embeddings, infrastructure restore and production deployment. No cloud deployment was performed.

The default app works without an AI key through transparent extractive retrieval and deterministic calculations. Enable Ollama or a hosted provider when you want model-written synthesis.

Read [README](README.md) for setup and features, [implementation status](docs/IMPLEMENTATION_STATUS.md) for actual test evidence, and [operations](docs/OPERATIONS.md) for the remaining release gates.
