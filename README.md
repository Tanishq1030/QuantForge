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

## Redis stream consumer (batch uploader) - conceptual

Use XADD to append messages.

Consumers use XREADGROUP to read and ACK messsages.

Batch; read N messages or up to T ms, then bulk insert into DB.

Use consumer groups for scaling and replay.

## Timescale schema example (Postgres SQL)
```sql
CREATE TABLE raw_trades (
    id BIGSERIAL PRIMARY KEY,
    exchange TEXT,
    symbol TEXT,
    price NUMERIC,
    size NUMERIC,
    side TEXT,
    ts TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload JSONB
);


SELECT create_hypertable('raw_trades', 'ts', chucnk_time_intervl => interval '1 day');


CREATE TABLE candles_1m (
    symbol TEXT,
    interval_start TIMESTAMPTZ,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume NUMERIC,
    trades_count INT,
    PRIMARY KEY (symbol, interval_start)
);
```

## Deployment notes

Start with docker-compose: FastAPI, Redis, TimescaleDB, simple poller.

Use persistent volumes for Timescale DB.

For prod: k8s with HPA (autoscale batch workers based on Redis queue depth), use node affinity for database pods.

## Operational checklist

Add liveness.readiness probes for pollers and batch workers.

Maintain SLAs for queue length and agregation lag.

Regu