"""Initial application schema with permission-scoped chunks and durable artifacts."""
from alembic import op
from app.db import Base
from app.config import settings

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute(f"ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS vector_embedding vector({settings.dimensions})")
        if settings.dimensions <= 2000:
            op.execute("CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON document_chunks USING hnsw (vector_embedding vector_cosine_ops)")
        op.execute("CREATE INDEX IF NOT EXISTS chunks_fts ON document_chunks USING gin(to_tsvector('english', text))")

def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
