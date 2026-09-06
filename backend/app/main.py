from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppBaseException
from app.core.logging import setup_logging

setup_logging()

# bearer_scheme = HTTPBearer(auto_error=False, bearerFormat="JWT")

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url=f"{settings.API_V1_STR}/docs" if settings.APP_DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.APP_DEBUG else None,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.APP_DEBUG else None,
    openapi_tags=[{"name": "auth", "description": "Bearer JWT (pyjwt+passlib)"}],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# HTTPS redirect in production
if settings.APP_ENV == "production" and settings.APP_DEBUG is False:
    app.add_middleware(HTTPSRedirectMiddleware)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    # response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler
@app.exception_handler(AppBaseException)
async def app_exception_handler(request, exc: AppBaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "details": exc.details},
    )

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
