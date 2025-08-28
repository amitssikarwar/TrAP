import re
from typing import Tuple, Optional


def ensure_safe_select(sql: str) -> Tuple[bool, Optional[str]]:
    """
    Ensure SQL is safe (SELECT/WITH/EXPLAIN only, no DDL/DML).
    
    Returns:
        Tuple of (is_safe, error_message)
    """
    # Normalize SQL for checking
    sql_upper = sql.strip().upper()
    
    # Block dangerous keywords
    dangerous_patterns = [
        r'\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|REINDEX|VACUUM|GRANT|REVOKE)\b',
        r'\b(EXEC|EXECUTE|EXECUTE IMMEDIATE)\b',
        r'\b(UNION ALL|UNION)\b.*\b(SELECT|INSERT|UPDATE|DELETE)\b',  # SQL injection attempts
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, sql_upper):
            return False, f"SQL contains forbidden keyword: {re.search(pattern, sql_upper).group(1)}"
    
    # Only allow SELECT, WITH, EXPLAIN at the beginning
    allowed_start_pattern = r'^(WITH|SELECT|EXPLAIN)\b'
    if not re.match(allowed_start_pattern, sql_upper):
        return False, "SQL must start with SELECT, WITH, or EXPLAIN"
    
    # Additional safety checks
    if ';' in sql:
        return False, "Multiple statements not allowed (semicolon detected)"
    
    if '--' in sql or '/*' in sql:
        return False, "Comments not allowed in SQL"
    
    return True, None


def sanitize_sql(sql: str) -> str:
    """
    Basic SQL sanitization (remove comments, normalize whitespace).
    """
    # Remove single-line comments
    sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    
    # Remove multi-line comments
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
    
    # Normalize whitespace
    sql = re.sub(r'\s+', ' ', sql).strip()
    
    return sql


def extract_sql_from_code_block(text: str) -> Optional[str]:
    """
    Extract SQL from markdown code block.
    """
    # Look for ```sql or ``` blocks
    sql_pattern = r'```(?:sql)?\s*\n(.*?)\n```'
    match = re.search(sql_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if match:
        return match.group(1).strip()
    
    # If no code block, assume the entire text is SQL
    return text.strip() if text.strip() else None
