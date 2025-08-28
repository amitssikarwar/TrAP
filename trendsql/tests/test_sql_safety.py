import pytest
from app.sql_safety import ensure_safe_select, sanitize_sql, extract_sql_from_code_block


class TestSQLSafety:
    def test_safe_select_queries(self):
        """Test that safe SELECT queries are allowed."""
        safe_queries = [
            "SELECT * FROM table",
            "SELECT column1, column2 FROM table WHERE condition",
            "WITH cte AS (SELECT * FROM table) SELECT * FROM cte",
            "EXPLAIN SELECT * FROM table",
            "SELECT * FROM table ORDER BY column1 LIMIT 10",
            "SELECT COUNT(*) FROM table",
        ]
        
        for query in safe_queries:
            is_safe, error = ensure_safe_select(query)
            assert is_safe, f"Query should be safe: {query}, error: {error}"
    
    def test_unsafe_queries(self):
        """Test that unsafe queries are blocked."""
        unsafe_queries = [
            ("INSERT INTO table VALUES (1, 2)", "INSERT"),
            ("UPDATE table SET column = 1", "UPDATE"),
            ("DELETE FROM table", "DELETE"),
            ("DROP TABLE table", "DROP"),
            ("CREATE TABLE table (id INT)", "CREATE"),
            ("ALTER TABLE table ADD COLUMN", "ALTER"),
            ("TRUNCATE TABLE table", "TRUNCATE"),
            ("GRANT SELECT ON table TO user", "GRANT"),
            ("REVOKE SELECT ON table FROM user", "REVOKE"),
        ]
        
        for query, expected_keyword in unsafe_queries:
            is_safe, error = ensure_safe_select(query)
            assert not is_safe, f"Query should be unsafe: {query}"
            assert expected_keyword in error, f"Error should mention {expected_keyword}"
    
    def test_sql_injection_attempts(self):
        """Test that SQL injection attempts are blocked."""
        injection_attempts = [
            "SELECT * FROM table; DROP TABLE users;",
            "SELECT * FROM table UNION SELECT * FROM users",
            "SELECT * FROM table UNION ALL SELECT * FROM users",
        ]
        
        for query in injection_attempts:
            is_safe, error = ensure_safe_select(query)
            assert not is_safe, f"SQL injection attempt should be blocked: {query}"
    
    def test_sanitize_sql(self):
        """Test SQL sanitization."""
        # Test comment removal
        sql_with_comments = "SELECT * FROM table -- this is a comment"
        sanitized = sanitize_sql(sql_with_comments)
        assert "--" not in sanitized
        
        # Test multi-line comment removal
        sql_with_ml_comments = "SELECT * FROM table /* multi-line comment */ WHERE id = 1"
        sanitized = sanitize_sql(sql_with_ml_comments)
        assert "/*" not in sanitized and "*/" not in sanitized
        
        # Test whitespace normalization
        sql_with_whitespace = "SELECT    *    FROM    table"
        sanitized = sanitize_sql(sql_with_whitespace)
        assert "    " not in sanitized
    
    def test_extract_sql_from_code_block(self):
        """Test SQL extraction from markdown code blocks."""
        # Test with ```sql block
        markdown = "Here's the SQL:\n```sql\nSELECT * FROM table\n```"
        sql = extract_sql_from_code_block(markdown)
        assert sql == "SELECT * FROM table"
        
        # Test with ``` block (no language)
        markdown = "Here's the SQL:\n```\nSELECT * FROM table\n```"
        sql = extract_sql_from_code_block(markdown)
        assert sql == "SELECT * FROM table"
        
        # Test without code block
        markdown = "SELECT * FROM table"
        sql = extract_sql_from_code_block(markdown)
        assert sql == "SELECT * FROM table"
        
        # Test empty input
        sql = extract_sql_from_code_block("")
        assert sql is None
    
    def test_case_insensitive_safety(self):
        """Test that safety checks are case insensitive."""
        # Test uppercase
        is_safe, _ = ensure_safe_select("SELECT * FROM table")
        assert is_safe
        
        # Test lowercase
        is_safe, _ = ensure_safe_select("select * from table")
        assert is_safe
        
        # Test mixed case
        is_safe, _ = ensure_safe_select("SeLeCt * FrOm table")
        assert is_safe
        
        # Test unsafe mixed case
        is_safe, _ = ensure_safe_select("InSeRt InTo table")
        assert not is_safe
