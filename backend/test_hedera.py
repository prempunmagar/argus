"""
test_hedera.py — Quick standalone Hedera connection test.

Run from the backend/ directory:
    ARGUS_USE_HEDERA=true \
    ARGUS_HEDERA_ACCOUNT_ID=0.0.7974152 \
    ARGUS_HEDERA_PRIVATE_KEY=<your-key> \
    ARGUS_HEDERA_TOPIC_ID=0.0.8008541 \
    ARGUS_HEDERA_NETWORK=testnet \
    python test_hedera.py

Then verify on: https://hashscan.io/testnet/topic/0.0.8008541
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings


def test_hedera():
    print(f"ARGUS_USE_HEDERA     = {settings.use_hedera}")
    print(f"ARGUS_HEDERA_ACCOUNT = {settings.hedera_account_id}")
    print(f"ARGUS_HEDERA_TOPIC   = {settings.hedera_topic_id}")
    print(f"ARGUS_HEDERA_NETWORK = {settings.hedera_network}")
    print(f"Private key set      = {'yes' if settings.hedera_private_key else 'NO — MISSING'}")
    print()

    if not settings.use_hedera:
        print("ERROR: ARGUS_USE_HEDERA is not true. Set it and re-run.")
        sys.exit(1)

    if not settings.hedera_private_key:
        print("ERROR: ARGUS_HEDERA_PRIVATE_KEY is not set.")
        sys.exit(1)

    print("Initializing Hedera client...")
    try:
        from hedera import (
            Client,
            AccountId,
            PrivateKey,
            TopicId,
            TopicMessageSubmitTransaction,
        )

        account_id = AccountId.fromString(settings.hedera_account_id)
        private_key = PrivateKey.fromString(settings.hedera_private_key)
        topic_id = TopicId.fromString(settings.hedera_topic_id)

        client = Client.forTestnet()
        client.setOperator(account_id, private_key)
        print("Client initialized OK")

    except Exception as e:
        print(f"ERROR: Client init failed: {e}")
        sys.exit(1)

    print("Submitting test message to HCS topic...")
    try:
        import json
        message = json.dumps({
            "e": "TEST",
            "msg": "Argus Hedera connection test",
            "ts": __import__("datetime").datetime.utcnow().isoformat(),
        }, separators=(",", ":"))

        tx = (
            TopicMessageSubmitTransaction()
            .setTopicId(topic_id)
            .setMessage(message)
        )

        response = tx.execute(client)
        response.getReceipt(client)
        tx_id = str(response.transactionId)

        print(f"\nSUCCESS!")
        print(f"  Transaction ID : {tx_id}")
        print(f"  Verify on      : https://hashscan.io/testnet/topic/{settings.hedera_topic_id}")

    except Exception as e:
        print(f"ERROR: Message submit failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_hedera()
