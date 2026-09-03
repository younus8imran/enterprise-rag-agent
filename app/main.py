from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppBaseException
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url=f"{settings.API_V1_STR}/docs" if settings.APP_DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.APP_DEBUG else None,
)

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

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
