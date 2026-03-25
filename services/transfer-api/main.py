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