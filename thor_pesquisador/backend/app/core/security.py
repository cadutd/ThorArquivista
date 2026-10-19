"""Browser request boundaries; no identity or raw URL enters telemetry."""
from time import monotonic
import hmac
import hashlib
from collections import OrderedDict
from threading import Lock
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from app.core.config import settings


class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        self.windows = OrderedDict()
        self.lock = Lock()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        method, path = scope["method"], scope["path"]
        limit = settings.upload_max_bytes + 1048576 if path in {
            "/api/v1/imagens/upload", "/api/v1/instrumentos/imagens-card"} else 1048576
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Content-Length invalido."}, 400)(scope, receive, send)
        if length < 0 or length > limit:
            return await JSONResponse({"detail": "Requisicao excede o limite permitido."}, 413)(scope, receive, send)
        origin = headers.get(b"origin", b"").decode("latin1")
        if method not in {"GET", "HEAD", "OPTIONS"} and (
                (origin and origin not in settings.cors_origins) or
                headers.get(b"sec-fetch-site") == b"cross-site"):
            return await JSONResponse({"detail": "Origem nao permitida."}, 403)(scope, receive, send)
        category = "login" if path == "/api/v1/auth/govbr/start" else "catalogo" if path in {
            "/api/v1/publico/instrumentos", "/api/v1/publico/destaques"} else None
        if category:
            ip = str(scope.get("client", ("unknown",))[0])
            key = hmac.new(settings.app_session_secret.encode(), (category+ip).encode(), hashlib.sha256).hexdigest()
            now = monotonic()
            with self.lock:
                window, count = self.windows.pop(key, (now, 0))
                if now - window >= 60:
                    window, count = now, 0
                count += 1
                self.windows[key] = (window, count)
                while len(self.windows) > 4096:
                    self.windows.popitem(last=False)
            if count > (30 if category == "login" else 300):
                return await JSONResponse({"detail": "Muitas solicitacoes. Tente novamente em instantes."}, 429,
                                          headers={"Retry-After": "60"})(scope, receive, send)

        async def secured(message):
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                # Responses may contain a session-dependent identity even under /publico.
                response_headers = [(k,v) for k,v in response_headers if k.lower() != b"cache-control"]
                response_headers += [(b"cache-control", b"private, no-store"),
                    (b"x-content-type-options", b"nosniff"), (b"referrer-policy", b"same-origin"),
                    (b"x-frame-options", b"DENY"), (b"permissions-policy", b"camera=(), microphone=(), geolocation=()")]
                message["headers"] = response_headers
            await send(message)
        received = 0
        async def bounded_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > limit:
                raise HTTPException(413, "Requisicao excede o limite permitido.")
            return message
        return await self.app(scope, bounded_receive, secured)
