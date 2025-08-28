import os
import time
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    HealthResponse, SchemaResponse, GenerateSQLRequest, GenerateSQLResponse,
    GenerateHTMLRequest, GenerateHTMLResponse, ChatRequest, ChatResponse,
    QueryRequest, QueryResponse, DownloadCSVRequest, ErrorResponse
)
from .sql_safety import ensure_safe_select, sanitize_sql
from .schema_introspect import get_schema_summary, format_schema_for_llm
from .llm_sql import LLMSQLGenerator
from .formatters import rows_to_html_table, csv_stream
from .pagination import add_pagination, create_count_query, validate_pagination_params
from .hints import format_error_with_hints

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
llm_generator = None
db_conn = None


def get_db_connection():
    """Get database connection."""
    global db_conn
    if db_conn is None or db_conn.closed:
        db_conn = psycopg.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "trendsql"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres")
        )
    return db_conn


def get_llm_generator():
    """Get LLM generator instance."""
    global llm_generator
    if llm_generator is None:
        llm_generator = LLMSQLGenerator()
    return llm_generator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting trendsql application...")
    try:
        # Test database connection
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down trendsql application...")
    if db_conn and not db_conn.closed:
        db_conn.close()


app = FastAPI(
    title="TrendSQL API",
    description="Text-to-SQL API for trend data analysis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(ok=True)


@app.get("/schema", response_model=SchemaResponse)
async def get_schema(schemas: str = "public"):
    """Get database schema information."""
    try:
        conn = get_db_connection()
        schema_list = [s.strip() for s in schemas.split(",")]
        schema_summary = get_schema_summary(conn, schema_list)
        return SchemaResponse(schemas=schema_summary)
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-sql", response_model=GenerateSQLResponse)
async def generate_sql(request: GenerateSQLRequest):
    """Generate SQL from natural language prompt."""
    start_time = time.time()
    
    try:
        # Validate pagination
        page, page_size = validate_pagination_params(request.page, request.page_size)
        
        # Get schema information
        conn = get_db_connection()
        schema_summary = get_schema_summary(conn, request.schemas)
        schema_text = format_schema_for_llm(schema_summary)
        
        # Generate SQL using LLM
        llm = get_llm_generator()
        sql = llm.generate_sql(request.prompt, schema_text)
        
        if not sql:
            raise HTTPException(status_code=400, detail="Failed to generate SQL")
        
        # Sanitize SQL
        sql = sanitize_sql(sql)
        
        # Validate SQL safety
        is_safe, error = ensure_safe_select(sql)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"Generated SQL failed safety check: {error}")
        
        response = GenerateSQLResponse(
            sql=sql,
            page=page,
            page_size=page_size
        )
        
        # Execute if requested
        if request.execute:
            try:
                # Add pagination
                paginated_sql = add_pagination(sql, page, page_size)
                
                # Execute query
                with conn.cursor() as cursor:
                    cursor.execute(paginated_sql)
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    
                    # Convert to list of dicts
                    results = [dict(zip(columns, row)) for row in rows]
                
                response.preview = results
                
                # Get total count if requested
                if request.include_total:
                    count_sql = create_count_query(sql)
                    with conn.cursor() as cursor:
                        cursor.execute(count_sql)
                        total = cursor.fetchone()[0]
                    response.total_rows = total
                
                # Generate HTML if requested
                if request.as_html:
                    response.html = rows_to_html_table(results, "Query Results")
                
                # Generate explanation
                response.explain = llm.explain_sql(sql)
                
            except Exception as e:
                logger.error(f"Error executing SQL: {e}")
                error_info = format_error_with_hints(str(e))
                raise HTTPException(
                    status_code=400,
                    detail=f"Error executing SQL: {error_info['error']}",
                    headers={"X-Error-Hint": error_info.get("hint", "")}
                )
        
        response.execution_time_ms = (time.time() - start_time) * 1000
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-html", response_model=GenerateHTMLResponse)
async def generate_html(request: GenerateHTMLRequest):
    """Generate HTML table from natural language prompt."""
    start_time = time.time()
    
    try:
        # Validate pagination
        page, page_size = validate_pagination_params(request.page, request.page_size)
        
        # Get schema information
        conn = get_db_connection()
        schema_summary = get_schema_summary(conn, request.schemas)
        schema_text = format_schema_for_llm(schema_summary)
        
        # Generate SQL using LLM
        llm = get_llm_generator()
        sql = llm.generate_sql(request.prompt, schema_text)
        
        if not sql:
            raise HTTPException(status_code=400, detail="Failed to generate SQL")
        
        # Sanitize and validate SQL
        sql = sanitize_sql(sql)
        is_safe, error = ensure_safe_select(sql)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"Generated SQL failed safety check: {error}")
        
        # Execute query with pagination
        paginated_sql = add_pagination(sql, page, page_size)
        
        with conn.cursor() as cursor:
            cursor.execute(paginated_sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
        
        # Generate HTML
        html = rows_to_html_table(results, "Query Results")
        
        return GenerateHTMLResponse(
            html=html,
            sql=sql,
            execution_time_ms=(time.time() - start_time) * 1000
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating HTML: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint with multi-block responses."""
    start_time = time.time()
    
    try:
        # Validate pagination
        page, page_size = validate_pagination_params(request.page, request.page_size)
        
        # Get schema information
        conn = get_db_connection()
        schema_summary = get_schema_summary(conn, request.schemas)
        schema_text = format_schema_for_llm(schema_summary)
        
        # Generate SQL using LLM
        llm = get_llm_generator()
        sql = llm.generate_sql(request.message, schema_text)
        
        results = None
        if sql:
            # Execute query with pagination
            paginated_sql = add_pagination(sql, page, page_size)
            
            with conn.cursor() as cursor:
                cursor.execute(paginated_sql)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in rows]
        
        # Generate chat response
        chat_response = llm.chat_response(request.message, sql, results)
        
        return ChatResponse(
            blocks=chat_response["blocks"],
            sql=sql,
            execution_time_ms=(time.time() - start_time) * 1000
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a safe SELECT query."""
    start_time = time.time()
    
    try:
        # Validate pagination
        page, page_size = validate_pagination_params(request.page, request.page_size)
        
        # Sanitize and validate SQL
        sql = sanitize_sql(request.sql)
        is_safe, error = ensure_safe_select(sql)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"SQL failed safety check: {error}")
        
        # Execute query with pagination
        conn = get_db_connection()
        paginated_sql = add_pagination(sql, page, page_size)
        
        with conn.cursor() as cursor:
            cursor.execute(paginated_sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
        
        response = QueryResponse(
            results=results,
            page=page,
            page_size=page_size,
            execution_time_ms=(time.time() - start_time) * 1000
        )
        
        # Get total count if requested
        if request.include_total:
            count_sql = create_count_query(sql)
            with conn.cursor() as cursor:
                cursor.execute(count_sql)
                total = cursor.fetchone()[0]
            response.total_rows = total
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        error_info = format_error_with_hints(str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Error executing query: {error_info['error']}",
            headers={"X-Error-Hint": error_info.get("hint", "")}
        )


@app.post("/download-csv")
async def download_csv(request: DownloadCSVRequest):
    """Download CSV data."""
    try:
        conn = get_db_connection()
        
        if request.sql:
            # Use provided SQL
            sql = sanitize_sql(request.sql)
            is_safe, error = ensure_safe_select(sql)
            if not is_safe:
                raise HTTPException(status_code=400, detail=f"SQL failed safety check: {error}")
        elif request.prompt:
            # Generate SQL from prompt
            schema_summary = get_schema_summary(conn, request.schemas)
            schema_text = format_schema_for_llm(schema_summary)
            
            llm = get_llm_generator()
            sql = llm.generate_sql(request.prompt, schema_text)
            
            if not sql:
                raise HTTPException(status_code=400, detail="Failed to generate SQL")
            
            sql = sanitize_sql(sql)
            is_safe, error = ensure_safe_select(sql)
            if not is_safe:
                raise HTTPException(status_code=400, detail=f"Generated SQL failed safety check: {error}")
        else:
            raise HTTPException(status_code=400, detail="Either sql or prompt must be provided")
        
        # Add row limit
        if "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip()} LIMIT {request.max_rows}"
        
        # Execute query
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
        
        # Generate CSV stream
        def generate_csv():
            for chunk in csv_stream(results, "export.csv"):
                yield chunk
        
        return StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=export.csv"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
