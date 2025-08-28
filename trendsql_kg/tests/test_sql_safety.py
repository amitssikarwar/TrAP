"""
Test SQL Safety Module
"""

import pytest
from app.sql_safety import is_safe_sql, sanitize_sql


class TestSQLSafety:
    """Test SQL safety validation"""
    
    def test_safe_select_query(self):
        """Test that safe SELECT queries pass validation"""
        safe_queries = [
            "SELECT * FROM exploding_topics",
            "SELECT topic, growth_score FROM exploding_topics WHERE region = 'IN'",
            "SELECT COUNT(*) FROM gt_interest_over_time",
            "WITH top_topics AS (SELECT topic FROM exploding_topics LIMIT 10) SELECT * FROM top_topics"
        ]
        
        for query in safe_queries:
            is_safe, error = is_safe_sql(query)
            assert is_safe, f"Query should be safe: {query}, error: {error}"
    
    def test_dangerous_queries(self):
        """Test that dangerous queries are blocked"""
        dangerous_queries = [
            "INSERT INTO exploding_topics VALUES (1, 'test')",
            "UPDATE exploding_topics SET topic = 'test'",
            "DELETE FROM exploding_topics",
            "DROP TABLE exploding_topics",
            "CREATE TABLE test (id INT)",
            "ALTER TABLE exploding_topics ADD COLUMN test TEXT",
            "TRUNCATE TABLE exploding_topics",
            "GRANT ALL ON exploding_topics TO user",
            "EXECUTE FUNCTION dangerous_function()"
        ]
        
        for query in dangerous_queries:
            is_safe, error = is_safe_sql(query)
            assert not is_safe, f"Query should be blocked: {query}"
            assert error is not None, f"Should have error message for: {query}"
    
    def test_sql_sanitization(self):
        """Test SQL sanitization"""
        # Test comment removal
        sql_with_comments = """
        SELECT topic -- This is a comment
        FROM exploding_topics
        /* Multi-line comment */
        WHERE region = 'IN'
        """
        sanitized = sanitize_sql(sql_with_comments)
        assert "--" not in sanitized
        assert "/*" not in sanitized
        assert "*/" not in sanitized
        
        # Test multiple statement removal
        multi_sql = "SELECT 1; SELECT 2; SELECT 3;"
        sanitized = sanitize_sql(multi_sql)
        assert sanitized.strip() == "SELECT 1"
    
    def test_empty_query(self):
        """Test empty query handling"""
        is_safe, error = is_safe_sql("")
        assert not is_safe
        assert "Empty SQL query" in error
        
        is_safe, error = is_safe_sql("   ")
        assert not is_safe
        assert "Empty SQL query" in error
    
    def test_complex_safe_queries(self):
        """Test complex but safe queries"""
        complex_queries = [
            """
            SELECT 
                t.topic,
                t.growth_score,
                COUNT(g.interest) as interest_count
            FROM exploding_topics t
            LEFT JOIN gt_interest_over_time g ON t.topic = g.keyword
            WHERE t.region = 'IN'
            GROUP BY t.topic, t.growth_score
            ORDER BY t.growth_score DESC
            LIMIT 10
            """,
            """
            WITH trending_topics AS (
                SELECT topic, growth_score
                FROM exploding_topics
                WHERE growth_score > 50
            )
            SELECT * FROM trending_topics
            """
        ]
        
        for query in complex_queries:
            is_safe, error = is_safe_sql(query)
            assert is_safe, f"Complex query should be safe: {error}"
