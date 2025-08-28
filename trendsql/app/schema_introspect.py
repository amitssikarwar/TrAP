import psycopg
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def get_schema_summary(conn: psycopg.Connection, schemas: List[str] = None) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    """
    Get schema summary for LLM prompting.
    
    Returns:
        Dict mapping schema -> table -> columns
    """
    if schemas is None:
        schemas = ["public"]
    
    schema_list = ",".join([f"'{s}'" for s in schemas])
    
    query = """
    SELECT 
        table_schema,
        table_name,
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns 
    WHERE table_schema IN ({})
    AND table_name NOT LIKE 'pg_%'
    AND table_name NOT LIKE 'information_schema%'
    ORDER BY table_schema, table_name, ordinal_position
    """.format(schema_list)
    
    result = {}
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                schema, table, column, data_type, is_nullable, default_val = row
                
                if schema not in result:
                    result[schema] = {}
                
                if table not in result[schema]:
                    result[schema][table] = []
                
                result[schema][table].append({
                    "column": column,
                    "type": data_type,
                    "nullable": is_nullable == "YES",
                    "default": default_val
                })
                
    except Exception as e:
        logger.error(f"Error introspecting schema: {e}")
        raise
    
    return result


def get_table_info(conn: psycopg.Connection, table_name: str, schema: str = "public") -> Dict[str, Any]:
    """
    Get detailed information about a specific table.
    """
    query = """
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length,
        numeric_precision,
        numeric_scale
    FROM information_schema.columns 
    WHERE table_schema = %s AND table_name = %s
    ORDER BY ordinal_position
    """
    
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (schema, table_name))
            columns = cursor.fetchall()
            
            return {
                "schema": schema,
                "table": table_name,
                "columns": [
                    {
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[2] == "YES",
                        "default": col[3],
                        "max_length": col[4],
                        "precision": col[5],
                        "scale": col[6]
                    }
                    for col in columns
                ]
            }
    except Exception as e:
        logger.error(f"Error getting table info for {schema}.{table_name}: {e}")
        raise


def format_schema_for_llm(schema_summary: Dict[str, Dict[str, List[Dict[str, str]]]]) -> str:
    """
    Format schema summary for LLM prompting.
    """
    lines = ["Database Schema:"]
    
    for schema_name, tables in schema_summary.items():
        lines.append(f"\nSchema: {schema_name}")
        
        for table_name, columns in tables.items():
            lines.append(f"  Table: {table_name}")
            
            for col in columns:
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col.get("default") else ""
                lines.append(f"    {col['column']}: {col['type']} {nullable}{default}")
    
    return "\n".join(lines)
