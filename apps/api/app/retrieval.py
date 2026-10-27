import math
import re
from collections import Counter
import httpx
from sqlalchemy import func, select, text
from .config import settings
from .db import Chunk, Document, Version

STOP = set("a an the is are was were and or of for to in on my me what how do does can please with from this that it i".split())

def tokens(value):
    return [t for t in re.findall(r"\w+", value.lower()) if t not in STOP and len(t) > 1]

def embed(value):
    with httpx.Client(timeout=90) as client:
        if settings.embedding_provider == "ollama":
            response = client.post(settings.ollama + "/api/embed",
                json={"model": settings.embedding_model, "input": value[:8000]})
            response.raise_for_status()
            vector = response.json()["embeddings"][0]
        elif settings.embedding_provider == "openai":
            response = client.post(settings.openai_url + "/embeddings",
                headers={"Authorization": "Bearer " + settings.openai_key},
                json={"model": settings.embedding_model, "input": value[:8000]})
            response.raise_for_status()
            vector = response.json()["data"][0]["embedding"]
        else:
            return None
    if len(vector) != settings.dimensions or any(not math.isfinite(v) for v in vector):
        raise ValueError("Embedding dimensions or values do not match the configured model.")
    return vector

def search(db, workspace, query, limit=8, document_ids=None, collection_id=None, version_id=None):
    latest = select(Version.document_id, func.max(Version.number).label("number")).group_by(Version.document_id).subquery()
    statement = select(Chunk, Version, Document).join(Version, Chunk.version_id == Version.id).join(
        Document, Version.document_id == Document.id).where(Chunk.workspace_id == workspace,
        Document.workspace_id == workspace, Version.status == "ready")
    if version_id:
        statement = statement.where(Version.id == version_id)
    else:
        statement = statement.join(latest, (latest.c.document_id == Document.id) & (latest.c.number == Version.number))
    if document_ids is not None:
        statement = statement.where(Document.id.in_(document_ids))
    if collection_id:
        statement = statement.where(Document.collection_id == collection_id)
    entries = db.execute(statement.limit(20000)).all()
    terms = tokens(query)
    if not terms or not entries:
        return []
    # BM25 ranking is available in local mode; production uses PostgreSQL FTS as its lexical ranking.
    docs = [Counter(tokens(c.text)) for c, _, _ in entries]
    lengths = [sum(c.values()) for c in docs]
    average = sum(lengths) / max(len(lengths), 1) or 1
    frequencies = {t: sum(t in d for d in docs) for t in terms}
    lexical = {}
    for i, counts in enumerate(docs):
        score = 0
        for term in terms:
            tf = counts[term]
            idf = math.log(1 + (len(docs) - frequencies[term] + .5) / (frequencies[term] + .5))
            score += idf * tf * 2.2 / (tf + 1.2 * (.25 + .75 * lengths[i] / average)) if tf else 0
        lexical[entries[i][0].id] = score
    if db.bind.dialect.name == "postgresql":
        ids = [e[0].id for e in entries]
        rows = db.execute(text("""SELECT id, ts_rank_cd(to_tsvector('english', text),
            plainto_tsquery('english', :q)) AS rank FROM document_chunks
            WHERE workspace_id=:w AND id = ANY(:ids)"""), {"q": query, "w": workspace, "ids": ids})
        lexical = {r.id: float(r.rank) for r in rows}
    ranked_lexical = sorted((k for k in lexical if lexical[k] > 0), key=lexical.get, reverse=True)
    fused = {k: 1 / (60 + i + 1) for i, k in enumerate(ranked_lexical)}
    semantic = {}
    if settings.embedding_provider != "lexical":
        vector = embed(query)
        matching = [e for e in entries if e[0].embedding_model == settings.embedding_model and e[0].dimensions == len(vector)]
        if db.bind.dialect.name == "postgresql" and matching:
            rows = db.execute(text("""SELECT id, 1 - (vector_embedding <=> CAST(:v AS vector)) AS similarity
                FROM document_chunks WHERE workspace_id=:w AND id=ANY(:ids) AND vector_embedding IS NOT NULL
                ORDER BY vector_embedding <=> CAST(:v AS vector) LIMIT 100"""),
                {"v": str(vector), "w": workspace, "ids": [e[0].id for e in matching]})
            semantic = {r.id: float(r.similarity) for r in rows}
        else:
            for c, _, _ in matching:
                den = math.sqrt(sum(v*v for v in vector) * sum(v*v for v in c.embedding)) or 1
                semantic[c.id] = sum(a*b for a,b in zip(vector,c.embedding)) / den
        for i, k in enumerate(sorted(semantic, key=semantic.get, reverse=True)):
            if semantic[k] > .35:
                fused[k] = fused.get(k, 0) + 1 / (60 + i + 1)
    entries.sort(key=lambda e: fused.get(e[0].id, 0), reverse=True)
    result = []
    for c, v, d in entries:
        if c.id not in fused:
            continue
        result.append({"id": c.id, "document_id": d.id, "version_id": v.id, "version": v.number,
            "name": d.name, "type": d.type, "text": c.text, "location": c.location,
            "score": round(fused[c.id], 6), "lexical_score": round(lexical.get(c.id, 0), 4),
            "semantic_score": round(semantic[c.id], 4) if c.id in semantic else None,
            "strategy": "hybrid-rrf" if semantic else "keyword-bm25" if db.bind.dialect.name == "sqlite" else "postgres-fts"})
        if len(result) >= limit:
            break
    return result

def resolve(db, workspace, chunk_id):
    row = db.execute(select(Chunk, Version, Document).join(Version, Chunk.version_id == Version.id).join(
        Document, Version.document_id == Document.id).where(Chunk.id == chunk_id,
        Chunk.workspace_id == workspace, Document.workspace_id == workspace)).first()
    if not row:
        return None
    c, v, d = row
    return {"id": c.id, "document_id": d.id, "version_id": v.id, "version": v.number,
        "name": d.name, "type": d.type, "text": c.text, "location": c.location}
