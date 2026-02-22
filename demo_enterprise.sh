#!/bin/bash
# ============================================================
# Argus Demo — Enterprise Flow (Refund Agent)
# ============================================================
# Run this while the enterprise dashboard is open:
#   Login: enterprise@argus.dev / argus2026
#
# Usage:  bash demo_enterprise.sh
# ============================================================

API="https://34-16-41-18.sslip.io/api/v1"
CK="argus_ck_ent_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"

echo ""
echo "=========================================="
echo "  ARGUS ENTERPRISE DEMO — Refund Agent"
echo "=========================================="
echo ""
echo "Make sure the dashboard is open:"
echo "  https://argus-principia.vercel.app"
echo "  Login: enterprise@argus.dev / argus2026"
echo ""
read -p "Press ENTER when ready to start..."

# ── Transaction 1: Small refund, auto-approved ──────────────
echo ""
echo "------------------------------------------"
echo "[1/3] Firing: \$45 damaged product refund"
echo "       Expected: AUTO-APPROVE"
echo "------------------------------------------"

RESULT1=$(curl -s "$API/evaluate" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CK" \
  -d '{
    "product": {
      "product_name": "Refund — Damaged Bluetooth Speaker (Order #ACM-50921)",
      "price": 45.00,
      "currency": "USD",
      "merchant_name": "Acme Corp Refunds",
      "merchant_url": "https://internal.acmecorp.com/refunds",
      "notes": "Customer reported cracked speaker grille on delivery. Photos attached and verified by agent."
    },
    "chat_history": "Customer: Hi, I received my Bluetooth speaker today but the grille is cracked. It looks like shipping damage.\nAgent: I can see the photos you uploaded. The damage is clearly visible. Let me process a refund for the full amount of $45.\nCustomer: Thank you, I appreciate the quick help."
  }')

DECISION1=$(echo "$RESULT1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null || echo "$RESULT1" | python -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null)
echo "  Result: $DECISION1"

echo ""
read -p "Press ENTER to fire next transaction..."

# ── Transaction 2: Medium goodwill credit, auto-approved ────
echo ""
echo "------------------------------------------"
echo "[2/3] Firing: \$30 goodwill credit (late delivery)"
echo "       Expected: AUTO-APPROVE"
echo "------------------------------------------"

RESULT2=$(curl -s "$API/evaluate" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CK" \
  -d '{
    "product": {
      "product_name": "Goodwill Credit — Delayed Shipment (Order #ACM-52104)",
      "price": 30.00,
      "currency": "USD",
      "merchant_name": "Acme Corp Credits",
      "merchant_url": "https://internal.acmecorp.com/credits",
      "notes": "Package arrived 6 days late. Customer is a 3-year loyalty member."
    },
    "chat_history": "Customer: My order was supposed to arrive last Monday and it just got here today, almost a week late.\nAgent: I sincerely apologize for the delay. I can see the shipment was stuck at a regional hub. As a valued loyalty member, I would like to offer you a $30 goodwill credit for the inconvenience.\nCustomer: That would be great, thank you."
  }')

DECISION2=$(echo "$RESULT2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null || echo "$RESULT2" | python -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null)
echo "  Result: $DECISION2"

echo ""
read -p "Press ENTER to fire the flagged transaction..."

# ── Transaction 3: Large suspicious refund, HUMAN_NEEDED ────
echo ""
echo "------------------------------------------"
echo "[3/3] Firing: \$380 suspicious refund"
echo "       Expected: HUMAN_NEEDED (flagged)"
echo "------------------------------------------"
echo "  Risk: Customer has 3 refunds in 7 days"
echo "  Risk: High-value 'not as described' claim"
echo ""

RESULT3=$(curl -s "$API/evaluate" \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CK" \
  -d '{
    "product": {
      "product_name": "Refund — Customer Dispute (Order #ACM-53387)",
      "price": 380.00,
      "currency": "USD",
      "merchant_name": "Acme Corp Refunds",
      "merchant_url": "https://internal.acmecorp.com/refunds",
      "notes": "Customer claims noise-canceling headphones are not as described. This is the customers 4th refund request this week. Previous refunds: $45 (speaker), $30 (credit), $89 (cable set). Pattern flagged."
    },
    "chat_history": "Customer: These headphones are nothing like the description. The noise canceling barely works and the sound quality is terrible.\nAgent: I understand your frustration. I can see you purchased the ProSound NC-400 headphones for $380. I should note that our system shows this would be your 4th refund request this week.\nCustomer: So what? The product is bad. I want my money back.\nAgent: Let me submit this for review. Given the amount and your recent refund history, this will need manager authorization."
  }')

DECISION3=$(echo "$RESULT3" | python3 -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null || echo "$RESULT3" | python -c "import sys,json; print(json.load(sys.stdin).get('decision','ERROR'))" 2>/dev/null)
REASON3=$(echo "$RESULT3" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ai_evaluation',{}).get('reasoning','')[:120])" 2>/dev/null || echo "$RESULT3" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('ai_evaluation',{}).get('reasoning','')[:120])" 2>/dev/null)
echo "  Result: $DECISION3"
echo "  AI says: $REASON3..."

echo ""
echo "=========================================="
echo "  DEMO COMPLETE"
echo "=========================================="
echo ""
echo "  Now show the dashboard:"
echo "  - Transaction 1 & 2: Auto-approved with virtual cards"
echo "  - Transaction 3: Waiting for manager review"
echo "  - Click on #3 to approve/deny with full context"
echo ""
