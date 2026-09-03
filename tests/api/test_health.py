import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import Settings

@pytest.mark.asyncio
async def test_health_endpoint():
    # httpx AsyncClient uses transport for FastAPI app testing
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "0.1.0"}

@pytest.mark.asyncio
async def test_config_loading():
    # Test if settings load default or provided values
    from app.core.config import settings
    # The .env.example has APP_NAME=enterprise-intelligence-agent
    # and we copied it to .env. We should check for that value.
    assert settings.APP_NAME == "enterprise-intelligence-agent"
