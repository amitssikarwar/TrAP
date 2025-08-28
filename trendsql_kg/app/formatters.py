"""
Formatters Module for TrendsQL-KG
Handles HTML table generation and CSV streaming
"""

import csv
import io
import logging
from typing import Dict, List, Any, Optional, Generator
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)


class HTMLFormatter:
    """HTML table formatter for SQL results"""
    
    def __init__(self):
        """Initialize HTML formatter"""
        self.css_styles = self._get_css_styles()
    
    def format_table(self, results: List[Dict[str, Any]], 
                    metadata: Optional[Dict[str, Any]] = None,
                    include_metadata: bool = True) -> str:
        """
        Format SQL results as HTML table
        
        Args:
            results: List of result rows
            metadata: Optional metadata (pagination, etc.)
            include_metadata: Whether to include metadata in HTML
            
        Returns:
            HTML table string
        """
        if not results:
            return self._format_empty_table()
        
        # Get column headers
        headers = list(results[0].keys()) if results else []
        
        # Build HTML
        html_parts = []
        
        # Add CSS styles
        html_parts.append(f"<style>{self.css_styles}</style>")
        
        # Add metadata if requested
        if include_metadata and metadata:
            html_parts.append(self._format_metadata(metadata))
        
        # Start table
        html_parts.append('<div class="table-container">')
        html_parts.append('<table class="data-table">')
        
        # Add header row
        html_parts.append('<thead>')
        html_parts.append('<tr>')
        for header in headers:
            html_parts.append(f'<th>{self._escape_html(header)}</th>')
        html_parts.append('</tr>')
        html_parts.append('</thead>')
        
        # Add data rows
        html_parts.append('<tbody>')
        for row in results:
            html_parts.append('<tr>')
            for header in headers:
                value = row.get(header)
                formatted_value = self._format_cell_value(value)
                html_parts.append(f'<td>{formatted_value}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody>')
        
        # End table
        html_parts.append('</table>')
        html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def _format_empty_table(self) -> str:
        """Format empty table message"""
        return """
        <style>
        .empty-table {
            text-align: center;
            padding: 2rem;
            color: #666;
            font-style: italic;
        }
        </style>
        <div class="empty-table">
            No data found
        </div>
        """
    
    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as HTML"""
        html_parts = []
        html_parts.append('<div class="metadata">')
        
        if 'pagination' in metadata:
            pagination = metadata['pagination']
            html_parts.append('<div class="pagination-info">')
            html_parts.append(f'<span>Page {pagination.get("page", 1)} of {pagination.get("total_pages", 1)}</span>')
            html_parts.append(f'<span>Showing {pagination.get("result_count", 0)} of {pagination.get("total_count", 0)} results</span>')
            html_parts.append('</div>')
        
        if 'execution_time' in metadata:
            html_parts.append(f'<div class="execution-time">Query executed in {metadata["execution_time"]:.3f}s</div>')
        
        html_parts.append('</div>')
        return '\n'.join(html_parts)
    
    def _format_cell_value(self, value: Any) -> str:
        """Format a cell value for HTML display"""
        if value is None:
            return '<span class="null-value">NULL</span>'
        
        if isinstance(value, (datetime, date)):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        
        if isinstance(value, (int, float)):
            return str(value)
        
        if isinstance(value, bool):
            return '✓' if value else '✗'
        
        if isinstance(value, (dict, list)):
            return f'<pre>{self._escape_html(json.dumps(value, indent=2))}</pre>'
        
        # Default: escape as string
        return self._escape_html(str(value))
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the table"""
        return """
        .table-container {
            margin: 1rem 0;
            overflow-x: auto;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .data-table th {
            background: #f8f9fa;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #dee2e6;
            color: #495057;
        }
        
        .data-table td {
            padding: 8px;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }
        
        .data-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        .data-table tbody tr:nth-child(even) {
            background-color: #fafbfc;
        }
        
        .null-value {
            color: #6c757d;
            font-style: italic;
        }
        
        .metadata {
            margin-bottom: 1rem;
            padding: 0.5rem;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 12px;
            color: #6c757d;
        }
        
        .pagination-info {
            display: flex;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        
        .execution-time {
            font-style: italic;
        }
        
        pre {
            margin: 0;
            white-space: pre-wrap;
            font-size: 12px;
            background: #f8f9fa;
            padding: 4px;
            border-radius: 2px;
        }
        """


