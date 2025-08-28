import csv
import io
from typing import List, Dict, Any, Generator
from datetime import datetime


def rows_to_html_table(rows: List[Dict[str, Any]], title: str = "Query Results") -> str:
    """
    Convert rows to HTML table.
    """
    if not rows:
        return f"<h3>{title}</h3><p>No results found.</p>"
    
    # Get column names from first row
    columns = list(rows[0].keys())
    
    html = f"""
    <div class="query-results">
        <h3>{title}</h3>
        <table class="data-table">
            <thead>
                <tr>
                    {''.join(f'<th>{col}</th>' for col in columns)}
                </tr>
            </thead>
            <tbody>
    """
    
    for row in rows:
        html += "<tr>"
        for col in columns:
            value = row.get(col)
            if value is None:
                html += "<td><em>NULL</em></td>"
            elif isinstance(value, (int, float)):
                html += f"<td class='numeric'>{value}</td>"
            elif isinstance(value, datetime):
                html += f"<td class='datetime'>{value.strftime('%Y-%m-%d %H:%M:%S')}</td>"
            else:
                # Escape HTML characters
                escaped_value = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html += f"<td>{escaped_value}</td>"
        html += "</tr>"
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html


def csv_stream(rows: List[Dict[str, Any]], filename: str = "export.csv") -> Generator[str, None, None]:
    """
    Generate CSV content as a stream.
    """
    if not rows:
        yield ""
        return
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    
    # Write header
    writer.writeheader()
    yield output.getvalue()
    output.seek(0)
    output.truncate()
    
    # Write rows in batches
    batch_size = 100
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        for row in batch:
            # Handle None values and format dates
            formatted_row = {}
            for key, value in row.items():
                if value is None:
                    formatted_row[key] = ""
                elif isinstance(value, datetime):
                    formatted_row[key] = value.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_row[key] = str(value)
            
            writer.writerow(formatted_row)
        
        yield output.getvalue()
        output.seek(0)
        output.truncate()


def format_number(value: Any) -> str:
    """
    Format numbers for display.
    """
    if isinstance(value, (int, float)):
        if isinstance(value, int):
            return f"{value:,}"
        else:
            return f"{value:,.2f}"
    return str(value)


def create_summary_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create summary statistics for the results.
    """
    if not rows:
        return {"row_count": 0}
    
    stats = {
        "row_count": len(rows),
        "column_count": len(rows[0]) if rows else 0,
        "columns": list(rows[0].keys()) if rows else []
    }
    
    # Add numeric column stats
    numeric_columns = []
    for col in stats["columns"]:
        values = [row[col] for row in rows if row[col] is not None and isinstance(row[col], (int, float))]
        if values:
            numeric_columns.append({
                "column": col,
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values)
            })
    
    stats["numeric_columns"] = numeric_columns
    
    return stats


def format_error_message(error: str, hint: str = None) -> str:
    """
    Format error message with optional hint.
    """
    html = f"""
    <div class="error-message">
        <h3>Error</h3>
        <p>{error}</p>
    """
    
    if hint:
        html += f"""
        <div class="hint">
            <strong>Hint:</strong> {hint}
        </div>
        """
    
    html += "</div>"
    
    return html
