from fastapi import FastAPI
from gateway.api.v1 import auth_routes
from shared.config.settings import settings


def create_app() -> FastAPI:

    app = FastAPI(
        title=settings.PROJECT_NAME
    )

    # Register Routers
    app.include_router(auth_routes.router, prefix="/api/v1/auth")

    return app


app = create_app()
