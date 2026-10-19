"""Correlation without recording URLs, query strings, credentials or request bodies."""
import json
import logging
import time
import uuid
from threading import Lock
from contextvars import ContextVar
from app.core.config import settings

request_id_context = ContextVar("request_id", default=None)
metrics_lock = Lock()
http_metrics = {}
HTTP_BUCKETS = (.01, .05, .1, .5, 1, 5)
logger = logging.getLogger("thor.requests")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())
logger.propagate = False
# Uvicorn's access log includes raw callback query strings (authorization codes).
logging.getLogger("uvicorn.access").disabled = True


class SanitizedExceptionFilter(logging.Filter):
    def filter(self, record):
        if record.exc_info:
            error = record.exc_info[1]
            record.msg = json.dumps({"evento": "falha_http", "request_id": request_id_context.get(),
                                     "erro_tipo": type(error).__name__})
            record.args = ()
            record.exc_info = record.exc_text = record.stack_info = None
        return True


logging.getLogger("uvicorn.error").addFilter(SanitizedExceptionFilter())


class RequestContextMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            request_id = str(uuid.UUID(headers.get(b"x-request-id", b"").decode("ascii")))
        except (ValueError, UnicodeError):
            request_id = str(uuid.uuid4())
        token = request_id_context.set(request_id)
        start, status = time.monotonic(), 500

        async def correlated(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"] = list(message.get("headers", [])) + [(b"x-request-id", request_id.encode())]
            await send(message)
        try:
            await self.app(scope, receive, correlated)
        finally:
            route = getattr(scope.get("route"), "path", "unmatched")
            # Included routers in recent FastAPI expose the local route template.
            if route != "unmatched" and not route.startswith("/api/v1"):
                module = getattr(scope.get("endpoint"), "__module__", "")
                prefix = "/api/v1/auth" if module.endswith(".auth") else (
                    "/api/v1/instrumentos" if module.endswith(".instrumentos") else "/api/v1")
                route = prefix + route
            data = {"request_id": request_id, "metodo": scope["method"], "rota": route,
                    "status": status, "duracao_ms": round((time.monotonic() - start) * 1000)}
            method = scope["method"] if scope["method"] in {"GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS"} else "OUTRO"
            key = (route, method, str(status // 100) + "xx")
            elapsed = time.monotonic() - start
            with metrics_lock:
                values = http_metrics.setdefault(key, [0, 0.0, [0] * len(HTTP_BUCKETS)])
                values[0] += 1
                values[1] += elapsed
                for index, bucket in enumerate(HTTP_BUCKETS):
                    if elapsed <= bucket:
                        values[2][index] += 1
            logger.info(json.dumps(data, separators=(",", ":")))
            try:
                from app.db.session import SessionLocal
                from app.models.conformidade import LogRequisicao
                with SessionLocal() as db:
                    if settings.log_tecnico_persistir:
                        db.add(LogRequisicao(**data, categoria="LOG_TECNICO"))
                    if settings.log_acesso_consultivo and route.startswith("/api/v1/publico"):
                        db.add(LogRequisicao(**data, categoria="ACESSO_CONSULTIVO"))
                    if route in {"/api/v1/auth/dev-login", "/api/v1/auth/govbr/callback"} and status >= 400:
                        from app.services.auditoria_service import registrar
                        registrar(db, "LOGIN_FALHOU", "sessao", detalhe={"status": status})
                    db.commit()
            except Exception:
                logger.warning(json.dumps({"request_id": request_id, "evento": "persistencia_log_indisponivel"}))
            request_id_context.reset(token)
