from alembic import context
from sqlalchemy import create_engine
from app.config import settings
from app.db import Base

config = context.config
target_metadata = Base.metadata

def offline():
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def online():
    engine = create_engine(settings.database_url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

offline() if context.is_offline_mode() else online()
