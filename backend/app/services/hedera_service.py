import json
import logging
import asyncio
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Module-level client — initialized once, reused across requests
_client = None
_topic_id = None


def _init_client():
    """Initialize and return the Hedera client. Returns (None, None) if Hedera is disabled."""
    global _client, _topic_id

    if not settings.use_hedera:
        return None, None

    if _client is not None:
        return _client, _topic_id

    try:
        from hedera import (
            Client,
            AccountId,
            PrivateKey,
            TopicId,
        )

        account_id = AccountId.fromString(settings.hedera_account_id)
        private_key = PrivateKey.fromString(settings.hedera_private_key)
        topic_id = TopicId.fromString(settings.hedera_topic_id)

        if settings.hedera_network == "testnet":
            client = Client.forTestnet()
        else:
            client = Client.forMainnet()

        client.setOperator(account_id, private_key)

        _client = client
        _topic_id = topic_id

        logger.info("Hedera client initialized — account: %s, topic: %s",
                    settings.hedera_account_id, settings.hedera_topic_id)
        return _client, _topic_id

    except Exception as e:
        logger.error("Hedera client init failed: %s", e)
        return None, None


def _build_message(payload: dict) -> str:
    """
    Serialize payload to compact JSON, truncate to 1024 bytes.
    Truncates 'intent', 'reason', and 'n' (note) fields if needed.
    """
    for field in ("intent", "reason", "n"):
        if field in payload and isinstance(payload[field], str):
            payload[field] = payload[field][:100]

    message = json.dumps(payload, separators=(",", ":"))

    if len(message.encode("utf-8")) > 1024:
        # Hard truncate as last resort
        message = message[:1020] + "..."

    return message


def _submit_sync(payload: dict) -> Optional[str]:
    """
    Synchronous Hedera submission. Runs in thread pool via asyncio.
    Returns hedera_tx_id string or None on failure.
    """
    client, topic_id = _init_client()
    if client is None:
        return None

    try:
        from hedera import TopicMessageSubmitTransaction

        message = _build_message(payload)

        tx = (
            TopicMessageSubmitTransaction()
            .setTopicId(topic_id)
            .setMessage(message)
        )

        response = tx.execute(client)
        response.getReceipt(client)  # wait for consensus confirmation
        hedera_tx_id = str(response.transactionId)

        logger.info("Hedera audit submitted — event: %s, tx_id: %s, hedera: %s",
                    payload.get("e"), payload.get("t"), hedera_tx_id)
        return hedera_tx_id

    except Exception as e:
        logger.warning("Hedera audit submit failed — event: %s, error: %s",
                       payload.get("e"), e)
        return None


async def submit_audit_message(event_type: str, payload: dict) -> Optional[str]:
    """
    Submit an audit event to Hedera HCS topic.

    Fire-and-forget — never raises, never blocks the main flow.
    Returns hedera_tx_id string or None if disabled/failed.

    Args:
        event_type: One of TRANSACTION_CREATED, EVALUATION_DECIDED, HUMAN_APPROVAL_RESPONSE
        payload: Dict of short-key fields (see hedera-audit-implementation-guide-v2.md)
    """
    if not settings.use_hedera:
        return None

    payload["e"] = event_type

    loop = asyncio.get_event_loop()
    hedera_tx_id = await loop.run_in_executor(None, _submit_sync, payload)
    return hedera_tx_id
