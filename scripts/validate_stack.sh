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