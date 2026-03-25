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