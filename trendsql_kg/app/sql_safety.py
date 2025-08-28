"""
SQL Safety Module for TrendsQL-KG
Ensures only safe SELECT queries are executed
"""

import re
import logging
from typing import List, Tuple, Optional
from sqlparse import parse, tokens
from sqlparse.sql import Statement, Token

logger = logging.getLogger(__name__)


class SQLSafetyError(Exception):
    """Exception raised when SQL safety check fails"""
    pass


class SQLSafetyChecker:
    """SQL safety checker for TrendsQL-KG"""
    
    # Dangerous SQL keywords that should be blocked
    DANGEROUS_KEYWORDS = {
        # DDL (Data Definition Language)
        'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'RENAME', 'COMMENT',
        
        # DML (Data Manipulation Language) - except SELECT
        'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'UPSERT',
        
        # Transaction Control
        'BEGIN', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'RELEASE',
        
        # System/Admin
        'GRANT', 'REVOKE', 'EXECUTE', 'CALL', 'DO',
        
        # File operations
        'COPY', 'IMPORT', 'EXPORT',
        
        # PostgreSQL specific
        'VACUUM', 'ANALYZE', 'REINDEX', 'CLUSTER',
        
        # Functions that could be dangerous
        'pg_read_file', 'pg_write_file', 'pg_ls_dir',
    }
    
    # Allowed SQL keywords for SELECT queries
    ALLOWED_KEYWORDS = {
        'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'HAVING', 'ORDER', 'LIMIT', 'OFFSET',
        'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'FULL', 'CROSS',
        'ON', 'USING', 'AS', 'DISTINCT', 'ALL',
        'UNION', 'INTERSECT', 'EXCEPT',
        'WITH', 'RECURSIVE',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE', 'ILIKE',
        'IS', 'NULL', 'TRUE', 'FALSE',
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'STDDEV', 'VARIANCE',
        'COALESCE', 'NULLIF', 'GREATEST', 'LEAST',
        'EXTRACT', 'DATE_TRUNC', 'NOW', 'CURRENT_DATE', 'CURRENT_TIMESTAMP',
        'TO_CHAR', 'TO_DATE', 'TO_TIMESTAMP',
        'UPPER', 'LOWER', 'TRIM', 'LENGTH', 'SUBSTRING', 'REPLACE',
        'ROUND', 'CEIL', 'FLOOR', 'ABS', 'POWER', 'SQRT',
        'RANDOM', 'ROW_NUMBER', 'RANK', 'DENSE_RANK', 'LAG', 'LEAD',
        'FIRST_VALUE', 'LAST_VALUE', 'NTH_VALUE',
        'PARTITION', 'OVER', 'WINDOW',
        'EXPLAIN', 'ANALYZE',
    }
    
    # Allowed functions (case-insensitive)
    ALLOWED_FUNCTIONS = {
        'count', 'sum', 'avg', 'min', 'max', 'stddev', 'variance',
        'coalesce', 'nullif', 'greatest', 'least',
        'extract', 'date_trunc', 'now', 'current_date', 'current_timestamp',
        'to_char', 'to_date', 'to_timestamp',
        'upper', 'lower', 'trim', 'length', 'substring', 'replace',
        'round', 'ceil', 'floor', 'abs', 'power', 'sqrt',
        'random', 'row_number', 'rank', 'dense_rank', 'lag', 'lead',
        'first_value', 'last_value', 'nth_value',
        'array_agg', 'string_agg', 'json_agg', 'jsonb_agg',
        'json_build_object', 'jsonb_build_object',
        'unnest', 'generate_series',
        'similarity', 'levenshtein', 'soundex',
        'pg_trgm', 'word_similarity',
    }
    
    def __init__(self):
        """Initialize the SQL safety checker"""
        self.dangerous_patterns = [
            r'\b(?:' + '|'.join(self.DANGEROUS_KEYWORDS) + r')\b',
            r'--.*$',  # SQL comments
            r'/\*.*?\*/',  # Multi-line comments
            r';\s*$',  # Multiple statements
            r'\\\s*$',  # Line continuation
            r'xp_cmdshell',  # SQL Server dangerous function
            r'sp_executesql',  # SQL Server dangerous procedure
            r'exec\s*\(',  # EXEC function calls
            r'execute\s*\(',  # EXECUTE function calls
        ]
        
        self.dangerous_regex = re.compile('|'.join(self.dangerous_patterns), re.IGNORECASE | re.MULTILINE | re.DOTALL)
    
    def check_sql_safety(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Check if SQL query is safe to execute
        
        Args:
            sql: SQL query string
            
        Returns:
            Tuple of (is_safe, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty SQL query"
        
        # Normalize SQL
        normalized_sql = self._normalize_sql(sql)
        
        # Check for dangerous patterns
        if self._has_dangerous_patterns(normalized_sql):
            return False, "Query contains dangerous SQL patterns"
        
        # Parse SQL to check structure
        try:
            parsed = parse(normalized_sql)
            if not parsed:
                return False, "Unable to parse SQL query"
            
            # Check if it's a SELECT query
            if not self._is_select_query(parsed):
                return False, "Only SELECT queries are allowed"
            
            # Check for dangerous tokens
            if self._has_dangerous_tokens(parsed):
                return False, "Query contains dangerous SQL tokens"
            
            # Check for multiple statements
            if len(parsed) > 1:
                return False, "Multiple SQL statements are not allowed"
            
            return True, None
            
        except Exception as e:
            logger.warning(f"SQL parsing error: {e}")
            return False, f"SQL parsing error: {str(e)}"
    
    def _normalize_sql(self, sql: str) -> str:
        """Normalize SQL string for analysis"""
        # Remove leading/trailing whitespace
        sql = sql.strip()
        
        # Convert to uppercase for keyword checking
        sql_upper = sql.upper()
        
        # Remove comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        return sql
    
    def _has_dangerous_patterns(self, sql: str) -> bool:
        """Check for dangerous patterns in SQL"""
        return bool(self.dangerous_regex.search(sql))
    
    def _is_select_query(self, parsed_statements) -> bool:
        """Check if parsed SQL is a SELECT query"""
        if not parsed_statements:
            return False
        
        statement = parsed_statements[0]
        
        # Check if statement starts with SELECT
        for token in statement.tokens:
            if token.is_whitespace:
                continue
            if token.ttype == tokens.Keyword and token.value.upper() == 'SELECT':
                return True
            if token.ttype == tokens.Keyword and token.value.upper() == 'WITH':
                # CTE queries are allowed
                return True
            break
        
        return False
    
    def _has_dangerous_tokens(self, parsed_statements) -> bool:
        """Check for dangerous tokens in parsed SQL"""
        def check_token(token):
            if token.is_whitespace or token.is_group:
                return False
            
            if token.ttype == tokens.Keyword:
                keyword = token.value.upper()
                if keyword in self.DANGEROUS_KEYWORDS:
                    return True
                if keyword not in self.ALLOWED_KEYWORDS:
                    logger.warning(f"Unknown keyword: {keyword}")
                    return True
            
            if token.ttype == tokens.Name.Function:
                func_name = token.value.lower()
                if func_name not in self.ALLOWED_FUNCTIONS:
                    logger.warning(f"Unknown function: {func_name}")
                    return True
            
            return False
        
        def check_statement(statement):
            for token in statement.tokens:
                if check_token(token):
                    return True
                if token.is_group:
                    if check_statement(token):
                        return True
            return False
        
        for statement in parsed_statements:
            if check_statement(statement):
                return True
        
        return False
    
    def sanitize_sql(self, sql: str) -> str:
        """
        Sanitize SQL query (remove comments, normalize)
        
        Args:
            sql: Raw SQL query
            
        Returns:
            Sanitized SQL query
        """
        # Remove comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Remove multiple statements (keep only first)
        statements = sql.split(';')
        sql = statements[0].strip()
        
        # Remove line continuations
        sql = re.sub(r'\\\s*\n', ' ', sql)
        
        return sql


# Global instance
sql_safety_checker = SQLSafetyChecker()


def is_safe_sql(sql: str) -> Tuple[bool, Optional[str]]:
    """
    Check if SQL query is safe to execute
    
    Args:
        sql: SQL query string
        
    Returns:
        Tuple of (is_safe, error_message)
    """
    return sql_safety_checker.check_sql_safety(sql)


def sanitize_sql(sql: str) -> str:
    """
    Sanitize SQL query
    
    Args:
        sql: Raw SQL query
        
    Returns:
        Sanitized SQL query
    """
    return sql_safety_checker.sanitize_sql(sql)
