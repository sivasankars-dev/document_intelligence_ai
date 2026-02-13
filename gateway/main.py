from fastapi import FastAPI
from gateway.api.v1 import auth_routes, document_routes
from shared.config.settings import settings
from gateway.api.v1.qa_routes import router as qa_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.PROJECT_NAME)

    # Register Routers
    app.include_router(auth_routes.router, prefix="/api/v1/auth")
    # Document Routers
    app.include_router(document_routes.router, prefix="/api/v1/documents")
    
    app.include_router(qa_router, prefix="/api/v1/qa", tags=["QA"])

    return app

app = create_app()
