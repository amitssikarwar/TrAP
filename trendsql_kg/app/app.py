"""
Main FastAPI Application for TrendsQL-KG
Provides Text-to-SQL and Agentic RAG endpoints
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg
from psycopg.rows import dict_row

from .models import (
    SQLRequest, SQLResponse, HTMLRequest, CSVRequest, RAGRequest, RAGAnswer,
    HealthResponse, SchemaResponse, KGSubgraphRequest, KGSubgraphResponse,
    IngestRequest, IngestResponse, KGBuildRequest, KGBuildResponse
)
from .sql_safety import is_safe_sql, sanitize_sql
from .schema_introspect import SchemaIntrospector
from .llm_sql import init_llm_sql_generator, generate_sql, validate_sql, improve_sql
from .pagination import init_pagination_helper, execute_paginated_query, validate_pagination_params
from .formatters import format_html_table, format_csv, stream_csv, get_csv_filename
from .hints import format_error_response

# Import RAG modules (to be implemented)
# from ..rag.planner import RAGPlanner
# from ..rag.retrievers import SqlRetriever, KgRetriever, VectorRetriever
# from ..rag.synthesize import RAGSynthesizer

# Import KG modules (to be implemented)
# from ..kg.neo4j_client import Neo4jClient
# from ..kg.build_graph import KGBuilder

# Import connector modules (to be implemented)
# from ..connectors.exploding import ExplodingConnector
# from ..connectors.google_trends import GoogleTrendsConnector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TrendsQL-KG",
    description="Knowledge Graph + Agentic RAG for Trend Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for initialized components
schema_introspector = None
pagination_helper = None
# rag_planner = None
# kg_client = None


def get_db_connection_string() -> str:
    """Get database connection string from environment"""
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "5432")
    database = os.getenv("DB_NAME", "trendsql_kg")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def get_openai_config() -> Dict[str, str]:
    """Get OpenAI configuration from environment"""
    return {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
    }


def initialize_components():
    """Initialize all application components"""
    global schema_introspector, pagination_helper
    
    # Get configuration
    db_connection_string = get_db_connection_string()
    openai_config = get_openai_config()
    
    # Initialize schema introspector
    schema_introspector = SchemaIntrospector(db_connection_string)
    
    # Initialize pagination helper
    pagination_helper = init_pagination_helper(db_connection_string)
    
    # Initialize LLM SQL generator
    if openai_config["api_key"]:
        init_llm_sql_generator(openai_config["api_key"], openai_config["model"])
    else:
        logger.warning("OpenAI API key not found. LLM features will be disabled.")
    
    # TODO: Initialize RAG components
    # rag_planner = RAGPlanner(openai_config)
    
    # TODO: Initialize KG components
    # kg_client = Neo4jClient()
    
    logger.info("Application components initialized successfully")


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    initialize_components()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {
        "database": False,
        "openai": False,
        "neo4j": False
    }
    
    # Check database connection
    try:
        db_connection_string = get_db_connection_string()
        with psycopg.connect(db_connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                services["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
    
    # Check OpenAI connection
    openai_config = get_openai_config()
    if openai_config["api_key"]:
        services["openai"] = True
    
    # TODO: Check Neo4j connection
    # try:
    #     if kg_client:
    #         kg_client.ping()
    #         services["neo4j"] = True
    # except Exception as e:
    #     logger.error(f"Neo4j health check failed: {e}")
    
    return HealthResponse(
        ok=all(services.values()),
        timestamp=datetime.now(),
        services=services
    )


@app.get("/schema", response_model=SchemaResponse)
async def get_schema(schemas: str = "public"):
    """Get database schema information"""
    if not schema_introspector:
        raise HTTPException(status_code=500, detail="Schema introspector not initialized")
    
    try:
        schema_list = [s.strip() for s in schemas.split(",")]
        schema_info = schema_introspector.get_schema_json(schema_list)
        
        return SchemaResponse(
            schemas=schema_info,
            tables=[table["name"] for table in schema_info.get("tables", [])]
        )
    except Exception as e:
        logger.error(f"Schema introspection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Schema introspection failed: {str(e)}")


@app.post("/generate-sql", response_model=SQLResponse)
async def generate_sql_endpoint(request: SQLRequest):
    """Generate SQL from natural language prompt"""
    try:
        # Get schema information
        schema_info = schema_introspector.get_schema_json()
        
        # Generate SQL
        sql, error = generate_sql(request.prompt, schema_info)
        if error:
            raise HTTPException(status_code=400, detail=f"SQL generation failed: {error}")
        
        # Validate SQL
        is_safe, safety_error = is_safe_sql(sql)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"SQL safety check failed: {safety_error}")
        
        # Execute if requested
        results = None
        total_rows = None
        execution_time = None
        execution_error = None
        
        if request.execute:
            start_time = time.time()
            try:
                results, total_rows, metadata = execute_paginated_query(
                    sql, request.page, request.page_size
                )
                execution_time = time.time() - start_time
            except Exception as e:
                execution_error = str(e)
                # Try to improve SQL
                improved_sql, improve_error = improve_sql(sql, execution_error, schema_info)
                if not improve_error:
                    sql = improved_sql
                    # Try again with improved SQL
                    try:
                        results, total_rows, metadata = execute_paginated_query(
                            sql, request.page, request.page_size
                        )
                        execution_time = time.time() - start_time
                        execution_error = None
                    except Exception as e2:
                        execution_error = str(e2)
        
        return SQLResponse(
            sql=sql,
            executed=request.execute and execution_error is None,
            results=results,
            total_rows=total_rows,
            page=request.page,
            page_size=request.page_size,
            execution_time=execution_time,
            error=execution_error
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SQL generation endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/generate-html", response_class=HTMLResponse)
async def generate_html_endpoint(request: HTMLRequest):
    """Generate HTML table from SQL query"""
    try:
        # Validate SQL safety
        is_safe, safety_error = is_safe_sql(request.sql)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"SQL safety check failed: {safety_error}")
        
        # Execute query
        results, total_rows, metadata = execute_paginated_query(
            request.sql, request.page, request.page_size
        )
        
        # Add execution metadata
        metadata["execution_time"] = metadata.get("execution_time", 0)
        
        # Generate HTML
        html = format_html_table(results, metadata, request.include_metadata)
        
        return HTMLResponse(content=html)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HTML generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"HTML generation failed: {str(e)}")


@app.post("/download-csv")
async def download_csv_endpoint(request: CSVRequest):
    """Download CSV from SQL query"""
    try:
        # Validate SQL safety
        is_safe, safety_error = is_safe_sql(request.sql)
        if not is_safe:
            raise HTTPException(status_code=400, detail=f"SQL safety check failed: {safety_error}")
        
        # Execute query (get all results for CSV)
        db_connection_string = get_db_connection_string()
        with psycopg.connect(db_connection_string) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(request.sql)
                results = cur.fetchall()
        
        # Generate CSV
        csv_content = format_csv(results)
        
        # Generate filename
        filename = request.filename or get_csv_filename("export")
        
        return StreamingResponse(
            iter([csv_content]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV download failed: {e}")
        raise HTTPException(status_code=500, detail=f"CSV download failed: {str(e)}")


@app.post("/rag/answer", response_model=RAGAnswer)
async def rag_answer_endpoint(request: RAGRequest):
    """Agentic RAG endpoint for answering questions"""
    # TODO: Implement RAG functionality
    raise HTTPException(status_code=501, detail="RAG functionality not yet implemented")
    
    # Placeholder implementation:
    # try:
    #     # Plan the query route
    #     route = await rag_planner.plan_query(request.question, request.mode)
    #     
    #     # Retrieve context from different sources
    #     contexts = {}
    #     citations = []
    #     
    #     if route in ["SQL_ONLY", "HYBRID"]:
    #         sql_context = await sql_retriever.retrieve(request.question)
    #         contexts["sql"] = sql_context
    #         citations.extend(sql_retriever.get_citations())
    #     
    #     if route in ["KG_ONLY", "HYBRID"]:
    #         kg_context = await kg_retriever.retrieve(request.question)
    #         contexts["kg"] = kg_context
    #         citations.extend(kg_retriever.get_citations())
    #     
    #     if route == "VECTOR_FALLBACK":
    #         vector_context = await vector_retriever.retrieve(request.question)
    #         contexts["vector"] = vector_context
    #         citations.extend(vector_retriever.get_citations())
    #     
    #     # Synthesize answer
    #     answer = await rag_synthesizer.synthesize(request.question, contexts, citations)
    #     
    #     return RAGAnswer(
    #         answer=answer,
    #         route=route,
    #         contexts=contexts,
    #         citations=citations
    #     )
    #     
    # except Exception as e:
    #     logger.error(f"RAG answer failed: {e}")
    #     raise HTTPException(status_code=500, detail=f"RAG answer failed: {str(e)}")


@app.post("/kg/ingest", response_model=IngestResponse)
async def kg_ingest_endpoint(request: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger data ingestion"""
    # TODO: Implement ingestion functionality
    raise HTTPException(status_code=501, detail="Ingestion functionality not yet implemented")
    
    # Placeholder implementation:
    # try:
    #     if request.source == "exploding":
    #         connector = ExplodingConnector(request.config_file)
    #     elif request.source == "google_trends":
    #         connector = GoogleTrendsConnector(request.config_file)
    #     else:
    #         raise HTTPException(status_code=400, detail=f"Unknown source: {request.source}")
    #     
    #     # Run ingestion in background
    #     background_tasks.add_task(connector.ingest, request.force_refresh)
    #     
    #     return IngestResponse(
    #         success=True,
    #         source=request.source,
    #         records_processed=0,  # Will be updated by background task
    #         records_inserted=0,
    #         records_updated=0,
    #         processing_time=0
    #     )
    #     
    # except Exception as e:
    #     logger.error(f"Ingestion failed: {e}")
    #     raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/kg/build", response_model=KGBuildResponse)
