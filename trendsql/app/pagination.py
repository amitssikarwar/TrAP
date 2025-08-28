from typing import Tuple, Optional


def add_pagination(sql: str, page: int = 1, page_size: int = 50) -> str:
    """
    Add LIMIT and OFFSET to SQL query for pagination.
    """
    # Remove existing LIMIT/OFFSET if present
    sql_upper = sql.upper()
    
    # Find the last occurrence of LIMIT
    limit_pos = sql_upper.rfind('LIMIT')
    if limit_pos != -1:
        # Find the end of the LIMIT clause
        end_pos = sql.find(';', limit_pos)
        if end_pos == -1:
            end_pos = len(sql)
        
        # Remove the LIMIT clause
        sql = sql[:limit_pos].rstrip() + sql[end_pos:]
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Add new LIMIT and OFFSET
    paginated_sql = f"{sql.rstrip()} LIMIT {page_size} OFFSET {offset}"
    
    return paginated_sql


def create_count_query(sql: str) -> str:
    """
    Create a COUNT query from the original SQL.
    """
    # Remove ORDER BY clause as it's not needed for count
    sql_upper = sql.upper()
    
    # Find ORDER BY
    order_pos = sql_upper.rfind('ORDER BY')
    if order_pos != -1:
        # Find the end of the ORDER BY clause
        end_pos = sql.find(';', order_pos)
        if end_pos == -1:
            end_pos = len(sql)
        
        # Remove the ORDER BY clause
        sql = sql[:order_pos].rstrip() + sql[end_pos:]
    
    # Remove LIMIT/OFFSET if present
    limit_pos = sql_upper.rfind('LIMIT')
    if limit_pos != -1:
        end_pos = sql.find(';', limit_pos)
        if end_pos == -1:
            end_pos = len(sql)
        sql = sql[:limit_pos].rstrip() + sql[end_pos:]
    
    # Wrap in COUNT
    count_sql = f"SELECT COUNT(*) as total FROM ({sql}) as count_query"
    
    return count_sql


def validate_pagination_params(page: int, page_size: int) -> Tuple[int, int]:
    """
    Validate and normalize pagination parameters.
    """
    # Ensure page is at least 1
    page = max(1, page)
    
    # Ensure page_size is between 1 and 1000
    page_size = max(1, min(1000, page_size))
    
    return page, page_size


def get_pagination_info(page: int, page_size: int, total_rows: Optional[int] = None) -> dict:
    """
    Get pagination metadata.
    """
    page, page_size = validate_pagination_params(page, page_size)
    
    info = {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size
    }
    
    if total_rows is not None:
        info.update({
            "total_rows": total_rows,
            "total_pages": (total_rows + page_size - 1) // page_size,
            "has_next": page * page_size < total_rows,
            "has_prev": page > 1
        })
    
    return info
