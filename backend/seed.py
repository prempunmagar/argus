"""
Seed the database with demo data from argus-data-spec.md Section 10.
Run: python seed.py  (from backend/ directory)

Idempotent — checks if demo user exists before inserting.
"""

import json
import sys
import os

# Add backend directory to path so we can import app modules
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
from app.services.auth_service import hash_password


def seed():
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if demo user already exists
        existing = db.query(User).filter(User.id == "usr_demo_001").first()
        if existing:
            print("Demo user already exists. Skipping seed.")
            return

        # --- 10.1 Demo User ---
        user = User(
            id="usr_demo_001",
            email="demo@argus.dev",
            password_hash=hash_password("argus2026"),
            name="Demo User",
        )
        db.add(user)

        # --- 10.2 Demo Payment Methods ---
        visa = PaymentMethod(
            id="pm_visa_001",
            user_id="usr_demo_001",
            method_type="CREDIT_CARD",
            nickname="Work Visa Card",
            detail=json.dumps({"brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2028}),
            is_default=True,
            status="active",
        )
        amex = PaymentMethod(
            id="pm_amex_001",
            user_id="usr_demo_001",
            method_type="CREDIT_CARD",
            nickname="Travel Amex Card",
            detail=json.dumps({"brand": "amex", "last4": "1234", "exp_month": 6, "exp_year": 2027}),
            is_default=False,
            status="active",
        )
        db.add_all([visa, amex])

        # --- 10.3 Demo Profile ---
        profile = Profile(
            id="profile_demo_001",
            user_id="usr_demo_001",
            name="Personal Shopper",
            description="My everyday shopping agent",
        )
        db.add(profile)

        # --- 10.4 Demo Spending Categories + Rules ---

        # Footwear
        cat_footwear = SpendingCategory(
            id="cat_footwear_001",
            profile_id="profile_demo_001",
            name="Footwear",
            description="Shoes, sneakers, boots, sandals, slippers",
            keywords=json.dumps(["shoes", "sneakers", "boots", "running shoes", "sandals", "slippers"]),
            is_default=False,
        )
        db.add(cat_footwear)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_footwear_001", rule_type="MAX_PER_TRANSACTION", value="200.00"),
            CategoryRule(category_id="cat_footwear_001", rule_type="AUTO_APPROVE_UNDER", value="80.00"),
            CategoryRule(category_id="cat_footwear_001", rule_type="DAILY_LIMIT", value="300.00"),
            CategoryRule(category_id="cat_footwear_001", rule_type="MERCHANT_WHITELIST", value='["amazon.com","nike.com","zappos.com","target.com","bestbuy.com"]'),
        ])

        # Electronics
        cat_electronics = SpendingCategory(
            id="cat_electronics_001",
            profile_id="profile_demo_001",
            name="Electronics",
            description="Computers, phones, tablets, gadgets, peripherals",
            keywords=json.dumps(["laptop", "phone", "headphones", "charger", "tablet", "computer", "monitor"]),
            is_default=False,
        )
        db.add(cat_electronics)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_electronics_001", rule_type="MAX_PER_TRANSACTION", value="500.00"),
            CategoryRule(category_id="cat_electronics_001", rule_type="AUTO_APPROVE_UNDER", value="100.00"),
            CategoryRule(category_id="cat_electronics_001", rule_type="MONTHLY_LIMIT", value="2000.00"),
        ])

        # Travel
        cat_travel = SpendingCategory(
            id="cat_travel_001",
            profile_id="profile_demo_001",
            name="Travel",
            description="Flights, hotels, car rentals, Airbnb, luggage",
            keywords=json.dumps(["flight", "hotel", "airbnb", "booking", "rental car", "luggage", "travel"]),
            is_default=False,
        )
        db.add(cat_travel)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_travel_001", rule_type="MAX_PER_TRANSACTION", value="2000.00"),
            CategoryRule(category_id="cat_travel_001", rule_type="ALWAYS_REQUIRE_APPROVAL", value="true"),
            CategoryRule(category_id="cat_travel_001", rule_type="MONTHLY_LIMIT", value="5000.00"),
        ])

        # General (default)
        cat_general = SpendingCategory(
            id="cat_general_001",
            profile_id="profile_demo_001",
            name="General",
            description="Default for anything that doesn't fit other categories",
            is_default=True,
        )
        db.add(cat_general)
        db.flush()
        db.add_all([
            CategoryRule(category_id="cat_general_001", rule_type="MAX_PER_TRANSACTION", value="500.00"),
            CategoryRule(category_id="cat_general_001", rule_type="AUTO_APPROVE_UNDER", value="50.00"),
            CategoryRule(category_id="cat_general_001", rule_type="DAILY_LIMIT", value="1000.00"),
        ])

        # --- 10.5 Demo Connection Key ---
        connection_key = ConnectionKey(
            id="ck_demo_001",
            profile_id="profile_demo_001",
            key_value="argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e",
            key_prefix="argus_ck_7f3b",
            label="Demo Shopping Agent",
        )
        db.add(connection_key)

        db.commit()
        print("Seed data inserted successfully.")
        print("  Demo user: demo@argus.dev / argus2026")
        print("  Connection key: argus_ck_7f3b2c9e4d5a6b7c8d9e0f1a2b3c4d5e")

    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
