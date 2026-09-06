import pytest
from app.services.sql.agent import SQLAgent, SQLResult
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

class MockSession:
    async def execute(self, query):
        class MockResult:
            def all(self):
                # Return mock schema data
                if "information_schema" in str(query):
                    class Row:
                        def __init__(self, table, col, dtype, nullable):
                            self.table_name = table
                            self.column_name = col
                            self.data_type = dtype
                            self.is_nullable = nullable
                    return [
                        Row("orders", "id", "integer", "NO"),
                        Row("orders", "total_amount", "numeric", "NO"),
                        Row("orders", "status", "varchar", "NO"),
                    ]
                return []
        return MockResult()

@pytest.mark.asyncio
async def test_sql_agent_schema_inspection():
    """Test that schema inspection works"""
    agent = SQLAgent(MockSession())
    schema = await agent.inspect_schema(tenant_id=1)
    assert len(schema) > 0

@pytest.mark.asyncio
async def test_sql_agent_identify_tables():
    """Test table identification from query"""
    agent = SQLAgent(MockSession())
    schema = []  # Not needed for this test
    query = "What is the total revenue?"
    tables = await agent.identify_relevant_tables(query, schema)
    assert "orders" in tables

@pytest.mark.asyncio
async def test_sql_agent_validation_blocks_writes():
    """Test that the agent rejects write operations"""
    agent = SQLAgent(MockSession())
    result = await agent.execute_sql(
        "INSERT INTO users (name) VALUES ('hacker')",
        tenant_id=1
    )
    assert not result.success
    assert "Validation error" in result.error
