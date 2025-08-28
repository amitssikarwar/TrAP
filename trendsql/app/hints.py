import re
from typing import Optional, List, Dict, Any


def extract_column_from_error(error_msg: str) -> Optional[str]:
    """
    Extract column name from PostgreSQL error messages.
    """
    # Common PostgreSQL error patterns
    patterns = [
        r'column "([^"]+)" does not exist',
        r'column ([^\s]+) does not exist',
        r'relation "([^"]+)" does not exist',
        r'relation ([^\s]+) does not exist',
        r'undefined column: ([^\s]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_msg, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def find_similar_columns(column_name: str, available_columns: List[str]) -> List[str]:
    """
    Find columns similar to the given column name.
    """
    if not column_name or not available_columns:
        return []
    
    column_lower = column_name.lower()
    similar = []
    
    for col in available_columns:
        col_lower = col.lower()
        
        # Exact match
        if col_lower == column_lower:
            return [col]
        
        # Contains the column name
        if column_lower in col_lower or col_lower in column_lower:
            similar.append(col)
        
        # Levenshtein-like similarity (simple version)
        elif len(set(column_lower) & set(col_lower)) >= len(column_lower) * 0.7:
            similar.append(col)
    
    return similar[:5]  # Limit to 5 suggestions


def generate_error_hint(error_msg: str, available_columns: List[str] = None) -> Optional[str]:
    """
    Generate helpful hint for common PostgreSQL errors.
    """
    error_lower = error_msg.lower()
    
    # Column does not exist
    if "does not exist" in error_lower:
        column = extract_column_from_error(error_msg)
        if column and available_columns:
            similar = find_similar_columns(column, available_columns)
            if similar:
                return f"Did you mean one of these columns: {', '.join(similar)}?"
            else:
                return f"Column '{column}' not found. Available columns: {', '.join(available_columns[:10])}"
    
    # Table does not exist
    if "relation" in error_lower and "does not exist" in error_lower:
        return "Table not found. Check the table name and ensure it exists in the database."
    
    # Syntax error
    if "syntax error" in error_lower:
        return "SQL syntax error. Check your query syntax, especially around keywords and operators."
    
    # Permission error
    if "permission denied" in error_lower:
        return "Permission denied. You may not have access to this table or column."
    
    # Type mismatch
    if "operator does not exist" in error_lower:
        return "Type mismatch. Check that you're comparing compatible data types."
    
    # Missing FROM clause
    if "missing from-clause entry" in error_lower:
        return "Missing FROM clause. Ensure all referenced tables are included in your FROM clause."
    
    return None


def suggest_query_improvements(sql: str) -> List[str]:
    """
    Suggest improvements for SQL queries.
    """
    suggestions = []
    sql_upper = sql.upper()
    
    # Check for missing LIMIT
    if "SELECT" in sql_upper and "LIMIT" not in sql_upper and "COUNT" not in sql_upper:
        suggestions.append("Consider adding LIMIT to prevent large result sets")
    
    # Check for missing ORDER BY in ranking queries
    if any(word in sql_upper for word in ["TOP", "FIRST", "BEST", "HIGHEST", "LOWEST"]):
        if "ORDER BY" not in sql_upper:
            suggestions.append("Add ORDER BY clause for ranking queries")
    
    # Check for potential performance issues
    if "SELECT *" in sql_upper:
        suggestions.append("Consider selecting specific columns instead of * for better performance")
    
    # Check for date filtering
    if any(word in sql_upper for word in ["DATE", "TIMESTAMP", "CREATED_AT", "UPDATED_AT"]):
        if "WHERE" not in sql_upper or not any(word in sql_upper for word in ["DATE", "TIMESTAMP", ">", "<", "BETWEEN"]):
            suggestions.append("Consider adding date filters to limit the result set")
    
    return suggestions


def format_error_with_hints(error_msg: str, sql: str = None, available_columns: List[str] = None) -> Dict[str, Any]:
    """
    Format error with hints and suggestions.
    """
    result = {
        "error": error_msg,
        "hint": generate_error_hint(error_msg, available_columns)
    }
    
    if sql:
        suggestions = suggest_query_improvements(sql)
        if suggestions:
            result["suggestions"] = suggestions
    
    return result
