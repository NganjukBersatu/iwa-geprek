"""Standalone FastAPI application that serves only the v2 routes."""
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import cache, live, logs, messages, query_budget, stock_balances
from app.core.cache_store import RedisStore
from app.core.database import Base, demo_schema_problem
from app.core.client_version import ClientVersionGate
from app.core import brand
from app.core.orders import open_bills_visibility
from app.core.error_answers import framework_refusal, unexpected_failure, validation_failed
from app.core.errors import DomainError, error_content
from app.core.stored_files import router as stored_files_router
from app.core.request_id import RequestId
from app.core.request_timing import RequestTiming
from app.core.security_headers import SecurityHeaders
from app.core.settings import SERVICE_ROOT, settings
from app.csp_reports.routes import router as csp_reports_router
from app.health import router as health_router
from app.router import router as v2_router

logs.install()

# Tanpa alamat publik, setiap foto akan menunjuk ke tempat yang salah, jadi layanan menolak jalan.
if not settings.public_url:
    raise RuntimeError("PUBLIC_URL belum diatur: isi dengan alamat publik layanan v2 ini, misalnya https://api.contoh.com")


def _refuse_stale_demo() -> None:
    """Proses demo menolak jalan bila skema demo belum ada atau tertinggal migrasi, karena tabel yang hilang di demo akan terbaca dari data asli."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    heads = ScriptDirectory.from_config(Config(str(SERVICE_ROOT / "alembic.ini"))).get_heads()
    problem = demo_schema_problem(heads[0]) if len(heads) == 1 else "Migrasi punya lebih dari satu ujung; gabungkan dulu."
    if problem is not None:
        raise RuntimeError(f"DEMO_MODE aktif tetapi data demo tidak siap. {problem}")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.demo_mode:
        _refuse_stale_demo()
    loop = asyncio.get_running_loop()
    live.hub.bind(loop)
    live.close_on_shutdown_signal(loop)
    open_bills_visibility.watch_open_bills()
    live.watch_commits()
    stock_balances.watch_card_writes()
    # Proses demo tidak memakai Redis, supaya cache dan sinyal langsungnya tidak pernah bercampur dengan proses asli.
    redis_url = "" if settings.demo_mode else settings.redis_url
    live.start_relay(redis_url)
    cache.start(RedisStore(redis_url) if redis_url else None, Base.metadata.tables, settings.railway_deployment_id)
    yield


# The API documentation lists every route, so it is served only when ENABLE_API_DOCS is set (development).
DOCS = {} if settings.enable_api_docs else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(title=brand.NAME, version="2.0.0", lifespan=lifespan, **DOCS)


@app.exception_handler(DBAPIError)
async def statement_too_long(request: Request, error: DBAPIError) -> JSONResponse:
    """A statement the database cancelled for passing the time limit answers clearly and is logged with the route; any other database error stays a server error."""
    if not query_budget.was_cancelled(error):
        raise error
    query_budget.log.error("cancelled past %d ms: %s %s", query_budget.QUERY_LIMIT_MILLISECONDS, request.method, request.url.path)
    return JSONResponse(status_code=503, content=error_content(503, messages.QUERY_TOO_LONG, "QUERY_TOO_LONG"))


@app.exception_handler(DomainError)
async def rule_refused(_: Request, error: DomainError) -> JSONResponse:
    """A business rule that reaches no route-level handling still answers with its own status and sentence, never a server error."""
    return JSONResponse(status_code=error.status, content=error_content(error.status, error.message, error.code, error.fields))


app.add_exception_handler(RequestValidationError, validation_failed)
app.add_exception_handler(StarletteHTTPException, framework_refusal)
app.add_exception_handler(Exception, unexpected_failure)

app.include_router(health_router)
app.include_router(csp_reports_router)
app.include_router(v2_router)
app.include_router(stored_files_router)
app.add_middleware(RequestTiming)
# Di dalam CORS, supaya penolakan versi lama tetap membawa izin CORS untuk PWA.
app.add_middleware(ClientVersionGate)
app.add_middleware(SecurityHeaders)
app.add_middleware(RequestId)

if settings.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"], expose_headers=["Content-Disposition"])
