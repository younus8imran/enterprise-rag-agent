from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.services.llm.mistral_chat import MistralChatProvider
from app.services.sql.validator import SQLValidationError, SQLValidator


class TableSchema(BaseModel):
    table_name: str
    columns: List[Dict[str, Any]]
    sample_values: Optional[Dict[str, Any]] = None


class SQLResult(BaseModel):
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    sql: str
    row_count: int = 0


class SQLAgent:
    """
    Production-conscious SQL agent with schema inspection,
    validation, and self-correction.
    """

    MAX_RETRIES = 2

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.validator = SQLValidator()

    async def inspect_schema(self, tenant_id: int) -> List[TableSchema]:
        """
        Inspects the database schema to understand available tables and columns.
        Never invents schema information.
        """
        logger.info("inspecting_schema", tenant_id=tenant_id)

        # Query information_schema for table and column metadata
        schema_query = text("""
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name IN ('tenants', 'users', 'employees', 'departments',
                               'regions', 'customers', 'products', 'orders',
                               'order_items', 'expenses')
            ORDER BY table_name, ordinal_position
        """)

        result = await self.db.execute(schema_query)
        rows = result.all()

        # Group by table
        tables = {}
        for row in rows:
            table_name = row.table_name
            if table_name not in tables:
                tables[table_name] = []
            tables[table_name].append(
                {
                    "column_name": row.column_name,
                    "data_type": row.data_type,
                    "nullable": row.is_nullable == "YES",
                }
            )

        return [
            TableSchema(table_name=name, columns=cols) for name, cols in tables.items()
        ]

    async def identify_relevant_tables(
        self, query: str, schema: List[TableSchema]
    ) -> List[str]:
        """
        Identifies which tables are relevant to answer the query.
        Uses keyword matching as a simple heuristic.
        """
        query_lower = query.lower()
        relevant = []

        keywords = {
            "revenue": ["orders", "order_items", "products"],
            "sales": ["orders", "order_items", "customers"],
            "employee": ["employees", "departments"],
            "customer": ["customers", "orders"],
            "product": ["products", "order_items"],
            "expense": ["expenses", "departments"],
            "region": ["regions", "customers", "departments"],
        }

        for keyword, tables in keywords.items():
            if keyword in query_lower:
                relevant.extend(tables)

        # Deduplicate
        return list(set(relevant))

    async def generate_sql(
        self, query: str, schema: List[TableSchema], relevant_tables: List[str]
    ) -> str:
        """Generates SQL using Mistral LLM given the query and schema."""
        logger.info("generating_sql", query=query, tables=relevant_tables)

        schema_lines = "\n".join(
            f"  {t.table_name}: " + ", ".join(c["column_name"] for c in t.columns)
            for t in schema if t.table_name in relevant_tables
        )
        prompt = (
            f"You are a SQL expert. Given the natural language question and database schema, "
            f"output ONLY the SQL query (no explanation).\n\nSchema:\n{schema_lines}\n\n"
            f"Question: {query}\n\nSQL:"
        )
        chat = MistralChatProvider()
        sql = await chat.generate_answer(query, f"Schema:\n{schema_lines}\n\nQuestion: {query}")
        # Strip markdown code fences if present
        return sql.strip().strip("```sql").strip("```").strip()

    async def execute_sql(self, sql: str, tenant_id: int) -> SQLResult:
        """
        Executes SQL with validation and returns structured results.
        """
        try:
            # Validate
            self.validator.validate(sql)

            # Add safety limit
            sql = self.validator.sanitize_limit(sql, max_rows=1000)

            # Execute
            logger.info("executing_sql", sql=sql[:100])
            result = await self.db.execute(text(sql))
            rows = result.all()

            # Convert to dict
            data = [dict(row._mapping) for row in rows]

            return SQLResult(success=True, data=data, sql=sql, row_count=len(data))

        except SQLValidationError as e:
            logger.error("sql_validation_failed", error=str(e))
            return SQLResult(
                success=False, error=f"Validation error: {str(e)}", sql=sql
            )
        except Exception as e:
            logger.error("sql_execution_failed", error=str(e))
            return SQLResult(success=False, error=f"Execution error: {str(e)}", sql=sql)

    async def analyze_error(self, error: str, sql: str) -> str:
        """
        Analyzes the error and suggests a correction.
        In production, this would use an LLM.
        """
        if "does not exist" in error.lower():
            return "Table or column does not exist. Check schema."
        elif "syntax error" in error.lower():
            return "SQL syntax error. Review query structure."
        else:
            return "Unknown error. Manual review needed."

    async def correct_sql(
        self, original_sql: str, error: str, schema: List[TableSchema]
    ) -> str:
        """Attempts to correct SQL using Mistral LLM given the error context."""
        logger.info("correcting_sql", error=error)
        schema_lines = "\n".join(
            f"  {t.table_name}: " + ", ".join(c["column_name"] for c in t.columns)
            for t in schema
        )
        prompt = (
            f"Correct the following SQL query based on the error.\n\n"
            f"Schema:\n{schema_lines}\n\n"
            f"Original SQL:\n{original_sql}\n\n"
            f"Error:\n{error}\n\n"
            f"Corrected SQL:"
        )
        chat = MistralChatProvider()
        corrected = await chat.generate_answer("", prompt)
        return corrected.strip().strip("```sql").strip("```").strip()

    async def query_with_retry(self, nl_query: str, tenant_id: int) -> SQLResult:
        """
        Full pipeline: Generate → Validate → Execute → Retry on failure.
        """
        logger.info("sql_agent_query", query=nl_query, tenant_id=tenant_id)

        # 1. Inspect schema
        schema = await self.inspect_schema(tenant_id)

        # 2. Identify relevant tables
        relevant_tables = await self.identify_relevant_tables(nl_query, schema)

        # 3. Generate SQL
        sql = await self.generate_sql(nl_query, schema, relevant_tables)

        # 4. Execute with retry loop
        for attempt in range(self.MAX_RETRIES + 1):
            result = await self.execute_sql(sql, tenant_id)

            if result.success:
                logger.info("sql_execution_success", attempt=attempt)
                return result

            # If failed and retries remain
            if attempt < self.MAX_RETRIES:
                logger.info("sql_retry", attempt=attempt, error=result.error)
                analysis = await self.analyze_error(result.error, sql)
                sql = await self.correct_sql(sql, result.error, schema)
            else:
                logger.error("sql_max_retries_exceeded")
                return result

        return result
