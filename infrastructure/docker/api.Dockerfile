FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/apps/api DATA_DIR=/app/data
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
RUN groupadd --gid 10001 insyvera && useradd --uid 10001 --gid 10001 --no-create-home insyvera
COPY apps/api ./apps/api
COPY datasets ./datasets
COPY infrastructure/scripts ./infrastructure/scripts
RUN mkdir -p /app/data && chown -R 10001:10001 /app/data
USER 10001:10001
EXPOSE 8100
CMD ["sh","-c","python -m alembic -c apps/api/alembic.ini upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8100"]
