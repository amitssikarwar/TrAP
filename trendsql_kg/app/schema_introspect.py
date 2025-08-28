"""
Schema Introspection Module for TrendsQL-KG
Provides database schema information for LLM SQL generation
"""

import json
import logging
from typing import Dict, List, Any, Optional
import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)


class SchemaIntrospector:
    """Database schema introspector for TrendsQL-KG"""
    
    def __init__(self, db_connection_string: str):
        """
        Initialize schema introspector
        
        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.db_connection_string = db_connection_string
        self._schema_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 3600  # 1 hour cache
    
    def get_schema_json(self, schemas: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get database schema as JSON for LLM consumption
        
        Args:
            schemas: List of schema names to include (default: ['public'])
            
        Returns:
            Schema information as JSON-serializable dict
        """
        if schemas is None:
            schemas = ['public']
        
        # Check cache
        if self._is_cache_valid():
            return self._schema_cache
        
        try:
            with psycopg.connect(self.db_connection_string) as conn:
                schema_info = self._introspect_schema(conn, schemas)
                self._update_cache(schema_info)
                return schema_info
                
        except Exception as e:
            logger.error(f"Schema introspection failed: {e}")
            raise
    
    def get_compact_schema(self, schemas: Optional[List[str]] = None) -> str:
        """
        Get compact schema representation for LLM prompts
        
        Args:
            schemas: List of schema names to include
            
        Returns:
            Compact schema string
        """
        schema_json = self.get_schema_json(schemas)
        return self._format_compact_schema(schema_json)
    
    def get_table_info(self, table_name: str, schema: str = 'public') -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific table
        
        Args:
            table_name: Name of the table
            schema: Schema name (default: 'public')
            
        Returns:
            Table information or None if not found
        """
        try:
            with psycopg.connect(self.db_connection_string) as conn:
                return self._get_table_details(conn, table_name, schema)
                
        except Exception as e:
            logger.error(f"Failed to get table info for {schema}.{table_name}: {e}")
            return None
    
    def get_sample_data(self, table_name: str, schema: str = 'public', limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sample data from a table
        
        Args:
            table_name: Name of the table
            schema: Schema name (default: 'public')
            limit: Number of sample rows
            
        Returns:
            List of sample rows
        """
        try:
            with psycopg.connect(self.db_connection_string) as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    cur.execute(
                        f"SELECT * FROM {schema}.{table_name} LIMIT %s",
                        (limit,)
                    )
                    return cur.fetchall()
                    
        except Exception as e:
            logger.error(f"Failed to get sample data for {schema}.{table_name}: {e}")
            return []
    
    def _introspect_schema(self, conn: psycopg.Connection, schemas: List[str]) -> Dict[str, Any]:
        """Introspect database schema"""
        schema_info = {
            'database': 'trendsql_kg',
            'schemas': {},
            'tables': [],
            'relationships': [],
            'indexes': [],
            'version': '1.0.0'
        }
        
        # Get tables for each schema
        for schema in schemas:
            schema_info['schemas'][schema] = self._get_schema_tables(conn, schema)
            schema_info['tables'].extend(schema_info['schemas'][schema])
        
        # Get relationships
        schema_info['relationships'] = self._get_relationships(conn, schemas)
        
        # Get indexes
        schema_info['indexes'] = self._get_indexes(conn, schemas)
        
        return schema_info
    
    def _get_schema_tables(self, conn: psycopg.Connection, schema: str) -> List[Dict[str, Any]]:
        """Get tables in a schema"""
        tables = []
        
        with conn.cursor(row_factory=dict_row) as cur:
            # Get table information
            cur.execute("""
                SELECT 
                    t.table_name,
                    t.table_type,
                    obj_description(format('%s.%s', %s, t.table_name)::regclass) as comment
                FROM information_schema.tables t
                WHERE t.table_schema = %s
                AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name
            """, (schema, schema, schema))
            
            for table_row in cur.fetchall():
                table_name = table_row['table_name']
                table_info = {
                    'name': table_name,
                    'schema': schema,
                    'type': table_row['table_type'],
                    'comment': table_row['comment'],
                    'columns': self._get_table_columns(cur, schema, table_name),
                    'primary_key': self._get_primary_key(cur, schema, table_name),
                    'foreign_keys': self._get_foreign_keys(cur, schema, table_name),
                    'unique_constraints': self._get_unique_constraints(cur, schema, table_name)
                }
                tables.append(table_info)
        
        return tables
    
    def _get_table_columns(self, cur, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Get columns for a table"""
        cur.execute("""
            SELECT 
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale,
                col_description(format('%s.%s', %s, %s)::regclass, c.ordinal_position) as comment
            FROM information_schema.columns c
            WHERE c.table_schema = %s AND c.table_name = %s
            ORDER BY c.ordinal_position
        """, (schema, table_name, schema, table_name, schema, table_name))
        
        return [dict(row) for row in cur.fetchall()]
    
    def _get_primary_key(self, cur, schema: str, table_name: str) -> Optional[List[str]]:
        """Get primary key columns for a table"""
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = %s 
                AND tc.table_name = %s 
                AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """, (schema, table_name))
        
        result = cur.fetchall()
        return [row['column_name'] for row in result] if result else None
    
    def _get_foreign_keys(self, cur, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Get foreign key constraints for a table"""
        cur.execute("""
            SELECT 
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = %s 
                AND tc.table_name = %s
        """, (schema, table_name))
        
        return [dict(row) for row in cur.fetchall()]
    
    def _get_unique_constraints(self, cur, schema: str, table_name: str) -> List[Dict[str, Any]]:
        """Get unique constraints for a table"""
        cur.execute("""
            SELECT 
                tc.constraint_name,
                array_agg(kcu.column_name ORDER BY kcu.ordinal_position) as columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = %s 
                AND tc.table_name = %s 
                AND tc.constraint_type = 'UNIQUE'
            GROUP BY tc.constraint_name
        """, (schema, table_name))
        
        return [dict(row) for row in cur.fetchall()]
    
    def _get_relationships(self, conn: psycopg.Connection, schemas: List[str]) -> List[Dict[str, Any]]:
        """Get relationships between tables"""
        relationships = []
        
        with conn.cursor(row_factory=dict_row) as cur:
            for schema in schemas:
                cur.execute("""
                    SELECT 
                        tc.table_schema,
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_schema AS foreign_table_schema,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' 
                        AND tc.table_schema = %s
                """, (schema,))
                
                for row in cur.fetchall():
                    relationships.append(dict(row))
        
        return relationships
    
    def _get_indexes(self, conn: psycopg.Connection, schemas: List[str]) -> List[Dict[str, Any]]:
        """Get indexes for tables"""
        indexes = []
        
        with conn.cursor(row_factory=dict_row) as cur:
            for schema in schemas:
                cur.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname = %s
                    ORDER BY tablename, indexname
                """, (schema,))
                
                for row in cur.fetchall():
                    indexes.append(dict(row))
        
        return indexes
    
    def _get_table_details(self, conn: psycopg.Connection, table_name: str, schema: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific table"""
        with conn.cursor(row_factory=dict_row) as cur:
            # Get table info
            cur.execute("""
                SELECT 
                    t.table_name,
                    t.table_type,
                    obj_description(format('%s.%s', %s, t.table_name)::regclass) as comment
                FROM information_schema.tables t
                WHERE t.table_schema = %s AND t.table_name = %s
            """, (schema, table_name, schema, schema, table_name))
            
            table_row = cur.fetchone()
            if not table_row:
                return None
            
            table_info = dict(table_row)
            table_info['columns'] = self._get_table_columns(cur, schema, table_name)
            table_info['primary_key'] = self._get_primary_key(cur, schema, table_name)
            table_info['foreign_keys'] = self._get_foreign_keys(cur, schema, table_name)
            table_info['unique_constraints'] = self._get_unique_constraints(cur, schema, table_name)
            
            return table_info
    
    def _format_compact_schema(self, schema_info: Dict[str, Any]) -> str:
        """Format schema as compact string for LLM prompts"""
        lines = []
        lines.append("Database Schema:")
        lines.append("=" * 50)
        
        for table in schema_info['tables']:
            lines.append(f"\nTable: {table['schema']}.{table['name']}")
            if table['comment']:
                lines.append(f"Comment: {table['comment']}")
            
            lines.append("Columns:")
            for col in table['columns']:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                comment = f" -- {col['comment']}" if col['comment'] else ""
                lines.append(f"  {col['column_name']}: {col['data_type']} {nullable}{default}{comment}")
            
            if table['primary_key']:
                lines.append(f"Primary Key: {', '.join(table['primary_key'])}")
            
            if table['foreign_keys']:
                lines.append("Foreign Keys:")
                for fk in table['foreign_keys']:
                    lines.append(f"  {fk['column_name']} -> {fk['foreign_table_schema']}.{fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        return "\n".join(lines)
    
    def _is_cache_valid(self) -> bool:
        """Check if schema cache is still valid"""
        if self._schema_cache is None or self._cache_timestamp is None:
            return False
        
        import time
        return (time.time() - self._cache_timestamp) < self._cache_ttl
    
    def _update_cache(self, schema_info: Dict[str, Any]) -> None:
        """Update schema cache"""
        import time
        self._schema_cache = schema_info
        self._cache_timestamp = time.time()
    
    def clear_cache(self) -> None:
        """Clear schema cache"""
        self._schema_cache = None
        self._cache_timestamp = None
