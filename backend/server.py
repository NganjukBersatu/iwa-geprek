"""Single entry point: the mobile app (/v2) plus the management web (/web/management) in one backend."""
from app.core import web_proxy
from app.main import app
from web.management.router import router as web_router

app.include_router(web_router)
web_proxy.install(app)
