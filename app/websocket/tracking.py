from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        self.connections: dict[
            str,
            set[WebSocket],
        ] = defaultdict(set)

    async def connect(
        self,
        request_id: str,
        websocket: WebSocket,
    ):

        await websocket.accept()

        self.connections[
            request_id
        ].add(websocket)

    def disconnect(
        self,
        request_id: str,
        websocket: WebSocket,
    ):

        connections = self.connections.get(
            request_id
        )

        if not connections:
            return

        connections.discard(websocket)

        if not connections:
            self.connections.pop(
                request_id,
                None,
            )

    async def broadcast(
        self,
        request_id: str,
        message: dict,
    ):

        connections = self.connections.get(
            request_id,
            set(),
        )

        disconnected = []

        for websocket in connections:

            try:

                await websocket.send_json(
                    message
                )

            except Exception:

                disconnected.append(
                    websocket
                )

        for websocket in disconnected:

            self.disconnect(
                request_id,
                websocket,
            )


manager = ConnectionManager()