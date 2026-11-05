"""Harbor Market application factory."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from demo_app.routes import router
from demo_app.store import Store

PACKAGE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    app = FastAPI(
        title="Harbor Market",
        version="1.0.0",
        description="Small demo shop used as the system under test.",
    )
    app.state.store = Store()
    app.state.templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
    app.mount("/static", StaticFiles(directory=str(PACKAGE_DIR / "static")), name="static")
    app.include_router(router)
    return app


app = create_app()
