"""
Pydantic models for TrendsQL-KG FastAPI application
"""

from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl


class RouteType(str, Enum):
    """RAG routing types"""
    SQL_ONLY = "sql_only"
    KG_ONLY = "kg_only"
    HYBRID = "hybrid"
    VECTOR_FALLBACK = "vector_fallback"
    AUTO = "auto"


class CitationType(str, Enum):
    """Citation types for provenance"""
    SQL = "sql"
    KG = "kg"
    VECTOR = "vector"
    URL = "url"


class Citation(BaseModel):
    """Citation model for answer provenance"""
    type: CitationType
    source: str
    identifier: str
    url: Optional[HttpUrl] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class RAGContext(BaseModel):
    """Context retrieved from different sources"""
    sql: Optional[List[Dict[str, Any]]] = None
    kg: Optional[Dict[str, Any]] = None
    vector: Optional[List[Dict[str, Any]]] = None


class RAGAnswer(BaseModel):
    """RAG answer with provenance"""
    answer: str
    route: RouteType
    contexts: RAGContext
    citations: List[Citation]
    confidence: Optional[float] = None
    processing_time: Optional[float] = None


class RAGRequest(BaseModel):
    """RAG query request"""
    question: str = Field(..., description="Natural language question")
    mode: RouteType = Field(RouteType.AUTO, description="Routing mode")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=100, description="Page size")
    include_citations: bool = Field(True, description="Include citations in response")
    max_tokens: Optional[int] = Field(None, ge=100, le=2000, description="Max tokens for answer")


class SQLRequest(BaseModel):
    """SQL generation request"""
    prompt: str = Field(..., description="Natural language prompt")
    execute: bool = Field(False, description="Execute the generated SQL")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Page size")


class SQLResponse(BaseModel):
    """SQL generation response"""
    sql: str
    executed: bool
    results: Optional[List[Dict[str, Any]]] = None
    total_rows: Optional[int] = None
    page: int
    page_size: int
    execution_time: Optional[float] = None
    error: Optional[str] = None


class HTMLRequest(BaseModel):
    """HTML table generation request"""
    sql: str = Field(..., description="SQL query to execute")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Page size")
    include_metadata: bool = Field(True, description="Include metadata in HTML")


class CSVRequest(BaseModel):
    """CSV download request"""
    sql: str = Field(..., description="SQL query to execute")
    filename: Optional[str] = Field(None, description="CSV filename")


class HealthResponse(BaseModel):
    """Health check response"""
    ok: bool
    timestamp: datetime
    version: str = "1.0.0"
    services: Dict[str, bool]


class SchemaResponse(BaseModel):
    """Database schema response"""
    schemas: Dict[str, Any]
    tables: List[str]
    version: str = "1.0.0"


class KGSubgraphRequest(BaseModel):
    """Knowledge Graph subgraph request"""
    topic: Optional[str] = Field(None, description="Topic to get subgraph for")
    node_id: Optional[str] = Field(None, description="Neo4j node ID")
    depth: int = Field(2, ge=1, le=5, description="Graph traversal depth")
    limit: int = Field(100, ge=1, le=1000, description="Maximum nodes to return")


class KGSubgraphResponse(BaseModel):
    """Knowledge Graph subgraph response"""
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class IngestRequest(BaseModel):
    """Data ingestion request"""
    source: str = Field(..., description="Data source (exploding, google_trends)")
    config_file: str = Field(..., description="Configuration file path")
    force_refresh: bool = Field(False, description="Force refresh existing data")


class IngestResponse(BaseModel):
    """Data ingestion response"""
    success: bool
    source: str
    records_processed: int
    records_inserted: int
    records_updated: int
    processing_time: float
    error: Optional[str] = None


class KGBuildRequest(BaseModel):
    """Knowledge Graph build request"""
    config_file: str = Field(..., description="KG configuration file path")
    force_rebuild: bool = Field(False, description="Force rebuild entire graph")
    incremental: bool = Field(True, description="Incremental update")


class KGBuildResponse(BaseModel):
    """Knowledge Graph build response"""
    success: bool
    nodes_created: int
    nodes_updated: int
    relationships_created: int
    relationships_updated: int
    summaries_generated: int
    processing_time: float
    error: Optional[str] = None
