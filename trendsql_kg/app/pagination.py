"""
Pagination Module for TrendsQL-KG
Handles LIMIT/OFFSET pagination and row counting
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


class PaginationHelper:
    """Pagination helper for SQL queries"""
    
    def __init__(self, db_connection_string: str):
        """
        Initialize pagination helper
        
        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.db_connection_string = db_connection_string
    
    def add_pagination(self, sql: str, page: int = 1, page_size: int = 50) -> str:
        """
        Add LIMIT/OFFSET pagination to SQL query
        
        Args:
            sql: Original SQL query
            page: Page number (1-based)
            page_size: Number of rows per page
            
        Returns:
            SQL query with pagination
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50
        
        offset = (page - 1) * page_size
        
        # Check if query already has LIMIT/OFFSET
        sql_upper = sql.upper().strip()
        if 'LIMIT' in sql_upper or 'OFFSET' in sql_upper:
            # Remove existing LIMIT/OFFSET
            sql = self._remove_existing_pagination(sql)
        
        # Add new pagination
        paginated_sql = f"{sql} LIMIT {page_size} OFFSET {offset}"
        
        return paginated_sql
    
    def get_total_count(self, sql: str) -> int:
        """
        Get total count of rows for a query
        
        Args:
            sql: SQL query to count
            
        Returns:
            Total number of rows
        """
        try:
            # Create count query
            count_sql = self._create_count_query(sql)
            
            with psycopg.connect(self.db_connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(count_sql)
                    result = cur.fetchone()
                    return result[0] if result else 0
                    
        except Exception as e:
            logger.error(f"Failed to get total count: {e}")
            return 0
    
    def execute_paginated_query(self, sql: str, page: int = 1, page_size: int = 50) -> Tuple[List[Dict[str, Any]], int, Dict[str, Any]]:
        """
        Execute a paginated query and return results with metadata
        
        Args:
            sql: SQL query to execute
            page: Page number (1-based)
            page_size: Number of rows per page
            
        Returns:
            Tuple of (results, total_count, metadata)
        """
        try:
            # Get total count first
            total_count = self.get_total_count(sql)
            
            # Add pagination to query
            paginated_sql = self.add_pagination(sql, page, page_size)
            
            # Execute paginated query
            with psycopg.connect(self.db_connection_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(paginated_sql)
                    results = cur.fetchall()
            
            # Calculate metadata
            metadata = self._calculate_pagination_metadata(page, page_size, total_count, len(results))
            
            return results, total_count, metadata
            
        except Exception as e:
            logger.error(f"Failed to execute paginated query: {e}")
            return [], 0, {}
    
    def _remove_existing_pagination(self, sql: str) -> str:
        """Remove existing LIMIT/OFFSET from SQL query"""
        import re
        
        # Remove LIMIT clause
        sql = re.sub(r'\bLIMIT\s+\d+(\s+OFFSET\s+\d+)?\s*$', '', sql, flags=re.IGNORECASE)
        
        # Remove OFFSET clause (if not already removed)
        sql = re.sub(r'\bOFFSET\s+\d+\s*$', '', sql, flags=re.IGNORECASE)
        
        return sql.strip()
    
    def _create_count_query(self, sql: str) -> str:
        """Create a COUNT query from the original SQL"""
        import re
        
        # Handle CTE queries
        if sql.upper().strip().startswith('WITH'):
            # For CTE queries, wrap in subquery
            return f"SELECT COUNT(*) FROM ({sql}) AS count_subquery"
        
        # Handle simple SELECT queries
        # Find the SELECT clause
        select_match = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1).strip()
            
            # If it's SELECT *, replace with COUNT(*)
            if select_clause.strip() == '*':
                count_sql = re.sub(r'SELECT\s+\*\s+FROM', 'SELECT COUNT(*) FROM', sql, flags=re.IGNORECASE)
            else:
                # For complex SELECT clauses, wrap in subquery
                count_sql = f"SELECT COUNT(*) FROM ({sql}) AS count_subquery"
        else:
            # Fallback: wrap in subquery
            count_sql = f"SELECT COUNT(*) FROM ({sql}) AS count_subquery"
        
        # Remove ORDER BY, LIMIT, OFFSET from count query
        count_sql = re.sub(r'\bORDER\s+BY\s+.+?(\s+LIMIT|\s+OFFSET|$)', '', count_sql, flags=re.IGNORECASE | re.DOTALL)
        count_sql = re.sub(r'\bLIMIT\s+\d+(\s+OFFSET\s+\d+)?\s*$', '', count_sql, flags=re.IGNORECASE)
        count_sql = re.sub(r'\bOFFSET\s+\d+\s*$', '', count_sql, flags=re.IGNORECASE)
        
        return count_sql.strip()
    
    def _calculate_pagination_metadata(self, page: int, page_size: int, total_count: int, result_count: int) -> Dict[str, Any]:
        """Calculate pagination metadata"""
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        
        return {
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'result_count': result_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1,
            'next_page': page + 1 if page < total_pages else None,
            'previous_page': page - 1 if page > 1 else None,
            'start_index': (page - 1) * page_size + 1 if total_count > 0 else 0,
            'end_index': min(page * page_size, total_count) if total_count > 0 else 0
        }
    
    def validate_pagination_params(self, page: int, page_size: int, max_page_size: int = 1000) -> Tuple[int, int]:
        """
        Validate and normalize pagination parameters
        
        Args:
            page: Page number
            page_size: Page size
            max_page_size: Maximum allowed page size
            
        Returns:
            Tuple of (normalized_page, normalized_page_size)
        """
        # Normalize page
        if page < 1:
            page = 1
        
        # Normalize page_size
        if page_size < 1:
            page_size = 50
        elif page_size > max_page_size:
            page_size = max_page_size
        
        return page, page_size


class PaginatedResponse:
    """Container for paginated response data"""
    
    def __init__(self, results: List[Dict[str, Any]], metadata: Dict[str, Any]):
        """
        Initialize paginated response
        
        Args:
            results: List of result rows
            metadata: Pagination metadata
        """
        self.results = results
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'results': self.results,
            'pagination': self.metadata
        }
    
    def get_page_info(self) -> Dict[str, Any]:
        """Get page information"""
        return {
            'current_page': self.metadata.get('page'),
            'page_size': self.metadata.get('page_size'),
            'total_count': self.metadata.get('total_count'),
            'total_pages': self.metadata.get('total_pages'),
            'has_next': self.metadata.get('has_next'),
            'has_previous': self.metadata.get('has_previous')
        }


# Global instance
pagination_helper = None


def init_pagination_helper(db_connection_string: str) -> None:
    """Initialize global pagination helper"""
    global pagination_helper
    pagination_helper = PaginationHelper(db_connection_string)


def add_pagination(sql: str, page: int = 1, page_size: int = 50) -> str:
    """Add pagination to SQL query using global helper"""
    if pagination_helper is None:
        raise RuntimeError("Pagination helper not initialized")
    
    return pagination_helper.add_pagination(sql, page, page_size)


def get_total_count(sql: str) -> int:
    """Get total count for SQL query using global helper"""
    if pagination_helper is None:
        raise RuntimeError("Pagination helper not initialized")
    
    return pagination_helper.get_total_count(sql)


def execute_paginated_query(sql: str, page: int = 1, page_size: int = 50) -> Tuple[List[Dict[str, Any]], int, Dict[str, Any]]:
    """Execute paginated query using global helper"""
    if pagination_helper is None:
        raise RuntimeError("Pagination helper not initialized")
    
    return pagination_helper.execute_paginated_query(sql, page, page_size)


def validate_pagination_params(page: int, page_size: int, max_page_size: int = 1000) -> Tuple[int, int]:
    """Validate pagination parameters using global helper"""
    if pagination_helper is None:
        raise RuntimeError("Pagination helper not initialized")
    
    return pagination_helper.validate_pagination_params(page, page_size, max_page_size)