async def kg_build_endpoint(request: KGBuildRequest, background_tasks: BackgroundTasks):
    """Build/refresh Knowledge Graph"""
    # TODO: Implement KG build functionality
    raise HTTPException(status_code=501, detail="KG build functionality not yet implemented")
    
    # Placeholder implementation:
    # try:
    #     builder = KGBuilder(request.config_file)
    #     
    #     # Run build in background
    #     background_tasks.add_task(builder.build, request.force_rebuild, request.incremental)
    #     
    #     return KGBuildResponse(
    #         success=True,
    #         nodes_created=0,
    #         nodes_updated=0,
    #         relationships_created=0,
    #         relationships_updated=0,
    #         summaries_generated=0,
    #         processing_time=0
    #     )
    #     
    # except Exception as e:
    #     logger.error(f"KG build failed: {e}")
    #     raise HTTPException(status_code=500, detail=f"KG build failed: {str(e)}")


@app.get("/kg/subgraph", response_model=KGSubgraphResponse)
async def kg_subgraph_endpoint(request: KGSubgraphRequest = Depends()):
    """Get Knowledge Graph subgraph"""
    # TODO: Implement KG subgraph functionality
    raise HTTPException(status_code=501, detail="KG subgraph functionality not yet implemented")
    
    # Placeholder implementation:
    # try:
    #     if request.topic:
    #         subgraph = await kg_client.get_topic_subgraph(
    #             request.topic, request.depth, request.limit
    #         )
    #     elif request.node_id:
    #         subgraph = await kg_client.get_node_subgraph(
    #             request.node_id, request.depth, request.limit
    #         )
    #     else:
    #         raise HTTPException(status_code=400, detail="Either topic or node_id must be provided")
    #     
    #     return KGSubgraphResponse(
    #         nodes=subgraph["nodes"],
    #         relationships=subgraph["relationships"],
    #         metadata=subgraph["metadata"]
    #     )
    #     
    # except Exception as e:
    #     logger.error(f"KG subgraph failed: {e}")
    #     raise HTTPException(status_code=500, detail=f"KG subgraph failed: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "TrendsQL-KG",
        "version": "1.0.0",
        "description": "Knowledge Graph + Agentic RAG for Trend Analysis",
        "endpoints": {
            "health": "/health",
            "schema": "/schema",
            "generate_sql": "/generate-sql",
            "generate_html": "/generate-html",
            "download_csv": "/download-csv",
            "rag_answer": "/rag/answer",
            "kg_ingest": "/kg/ingest",
            "kg_build": "/kg/build",
            "kg_subgraph": "/kg/subgraph",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)
