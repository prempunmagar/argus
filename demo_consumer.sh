#!/bin/bash
# ============================================================
# Argus Demo — Consumer Flow (Shopping Agent)
# ============================================================
# Run this while the consumer dashboard is open:
#   Login: demo@argus.dev / argus2026
#
# Usage:  bash demo_consumer.sh
# ============================================================

API="https://34-16-41-18.sslip.io/api/v1"
CK="argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e"

echo ""
echo "=========================================="
echo "  ARGUS CONSUMER DEMO — Shopping Agent"
echo "=========================================="
echo ""
echo "Make sure the dashboard is open:"
echo "  https://argus-principia.vercel.app"
echo "  Login: demo@argus.dev / argus2026"
echo ""
read -p "Press ENTER when ready to start..."

# ── Transaction 1: Running shoes at $95, user said "under $80" → should be denied/flagged ──
echo ""
echo "------------------------------------------"
echo "[1/2] Firing: \$95 running shoes"
echo "       User budget: under \$80"
echo "       Expected: DENIED or FLAGGED"
echo "       (price exceeds user's stated budget)"
echo "------------------------------------------"

RESULT1=$(curl -s "$API/evaluate" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CK" \
  -d '{
    "product": {
      "product_name": "Nike Air Zoom Pegasus 41 Running Shoes",
      "price": 95.00,
      "currency": "USD",
      "merchant_name": "Nike",
      "merchant_url": "https://nike.com/checkout",
      "product_url": "https://nike.com/t/air-zoom-pegasus-41",
      "notes": "Mens running shoe, size 10. Neutral cushioning, daily trainer."
    },
    "chat_history": "User: Find me running shoes under $80. I just need something solid for daily runs.\nAgent: Searching for running shoes under $80... I found the Nike Air Zoom Pegasus 41 for $95 on nike.com. It is a top-rated daily trainer with excellent cushioning.\nUser: Okay sure, grab those.\nAgent: Submitting purchase request to Argus for authorization..."
  }')

DECISION1=$(echo "$RESULT1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null || echo "$RESULT1" | python -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null)
REASON1=$(echo "$RESULT1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ai_evaluation',{}).get('reasoning','')[:150])" 2>/dev/null || echo "$RESULT1" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('ai_evaluation',{}).get('reasoning','')[:150])" 2>/dev/null)
echo "  Result: $DECISION1"
echo "  AI says: $REASON1..."

echo ""
read -p "Press ENTER to fire the approved transaction..."

# ── Transaction 2: Cheaper shoes at $60, whitelisted merchant → auto-approved ──
echo ""
echo "------------------------------------------"
echo "[2/2] Firing: \$60 running shoes (cheaper option)"
echo "       Under \$80 auto-approve threshold"
echo "       Merchant: Amazon (whitelisted)"
echo "       Expected: AUTO-APPROVE + virtual card"
echo "------------------------------------------"

RESULT2=$(curl -s "$API/evaluate" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CK" \
  -d '{
    "product": {
      "product_name": "ASICS Gel-Contend 8 Running Shoes",
      "price": 59.95,
      "currency": "USD",
      "merchant_name": "Amazon",
      "merchant_url": "https://amazon.com/checkout",
      "product_url": "https://amazon.com/dp/B0BXYZ1234",
      "notes": "Mens running shoe, size 10. Gel cushioning, 4.5 stars, 12,000 reviews. Prime eligible."
    },
    "chat_history": "User: Find me running shoes under $80. I just need something solid for daily runs.\nAgent: The Nike option was denied by Argus — it exceeded your $80 budget. Let me find something cheaper.\nAgent: Found the ASICS Gel-Contend 8 on Amazon for $59.95. Highly rated daily trainer, Prime delivery.\nUser: Perfect, get those instead.\nAgent: Submitting purchase request to Argus for authorization..."
  }')

DECISION2=$(echo "$RESULT2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null || echo "$RESULT2" | python -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null)
REASON2=$(echo "$RESULT2" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ai_evaluation',{}).get('reasoning','')[:150])" 2>/dev/null || echo "$RESULT2" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('ai_evaluation',{}).get('reasoning','')[:150])" 2>/dev/null)
CARD=$(echo "$RESULT2" | python3 -c "import sys,json; vc=json.load(sys.stdin).get('virtual_card',{}); print(f\"****{vc.get('last_four','????')} | Limit: \${vc.get('spend_limit','?')} | Locked to: {vc.get('merchant_lock','?')} | Expires: {vc.get('expires_at','?')[:19]}\")" 2>/dev/null || echo "$RESULT2" | python -c "import sys,json; vc=json.load(sys.stdin).get('virtual_card',{}); print(f\"****{vc.get('last_four','????')} | Limit: \${vc.get('spend_limit','?')} | Locked to: {vc.get('merchant_lock','?')} | Expires: {vc.get('expires_at','?')[:19]}\")" 2>/dev/null)
echo "  Result: $DECISION2"
echo "  AI says: $REASON2..."
if [ "$DECISION2" = "APPROVE" ]; then
  echo ""
  echo "  Virtual Card Issued:"
  echo "  $CARD"
fi

echo ""
echo "=========================================="
echo "  DEMO COMPLETE"
echo "=========================================="
echo ""
echo "  Dashboard should show:"
echo "  - Transaction 1: Denied/flagged (over budget)"
echo "  - Transaction 2: Approved with virtual card"
echo "    (locked to Amazon, capped at purchase amount,"
echo "     expires in 30 minutes)"
echo ""
