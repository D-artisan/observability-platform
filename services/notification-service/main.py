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