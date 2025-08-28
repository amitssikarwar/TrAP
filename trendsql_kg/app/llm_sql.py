"""
LLM SQL Generation Module for TrendsQL-KG
Uses OpenAI to convert natural language to SQL queries
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMSQLGenerator:
    """LLM-based SQL generator for TrendsQL-KG"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize LLM SQL generator
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
        # System prompt for SQL generation
        self.system_prompt = """You are a SQL expert for a trend analysis database. 
Generate safe PostgreSQL SELECT queries only. Never generate INSERT, UPDATE, DELETE, or DDL statements.

Database contains trend data:
- exploding_topics: trending topics with growth/popularity scores
- gt_interest_over_time: Google Trends interest data over time
- gt_related_topics: related topics from Google Trends
- kg_node_summaries: Knowledge Graph node summaries
- kg_community_summaries: Knowledge Graph community summaries

Key rules:
1. Only generate SELECT queries
2. Use proper table aliases for readability
3. Include LIMIT clauses for large result sets
4. Use appropriate date functions for time-based queries
5. Handle NULL values appropriately
6. Use proper JOIN syntax when combining tables
7. Include ORDER BY for ranking queries
8. Use window functions for ranking when needed

Return only the SQL query, no explanations."""
    
    def generate_sql(self, prompt: str, schema_info: Dict[str, Any], 
                    sample_data: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Tuple[str, Optional[str]]:
        """
        Generate SQL from natural language prompt
        
        Args:
            prompt: Natural language prompt
            schema_info: Database schema information
            sample_data: Optional sample data for context
            
        Returns:
            Tuple of (sql_query, error_message)
        """
        try:
            # Build the user prompt
            user_prompt = self._build_user_prompt(prompt, schema_info, sample_data)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                stop=None
            )
            
            # Extract SQL from response
            sql = response.choices[0].message.content.strip()
            
            # Clean up SQL
            sql = self._clean_sql(sql)
            
            return sql, None
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return "", str(e)
    
    def _build_user_prompt(self, prompt: str, schema_info: Dict[str, Any], 
                          sample_data: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> str:
        """Build the user prompt for SQL generation"""
        lines = []
        
        # Add schema information
        lines.append("Database Schema:")
        lines.append("=" * 50)
        
        for table in schema_info.get('tables', []):
            lines.append(f"\nTable: {table['schema']}.{table['name']}")
            if table.get('comment'):
                lines.append(f"Description: {table['comment']}")
            
            lines.append("Columns:")
            for col in table.get('columns', []):
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                comment = f" -- {col['comment']}" if col['comment'] else ""
                lines.append(f"  {col['column_name']}: {col['data_type']} {nullable}{default}{comment}")
            
            if table.get('primary_key'):
                lines.append(f"Primary Key: {', '.join(table['primary_key'])}")
            
            if table.get('foreign_keys'):
                lines.append("Foreign Keys:")
                for fk in table['foreign_keys']:
                    lines.append(f"  {fk['column_name']} -> {fk['foreign_table_schema']}.{fk['foreign_table_name']}.{fk['foreign_column_name']}")
        
        # Add sample data if provided
        if sample_data:
            lines.append("\nSample Data:")
            lines.append("=" * 50)
            for table_name, data in sample_data.items():
                if data:
                    lines.append(f"\n{table_name} (first 3 rows):")
                    for i, row in enumerate(data[:3]):
                        lines.append(f"  Row {i+1}: {row}")
        
        # Add the user's prompt
        lines.append(f"\nUser Query: {prompt}")
        lines.append("\nGenerate a PostgreSQL SELECT query:")
        
        return "\n".join(lines)
    
    def _clean_sql(self, sql: str) -> str:
        """Clean and normalize generated SQL"""
        # Remove markdown code blocks
        sql = sql.replace('```sql', '').replace('```', '')
        
        # Remove leading/trailing whitespace
        sql = sql.strip()
        
        # Ensure it starts with SELECT or WITH
        if not sql.upper().startswith(('SELECT', 'WITH')):
            # Try to find SQL in the response
            import re
            sql_match = re.search(r'(SELECT\s+.+?)(?:\n|$)', sql, re.IGNORECASE | re.DOTALL)
            if sql_match:
                sql = sql_match.group(1).strip()
        
        return sql
    
    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate generated SQL
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty SQL query"
        
        # Check if it starts with SELECT or WITH
        sql_upper = sql.upper().strip()
        if not sql_upper.startswith(('SELECT', 'WITH')):
            return False, "Query must start with SELECT or WITH"
        
        # Check for dangerous keywords
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE',
            'GRANT', 'REVOKE', 'EXECUTE', 'CALL', 'DO'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False, f"Query contains dangerous keyword: {keyword}"
        
        return True, None
    
    def improve_sql(self, sql: str, error_message: str, schema_info: Dict[str, Any]) -> Tuple[str, Optional[str]]:
        """
        Improve SQL based on error message
        
        Args:
            sql: Original SQL query
            error_message: Error message from execution
            schema_info: Database schema information
            
        Returns:
            Tuple of (improved_sql, error_message)
        """
        try:
            improvement_prompt = f"""
The following SQL query failed with error: {error_message}

Original SQL:
{sql}

Please fix the SQL query based on the error message. Common fixes:
- Check table and column names exist in schema
- Fix syntax errors
- Use proper data types
- Handle NULL values appropriately
- Use correct JOIN syntax

Return only the corrected SQL query:
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": improvement_prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                stop=None
            )
            
            improved_sql = response.choices[0].message.content.strip()
            improved_sql = self._clean_sql(improved_sql)
            
            return improved_sql, None
            
        except Exception as e:
            logger.error(f"SQL improvement failed: {e}")
            return sql, str(e)
    
    def explain_sql(self, sql: str) -> str:
        """
        Generate explanation for SQL query
        
        Args:
            sql: SQL query to explain
            
        Returns:
            Explanation of the SQL query
        """
        try:
            explanation_prompt = f"""
Explain this SQL query in simple terms:

{sql}

Explain what this query does, what tables it uses, and what results it will return.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a SQL expert who explains queries clearly and concisely."},
                    {"role": "user", "content": explanation_prompt}
                ],
                temperature=0.3,
                max_tokens=500,
                stop=None
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"SQL explanation failed: {e}")
            return f"Unable to explain SQL: {str(e)}"


