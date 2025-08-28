import os
import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
from .sql_safety import extract_sql_from_code_block, ensure_safe_select

logger = logging.getLogger(__name__)


class LLMSQLGenerator:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")  # Optional for custom endpoints
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not os.getenv("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY not set - LLM features will not work")
    
    def generate_sql(self, prompt: str, schema_summary: str) -> Optional[str]:
        """
        Generate SQL from natural language prompt using OpenAI.
        """
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not configured")
        
        system_prompt = f"""You are a SQL expert. Generate PostgreSQL SELECT queries based on user requests.

{schema_summary}

Rules:
- Output ONLY SQL in a fenced code block
- Use PostgreSQL dialect
- No comments in SQL
- Only SELECT, WITH, or EXPLAIN statements
- Use proper table aliases when joining
- Include ORDER BY for ranking queries
- Use LIMIT for top N queries
- Handle NULL values appropriately

Example output:
```sql
SELECT column1, column2 FROM table WHERE condition ORDER BY column1 DESC LIMIT 10
```"""

        user_prompt = f"Generate SQL for: {prompt}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM response: {content}")
            
            # Extract SQL from code block
            sql = extract_sql_from_code_block(content)
            
            if not sql:
                logger.error("No SQL found in LLM response")
                return None
            
            # Validate SQL safety
            is_safe, error = ensure_safe_select(sql)
            if not is_safe:
                logger.error(f"Generated SQL failed safety check: {error}")
                return None
            
            return sql
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise
    
    def explain_sql(self, sql: str) -> Optional[str]:
        """
        Generate explanation for SQL query.
        """
        if not os.getenv("OPENAI_API_KEY"):
            return None
        
        system_prompt = """You are a SQL expert. Explain what a SQL query does in simple terms.

Rules:
- Keep explanation concise and clear
- Focus on the business logic
- Explain any complex joins or aggregations
- Mention the expected output format"""

        user_prompt = f"Explain this SQL query: {sql}"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error explaining SQL: {e}")
            return None
    
    def chat_response(self, message: str, sql: Optional[str] = None, results: Optional[list] = None) -> Dict[str, Any]:
        """
        Generate chat-style response with multiple blocks.
        """
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "blocks": [
                    {"type": "markdown", "content": "I can help you query the database. Please provide a natural language description of what you're looking for."}
                ]
            }
        
        system_prompt = """You are a helpful database assistant. Provide responses with multiple content blocks.

Available blocks:
- markdown: General text and explanations
- code: SQL queries
- html: Data tables
- meta: Additional information

Format your response as a JSON object with a "blocks" array."""

        context = f"User message: {message}"
        if sql:
            context += f"\nGenerated SQL: {sql}"
        if results:
            context += f"\nQuery results: {json.dumps(results[:5])}"  # First 5 rows for context
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to markdown
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "blocks": [
                        {"type": "markdown", "content": content}
                    ]
                }
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return {
                "blocks": [
                    {"type": "markdown", "content": "I encountered an error while processing your request. Please try again."}
                ]
            }