class CSVFormatter:
    """CSV formatter for SQL results"""
    
    def __init__(self, dialect: str = 'excel'):
        """
        Initialize CSV formatter
        
        Args:
            dialect: CSV dialect to use
        """
        self.dialect = dialect
    
    def format_csv(self, results: List[Dict[str, Any]], 
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Format SQL results as CSV string
        
        Args:
            results: List of result rows
            metadata: Optional metadata
            
        Returns:
            CSV string
        """
        if not results:
            return ""
        
        # Get column headers
        headers = list(results[0].keys()) if results else []
        
        # Create CSV string
        output = io.StringIO()
        writer = csv.writer(output, dialect=self.dialect)
        
        # Write header
        writer.writerow(headers)
        
        # Write data rows
        for row in results:
            writer.writerow([self._format_csv_value(row.get(header)) for header in headers])
        
        return output.getvalue()
    
    def stream_csv(self, results: List[Dict[str, Any]], 
                  metadata: Optional[Dict[str, Any]] = None) -> Generator[str, None, None]:
        """
        Stream SQL results as CSV chunks
        
        Args:
            results: List of result rows
            metadata: Optional metadata
            
        Yields:
            CSV chunks
        """
        if not results:
            return
        
        # Get column headers
        headers = list(results[0].keys()) if results else []
        
        # Create CSV writer
        output = io.StringIO()
        writer = csv.writer(output, dialect=self.dialect)
        
        # Write header
        writer.writerow(headers)
        yield output.getvalue()
        output.seek(0)
        output.truncate()
        
        # Write data rows in chunks
        chunk_size = 1000
        for i in range(0, len(results), chunk_size):
            chunk = results[i:i + chunk_size]
            
            for row in chunk:
                writer.writerow([self._format_csv_value(row.get(header)) for header in headers])
            
            yield output.getvalue()
            output.seek(0)
            output.truncate()
    
    def _format_csv_value(self, value: Any) -> str:
        """Format a value for CSV output"""
        if value is None:
            return ""
        
        if isinstance(value, (datetime, date)):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        
        return str(value)
    
    def get_csv_filename(self, base_name: str = "export") -> str:
        """Generate CSV filename with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.csv"


class JSONFormatter:
    """JSON formatter for SQL results"""
    
    def format_json(self, results: List[Dict[str, Any]], 
                   metadata: Optional[Dict[str, Any]] = None,
                   pretty: bool = True) -> str:
        """
        Format SQL results as JSON
        
        Args:
            results: List of result rows
            metadata: Optional metadata
            pretty: Whether to format with indentation
            
        Returns:
            JSON string
        """
        response = {
            'results': results,
            'metadata': metadata or {}
        }
        
        if pretty:
            return json.dumps(response, indent=2, default=self._json_serializer)
        else:
            return json.dumps(response, default=self._json_serializer)
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime objects"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


# Global instances
html_formatter = HTMLFormatter()
csv_formatter = CSVFormatter()
json_formatter = JSONFormatter()


def format_html_table(results: List[Dict[str, Any]], 
                     metadata: Optional[Dict[str, Any]] = None,
                     include_metadata: bool = True) -> str:
    """Format results as HTML table using global formatter"""
    return html_formatter.format_table(results, metadata, include_metadata)


def format_csv(results: List[Dict[str, Any]], 
              metadata: Optional[Dict[str, Any]] = None) -> str:
    """Format results as CSV using global formatter"""
    return csv_formatter.format_csv(results, metadata)


def stream_csv(results: List[Dict[str, Any]], 
              metadata: Optional[Dict[str, Any]] = None) -> Generator[str, None, None]:
    """Stream results as CSV using global formatter"""
    return csv_formatter.stream_csv(results, metadata)


def format_json(results: List[Dict[str, Any]], 
               metadata: Optional[Dict[str, Any]] = None,
               pretty: bool = True) -> str:
    """Format results as JSON using global formatter"""
    return json_formatter.format_json(results, metadata, pretty)


def get_csv_filename(base_name: str = "export") -> str:
    """Get CSV filename using global formatter"""
    return csv_formatter.get_csv_filename(base_name)
