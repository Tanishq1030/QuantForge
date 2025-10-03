# QuantForge

## Project Summary

This repo contains the trading-data pipeline: WebSocket ingestion, real-time pub/sub for charts, batch uploader to TimeScaleDB, and API server for frontend consumption.

## Recommended tech stack (opinionated)

Ingestion & API: Python + FastAPI (async), or Go for lower latency.

Real-time distribution: Redis Streams for v1; kafka for v2.

WS server: FastAPI (uvicorn + websockets) or a specialized Node.js cluster (socket.io / ws) if many browser clients.

Time-series DB: TimescaleDB (on PostgreSQL) for ACID + time-series functions. Alternative:
ClickHouse for heavy analytics.

Containerization: Docker + docker-compose for dev; Kubernetes for prod.

Monitoring: Prometheus + Grafana. Traces: Jaeger.

## Repo layout
/backend
  /ingestion
    poller.py
    normalizer.py
  /api
    main.py                # FastAPI app
    routes/
    services/
  /batch
    consumer.py
    uploader.py
  /workers
    aggregator.py          # cron/continuous aggregator
  /utils
    redis_client.py
    db.py
/docker
  docker-compose.yml
/k8s
  deployment.yaml
/docs
  architecture.md
  runbook.md

## FastAPI skeleton (example)
```python
# backend/api/main.py
from fastapi import FastAPI, Query
from pydantic import BaseModel


app = FastAPI()


class CandleQuery(BaseModel):
    symbol: str
    interval: str
    _from: str | None = None
    to: str | None = None

@app.get('/candles')
async def get_condles(symbol: str = Query(...), interval: str = Query('1m'), from_ts: str |None = None, to_ts: str | None = None):
    # 1) validate interval
    # 2) check cache (Redis)
    # 3) fallback to TimeScaleDB query
    return {"symbol": symbol, "interval": interval, "candles": []}


@app.post('/trade')
async def post_trade(payload: dict):
    # verify JWT
    # write to transactional DB
    return {"status": "ok"}
```

## Redis stream consumer 