import pytest
from app.services.sql.validator import SQLValidator, SQLValidationError

def test_valid_select():
    """Test that valid SELECT queries pass"""
    sql = "SELECT * FROM users WHERE id = 1"
    SQLValidator.validate(sql)  # Should not raise

def test_reject_insert():
    """Test that INSERT is rejected"""
    sql = "INSERT INTO users (name) VALUES ('hacker')"
    with pytest.raises(SQLValidationError, match="INSERT"):
        SQLValidator.validate(sql)

def test_reject_update():
    """Test that UPDATE is rejected"""
    sql = "UPDATE users SET role = 'admin' WHERE id = 1"
    with pytest.raises(SQLValidationError, match="UPDATE"):
        SQLValidator.validate(sql)

def test_reject_delete():
    """Test that DELETE is rejected"""
    sql = "DELETE FROM users WHERE id = 1"
    with pytest.raises(SQLValidationError, match="DELETE"):
        SQLValidator.validate(sql)

def test_reject_drop():
    """Test that DROP is rejected"""
    sql = "DROP TABLE users"
    with pytest.raises(SQLValidationError, match="DROP"):
        SQLValidator.validate(sql)

def test_reject_alter():
    """Test that ALTER is rejected"""
    sql = "ALTER TABLE users ADD COLUMN hacked TEXT"
    with pytest.raises(SQLValidationError, match="ALTER"):
        SQLValidator.validate(sql)

def test_reject_truncate():
    """Test that TRUNCATE is rejected"""
    sql = "TRUNCATE TABLE users"
    with pytest.raises(SQLValidationError, match="TRUNCATE"):
        SQLValidator.validate(sql)

def test_reject_create():
    """Test that CREATE is rejected"""
    sql = "CREATE TABLE malicious (id INT)"
    with pytest.raises(SQLValidationError, match="CREATE"):
        SQLValidator.validate(sql)

def test_reject_stacked_queries():
    """Test that stacked queries are rejected"""
    sql = "SELECT * FROM users; DROP TABLE users"
    # Will be caught by DROP keyword check
    with pytest.raises(SQLValidationError, match="DROP"):
        SQLValidator.validate(sql)

def test_sanitize_limit_adds_limit():
    """Test that LIMIT is added if missing"""
    sql = "SELECT * FROM users"
    result = SQLValidator.sanitize_limit(sql, max_rows=100)
    assert "LIMIT 100" in result

def test_sanitize_limit_caps_existing():
    """Test that excessive LIMIT is capped"""
    sql = "SELECT * FROM users LIMIT 5000"
    result = SQLValidator.sanitize_limit(sql, max_rows=1000)
    assert "LIMIT 1000" in result
    assert "LIMIT 5000" not in result

def test_with_cte_allowed():
    """Test that CTEs starting with WITH are allowed"""
    sql = """
        WITH revenue AS (
            SELECT SUM(amount) as total FROM orders
        )
        SELECT * FROM revenue
    """
    SQLValidator.validate(sql)  # Should not raise

def test_case_insensitive_keyword_detection():
    """Test that validation is case-insensitive"""
    sql = "select * from users; InSeRt InTo users (name) VALUES ('x')"
    with pytest.raises(SQLValidationError):
        SQLValidator.validate(sql)

# Adversarial SQL Injection Tests

def test_sql_injection_union():
    """Test that UNION-based injection is handled"""
    sql = "SELECT * FROM users WHERE id = 1 UNION SELECT * FROM passwords"
    # This should pass validation (it's still a SELECT)
    # but would fail if passwords table doesn't exist
    SQLValidator.validate(sql)

def test_sql_injection_comment():
    """Test comment-based injection attempts"""
    sql = "SELECT * FROM users WHERE id = 1 -- AND role = 'user'"
    # Comments are suspicious but not automatically rejected
    # The actual query is still valid SELECT
    SQLValidator.validate(sql)

def test_sql_injection_always_true():
    """Test always-true condition injection"""
    sql = "SELECT * FROM users WHERE id = 1 OR 1=1"
    # This is a valid SELECT, just with a logic flaw
    # Business logic should prevent this at query generation
    SQLValidator.validate(sql)

def test_empty_query():
    """Test that empty queries are rejected"""
    with pytest.raises(SQLValidationError, match="Empty"):
        SQLValidator.validate("")

def test_only_whitespace():
    """Test that whitespace-only queries are rejected"""
    with pytest.raises(SQLValidationError, match="Empty"):
        SQLValidator.validate("   \n   ")
