import pytest
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

@pytest.mark.asyncio
async def test_database_connectivity():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT 1"))
        assert res.scalar() == 1

@pytest.mark.asyncio
async def test_seed_data_presence():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        # Test if tenants exist
        res = await conn.execute(text("SELECT count(*) FROM tenants"))
        assert res.scalar() > 0

        # Test if employees exist
        res = await conn.execute(text("SELECT count(*) FROM employees"))
        assert res.scalar() > 0

        # Test if orders exist
        res = await conn.execute(text("SELECT count(*) FROM orders"))
        assert res.scalar() > 0

@pytest.mark.asyncio
async def test_read_only_sql_access():
    # Connect as the read-only user
    ro_url = settings.DATABASE_URL.replace(
        "postgres:postgres", "sql_agent_user:read_only_password"
    )
    engine = create_async_engine(ro_url)
    async with engine.connect() as conn:
        # SELECT should work
        res = await conn.execute(text("SELECT 1"))
        assert res.scalar() == 1

        # INSERT should fail
        with pytest.raises(Exception):
            await conn.execute(text("INSERT INTO tenants (name) VALUES ('Hack')"))
