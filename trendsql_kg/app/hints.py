"""
Hints Module for TrendsQL-KG
Provides intelligent error messages and suggestions
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class ErrorHints:
    """Error hints and suggestions for SQL queries"""
    
    def __init__(self):
        """Initialize error hints"""
        self.error_patterns = self._load_error_patterns()
        self.suggestion_templates = self._load_suggestion_templates()
    
    def get_hints(self, error_message: str, sql_query: str = "") -> Dict[str, Any]:
        """
        Get hints and suggestions for an error
        
        Args:
            error_message: PostgreSQL error message
            sql_query: Original SQL query (optional)
            
        Returns:
            Dictionary with hints and suggestions
        """
        hints = {
            'error_type': 'unknown',
            'suggestions': [],
            'examples': [],
            'documentation': []
        }
        
        # Determine error type and get specific hints
        error_type = self._classify_error(error_message)
        hints['error_type'] = error_type
        
        # Get suggestions based on error type
        hints['suggestions'] = self._get_suggestions(error_type, error_message, sql_query)
        
        # Get examples
        hints['examples'] = self._get_examples(error_type)
        
        # Get documentation links
        hints['documentation'] = self._get_documentation(error_type)
        
        return hints
    
    def _classify_error(self, error_message: str) -> str:
        """Classify the type of error"""
        error_lower = error_message.lower()
        
        if 'syntax error' in error_lower:
            return 'syntax_error'
        elif 'column' in error_lower and ('does not exist' in error_lower or 'not found' in error_lower):
            return 'column_not_found'
        elif 'table' in error_lower and ('does not exist' in error_lower or 'not found' in error_lower):
            return 'table_not_found'
        elif 'function' in error_lower and ('does not exist' in error_lower or 'not found' in error_lower):
            return 'function_not_found'
        elif 'type' in error_lower and 'does not exist' in error_lower:
            return 'type_not_found'
        elif 'permission denied' in error_lower:
            return 'permission_denied'
        elif 'duplicate key' in error_lower:
            return 'duplicate_key'
        elif 'foreign key' in error_lower:
            return 'foreign_key_violation'
        elif 'check constraint' in error_lower:
            return 'check_constraint'
        elif 'not null' in error_lower:
            return 'not_null_violation'
        elif 'data type' in error_lower:
            return 'data_type_mismatch'
        elif 'limit' in error_lower and 'exceeded' in error_lower:
            return 'limit_exceeded'
        else:
            return 'unknown'
    
    def _get_suggestions(self, error_type: str, error_message: str, sql_query: str) -> List[str]:
        """Get suggestions based on error type"""
        suggestions = []
        
        if error_type == 'syntax_error':
            suggestions.extend([
                "Check for missing or extra parentheses, quotes, or semicolons",
                "Verify that all keywords are spelled correctly",
                "Ensure proper spacing around operators",
                "Check for balanced parentheses in complex expressions"
            ])
            
            # Specific syntax suggestions
            if 'unterminated' in error_message.lower():
                suggestions.append("Check for unclosed quotes, parentheses, or comments")
            elif 'unexpected' in error_message.lower():
                suggestions.append("Look for misplaced keywords or operators")
        
        elif error_type == 'column_not_found':
            suggestions.extend([
                "Verify the column name exists in the specified table",
                "Check for typos in column names",
                "Ensure you're using the correct table alias",
                "Use the schema introspection to see available columns"
            ])
            
            # Try to extract column name from error
            column_match = re.search(r'column "([^"]+)"', error_message)
            if column_match:
                column_name = column_match.group(1)
                suggestions.append(f"Column '{column_name}' was not found. Check the table schema.")
        
        elif error_type == 'table_not_found':
            suggestions.extend([
                "Verify the table name exists in the database",
                "Check for typos in table names",
                "Ensure you're using the correct schema name",
                "Use the schema introspection to see available tables"
            ])
            
            # Try to extract table name from error
            table_match = re.search(r'relation "([^"]+)"', error_message)
            if table_match:
                table_name = table_match.group(1)
                suggestions.append(f"Table '{table_name}' was not found. Check the database schema.")
        
        elif error_type == 'function_not_found':
            suggestions.extend([
                "Verify the function name is correct",
                "Check if the function exists in the current schema",
                "Ensure you're using the correct number of arguments",
                "Check if the function requires specific data types"
            ])
        
        elif error_type == 'data_type_mismatch':
            suggestions.extend([
                "Check that column data types match your values",
                "Use explicit type casting if needed (e.g., ::text, ::integer)",
                "Verify date/time formats are correct",
                "Check for NULL values where NOT NULL is required"
            ])
        
        elif error_type == 'permission_denied':
            suggestions.extend([
                "This appears to be a permission issue",
                "Only SELECT queries are allowed in this system",
                "Check that you're not trying to modify data",
                "Verify your query only uses allowed tables and columns"
            ])
        
        elif error_type == 'limit_exceeded':
            suggestions.extend([
                "Add a LIMIT clause to restrict the number of results",
                "Use more specific WHERE conditions to reduce the result set",
                "Consider using pagination for large datasets"
            ])
        
        # General suggestions for all errors
        suggestions.extend([
            "Use the schema introspection endpoint to see available tables and columns",
            "Check the documentation for supported SQL features",
            "Try breaking down complex queries into simpler parts"
        ])
        
        return suggestions
    
    def _get_examples(self, error_type: str) -> List[Dict[str, str]]:
        """Get example queries for the error type"""
        examples = []
        
        if error_type == 'syntax_error':
            examples.extend([
                {
                    'title': 'Basic SELECT query',
                    'sql': 'SELECT topic, growth_score FROM exploding_topics LIMIT 10'
                },
                {
                    'title': 'SELECT with WHERE clause',
                    'sql': 'SELECT topic, region FROM exploding_topics WHERE region = \'IN\''
                },
                {
                    'title': 'SELECT with ORDER BY',
                    'sql': 'SELECT topic, growth_score FROM exploding_topics ORDER BY growth_score DESC'
                }
            ])
        
        elif error_type == 'column_not_found':
            examples.extend([
                {
                    'title': 'Check available columns',
                    'sql': 'SELECT column_name FROM information_schema.columns WHERE table_name = \'exploding_topics\''
                },
                {
                    'title': 'Correct column reference',
                    'sql': 'SELECT topic, growth_score FROM exploding_topics WHERE growth_score > 50'
                }
            ])
        
        elif error_type == 'table_not_found':
            examples.extend([
                {
                    'title': 'Check available tables',
                    'sql': 'SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\''
                },
                {
                    'title': 'Correct table reference',
                    'sql': 'SELECT topic FROM exploding_topics LIMIT 5'
                }
            ])
        
        elif error_type == 'data_type_mismatch':
            examples.extend([
                {
                    'title': 'String comparison',
                    'sql': 'SELECT topic FROM exploding_topics WHERE topic = \'Ayurveda for dogs\''
                },
                {
                    'title': 'Numeric comparison',
                    'sql': 'SELECT topic FROM exploding_topics WHERE growth_score > 50'
                },
                {
                    'title': 'Date comparison',
                    'sql': 'SELECT topic FROM exploding_topics WHERE first_seen_date > \'2023-01-01\''
                }
            ])
        
        return examples
    
    def _get_documentation(self, error_type: str) -> List[Dict[str, str]]:
        """Get documentation links for the error type"""
        docs = []
        
        base_docs = [
            {
                'title': 'TrendsQL-KG API Documentation',
                'url': '/docs'
            },
            {
                'title': 'Database Schema',
                'url': '/schema'
            }
        ]
        
        if error_type == 'syntax_error':
            docs.extend([
                {
                    'title': 'PostgreSQL SELECT Syntax',
                    'url': 'https://www.postgresql.org/docs/current/sql-select.html'
                }
            ])
        
        elif error_type in ['column_not_found', 'table_not_found']:
            docs.extend([
                {
                    'title': 'PostgreSQL Information Schema',
                    'url': 'https://www.postgresql.org/docs/current/information-schema.html'
                }
            ])
        
        elif error_type == 'function_not_found':
            docs.extend([
                {
                    'title': 'PostgreSQL Functions',
                    'url': 'https://www.postgresql.org/docs/current/functions.html'
                }
            ])
        
        docs.extend(base_docs)
        return docs
    
    def _load_error_patterns(self) -> Dict[str, List[str]]:
        """Load error patterns for classification"""
        return {
            'syntax_error': [
                r'syntax error',
                r'unterminated',
                r'unexpected',
                r'missing',
                r'extra'
            ],
            'column_not_found': [
                r'column "[^"]+" does not exist',
                r'column "[^"]+" not found'
            ],
            'table_not_found': [
                r'relation "[^"]+" does not exist',
                r'table "[^"]+" not found'
            ],
            'function_not_found': [
                r'function "[^"]+" does not exist',
                r'function "[^"]+" not found'
            ]
        }
    
    def _load_suggestion_templates(self) -> Dict[str, List[str]]:
        """Load suggestion templates"""
        return {
            'syntax_error': [
                "Check for {issue} in your SQL query",
                "Verify that {element} is correct",
                "Ensure proper {aspect} in your query"
            ],
            'column_not_found': [
                "Column '{column}' was not found in table '{table}'",
                "Check the schema for available columns in {table}",
                "Verify the column name spelling"
            ]
        }


class QueryOptimizer:
    """Query optimization suggestions"""
    
    def __init__(self):
        """Initialize query optimizer"""
        self.optimization_patterns = self._load_optimization_patterns()
    
    def get_optimization_suggestions(self, sql_query: str) -> List[str]:
        """
        Get optimization suggestions for a SQL query
        
        Args:
            sql_query: SQL query to analyze
            
        Returns:
            List of optimization suggestions
        """
        suggestions = []
        
        # Check for common optimization opportunities
        if self._has_no_limit(sql_query):
            suggestions.append("Consider adding a LIMIT clause to prevent large result sets")
        
        if self._has_no_where(sql_query):
            suggestions.append("Consider adding WHERE conditions to filter results")
        
        if self._has_select_star(sql_query):
            suggestions.append("Consider selecting specific columns instead of * for better performance")
        
        if self._has_no_order_by(sql_query):
            suggestions.append("Consider adding ORDER BY for consistent result ordering")
        
        if self._has_complex_joins(sql_query):
            suggestions.append("Consider optimizing JOIN conditions for better performance")
        
        return suggestions
    
    def _has_no_limit(self, sql_query: str) -> bool:
        """Check if query has no LIMIT clause"""
        return 'limit' not in sql_query.lower()
    
    def _has_no_where(self, sql_query: str) -> bool:
        """Check if query has no WHERE clause"""
        return 'where' not in sql_query.lower()
    
    def _has_select_star(self, sql_query: str) -> bool:
        """Check if query uses SELECT *"""
        return re.search(r'select\s+\*\s+from', sql_query, re.IGNORECASE) is not None
    
    def _has_no_order_by(self, sql_query: str) -> bool:
        """Check if query has no ORDER BY clause"""
        return 'order by' not in sql_query.lower()
    
    def _has_complex_joins(self, sql_query: str) -> bool:
        """Check if query has complex JOIN conditions"""
        # Count JOIN keywords
        join_count = len(re.findall(r'\bjoin\b', sql_query, re.IGNORECASE))
        return join_count > 2
    
    def _load_optimization_patterns(self) -> Dict[str, Any]:
        """Load optimization patterns"""
        return {
            'performance': [
                'SELECT *',
                'no LIMIT',
                'no WHERE',
                'complex JOINs'
            ]
        }


# Global instances
error_hints = ErrorHints()
query_optimizer = QueryOptimizer()


def get_error_hints(error_message: str, sql_query: str = "") -> Dict[str, Any]:
    """Get error hints using global instance"""
    return error_hints.get_hints(error_message, sql_query)


def get_optimization_suggestions(sql_query: str) -> List[str]:
    """Get optimization suggestions using global instance"""
    return query_optimizer.get_optimization_suggestions(sql_query)


def format_error_response(error_message: str, sql_query: str = "", 
                         include_hints: bool = True) -> Dict[str, Any]:
    """
    Format a complete error response with hints
    
    Args:
        error_message: PostgreSQL error message
        sql_query: Original SQL query
        include_hints: Whether to include hints and suggestions
        
    Returns:
        Formatted error response
    """
    response = {
        'error': error_message,
        'sql_query': sql_query,
        'success': False
    }
    
    if include_hints:
        hints = get_error_hints(error_message, sql_query)
        response['hints'] = hints
        
        # Add optimization suggestions
        if sql_query:
            response['optimization_suggestions'] = get_optimization_suggestions(sql_query)
    
    return response
