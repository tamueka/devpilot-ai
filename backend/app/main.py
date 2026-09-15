from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.chat import router as chat_router
from app.routers.conversations import router as conversations_router
from app.routers.projects import router as projects_router
from app.routers.readme import router as readme_router

from app.security.security_headers import (
    SecurityHeadersMiddleware,
)
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware,
)
from app.security.config import (
    get_allowed_origins,
    get_trusted_hosts,
)
from app.routers.auth import router as auth_router

app = FastAPI(
    title="DevPilot AI API",
    description="Backend de la plataforma de análisis inteligente de código",
    version="0.1.0",
)


app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=get_trusted_hosts(),
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "devpilot-ai",
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


app.include_router(projects_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(readme_router)
app.include_router(auth_router)
