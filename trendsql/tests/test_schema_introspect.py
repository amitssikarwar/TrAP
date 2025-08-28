import pytest
import psycopg
from unittest.mock import Mock, patch
from app.schema_introspect import get_schema_summary, format_schema_for_llm


class TestSchemaIntrospect:
    def test_get_schema_summary(self):
        """Test schema summary retrieval."""
        # Mock database connection and cursor
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("public", "users", "id", "integer", "NO", None),
            ("public", "users", "name", "text", "YES", None),
            ("public", "users", "email", "text", "NO", None),
            ("public", "posts", "id", "integer", "NO", None),
            ("public", "posts", "title", "text", "NO", None),
            ("public", "posts", "user_id", "integer", "YES", None),
        ]
        
        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Test schema summary
        result = get_schema_summary(mock_conn, ["public"])
        
        # Verify structure
        assert "public" in result
        assert "users" in result["public"]
        assert "posts" in result["public"]
        
        # Verify columns
        users_columns = result["public"]["users"]
        assert len(users_columns) == 3
        assert users_columns[0]["column"] == "id"
        assert users_columns[0]["type"] == "integer"
        assert users_columns[0]["nullable"] == False
        
        posts_columns = result["public"]["posts"]
        assert len(posts_columns) == 3
        assert posts_columns[1]["column"] == "title"
        assert posts_columns[1]["type"] == "text"
        assert posts_columns[1]["nullable"] == False
    
    def test_get_schema_summary_multiple_schemas(self):
        """Test schema summary with multiple schemas."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("public", "users", "id", "integer", "NO", None),
            ("private", "secrets", "key", "text", "NO", None),
        ]
        
        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = get_schema_summary(mock_conn, ["public", "private"])
        
        assert "public" in result
        assert "private" in result
        assert "users" in result["public"]
        assert "secrets" in result["private"]
    
    def test_get_schema_summary_default_schema(self):
        """Test schema summary with default schema."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("public", "users", "id", "integer", "NO", None),
        ]
        
        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = get_schema_summary(mock_conn)  # No schemas specified
        
        assert "public" in result
        assert "users" in result["public"]
    
    def test_format_schema_for_llm(self):
        """Test schema formatting for LLM."""
        schema_summary = {
            "public": {
                "users": [
                    {"column": "id", "type": "integer", "nullable": False, "default": None},
                    {"column": "name", "type": "text", "nullable": True, "default": None},
                    {"column": "email", "type": "text", "nullable": False, "default": "'user@example.com'"},
                ],
                "posts": [
                    {"column": "id", "type": "integer", "nullable": False, "default": None},
                    {"column": "title", "type": "text", "nullable": False, "default": None},
                ]
            }
        }
        
        formatted = format_schema_for_llm(schema_summary)
        
        # Check that it contains expected elements
        assert "Database Schema:" in formatted
        assert "Schema: public" in formatted
        assert "Table: users" in formatted
        assert "Table: posts" in formatted
        assert "id: integer NOT NULL" in formatted
        assert "name: text NULL" in formatted
        assert "email: text NOT NULL DEFAULT 'user@example.com'" in formatted
    
    def test_format_schema_for_llm_empty(self):
        """Test schema formatting with empty schema."""
        schema_summary = {}
        formatted = format_schema_for_llm(schema_summary)
        
        assert "Database Schema:" in formatted
        assert len(formatted.split('\n')) == 1  # Only the header
    
    def test_database_error_handling(self):
        """Test error handling when database query fails."""
        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            get_schema_summary(mock_conn, ["public"])
    
    def test_schema_filtering(self):
        """Test that only requested schemas are included."""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("public", "users", "id", "integer", "NO", None),
            ("private", "secrets", "key", "text", "NO", None),
            ("system", "config", "setting", "text", "NO", None),
        ]
        
        mock_conn = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        result = get_schema_summary(mock_conn, ["public", "private"])
        
        assert "public" in result
        assert "private" in result
        assert "system" not in result  # Should be filtered out
