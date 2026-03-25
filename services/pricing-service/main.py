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