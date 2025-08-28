from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class HealthResponse(BaseModel):
    ok: bool = True


class SchemaResponse(BaseModel):
    schemas: Dict[str, Dict[str, List[Dict[str, str]]]]


class GenerateSQLRequest(BaseModel):
    prompt: str = Field(..., description="Natural language query")
    execute: bool = Field(False, description="Whether to execute the generated SQL")
    schemas: List[str] = Field(default=["public"], description="Database schemas to include")
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    page_size: int = Field(default=50, ge=1, le=1000, description="Page size for pagination")
    include_total: bool = Field(default=False, description="Include total row count")
    as_html: bool = Field(default=False, description="Return results as HTML table")


class GenerateSQLResponse(BaseModel):
    sql: str
    explain: Optional[str] = None
    preview: Optional[List[Dict[str, Any]]] = None
    html: Optional[str] = None
    page: int
    page_size: int
    total_rows: Optional[int] = None
    execution_time_ms: Optional[float] = None


class GenerateHTMLRequest(BaseModel):
    prompt: str = Field(..., description="Natural language query")
    schemas: List[str] = Field(default=["public"], description="Database schemas to include")
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    page_size: int = Field(default=50, ge=1, le=1000, description="Page size for pagination")


class GenerateHTMLResponse(BaseModel):
    html: str
    sql: str
    execution_time_ms: Optional[float] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    schemas: List[str] = Field(default=["public"], description="Database schemas to include")
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    page_size: int = Field(default=50, ge=1, le=1000, description="Page size for pagination")


class ChatResponse(BaseModel):
    blocks: List[Dict[str, Any]]  # markdown, code, html, meta blocks
    sql: Optional[str] = None
    execution_time_ms: Optional[float] = None


class QueryRequest(BaseModel):
    sql: str = Field(..., description="SQL query to execute")
    page: int = Field(default=1, ge=1, description="Page number for pagination")
    page_size: int = Field(default=50, ge=1, le=1000, description="Page size for pagination")
    include_total: bool = Field(default=False, description="Include total row count")


class QueryResponse(BaseModel):
    results: List[Dict[str, Any]]
    page: int
    page_size: int
    total_rows: Optional[int] = None
    execution_time_ms: Optional[float] = None


class DownloadCSVRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="Natural language query")
    sql: Optional[str] = Field(None, description="SQL query to execute")
    schemas: List[str] = Field(default=["public"], description="Database schemas to include")
    max_rows: int = Field(default=5000, ge=1, le=50000, description="Maximum rows to export")


class ErrorResponse(BaseModel):
    error: str
    hint: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
