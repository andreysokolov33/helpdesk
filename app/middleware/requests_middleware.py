import uuid
import time
import logging
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from .context import request_id_ctx_var

class RequestIDMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Request-ID"
    ):
        self.app = app
        self.header_name = header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Получаем request_id из заголовков
        headers = dict(scope.get("headers", []))
        request_id = headers.get(self.header_name.lower().encode(), str(uuid.uuid4()).encode())
        if isinstance(request_id, bytes):
            request_id = request_id.decode()

        # Устанавливаем request_id в контекст
        token = request_id_ctx_var.set(request_id)

        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (self.header_name.lower().encode(), str(request_id).encode())
                )
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_ctx_var.reset(token)

class TimingMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        logger: logging.Logger
    ):
        self.app = app
        self.logger = logger

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                duration = (time.time() - start_time) * 1000
                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-process-time-ms", str(f"{duration:.2f}").encode())
                )
                message["headers"] = headers

                # Получаем request_id в момент логирования
                current_request_id = request_id_ctx_var.get()

                self.logger.debug(
                    f"Request {scope['method']} {scope['path']} completed in {duration:.2f} ms",
                    extra={"request_id": current_request_id}
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)