# Global instance
llm_sql_generator = None


def init_llm_sql_generator(api_key: str, model: str = "gpt-4o-mini") -> None:
    """Initialize global LLM SQL generator"""
    global llm_sql_generator
    llm_sql_generator = LLMSQLGenerator(api_key, model)


def generate_sql(prompt: str, schema_info: Dict[str, Any], 
                sample_data: Optional[Dict[str, List[Dict[str, Any]]]] = None) -> Tuple[str, Optional[str]]:
    """Generate SQL using global LLM SQL generator"""
    if llm_sql_generator is None:
        raise RuntimeError("LLM SQL generator not initialized")
    
    return llm_sql_generator.generate_sql(prompt, schema_info, sample_data)


def validate_sql(sql: str) -> Tuple[bool, Optional[str]]:
    """Validate SQL using global LLM SQL generator"""
    if llm_sql_generator is None:
        raise RuntimeError("LLM SQL generator not initialized")
    
    return llm_sql_generator.validate_sql(sql)


def improve_sql(sql: str, error_message: str, schema_info: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Improve SQL using global LLM SQL generator"""
    if llm_sql_generator is None:
        raise RuntimeError("LLM SQL generator not initialized")
    
    return llm_sql_generator.improve_sql(sql, error_message, schema_info)


def explain_sql(sql: str) -> str:
    """Explain SQL using global LLM SQL generator"""
    if llm_sql_generator is None:
        raise RuntimeError("LLM SQL generator not initialized")
    
    return llm_sql_generator.explain_sql(sql)
