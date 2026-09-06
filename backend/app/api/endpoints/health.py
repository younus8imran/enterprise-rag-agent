from fastapi import APIRouter
from app.core.logging import logger

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    logger.info("health_check_called")
    return {"status": "healthy", "version": "0.1.0"}
