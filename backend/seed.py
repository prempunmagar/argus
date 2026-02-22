"""
Seed the database with demo data.
Run: python seed.py  (from backend/ directory)

Idempotent — checks if demo user exists before inserting.
"""

import json
import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models import (
    User,
    Profile,
    PaymentMethod,
    SpendingCategory,
    CategoryRule,
    ConnectionKey,
)
from app.models.transaction import Transaction
from app.models.evaluation import Evaluation
from app.models.human_approval import HumanApproval
from app.models.virtual_card import VirtualCard
from app.services.auth_service import hash_password


def _make_request_data(product_name, price, merchant_name, merchant_url, currency="USD", product_url=None, context=None):
    return json.dumps({
        "product_name": product_name,
        "price": price,
        "currency": currency,
        "merchant_name": merchant_name,
        "merchant_url": merchant_url,
        "merchant_domain": merchant_url.split("//")[-1].split("/")[0] if merchant_url else "",
        "product_url": product_url,
        "conversation_context": context,
    })


def seed():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.id == "usr_demo_001").first()
        if existing:
            print("Demo user already exists. Skipping seed.")
            return

        # --- Demo User ---
        user = User(
            id="usr_demo_001",
            email="demo@argus.dev",
            password_hash=hash_password("argus2026"),
            name="Demo User",
        )
        db.add(user)

        # --- Payment Methods ---
        visa = PaymentMethod(
            id="pm_visa_001", user_id="usr_demo_001", method_type="CREDIT_CARD",
            nickname="Work Visa Card",
            detail=json.dumps({"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2028}),
            is_default=True, status="active",
        )
        amex = PaymentMethod(
            id="pm_amex_001", user_id="usr_demo_001", method_type="CREDIT_CARD",
            nickname="Travel Amex Card",
            detail=json.dumps({"brand": "amex", "last4": "1234", "exp_month": 6, "exp_year": 2027}),
            is_default=False, status="active",
        )
        db.add_all([visa, amex])

        # --- Profile ---
        profile = Profile(
            id="profile_demo_001", user_id="usr_demo_001",
            name="Personal Shopper", description="My everyday shopping agent",
        )
        db.add(profile)

        # --- Spending Categories + Rules ---
        cat_footwear = SpendingCategory(
            id="cat_footwear_001", profile_id="profile_demo_001",
            name="Footwear", description="Shoes, sneakers, boots, sandals, slippers",
            is_default=False,
        )
        db.add(cat_footwear)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_footwear_001", rule_type="MAX_PER_TRANSACTION", value="200.00"),
            CategoryRule(category_id="cat_footwear_001", rule_type="AUTO_APPROVE_UNDER", value="80.00"),
            CategoryRule(category_id="cat_footwear_001", rule_type="DAILY_LIMIT", value="300.00"),
            CategoryRule(category_id="cat_footwear_001", rule_type="MERCHANT_WHITELIST", value='["amazon.com","zappos.com","target.com","bestbuy.com","adidas.com"]'),
        ])

        cat_electronics = SpendingCategory(
            id="cat_electronics_001", profile_id="profile_demo_001",
            name="Electronics", description="Computers, phones, tablets, gadgets, peripherals",
            is_default=False,
        )
        db.add(cat_electronics)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_electronics_001", rule_type="MAX_PER_TRANSACTION", value="500.00"),
            CategoryRule(category_id="cat_electronics_001", rule_type="AUTO_APPROVE_UNDER", value="100.00"),
            CategoryRule(category_id="cat_electronics_001", rule_type="MONTHLY_LIMIT", value="2000.00"),
        ])

        cat_travel = SpendingCategory(
            id="cat_travel_001", profile_id="profile_demo_001",
            name="Travel", description="Flights, hotels, car rentals, Airbnb, luggage",
            is_default=False,
        )
        db.add(cat_travel)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_travel_001", rule_type="MAX_PER_TRANSACTION", value="2000.00"),
            CategoryRule(category_id="cat_travel_001", rule_type="ALWAYS_REQUIRE_APPROVAL", value="true"),
            CategoryRule(category_id="cat_travel_001", rule_type="MONTHLY_LIMIT", value="5000.00"),
        ])

        cat_general = SpendingCategory(
            id="cat_general_001", profile_id="profile_demo_001",
            name="General", description="Default for anything that doesn't fit other categories",
            is_default=True,
        )
        db.add(cat_general)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_general_001", rule_type="MAX_PER_TRANSACTION", value="500.00"),
            CategoryRule(category_id="cat_general_001", rule_type="AUTO_APPROVE_UNDER", value="50.00"),
            CategoryRule(category_id="cat_general_001", rule_type="DAILY_LIMIT", value="1000.00"),
        ])

        # --- Connection Key ---
        connection_key = ConnectionKey(
            id="ck_demo_001", profile_id="profile_demo_001",
            key_value="argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e",
            key_prefix="argus_ck_7f3b", label="Demo Shopping Agent",
        )
        db.add(connection_key)
        db.flush()

        # --- Demo Transactions (10 — one per status) ---
        now = datetime.now(timezone.utc)

        def add_txn(txn_id, eval_id, status, decision, request_data, category_id,
                     confidence, intent, intent_summary, reasoning,
                     risk_flags=None, rules_checked=None, vc=None, human=None, hours_ago=0,
                     user_id="usr_demo_001", ck_id="ck_demo_001", pm_id="pm_visa_001"):
            t = Transaction(
                id=txn_id, user_id=user_id, connection_key_id=ck_id,
                status=status, request_data=request_data,
                created_at=now - timedelta(hours=hours_ago),
                updated_at=now - timedelta(hours=max(hours_ago - 0.1, 0)),
            )
            db.add(t)
            db.flush()

            if decision:
                e = Evaluation(
                    id=eval_id, transaction_id=txn_id, category_id=category_id,
                    category_confidence=confidence, intent_match=intent,
                    intent_summary=intent_summary, decision_reasoning=reasoning,
                    risk_flags=json.dumps(risk_flags or []),
                    rules_checked=json.dumps(rules_checked or []),
                    decision=decision,
                    created_at=now - timedelta(hours=max(hours_ago - 0.05, 0)),
                )
                db.add(e)
                db.flush()

            if human:
                h = HumanApproval(
                    id=str(uuid.uuid4()), transaction_id=txn_id, evaluation_id=eval_id,
                    requested_at=now - timedelta(hours=max(hours_ago - 0.05, 0)),
                    responded_at=human.get("responded_at"), value=human.get("value"), note=human.get("note"),
                )
                db.add(h)
                db.flush()

            if vc:
                v = VirtualCard(
                    id=str(uuid.uuid4()), transaction_id=txn_id, user_id=user_id,
                    payment_method_id=vc.get("pm_id", pm_id),
                    card_number=vc.get("card_number", "4111111111118847"),
                    expiry_month="03", expiry_year="2026", cvv="731",
                    last_four=vc.get("last_four", "8847"),
                    spend_limit=vc.get("spend_limit", 0), spend_limit_buffer=vc.get("buffer", 5.00),
                    merchant_lock=vc.get("merchant_lock"),
                    status=vc.get("status", "ACTIVE"),
                    issued_at=now - timedelta(hours=max(hours_ago - 0.05, 0)),
                    expires_at=now + timedelta(minutes=30),
                )
                db.add(v)
                db.flush()

        # 1. PENDING_EVALUATION — just submitted, not evaluated yet
        add_txn(
            txn_id="txn_demo_001", eval_id="eval_demo_001",
            status="PENDING_EVALUATION", decision=None,
            request_data=_make_request_data(
                "Logitech MX Master 3S Mouse", 99.99, "Amazon", "https://amazon.com/checkout",
                context="User: I need a good wireless mouse for work.\nAgent: Found Logitech MX Master 3S at $99.99 on Amazon."
            ),
            category_id=None, confidence=None, intent=None,
            intent_summary=None, reasoning=None,
            hours_ago=0.1,
        )

        # 2. AI_APPROVED — cheap book, auto-approved
        add_txn(
            txn_id="txn_demo_002", eval_id="eval_demo_002",
            status="AI_APPROVED", decision="APPROVE",
            request_data=_make_request_data(
                "Atomic Habits by James Clear", 14.99, "Amazon", "https://amazon.com/checkout",
                product_url="https://amazon.com/dp/B07D23CFGR",
                context="User: Buy me Atomic Habits.\nAgent: Found it on Amazon for $14.99 (paperback)."
            ),
            category_id="cat_general_001", confidence=0.82, intent=0.95,
            intent_summary="User wants to purchase the book Atomic Habits.",
            reasoning="Price $14.99 is under the $50 auto-approve threshold for General. Clear purchase intent. Auto-approved.",
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": True, "detail": "$14.99 < $50.00 threshold"},
                {"rule_type": "DAILY_LIMIT", "passed": True, "detail": "$14.99 / $1,000.00 daily limit"},
            ],
            vc={"last_four": "7703", "spend_limit": 19.99, "merchant_lock": "amazon.com"},
            hours_ago=3,
        )

        # 3. AI_APPROVED — USB cable, cheap electronics
        add_txn(
            txn_id="txn_demo_003", eval_id="eval_demo_003",
            status="AI_APPROVED", decision="APPROVE",
            request_data=_make_request_data(
                "Anker USB-C to USB-C Cable (2-Pack)", 12.99, "Amazon", "https://amazon.com/checkout",
                context="User: I need a USB-C cable for my laptop.\nAgent: Found Anker 2-pack at $12.99."
            ),
            category_id="cat_electronics_001", confidence=0.88, intent=0.90,
            intent_summary="User needs a USB-C charging cable for laptop.",
            reasoning="Price $12.99 is well under the $100 auto-approve threshold for Electronics. Approved automatically.",
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": True, "detail": "$12.99 < $100.00 threshold"},
                {"rule_type": "MONTHLY_LIMIT", "passed": True, "detail": "$12.99 / $2,000.00 monthly limit"},
            ],
            vc={"last_four": "5512", "spend_limit": 17.99, "merchant_lock": "amazon.com"},
            hours_ago=6,
        )

        # 4. AI_DENIED — Rolex watch, way over limit
        add_txn(
            txn_id="txn_demo_004", eval_id="eval_demo_004",
            status="AI_DENIED", decision="DENY",
            request_data=_make_request_data(
                "Rolex Submariner Date", 14250.00, "Chrono24", "https://chrono24.com/checkout",
                context="User: Find me a nice watch.\nAgent: Found Rolex Submariner at $14,250 on Chrono24."
            ),
            category_id="cat_general_001", confidence=0.78, intent=0.40,
            intent_summary="User asked for a 'nice watch' — agent found a luxury Rolex.",
            reasoning="Price $14,250 massively exceeds the $500 max-per-transaction limit. The vague request 'find me a nice watch' does not indicate intent to spend $14K. Denied.",
            risk_flags=["Extreme price for vague request", "Unknown merchant"],
            rules_checked=[
                {"rule_type": "MAX_PER_TRANSACTION", "passed": False, "detail": "$14,250.00 > $500.00 limit"},
                {"rule_type": "DAILY_LIMIT", "passed": False, "detail": "$14,250.00 > $1,000.00 daily limit"},
            ],
            hours_ago=14,
        )

        # 5. AI_DENIED — gaming laptop, exceeds electronics limit
        add_txn(
            txn_id="txn_demo_005", eval_id="eval_demo_005",
            status="AI_DENIED", decision="DENY",
            request_data=_make_request_data(
                "ASUS ROG Strix G16 Gaming Laptop", 1899.99, "Best Buy", "https://bestbuy.com/checkout",
                context="User: Get me a gaming laptop.\nAgent: Found ASUS ROG Strix G16 at $1,899.99 on Best Buy."
            ),
            category_id="cat_electronics_001", confidence=0.94, intent=0.75,
            intent_summary="User wants a gaming laptop.",
            reasoning="Price $1,899.99 exceeds the $500 max-per-transaction limit for Electronics. Denied.",
            risk_flags=["High-value electronics purchase"],
            rules_checked=[
                {"rule_type": "MAX_PER_TRANSACTION", "passed": False, "detail": "$1,899.99 > $500.00 limit"},
                {"rule_type": "MONTHLY_LIMIT", "passed": True, "detail": "$1,899.99 / $2,000.00 monthly limit"},
            ],
            hours_ago=20,
        )

        # 6. HUMAN_NEEDED — Sony headphones, waiting for approval
        add_txn(
            txn_id="txn_demo_006", eval_id="eval_demo_006",
            status="HUMAN_NEEDED", decision="HUMAN_NEEDED",
            request_data=_make_request_data(
                "Sony WH-1000XM5 Wireless Headphones", 278.00, "Amazon", "https://amazon.com/checkout",
                product_url="https://amazon.com/dp/B0BX2L8PBT",
                context="User: Get me the best noise-canceling headphones.\nAgent: Found Sony WH-1000XM5 at $278 on Amazon."
            ),
            category_id="cat_electronics_001", confidence=0.93, intent=0.82,
            intent_summary="User wants premium noise-canceling headphones.",
            reasoning="Price $278 exceeds the $100 auto-approve threshold but is under the $500 max for Electronics. Escalating for human review.",
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": False, "detail": "$278.00 > $100.00 threshold"},
                {"rule_type": "MAX_PER_TRANSACTION", "passed": True, "detail": "$278.00 < $500.00 limit"},
                {"rule_type": "MONTHLY_LIMIT", "passed": True, "detail": "$278.00 / $2,000.00 monthly limit"},
            ],
            human={"value": None, "responded_at": None},
            hours_ago=0.5,
        )

        # 7. HUMAN_NEEDED — Airbnb trip, travel always requires approval
        add_txn(
            txn_id="txn_demo_007", eval_id="eval_demo_007",
            status="HUMAN_NEEDED", decision="HUMAN_NEEDED",
            request_data=_make_request_data(
                "Airbnb — Beachfront Condo (3 nights)", 487.00, "Airbnb", "https://airbnb.com/checkout",
                context="User: Book me a beachfront place in Miami for this weekend, 3 nights.\nAgent: Found a beachfront condo on Airbnb for $487 total."
            ),
            category_id="cat_travel_001", confidence=0.96, intent=0.85,
            intent_summary="User wants to book a 3-night beachfront Airbnb in Miami.",
            reasoning="Travel category has ALWAYS_REQUIRE_APPROVAL enabled. Price $487 is within the $2,000 max. Requires human authorization.",
            rules_checked=[
                {"rule_type": "ALWAYS_REQUIRE_APPROVAL", "passed": False, "detail": "Travel requires human approval"},
                {"rule_type": "MAX_PER_TRANSACTION", "passed": True, "detail": "$487.00 < $2,000.00 limit"},
                {"rule_type": "MONTHLY_LIMIT", "passed": True, "detail": "$487.00 / $5,000.00 monthly limit"},
            ],
            human={"value": None, "responded_at": None},
            hours_ago=1,
        )

        # 8. HUMAN_APPROVED — Adidas running shoes, approved by user
        add_txn(
            txn_id="txn_demo_008", eval_id="eval_demo_008",
            status="HUMAN_APPROVED", decision="HUMAN_NEEDED",
            request_data=_make_request_data(
                "Adidas Ultraboost Light Running Shoes", 159.99, "Adidas", "https://adidas.com/checkout",
                product_url="https://adidas.com/ultraboost-light",
                context="User: Find me good running shoes around $150.\nAgent: Found Adidas Ultraboost Light at $159.99."
            ),
            category_id="cat_footwear_001", confidence=0.96, intent=0.90,
            intent_summary="User wants running shoes around $150.",
            reasoning="Price $159.99 exceeds the $80 auto-approve but is under $200 max for Footwear. Merchant adidas.com is whitelisted. Escalated for human review. User approved.",
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": False, "detail": "$159.99 > $80.00 threshold"},
                {"rule_type": "MAX_PER_TRANSACTION", "passed": True, "detail": "$159.99 < $200.00 limit"},
                {"rule_type": "MERCHANT_WHITELIST", "passed": True, "detail": "adidas.com is whitelisted"},
            ],
            human={"value": "APPROVE", "responded_at": now - timedelta(hours=4), "note": "Good deal on Ultraboosts"},
            vc={"last_four": "6641", "spend_limit": 175.00, "merchant_lock": "adidas.com"},
            hours_ago=5,
        )

        # 9. HUMAN_DENIED — expensive luggage, denied by user
        add_txn(
            txn_id="txn_demo_009", eval_id="eval_demo_009",
            status="HUMAN_DENIED", decision="HUMAN_NEEDED",
            request_data=_make_request_data(
                "Samsonite Freeform 28\" Hardside Luggage", 349.99, "Amazon", "https://amazon.com/checkout",
                context="User: I need a large suitcase for my trip.\nAgent: Found Samsonite Freeform 28\" at $349.99."
            ),
            category_id="cat_travel_001", confidence=0.89, intent=0.72,
            intent_summary="User needs a large suitcase for travel.",
            reasoning="Travel always requires approval. Price $349.99 is within limits. Escalated. User denied — too expensive.",
            rules_checked=[
                {"rule_type": "ALWAYS_REQUIRE_APPROVAL", "passed": False, "detail": "Travel requires human approval"},
                {"rule_type": "MAX_PER_TRANSACTION", "passed": True, "detail": "$349.99 < $2,000.00 limit"},
            ],
            human={"value": "DENY", "responded_at": now - timedelta(hours=8), "note": "Too expensive, find something under $200"},
            hours_ago=10,
        )

        # 10. HUMAN_TIMEOUT — flight booking, user didn't respond in time
        add_txn(
            txn_id="txn_demo_010", eval_id="eval_demo_010",
            status="HUMAN_TIMEOUT", decision="HUMAN_NEEDED",
            request_data=_make_request_data(
                "Delta LAX→JFK Round Trip", 389.00, "Delta Airlines", "https://delta.com/checkout",
                context="User: Book me the cheapest round trip from LA to New York next Friday.\nAgent: Found Delta LAX to JFK for $389 round trip."
            ),
            category_id="cat_travel_001", confidence=0.97, intent=0.88,
            intent_summary="User wants the cheapest LAX to JFK round trip flight.",
            reasoning="Travel always requires approval. Price $389 within limits. Escalated for human review. User did not respond within 5 minutes — timed out.",
            rules_checked=[
                {"rule_type": "ALWAYS_REQUIRE_APPROVAL", "passed": False, "detail": "Travel requires human approval"},
                {"rule_type": "MAX_PER_TRANSACTION", "passed": True, "detail": "$389.00 < $2,000.00 limit"},
            ],
            human={"value": "TIMEOUT_DENY", "responded_at": None},
            hours_ago=30,
        )

        # 11. COMPLETED — water bottle, auto-approved, card used successfully
        add_txn(
            txn_id="txn_demo_011", eval_id="eval_demo_011",
            status="COMPLETED", decision="APPROVE",
            request_data=_make_request_data(
                "Hydro Flask 32oz Wide Mouth", 44.95, "Amazon", "https://amazon.com/checkout",
                context="User: Buy me a Hydro Flask water bottle.\nAgent: Found 32oz Wide Mouth at $44.95 on Amazon."
            ),
            category_id="cat_general_001", confidence=0.85, intent=0.93,
            intent_summary="User wants to purchase a Hydro Flask water bottle.",
            reasoning="Price $44.95 is under the $50 auto-approve threshold for General. Auto-approved. Card used successfully.",
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": True, "detail": "$44.95 < $50.00 threshold"},
                {"rule_type": "DAILY_LIMIT", "passed": True, "detail": "$44.95 / $1,000.00 daily limit"},
            ],
            vc={"last_four": "2290", "spend_limit": 54.95, "merchant_lock": "amazon.com", "status": "USED"},
            hours_ago=48,
        )

        # 12. EXPIRED — card issued but not used before expiry
        add_txn(
            txn_id="txn_demo_012", eval_id="eval_demo_012",
            status="EXPIRED", decision="APPROVE",
            request_data=_make_request_data(
                "Kindle Paperwhite (16GB)", 149.99, "Amazon", "https://amazon.com/checkout",
                context="User: Get me a Kindle.\nAgent: Found Kindle Paperwhite 16GB at $149.99."
            ),
            category_id="cat_electronics_001", confidence=0.91, intent=0.87,
            intent_summary="User wants a Kindle e-reader.",
            reasoning="Price $149.99 exceeds auto-approve but is under $500 max. Escalated and approved by human. Virtual card issued but expired unused after 30 minutes.",
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": False, "detail": "$149.99 > $100.00 threshold"},
                {"rule_type": "MAX_PER_TRANSACTION", "passed": True, "detail": "$149.99 < $500.00 limit"},
            ],
            human={"value": "APPROVE", "responded_at": now - timedelta(hours=71)},
            vc={"last_four": "4418", "spend_limit": 164.99, "merchant_lock": "amazon.com", "status": "EXPIRED"},
            hours_ago=72,
        )

        # 13. FAILED — system error during evaluation
        add_txn(
            txn_id="txn_demo_013", eval_id="eval_demo_013",
            status="FAILED", decision=None,
            request_data=_make_request_data(
                "Bose QuietComfort Ultra Earbuds", 299.00, "Bose", "https://bose.com/checkout",
                context="User: Buy me the best wireless earbuds.\nAgent: Found Bose QC Ultra at $299 on bose.com."
            ),
            category_id=None, confidence=None, intent=None,
            intent_summary=None, reasoning=None,
            hours_ago=96,
        )

        # =====================================================
        # ENTERPRISE USER — Flow 2: Refund Agent Demo
        # =====================================================
        ent_user = User(
            id="usr_enterprise_001",
            email="enterprise@argus.dev",
            password_hash=hash_password("argus2026"),
            name="Acme Corp Admin",
        )
        db.add(ent_user)

        # --- Enterprise Payment Method ---
        ent_pm = PaymentMethod(
            id="pm_ent_corp_001", user_id="usr_enterprise_001", method_type="CREDIT_CARD",
            nickname="Corporate Amex",
            detail=json.dumps({"brand": "amex", "last4": "9001", "exp_month": 9, "exp_year": 2028}),
            is_default=True, status="active",
        )
        db.add(ent_pm)

        # --- Enterprise Profile ---
        ent_profile = Profile(
            id="profile_enterprise_001", user_id="usr_enterprise_001",
            name="Customer Service Agent", description="AI agent for customer support refunds and credits",
        )
        db.add(ent_profile)

        # --- Enterprise Categories + Rules ---
        cat_refunds = SpendingCategory(
            id="cat_refunds_001", profile_id="profile_enterprise_001",
            name="Refunds", description="Customer refund processing — returns, damaged goods, wrong items",
            is_default=False,
        )
        db.add(cat_refunds)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_refunds_001", rule_type="AUTO_APPROVE_UNDER", value="100.00"),
            CategoryRule(category_id="cat_refunds_001", rule_type="MAX_PER_TRANSACTION", value="500.00"),
            CategoryRule(category_id="cat_refunds_001", rule_type="DAILY_LIMIT", value="2000.00"),
        ])

        cat_cs = SpendingCategory(
            id="cat_cs_001", profile_id="profile_enterprise_001",
            name="Customer Service", description="General CS operations — goodwill credits, shipping adjustments, loyalty points",
            is_default=True,
        )
        db.add(cat_cs)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_cs_001", rule_type="AUTO_APPROVE_UNDER", value="50.00"),
            CategoryRule(category_id="cat_cs_001", rule_type="MAX_PER_TRANSACTION", value="250.00"),
            CategoryRule(category_id="cat_cs_001", rule_type="DAILY_LIMIT", value="1000.00"),
        ])

        # --- Enterprise Connection Key ---
        ent_ck = ConnectionKey(
            id="ck_enterprise_001", profile_id="profile_enterprise_001",
            key_value="argus_ck_ent_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
            key_prefix="argus_ck_ent_a1b2", label="CS Refund Agent",
        )
        db.add(ent_ck)
        db.flush()

        # --- Enterprise Transactions ---

        # E1. Auto-approved small refund ($45) — the "routine" one from the demo script
        add_txn(
            txn_id="txn_ent_001", eval_id="eval_ent_001",
            status="AI_APPROVED", decision="APPROVE",
            user_id="usr_enterprise_001", ck_id="ck_enterprise_001", pm_id="pm_ent_corp_001",
            request_data=_make_request_data(
                "Refund — Damaged Product (Order #ACM-28491)", 45.00,
                "Acme Corp Refunds", "https://internal.acmecorp.com/refunds",
                context="Customer reported damaged packaging on order #ACM-28491 (wireless charger). Photos verified. Agent initiating $45 refund."
            ),
            category_id="cat_refunds_001", confidence=0.94, intent=0.96,
            intent_summary="Customer received a damaged wireless charger. Refund requested with photo evidence.",
            reasoning="Refund amount $45.00 is under the $100 auto-approve threshold. Damage claim has photo evidence. Auto-approved.",
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": True, "detail": "$45.00 < $100.00 threshold"},
                {"rule_type": "DAILY_LIMIT", "passed": True, "detail": "$45.00 / $2,000.00 daily limit"},
            ],
            hours_ago=2,
        )

        # E2. Auto-approved small goodwill credit ($25)
        add_txn(
            txn_id="txn_ent_002", eval_id="eval_ent_002",
            status="AI_APPROVED", decision="APPROVE",
            user_id="usr_enterprise_001", ck_id="ck_enterprise_001", pm_id="pm_ent_corp_001",
            request_data=_make_request_data(
                "Goodwill Credit — Late Delivery (Order #ACM-31205)", 25.00,
                "Acme Corp Credits", "https://internal.acmecorp.com/credits",
                context="Customer complained about 5-day late delivery on order #ACM-31205. Agent issuing $25 goodwill credit."
            ),
            category_id="cat_cs_001", confidence=0.90, intent=0.92,
            intent_summary="Customer received late delivery. Goodwill credit for inconvenience.",
            reasoning="Credit $25.00 is under the $50 auto-approve threshold for Customer Service. Routine late delivery compensation. Auto-approved.",
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": True, "detail": "$25.00 < $50.00 threshold"},
                {"rule_type": "DAILY_LIMIT", "passed": True, "detail": "$25.00 / $1,000.00 daily limit"},
            ],
            hours_ago=4,
        )

        # E3. Flagged $380 refund — the key demo moment (HUMAN_NEEDED)
        add_txn(
            txn_id="txn_ent_003", eval_id="eval_ent_003",
            status="HUMAN_NEEDED", decision="HUMAN_NEEDED",
            user_id="usr_enterprise_001", ck_id="ck_enterprise_001", pm_id="pm_ent_corp_001",
            request_data=_make_request_data(
                "Refund — Customer Complaint (Order #ACM-44712)", 380.00,
                "Acme Corp Refunds", "https://internal.acmecorp.com/refunds",
                context="Customer claims item 'not as described' on order #ACM-44712 (premium headphones, $380). Requesting full refund. Customer has had 3 refunds in past 7 days."
            ),
            category_id="cat_refunds_001", confidence=0.88, intent=0.65,
            intent_summary="Customer requests full refund on premium headphones claiming item not as described.",
            reasoning="Refund amount $380.00 exceeds the $100 auto-approve threshold. Customer has 3 refunds in past 7 days — possible refund abuse pattern. Flagged for manager review.",
            risk_flags=["3 refunds in 7 days", "Possible refund abuse pattern", "High-value refund"],
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": False, "detail": "$380.00 > $100.00 threshold"},
                {"rule_type": "MAX_PER_TRANSACTION", "passed": True, "detail": "$380.00 < $500.00 limit"},
                {"rule_type": "DAILY_LIMIT", "passed": True, "detail": "$380.00 / $2,000.00 daily limit"},
            ],
            human={"value": None, "responded_at": None},
            hours_ago=0.3,
        )

        # E4. Previously approved medium refund ($120) — shows history
        add_txn(
            txn_id="txn_ent_004", eval_id="eval_ent_004",
            status="HUMAN_APPROVED", decision="HUMAN_NEEDED",
            user_id="usr_enterprise_001", ck_id="ck_enterprise_001", pm_id="pm_ent_corp_001",
            request_data=_make_request_data(
                "Refund — Wrong Item Shipped (Order #ACM-39876)", 120.00,
                "Acme Corp Refunds", "https://internal.acmecorp.com/refunds",
                context="Customer received wrong item on order #ACM-39876 (ordered blue, received red). Requesting refund. Agent verified mismatch."
            ),
            category_id="cat_refunds_001", confidence=0.92, intent=0.91,
            intent_summary="Wrong item shipped to customer. Refund for shipping error.",
            reasoning="Refund $120.00 exceeds auto-approve threshold. Shipping error verified by agent. Escalated for manager review. Manager approved.",
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": False, "detail": "$120.00 > $100.00 threshold"},
                {"rule_type": "MAX_PER_TRANSACTION", "passed": True, "detail": "$120.00 < $500.00 limit"},
                {"rule_type": "DAILY_LIMIT", "passed": True, "detail": "$120.00 / $2,000.00 daily limit"},
            ],
            human={"value": "APPROVE", "responded_at": now - timedelta(hours=6), "note": "Verified — wrong item shipped"},
            hours_ago=8,
        )

        # E5. Denied suspicious refund ($490) — near the hard cap
        add_txn(
            txn_id="txn_ent_005", eval_id="eval_ent_005",
            status="HUMAN_DENIED", decision="HUMAN_NEEDED",
            user_id="usr_enterprise_001", ck_id="ck_enterprise_001", pm_id="pm_ent_corp_001",
            request_data=_make_request_data(
                "Refund — 'Never Received' Claim (Order #ACM-27033)", 490.00,
                "Acme Corp Refunds", "https://internal.acmecorp.com/refunds",
                context="Customer claims order #ACM-27033 (smart TV, $490) was never delivered. Tracking shows delivered and signed for."
            ),
            category_id="cat_refunds_001", confidence=0.85, intent=0.42,
            intent_summary="Customer claims non-delivery of smart TV despite tracking showing delivery confirmation.",
            reasoning="Refund $490.00 exceeds auto-approve threshold. Tracking shows successful delivery with signature. High risk of fraudulent claim. Escalated for manager review. Manager denied.",
            risk_flags=["Tracking confirms delivery", "Signature on file", "High-value claim", "Possible fraud"],
            rules_checked=[
                {"rule_type": "AUTO_APPROVE_UNDER", "passed": False, "detail": "$490.00 > $100.00 threshold"},
                {"rule_type": "MAX_PER_TRANSACTION", "passed": True, "detail": "$490.00 < $500.00 limit"},
                {"rule_type": "DAILY_LIMIT", "passed": True, "detail": "$490.00 / $2,000.00 daily limit"},
            ],
            human={"value": "DENY", "responded_at": now - timedelta(hours=22), "note": "Tracking confirms delivery. Denied — escalate to fraud team."},
            hours_ago=24,
        )

        db.commit()
        print("Seed data inserted successfully.")
        print("  Consumer user: demo@argus.dev / argus2026")
        print("  Enterprise user: enterprise@argus.dev / argus2026")
        print("  Consumer connection key: argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e")
        print("  Enterprise connection key: argus_ck_ent_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")
        print("  Consumer transactions: 13 | Enterprise transactions: 5")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
