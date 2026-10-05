# app/services/tracking_pubsub.py

import json
from typing import Any
from uuid import UUID

from redis.asyncio.client import PubSub

from app.core.redis import redis_client


def tracking_channel(request_id: UUID | str) -> str:
    """
    Return the Redis channel for one service request.
    """
    return f"tracking:{request_id}"


async def publish_tracking_event(
    request_id: UUID | str,
    event: dict[str, Any],
) -> int:
    """
    Publish a tracking event to the request-specific Redis channel.

    Returns:
        Number of Redis subscribers that received the event.
    """

    channel = tracking_channel(request_id)

    return await redis_client.publish(
        channel,
        json.dumps(event, default=str),
    )


async def create_tracking_subscription(
    request_id: UUID | str,
) -> PubSub:
    """
    Create a dedicated Redis Pub/Sub connection for one WebSocket.
    """

    pubsub = redis_client.pubsub()

    await pubsub.subscribe(
        tracking_channel(request_id)
    )

    return pubsub


async def close_tracking_subscription(
    pubsub: PubSub,
    request_id: UUID | str,
) -> None:
    """
    Unsubscribe and close the dedicated Pub/Sub connection.
    """

    try:
        await pubsub.unsubscribe(
            tracking_channel(request_id)
        )
    finally:
        await pubsub.aclose()