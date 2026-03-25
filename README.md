# Building a Production-Grade Observability Platform: LGTM Stack Project

## Complete Hands-On Guide for Building a Full Observability Stack

---

## Table of Contents

1. [Why This Project Exists](#1-why-this-project-exists)
2. [What You Will Build](#2-what-you-will-build)
3. [Understanding the Observability Stack](#3-understanding-the-observability-stack)
4. [Prerequisites and Environment Setup](#4-prerequisites-and-environment-setup)
5. [Part 1: Build the Microservices Application (Python)](#5-part-1-build-the-microservices-application)
6. [Part 2: Instrument with OpenTelemetry](#6-part-2-instrument-with-opentelemetry)
7. [Part 3: Deploy the LGTM Stack](#7-part-3-deploy-the-lgtm-stack)
8. [Part 4: Centralised Observability Configuration](#8-part-4-centralised-observability-configuration)
9. [Part 5: Dashboards, Alerts and Profiling](#9-part-5-dashboards-alerts-and-profiling)
10. [Part 6: ELK Stack Integration](#10-part-6-elk-stack-integration)
11. [Part 7: Cost Efficiency and Automation](#11-part-7-cost-efficiency-and-automation)
12. [Part 8: Deploy to Kubernetes (Kind)](#12-part-8-deploy-to-kubernetes-kind)
13. [Part 9: Push to GitHub and Document](#13-part-9-push-to-github-and-document)
14. [Teardown Commands](#14-teardown-commands)
15. [Glossary of Key Concepts](#15-glossary-of-key-concepts)

---

## 1. Project Goal

This project demonstrates building a production-grade observability platform covering:

| Skill Area | Where Covered |
|---|---|
| Software engineering in Python | Part 1 (three Python/FastAPI microservices) |
| LGTM stack (Loki, Grafana, Tempo, Mimir) | Part 3 |
| ELK stack (Elasticsearch, Logstash, Kibana) | Part 6 |
| OpenTelemetry instrumentation | Part 2 |
| Microservices understanding | Part 1 |
| Centralised observability configuration | Part 4 |
| Metrics, logs, traces, alerts, profiling | Parts 3, 5 |
| High-scale, mission-critical infrastructure | Parts 7, 8 |
| Automation, peer-reviewed code | Parts 7, 9 |
| Cost-efficiency | Part 7 |

---

## 2. What You Will Build

You will build a **mini payment transfer system** consisting of three Python/FastAPI microservices, fully instrumented with OpenTelemetry, feeding into the complete LGTM stack. The system simulates:

- A **Transfer API** (Python/FastAPI) that accepts money transfer requests
- A **Pricing Service** (Python/FastAPI) that calculates exchange rates and fees
- A **Notification Service** (Python/FastAPI) that sends transfer confirmations

All three services emit metrics, logs, and traces through a single OpenTelemetry Collector, which routes telemetry to:

- **Grafana Mimir** for metrics
- **Grafana Loki** for logs
- **Grafana Tempo** for traces
- **Grafana** for dashboards and visualisation
- **Elasticsearch + Kibana** (ELK) as a secondary log backend

```
                   +-----------------+
                   |  Transfer API   |  (Python/FastAPI)
                   |  :8080          |
                   +--------+--------+
                            |
              +-------------+-------------+
              |                           |
     +--------v--------+        +--------v--------+
     | Pricing Service |        | Notification Svc|
     | (Python/FastAPI) |        | (Python/FastAPI) |
     | :8081           |        | :8082           |
     +--------+--------+        +--------+--------+
              |                           |
              +-------------+-------------+
                            |
                   +--------v--------+
                   |   OTel Collector |
                   |   :4317 (gRPC)  |
                   |   :4318 (HTTP)  |
                   +--+-----+-----+--+
                      |     |     |
            +---------+  +--+--+  +---------+
            |            |     |            |
      +-----v-----+ +---v---+ +------v-----+ +-----v------+
      | Mimir      | | Loki  | | Tempo      | | Elastic    |
      | (metrics)  | | (logs)| | (traces)   | | (logs)     |
      | :9009      | | :3100 | | :3200      | | :9200      |
      +-----+------+ +---+---+ +------+-----+ +-----+------+
            |             |            |             |
            +------+------+------+-----+             |
                   |                           +-----v------+
              +----v----+                      | Kibana     |
              | Grafana |                      | :5601      |
              | :3000   |                      +------------+
              +---------+
```

---

## 3. Understanding the Observability Stack

### 3.1 The Three Pillars of Observability

**Observability** is the ability to understand a system's internal state by examining its external outputs. There are three pillars:

**Metrics** are numerical measurements collected over time. Examples: request count, error rate, response latency (p50, p95, p99), CPU usage. Metrics answer "Is something wrong?" They are cheap to store and fast to query, making them ideal for alerting and dashboards.

**Logs** are timestamped text records of discrete events. Examples: "Transfer T-12345 created for GBP 500 to EUR", "Exchange rate lookup failed: timeout after 3s". Logs answer "What happened?" They provide rich context but are expensive to store at scale.

**Traces** follow a single request as it travels through multiple services. A trace consists of spans, where each span represents one unit of work. Traces answer "Where is the bottleneck?"

### 3.2 LGTM Stack Components

| Component | Role | Port | What It Replaces |
|---|---|---|---|
| **Loki** | Log aggregation and storage | 3100 | Elasticsearch (for logs) |
| **Grafana** | Visualisation, dashboards, alerting | 3000 | Kibana |
| **Tempo** | Distributed trace storage | 3200 | Jaeger, Zipkin |
| **Mimir** | Long-term metrics storage | 9009 | Thanos, Cortex |

**Why Mimir over Thanos?** Mimir is Grafana Labs' horizontally scalable, highly available metrics backend. Compatible with Prometheus but designed for multi-tenant environments at scale.

### 3.3 OpenTelemetry (OTel)

OpenTelemetry is a vendor-neutral, open-source observability framework. It provides a single set of APIs, SDKs, and tools to instrument applications and collect telemetry data. The key insight: **instrument once, send anywhere**.

In this architecture, the **centralised OTel configuration** is owned by the platform team and used by all product services. Product engineers do not need to know which backend stores their data — they instrument with the OTel SDK, and the centralised configuration routes data.

**Key OTel concepts:**

- **SDK**: Language-specific libraries added to your application
- **Collector**: Standalone binary that receives, processes, and exports telemetry. Acts as a pipeline with receivers, processors, and exporters
- **Auto-instrumentation**: OTel can automatically instrument common libraries (HTTP clients, databases) without code changes
- **Context Propagation**: Automatically passes trace context between services via HTTP headers (W3C Trace Context standard)

### 3.4 ELK Stack

| Component | Role | Port |
|---|---|---|
| **Elasticsearch** | Search and analytics engine for logs | 9200 |
| **Logstash** | Log processing pipeline | 5044 |
| **Kibana** | Visualisation for Elasticsearch data | 5601 |

This project uses Elasticsearch alongside Loki to demonstrate both backends.

---

## 4. Prerequisites and Environment Setup

### 4.1 System Requirements

You are running **Windows with Ubuntu WSL2**. You need:

- **WSL2 with Ubuntu** (you already have this)
- **Docker Desktop** (you already have this, ensure WSL2 integration is enabled)
- **Python 3.10+** (for all three microservices)
- **Git** (for version control)
- **Kind** (Kubernetes in Docker, for Part 8)
- **kubectl** (Kubernetes CLI)
- **At least 8 GB RAM allocated to WSL2**

### 4.2 WSL2 Memory Configuration

Create or edit `C:\Users\<your-username>\.wslconfig`:

```ini
[wsl2]
memory=10GB
swap=4GB
processors=4
```

Restart WSL from PowerShell: `wsl --shutdown`

### 4.3 Install Dependencies in WSL2

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv

# Verify
python3 --version

# Install Kind
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.24.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify Docker
docker --version
docker compose version
```

### 4.4 Create the Project Structure

```bash
mkdir -p ~/observability-platform
cd ~/observability-platform

mkdir -p services/{shared,transfer-api,pricing-service,notification-service}
mkdir -p otel-config
mkdir -p lgtm/{mimir,loki,tempo,grafana/provisioning/{datasources,dashboards}}
mkdir -p elk
mkdir -p k8s/{base,observability}
mkdir -p dashboards
mkdir -p scripts

git init
```

---

## 5. Part 1: Build the Microservices Application

All three services are built with **Python 3.11 and FastAPI**. Each follows the same OTel instrumentation pattern, demonstrating a standardised and seamless observability experience.

### 5.1 Shared OTel Instrumentation Module

To avoid duplicating OTel setup code, we create a shared module — an internal library the platform team maintains and distributes to product teams.

Create `services/shared/otel_setup.py`:

```python
"""
Shared OpenTelemetry instrumentation setup.

Represents the "centralised observability configuration" from
the product service's perspective. The platform team distributes
this helper so product engineers get standardised instrumentation
out of the box.

Usage:
    from otel_setup import setup_otel, get_tracer, get_meter, get_logger
    setup_otel(service_name="my-service")
    tracer = get_tracer("my-service")
"""

import logging
import os

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource


def setup_otel(
    service_name: str,
    service_version: str = "1.0.0",
    environment: str = "development",
    collector_endpoint: str | None = None,
):
    """
    Initialise all three pillars of OpenTelemetry: traces, metrics, logs.

    Parameters
    ----------
    service_name : str
        Identifies this service in dashboards and traces.
    service_version : str
        Semantic version. Useful for tracking regressions after deploys.
    environment : str
        Deployment environment (development, staging, production).
    collector_endpoint : str or None
        OTel Collector gRPC endpoint. Defaults to OTEL_EXPORTER_OTLP_ENDPOINT
        env var, then http://otel-collector:4317.
    """
    endpoint = collector_endpoint or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317"
    )

    # Resource: describes the entity producing telemetry
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": environment,
    })

    # TRACES
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(trace_provider)

    # METRICS
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=True),
        export_interval_millis=15_000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # LOGS
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True))
    )
    set_logger_provider(logger_provider)
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)


def get_tracer(name: str) -> trace.Tracer:
    return trace.get_tracer(name)


def get_meter(name: str) -> metrics.Meter:
    return metrics.get_meter(name)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
```

Create `services/shared/requirements-common.txt`:

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
httpx==0.27.0
opentelemetry-api==1.24.0
opentelemetry-sdk==1.24.0
opentelemetry-instrumentation-fastapi==0.45b0
opentelemetry-instrumentation-httpx==0.45b0
opentelemetry-instrumentation-logging==0.45b0
opentelemetry-exporter-otlp-proto-grpc==1.24.0
prometheus-client==0.21.0
grpcio==1.62.1
```

**What each dependency does:**

- `fastapi`: Modern Python web framework with async support and automatic OpenAPI docs
- `uvicorn`: ASGI server that runs FastAPI
- `httpx`: Async HTTP client. OTel auto-instruments it so inter-service calls propagate trace context automatically
- `opentelemetry-instrumentation-fastapi`: Auto-instruments incoming HTTP requests
- `opentelemetry-instrumentation-httpx`: Auto-instruments outgoing HTTP calls (creates child spans, injects W3C headers)
- `opentelemetry-instrumentation-logging`: Injects trace_id and span_id into Python log records
- `opentelemetry-exporter-otlp-proto-grpc`: Sends telemetry to the OTel Collector over gRPC
- `prometheus-client`: Exposes /metrics in Prometheus format for the Collector to scrape

### 5.2 Transfer API

Create `services/transfer-api/main.py`:

```python
"""
Transfer API - Main entry point for money transfers.

Demonstrates:
- Structured logging with trace correlation
- Custom metrics (counters, histograms) via OTel AND Prometheus
- Distributed tracing across three services via httpx auto-instrumentation
- Health endpoint for Kubernetes probes
"""

import sys, os, time, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from otel_setup import setup_otel, get_tracer, get_meter, get_logger
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from prometheus_client import make_asgi_app, Counter, Histogram

# ---- OTel init ----
setup_otel(service_name="transfer-api", service_version="1.0.0")
tracer = get_tracer("transfer-api")
meter = get_meter("transfer-api")
log = get_logger("transfer-api")
HTTPXClientInstrumentor().instrument()
LoggingInstrumentor().instrument()

# ---- OTel custom metrics (push via OTLP) ----
otel_transfer_counter = meter.create_counter("transfers.total", description="Total transfers", unit="1")
otel_transfer_errors = meter.create_counter("transfers.errors", description="Failed transfers", unit="1")
otel_transfer_duration = meter.create_histogram("transfers.duration", description="Transfer duration", unit="ms")

# ---- Prometheus metrics (pull via /metrics scrape) ----
PROM_TOTAL = Counter("transfer_requests_total", "Total transfer requests", ["source_currency", "target_currency", "status"])
PROM_LATENCY = Histogram("transfer_request_duration_seconds", "Latency", ["source_currency", "target_currency"],
                         buckets=[0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0])

# ---- App ----
app = FastAPI(title="Transfer API", version="1.0.0")
FastAPIInstrumentor().instrument_app(app)
app.mount("/metrics", make_asgi_app())

PRICING_URL = os.getenv("PRICING_SERVICE_URL", "http://pricing-service:8081")
NOTIFICATION_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8082")


class TransferRequest(BaseModel):
    source_currency: str
    target_currency: str
    amount: float
    recipient_email: str


class TransferResponse(BaseModel):
    transfer_id: str
    status: str
    source_amount: float
    source_currency: str
    target_amount: float
    target_currency: str
    exchange_rate: float
    fee: float


@app.post("/api/v1/transfers", response_model=TransferResponse)
async def create_transfer(req: TransferRequest):
    start = time.time()
    tid = f"T-{uuid.uuid4().hex[:8].upper()}"

    log.info("Processing transfer: id=%s source=%s target=%s amount=%.2f",
             tid, req.source_currency, req.target_currency, req.amount)

    with tracer.start_as_current_span("process_transfer") as span:
        span.set_attribute("transfer.id", tid)
        span.set_attribute("transfer.source_currency", req.source_currency)
        span.set_attribute("transfer.target_currency", req.target_currency)
        span.set_attribute("transfer.amount", req.amount)

        try:
            # Step 1: Get pricing
            async with httpx.AsyncClient(timeout=10.0) as client:
                pr = await client.get(f"{PRICING_URL}/api/v1/pricing",
                    params={"source": req.source_currency, "target": req.target_currency, "amount": req.amount})
                pr.raise_for_status()
                pricing = pr.json()

            log.info("Pricing received: tid=%s rate=%.4f fee=%.2f converted=%.2f",
                     tid, pricing["exchange_rate"], pricing["fee"], pricing["converted_amount"])

            # Step 2: Send notification
            async with httpx.AsyncClient(timeout=10.0) as client:
                nr = await client.post(f"{NOTIFICATION_URL}/api/v1/notify",
                    json={"transfer_id": tid, "recipient_email": req.recipient_email,
                          "amount": pricing["converted_amount"], "currency": req.target_currency})
                nr.raise_for_status()

            log.info("Transfer completed: %s", tid)

            dur_ms = (time.time() - start) * 1000
            otel_transfer_counter.add(1, {"source": req.source_currency, "target": req.target_currency})
            otel_transfer_duration.record(dur_ms, {"source": req.source_currency, "target": req.target_currency})
            PROM_TOTAL.labels(req.source_currency, req.target_currency, "success").inc()
            PROM_LATENCY.labels(req.source_currency, req.target_currency).observe(time.time() - start)

            return TransferResponse(transfer_id=tid, status="PROCESSING", source_amount=req.amount,
                source_currency=req.source_currency, target_amount=pricing["converted_amount"],
                target_currency=req.target_currency, exchange_rate=pricing["exchange_rate"], fee=pricing["fee"])

        except httpx.HTTPStatusError as e:
            otel_transfer_errors.add(1, {"error_type": "http_error"})
            PROM_TOTAL.labels(req.source_currency, req.target_currency, "error").inc()
            log.error("Transfer failed (HTTP): tid=%s status=%d", tid, e.response.status_code)
            span.set_attribute("error", True)
            raise HTTPException(status_code=502, detail=f"Downstream error: {e}")

        except Exception as e:
            otel_transfer_errors.add(1, {"error_type": "internal"})
            PROM_TOTAL.labels(req.source_currency, req.target_currency, "error").inc()
            log.error("Transfer failed: tid=%s error=%s", tid, str(e), exc_info=True)
            span.set_attribute("error", True)
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health():
    return {"status": "UP", "service": "transfer-api"}
```

Create `services/transfer-api/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY shared /app/shared
COPY transfer-api/main.py .
RUN pip install --no-cache-dir -r shared/requirements-common.txt
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--log-level", "info"]
```

### 5.3 Pricing Service

Create `services/pricing-service/main.py`:

```python
"""
Pricing Service - Calculates exchange rates and fees.

Demonstrates custom spans, structured logging, and simulated latency.
"""

import sys, os, random, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))

from fastapi import FastAPI, Query, HTTPException
from otel_setup import setup_otel, get_tracer, get_meter, get_logger
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from prometheus_client import make_asgi_app, Counter, Histogram

setup_otel(service_name="pricing-service", service_version="1.0.0")
tracer = get_tracer("pricing-service")
meter = get_meter("pricing-service")
log = get_logger("pricing-service")
LoggingInstrumentor().instrument()

otel_pricing_reqs = meter.create_counter("pricing.requests.total", description="Pricing requests", unit="1")
PROM_PRICING = Counter("pricing_requests_total", "Pricing requests", ["currency_pair", "status"])
PROM_PRICING_LAT = Histogram("pricing_duration_seconds", "Pricing latency", ["currency_pair"],
                              buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25])

app = FastAPI(title="Pricing Service", version="1.0.0")
FastAPIInstrumentor().instrument_app(app)
app.mount("/metrics", make_asgi_app())

EXCHANGE_RATES = {
    ("GBP", "EUR"): 1.17, ("GBP", "USD"): 1.27,
    ("EUR", "GBP"): 0.85, ("EUR", "USD"): 1.09,
    ("USD", "GBP"): 0.79, ("USD", "EUR"): 0.92,
}
FEE_RATES = {
    ("GBP", "EUR"): 0.0035, ("GBP", "USD"): 0.0040,
    ("EUR", "GBP"): 0.0038, ("EUR", "USD"): 0.0036,
    ("USD", "GBP"): 0.0042, ("USD", "EUR"): 0.0039,
}


@app.get("/api/v1/pricing")
async def get_pricing(
    source: str = Query(...), target: str = Query(...), amount: float = Query(..., gt=0),
):
    start = time.time()
    pair = (source.upper(), target.upper())
    pair_label = f"{source.upper()}_{target.upper()}"

    with tracer.start_as_current_span("calculate_pricing") as span:
        span.set_attribute("pricing.source_currency", source)
        span.set_attribute("pricing.target_currency", target)
        span.set_attribute("pricing.amount", amount)

        time.sleep(random.uniform(0.01, 0.05))  # Simulate latency

        if pair not in EXCHANGE_RATES:
            log.warning("Unsupported currency pair: %s -> %s", source, target)
            PROM_PRICING.labels(pair_label, "error").inc()
            raise HTTPException(status_code=400, detail=f"Unsupported pair: {source} -> {target}")

        rate = EXCHANGE_RATES[pair]
        fee = round(amount * FEE_RATES.get(pair, 0.004), 2)
        converted = round((amount - fee) * rate, 2)

        log.info("Pricing: pair=%s/%s amount=%.2f rate=%.4f fee=%.2f converted=%.2f",
                 source, target, amount, rate, fee, converted)

        otel_pricing_reqs.add(1, {"currency_pair": pair_label})
        PROM_PRICING.labels(pair_label, "success").inc()
        PROM_PRICING_LAT.labels(pair_label).observe(time.time() - start)

        span.set_attribute("pricing.exchange_rate", rate)
        span.set_attribute("pricing.fee", fee)
        return {"exchange_rate": rate, "fee": fee, "converted_amount": converted}


@app.get("/health")
async def health():
    return {"status": "UP", "service": "pricing-service"}
```

Create `services/pricing-service/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY shared /app/shared
COPY pricing-service/main.py .
RUN pip install --no-cache-dir -r shared/requirements-common.txt
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"
EXPOSE 8081
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081", "--log-level", "info"]
```

### 5.4 Notification Service

Create `services/notification-service/main.py`:

```python
"""
Notification Service - Sends transfer confirmations.

Introduces a 10% failure rate to demonstrate error tracking
in traces (Tempo), logs (Loki), and metrics (Mimir/Grafana).
"""

import sys, os, random, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))

from fastapi import FastAPI, Request
from otel_setup import setup_otel, get_tracer, get_meter, get_logger
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from prometheus_client import make_asgi_app, Counter

setup_otel(service_name="notification-service", service_version="1.0.0")
tracer = get_tracer("notification-service")
meter = get_meter("notification-service")
log = get_logger("notification-service")
LoggingInstrumentor().instrument()

otel_notif_ok = meter.create_counter("notifications.total", description="Notifications sent", unit="1")
otel_notif_err = meter.create_counter("notifications.errors", description="Notification failures", unit="1")
PROM_NOTIF = Counter("notification_requests_total", "Notification requests", ["channel", "status"])

app = FastAPI(title="Notification Service", version="1.0.0")
FastAPIInstrumentor().instrument_app(app)
app.mount("/metrics", make_asgi_app())


@app.post("/api/v1/notify")
async def send_notification(request: Request):
    body = await request.json()
    tid = body.get("transfer_id", "unknown")
    recipient = body.get("recipient_email", "unknown")
    amount = body.get("amount", 0)
    currency = body.get("currency", "???")

    with tracer.start_as_current_span("send_email_notification") as span:
        span.set_attribute("notification.transfer_id", tid)
        span.set_attribute("notification.recipient", recipient)
        span.set_attribute("notification.channel", "email")

        time.sleep(random.uniform(0.02, 0.08))  # Simulate email sending

        # 10% failure rate
        if random.random() < 0.10:
            error_msg = f"Email provider timeout for transfer {tid}"
            log.error("Notification failed: tid=%s recipient=%s error=%s", tid, recipient, error_msg)
            span.set_attribute("error", True)
            otel_notif_err.add(1, {"channel": "email"})
            PROM_NOTIF.labels("email", "error").inc()
            return {"status": "FAILED", "error": error_msg}

        log.info("Notification sent: tid=%s recipient=%s amount=%.2f %s", tid, recipient, amount, currency)
        otel_notif_ok.add(1, {"channel": "email"})
        PROM_NOTIF.labels("email", "success").inc()
        return {"status": "SENT", "transfer_id": tid}


@app.get("/health")
async def health():
    return {"status": "UP", "service": "notification-service"}
```

Create `services/notification-service/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY shared /app/shared
COPY notification-service/main.py .
RUN pip install --no-cache-dir -r shared/requirements-common.txt
ENV PYTHONPATH="/app/shared:${PYTHONPATH}"
EXPOSE 8082
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082", "--log-level", "info"]
```

---

## 6. Part 2: Instrument with OpenTelemetry

### 6.1 The OTel Collector Configuration

Create `otel-config/otel-collector-config.yaml`:

```yaml
# ============================================================================
# OpenTelemetry Collector - Centralised Observability Configuration
# ============================================================================
# Version-controlled, peer-reviewed, deployed programmatically.
# ============================================================================

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"

  prometheus:
    config:
      scrape_configs:
        - job_name: "transfer-api"
          scrape_interval: 15s
          static_configs:
            - targets: ["transfer-api:8080"]
          metrics_path: "/metrics"
        - job_name: "pricing-service"
          scrape_interval: 15s
          static_configs:
            - targets: ["pricing-service:8081"]
          metrics_path: "/metrics"
        - job_name: "notification-service"
          scrape_interval: 15s
          static_configs:
            - targets: ["notification-service:8082"]
          metrics_path: "/metrics"

processors:
  batch:
    timeout: 5s
    send_batch_size: 1024
    send_batch_max_size: 2048
  resource:
    attributes:
      - key: "environment"
        value: "development"
        action: upsert
      - key: "team"
        value: "observability"
        action: upsert
  memory_limiter:
    check_interval: 5s
    limit_mib: 512
    spike_limit_mib: 128

exporters:
  prometheusremotewrite:
    endpoint: "http://mimir:9009/api/v1/push"
    tls:
      insecure: true
  loki:
    endpoint: "http://loki:3100/loki/api/v1/push"
  otlp/tempo:
    endpoint: "http://tempo:4317"
    tls:
      insecure: true
  elasticsearch:
    endpoints: ["http://elasticsearch:9200"]
    logs_index: "otel-logs"
    sending_queue:
      enabled: true
      num_consumers: 2
      queue_size: 1000
  debug:
    verbosity: basic

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [otlp/tempo, debug]
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, resource, batch]
      exporters: [prometheusremotewrite, debug]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [loki, elasticsearch, debug]
  telemetry:
    logs:
      level: info
    metrics:
      address: ":8888"
```

---

## 7. Part 3: Deploy the LGTM Stack

### 7.1 Mimir Configuration

Create `lgtm/mimir/mimir-config.yaml`:

```yaml
multitenancy_enabled: false
blocks_storage:
  backend: filesystem
  filesystem:
    dir: /data/mimir/blocks
  tsdb:
    dir: /data/mimir/tsdb
compactor:
  data_dir: /data/mimir/compactor
  sharding_ring:
    kvstore:
      store: memberlist
distributor:
  ring:
    kvstore:
      store: memberlist
ingester:
  ring:
    kvstore:
      store: memberlist
    replication_factor: 1
ruler_storage:
  backend: filesystem
  filesystem:
    dir: /data/mimir/rules
server:
  http_listen_port: 9009
  log_level: warn
store_gateway:
  sharding_ring:
    replication_factor: 1
```

### 7.2 Loki Configuration

Create `lgtm/loki/loki-config.yaml`:

```yaml
auth_enabled: false
server:
  http_listen_port: 3100
common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory
schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h
limits_config:
  allow_structured_metadata: true
  volume_enabled: true
```

### 7.3 Tempo Configuration

Create `lgtm/tempo/tempo-config.yaml`:

```yaml
server:
  http_listen_port: 3200
distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal
metrics_generator:
  registry:
    external_labels:
      source: tempo
      cluster: docker-compose
  storage:
    path: /var/tempo/generator/wal
    remote_write:
      - url: http://mimir:9009/api/v1/push
        send_exemplars: true
overrides:
  defaults:
    metrics_generator:
      processors: [service-graphs, span-metrics]
```

### 7.4 Grafana Datasources

Create `lgtm/grafana/provisioning/datasources/datasources.yaml`:

```yaml
apiVersion: 1
datasources:
  - name: Mimir
    type: prometheus
    access: proxy
    url: http://mimir:9009/prometheus
    isDefault: true
    jsonData:
      httpMethod: POST
      prometheusType: Mimir
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"
  - name: Tempo
    type: tempo
    access: proxy
    uid: tempo
    url: http://tempo:3200
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki
        filterByTraceID: true
      tracesToMetrics:
        datasourceUid: mimir
      nodeGraph:
        enabled: true
      serviceMap:
        datasourceUid: mimir
  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: http://elasticsearch:9200
    jsonData:
      index: "otel-logs"
      timeField: "@timestamp"
      logMessageField: body
```

---

## 8. Part 4: Centralised Observability Configuration

### 8.1 Docker Compose

Create `docker-compose.yml`:

```yaml
version: "3.9"

services:
  transfer-api:
    build:
      context: ./services
      dockerfile: transfer-api/Dockerfile
    ports: ["8080:8080"]
    environment:
      - PRICING_SERVICE_URL=http://pricing-service:8081
      - NOTIFICATION_SERVICE_URL=http://notification-service:8082
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
    depends_on: [otel-collector, pricing-service, notification-service]
    networks: [observability]

  pricing-service:
    build:
      context: ./services
      dockerfile: pricing-service/Dockerfile
    ports: ["8081:8081"]
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
    depends_on: [otel-collector]
    networks: [observability]

  notification-service:
    build:
      context: ./services
      dockerfile: notification-service/Dockerfile
    ports: ["8082:8082"]
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
    depends_on: [otel-collector]
    networks: [observability]

  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.100.0
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-config/otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports: ["4317:4317", "4318:4318", "8888:8888"]
    depends_on: [mimir, loki, tempo, elasticsearch]
    networks: [observability]

  mimir:
    image: grafana/mimir:2.12.0
    command: ["-config.file=/etc/mimir/mimir-config.yaml"]
    volumes:
      - ./lgtm/mimir/mimir-config.yaml:/etc/mimir/mimir-config.yaml
      - mimir-data:/data/mimir
    ports: ["9009:9009"]
    networks: [observability]

  loki:
    image: grafana/loki:3.0.0
    command: ["-config.file=/etc/loki/loki-config.yaml"]
    volumes:
      - ./lgtm/loki/loki-config.yaml:/etc/loki/loki-config.yaml
      - loki-data:/loki
    ports: ["3100:3100"]
    networks: [observability]

  tempo:
    image: grafana/tempo:2.4.1
    command: ["-config.file=/etc/tempo/tempo-config.yaml"]
    volumes:
      - ./lgtm/tempo/tempo-config.yaml:/etc/tempo/tempo-config.yaml
      - tempo-data:/var/tempo
    ports: ["3200:3200"]
    networks: [observability]

  grafana:
    image: grafana/grafana:10.4.2
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
    volumes:
      - ./lgtm/grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    ports: ["3000:3000"]
    depends_on: [mimir, loki, tempo]
    networks: [observability]

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes: [es-data:/usr/share/elasticsearch/data]
    ports: ["9200:9200"]
    networks: [observability]

  kibana:
    image: docker.elastic.co/kibana/kibana:8.13.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports: ["5601:5601"]
    depends_on: [elasticsearch]
    networks: [observability]

networks:
  observability:
    driver: bridge

volumes:
  mimir-data:
  loki-data:
  tempo-data:
  grafana-data:
  es-data:
```

### 8.2 Build and Start

```bash
cd ~/observability-platform
docker compose up --build -d
docker compose logs -f otel-collector
```

Wait ~60 seconds, then verify endpoints:

| Service | URL |
|---|---|
| Grafana | http://localhost:3000 (admin/admin) |
| Transfer API | http://localhost:8080/api/v1/health |
| Pricing | http://localhost:8081/health |
| Notification | http://localhost:8082/health |
| Kibana | http://localhost:5601 |

### 8.3 Generate Traffic

Create `scripts/generate_traffic.sh`:

```bash
#!/bin/bash
CURRENCIES=("GBP" "EUR" "USD")
AMOUNTS=(100 250 500 750 1000 2500 5000)
EMAILS=("user1@example.com" "user2@example.com" "user3@example.com")

echo "Generating traffic... Ctrl+C to stop."
while true; do
    SRC=${CURRENCIES[$RANDOM % ${#CURRENCIES[@]}]}
    TGT=${CURRENCIES[$RANDOM % ${#CURRENCIES[@]}]}
    while [ "$SRC" = "$TGT" ]; do TGT=${CURRENCIES[$RANDOM % ${#CURRENCIES[@]}]}; done
    AMT=${AMOUNTS[$RANDOM % ${#AMOUNTS[@]}]}
    EMAIL=${EMAILS[$RANDOM % ${#EMAILS[@]}]}

    curl -s -X POST http://localhost:8080/api/v1/transfers \
      -H "Content-Type: application/json" \
      -d "{\"source_currency\":\"$SRC\",\"target_currency\":\"$TGT\",\"amount\":$AMT,\"recipient_email\":\"$EMAIL\"}" \
      | python3 -m json.tool 2>/dev/null || echo "(sent)"
    sleep $(python3 -c "import random; print(f'{random.uniform(0.5, 2.0):.2f}')")
done
```

```bash
chmod +x scripts/generate_traffic.sh
./scripts/generate_traffic.sh
```

---

## 9. Part 5: Dashboards, Alerts and Profiling

### 9.1 Exploring in Grafana

Open http://localhost:3000 (admin/admin).

**Metrics (Mimir):** Explore > Mimir datasource
- `rate(transfer_requests_total[5m])` -- Request rate
- `histogram_quantile(0.95, rate(transfer_request_duration_seconds_bucket[5m]))` -- p95 latency
- `sum(rate(transfer_requests_total{status="error"}[5m])) / sum(rate(transfer_requests_total[5m]))` -- Error rate

**Logs (Loki):** Explore > Loki datasource
- `{service_name="pricing-service"} |= "Pricing"`
- `{service_name="notification-service"} |= "error"`

**Traces (Tempo):** Explore > Tempo datasource
- Search by service "transfer-api" to see full waterfall across all three services

### 9.2 Alert Rules

Create `lgtm/mimir/alert-rules.yaml`:

```yaml
groups:
  - name: transfer-slos
    rules:
      - alert: HighTransferErrorRate
        expr: |
          sum(rate(transfer_requests_total{status="error"}[5m]))
          / sum(rate(transfer_requests_total[5m])) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Transfer error rate > 5%"
      - alert: HighTransferLatency
        expr: |
          histogram_quantile(0.95, rate(transfer_request_duration_seconds_bucket[5m])) > 2
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "p95 latency > 2s"
```

---

## 10. Part 6: ELK Stack Integration

```bash
# Verify Elasticsearch receives logs
curl -s http://localhost:9200/otel-logs/_count | python3 -m json.tool
```

Configure Kibana at http://localhost:5601: Stack Management > Data Views > create `otel-logs*` with `@timestamp`.

**Key trade-off:** Elasticsearch indexes all fields (powerful search, expensive storage). Loki indexes only labels (cheap, less flexible). This project uses both to demonstrate the difference.

---

## 11. Part 7: Cost Efficiency and Automation

**Cost strategies in this project:**
1. **Loki as primary log backend** (label-indexed, cheap)
2. **Batch processing** reduces network overhead
3. **Memory limiter** prevents OOM under load spikes
4. **Sampling** (add `probabilistic_sampler` processor for 25% trace retention)

Create `scripts/validate_stack.sh`:

```bash
#!/bin/bash
echo "=== Health Check ==="
for svc in "Transfer API:http://localhost:8080/api/v1/health" \
           "Pricing:http://localhost:8081/health" \
           "Notification:http://localhost:8082/health" \
           "Grafana:http://localhost:3000/api/health" \
           "Mimir:http://localhost:9009/ready" \
           "Loki:http://localhost:3100/ready" \
           "Tempo:http://localhost:3200/ready" \
           "Elasticsearch:http://localhost:9200/_cluster/health" \
           "OTel Collector:http://localhost:8888/metrics"; do
    IFS=: read -r name url <<< "$svc"
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    [ "$code" = "200" ] && echo "[OK]   $name" || echo "[FAIL] $name (HTTP $code)"
done
```

---

## 12. Part 8: Deploy to Kubernetes (Kind)

```bash
# Create cluster
cat <<EOF | kind create cluster --name observability-platform --config -
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
EOF

# Apply namespace
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/observability/
```

See k8s/ directory for full manifests (same pattern as Docker Compose but with Deployments, Services, and ConfigMaps).

---

## 13. Part 9: Push to GitHub

```bash
cd ~/observability-platform
git add -A
git commit -m "feat: LGTM observability platform (Python/FastAPI)"
git branch -M main
git remote add origin https://github.com/<your-username>/observability-platform.git
git push -u origin main
```

---

## 14. Teardown Commands

```bash
docker compose down -v
kind delete cluster --name observability-platform
docker image prune -a  # optional
rm -rf ~/observability-platform  # optional
```

---

## 15. Glossary

**Batch Processor:** Groups telemetry before export. Reduces network overhead.
**Context Propagation:** Passes trace ID between services via W3C traceparent headers.
**Exemplar:** A trace linked to a metric data point. Click a latency spike to see the trace.
**LGTM:** Loki + Grafana + Tempo + Mimir. A modern production observability stack.
**LogQL:** Loki query language. Example: `{service_name="transfer-api"} |= "error"`
**Mimir:** Horizontally scalable Prometheus-compatible metrics store.
**OTLP:** OpenTelemetry Protocol. gRPC (4317) or HTTP (4318).
**PromQL:** Prometheus Query Language for Mimir. `rate()`, `histogram_quantile()`, `sum by()`.
**Resource:** OTel concept. Attributes (service.name, version, environment) on all telemetry.
**SLI/SLO:** Service Level Indicator/Objective. Histogram metrics enable SLI calculation.
**Span:** A unit of work in a trace. Has name, duration, attributes, parent.
**Trace:** Collection of spans across services sharing a trace ID.
