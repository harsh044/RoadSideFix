# app/routers/tracking.py

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.database import SessionLocal
from app.services.tracking_pubsub import (
    close_tracking_subscription,
    create_tracking_subscription,
)
from app.services.tracking_service import customer_can_track_request
from app.websocket.auth import authenticate_websocket


router = APIRouter(
    tags=["Real-Time Tracking"],
)


async def read_websocket_messages(
    websocket: WebSocket,
) -> None:
    """
    Read messages sent by the customer WebSocket client.

    The customer cannot publish GPS data. They can only send
    connection-level messages such as ping.
    """

    while True:
        message = await websocket.receive_text()

        if message == "ping":
            await websocket.send_json(
                {
                    "type": "pong",
                }
            )


async def read_redis_messages(
    websocket: WebSocket,
    pubsub,
) -> None:
    """
    Read location events from Redis and forward them
    to the connected customer.
    """

    while True:
        message = await pubsub.get_message(
            ignore_subscribe_messages=True,
            timeout=1.0,
        )

        if message is None:
            await asyncio.sleep(0.05)
            continue

        if message["type"] != "message":
            continue

        raw_data = message["data"]

        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode("utf-8")

        try:
            event = json.loads(raw_data)
        except json.JSONDecodeError:
            continue

        await websocket.send_json(event)


@router.websocket(
    "/ws/service-requests/{request_id}/tracking"
)
async def tracking_websocket(
    websocket: WebSocket,
    request_id: UUID,
):
    """
    Secure customer tracking WebSocket.

    Connection format:

    ws://localhost:8000/ws/service-requests/{request_id}/tracking?token=JWT
    """

    token = websocket.query_params.get("token")

    user_id = authenticate_websocket(token)

    if user_id is None:
        await websocket.close(
            code=1008,
            reason="Invalid authentication",
        )
        return

    db = SessionLocal()

    pubsub = None
    websocket_reader_task = None
    redis_reader_task = None

    try:
        request = customer_can_track_request(
            db=db,
            customer_id=user_id,
            request_id=request_id,
        )

        if request is None:
            await websocket.close(
                code=1008,
                reason="You are not authorized to track this request",
            )
            return

        pubsub = await create_tracking_subscription(
            request_id=request_id,
        )

        await websocket.accept()

        await websocket.send_json(
            {
                "type": "tracking_connected",
                "request_id": str(request_id),
                "message": "Live provider tracking connected",
            }
        )

        websocket_reader_task = asyncio.create_task(
            read_websocket_messages(websocket)
        )

        redis_reader_task = asyncio.create_task(
            read_redis_messages(websocket, pubsub)
        )

        done, pending = await asyncio.wait(
            {
                websocket_reader_task,
                redis_reader_task,
            },
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        await asyncio.gather(
            *pending,
            return_exceptions=True,
        )

        for task in done:
            exception = task.exception()

            if exception is not None:
                raise exception

    except WebSocketDisconnect:
        pass

    except asyncio.CancelledError:
        raise

    except Exception as exc:
        print(
            f"Tracking WebSocket closed for request "
            f"{request_id}: {type(exc).__name__}"
        )

    finally:
        if websocket_reader_task is not None:
            websocket_reader_task.cancel()

        if redis_reader_task is not None:
            redis_reader_task.cancel()

        tasks_to_wait = [
            task
            for task in (
                websocket_reader_task,
                redis_reader_task,
            )
            if task is not None
        ]

        if tasks_to_wait:
            await asyncio.gather(
                *tasks_to_wait,
                return_exceptions=True,
            )

        if pubsub is not None:
            await close_tracking_subscription(
                pubsub=pubsub,
                request_id=request_id,
            )

        db.close()