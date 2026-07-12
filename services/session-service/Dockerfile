FROM python:3.12-slim AS builder

WORKDIR /app
COPY services/session-service/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

WORKDIR /app
COPY --from=builder /install /usr/local
COPY shared/ /app/shared/
COPY services/session-service/app/ /app/app/

ENV PYTHONPATH=/app
EXPOSE 8003

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
