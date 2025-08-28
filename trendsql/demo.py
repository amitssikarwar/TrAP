#!/usr/bin/env python3
"""
TrendsQL Demo Script

This script demonstrates the key features of TrendsQL:
1. SQL safety validation
2. Schema introspection
3. LLM SQL generation (mock)
4. Data formatting
"""

import json
from datetime import datetime

# Import our modules
from app.sql_safety import ensure_safe_select, sanitize_sql
from app.formatters import rows_to_html_table, create_summary_stats
from app.pagination import validate_pagination_params, get_pagination_info


def demo_sql_safety():
    """Demonstrate SQL safety features."""
    print("🔒 SQL Safety Demo")
    print("-" * 40)
    
    # Test safe queries
    safe_queries = [
        "SELECT * FROM exploding_topics WHERE region = 'IN'",
        "SELECT topic, growth_score FROM exploding_topics ORDER BY growth_score DESC LIMIT 10",
        "WITH top_topics AS (SELECT * FROM exploding_topics WHERE growth_score > 80) SELECT * FROM top_topics"
    ]
    
    print("✅ Safe queries:")
    for query in safe_queries:
        is_safe, error = ensure_safe_select(query)
        print(f"  {query}")
        print(f"    Result: {'✅ Safe' if is_safe else '❌ Blocked'}")
    
    # Test unsafe queries
    unsafe_queries = [
        "INSERT INTO exploding_topics VALUES ('test', 'tech', 85.5)",
        "DROP TABLE exploding_topics",
        "DELETE FROM exploding_topics WHERE region = 'IN'"
    ]
    
    print("\n❌ Unsafe queries:")
    for query in unsafe_queries:
        is_safe, error = ensure_safe_select(query)
        print(f"  {query}")
        print(f"    Result: {'✅ Safe' if is_safe else '❌ Blocked'}")
        if not is_safe:
            print(f"    Error: {error}")


def demo_data_formatting():
    """Demonstrate data formatting features."""
    print("\n📊 Data Formatting Demo")
    print("-" * 40)
    
    # Sample data
    sample_data = [
        {
            "topic": "AI-powered pet care",
            "category": "Technology",
            "growth_score": 85.5,
            "popularity_score": 92.3,
            "region": "US",
            "first_seen_date": datetime(2024, 1, 15)
        },
        {
            "topic": "Sustainable fashion trends",
            "category": "Fashion",
            "growth_score": 78.2,
            "popularity_score": 88.7,
            "region": "US",
            "first_seen_date": datetime(2024, 1, 10)
        },
        {
            "topic": "Ayurvedic skincare",
            "category": "Beauty",
            "growth_score": 82.3,
            "popularity_score": 87.9,
            "region": "IN",
            "first_seen_date": datetime(2024, 1, 5)
        }
    ]
    
    # Generate HTML table
    html_table = rows_to_html_table(sample_data, "Trending Topics")
    print("HTML Table Preview:")
    print(html_table[:500] + "..." if len(html_table) > 500 else html_table)
    
    # Generate summary stats
    stats = create_summary_stats(sample_data)
    print(f"\n📈 Summary Statistics:")
    print(f"  Total rows: {stats['row_count']}")
    print(f"  Columns: {stats['column_count']}")
    print(f"  Numeric columns: {len(stats['numeric_columns'])}")
    
    for col in stats['numeric_columns']:
        print(f"    {col['column']}: min={col['min']}, max={col['max']}, avg={col['avg']:.2f}")


def demo_pagination():
    """Demonstrate pagination features."""
    print("\n📄 Pagination Demo")
    print("-" * 40)
    
    # Test pagination parameters
    test_cases = [
        (1, 10),
        (5, 50),
        (0, 1000),  # Invalid page
        (1, 2000),  # Invalid page size
    ]
    
    for page, page_size in test_cases:
        try:
            valid_page, valid_page_size = validate_pagination_params(page, page_size)
            print(f"Input: page={page}, page_size={page_size}")
            print(f"Validated: page={valid_page}, page_size={valid_page_size}")
            
            # Get pagination info
            pagination_info = get_pagination_info(valid_page, valid_page_size, total_rows=150)
            print(f"Pagination info: {json.dumps(pagination_info, indent=2)}")
            print()
        except Exception as e:
            print(f"Error: {e}")


def demo_api_endpoints():
    """Demonstrate API endpoint usage."""
    print("\n🌐 API Endpoints Demo")
    print("-" * 40)
    
    endpoints = [
        {
            "name": "Health Check",
            "method": "GET",
            "url": "/health",
            "description": "Check if the API is running"
        },
        {
            "name": "Generate SQL",
            "method": "POST",
            "url": "/generate-sql",
            "description": "Convert natural language to SQL",
            "example": {
                "prompt": "Show top 10 trending topics in India",
                "execute": True,
                "page": 1,
                "page_size": 10
            }
        },
        {
            "name": "Generate HTML",
            "method": "POST",
            "url": "/generate-html",
            "description": "Generate HTML table from natural language",
            "example": {
                "prompt": "Show topics with growth score above 80",
                "page": 1,
                "page_size": 20
            }
        },
        {
            "name": "Execute Query",
            "method": "POST",
            "url": "/query",
            "description": "Execute safe SELECT query",
            "example": {
                "sql": "SELECT topic, growth_score FROM exploding_topics WHERE region = 'IN' ORDER BY growth_score DESC LIMIT 5",
                "page": 1,
                "page_size": 10
            }
        },
        {
            "name": "Download CSV",
            "method": "POST",
            "url": "/download-csv",
            "description": "Export data as CSV",
            "example": {
                "prompt": "Export all AI-related topics",
                "max_rows": 1000
            }
        }
    ]
    
    for endpoint in endpoints:
        print(f"🔗 {endpoint['name']}")
        print(f"   {endpoint['method']} {endpoint['url']}")
        print(f"   {endpoint['description']}")
        if 'example' in endpoint:
            print(f"   Example: {json.dumps(endpoint['example'], indent=6)}")
        print()


def demo_configuration():
    """Demonstrate configuration options."""
    print("\n⚙️ Configuration Demo")
    print("-" * 40)
    
    print("📁 Environment Variables (.env):")
    env_vars = [
        "OPENAI_API_KEY=sk-your-key-here",
        "OPENAI_MODEL=gpt-4o-mini",
        "DB_HOST=127.0.0.1",
        "DB_PORT=5432",
        "DB_NAME=trendsql",
        "DB_USER=postgres",
        "DB_PASSWORD=postgres"
    ]
    
    for var in env_vars:
        print(f"  {var}")
    
    print("\n📁 Exploding Topics Config (config/exploding.yml):")
    exploding_config = {
        "provider": "exploding_topics",
        "fetch_mode": "csv",
        "csv_path": "./data/exploding_topics.csv",
        "filters": {
            "min_growth_score": 0,
            "regions": ["US", "IN"],
            "categories": []
        },
        "upsert": True
    }
    print(json.dumps(exploding_config, indent=2))
    
    print("\n📁 Google Trends Config (config/google_trends.yml):")
    gt_config = {
        "keywords": ["AI", "Machine Learning", "ChatGPT"],
        "timeframe": "today 3-m",
        "geo": "US",
        "category": 0,
        "gprop": "",
        "tz_offset_minutes": 0,
        "fetch_related_topics": True
    }
    print(json.dumps(gt_config, indent=2))


def main():
    """Run all demos."""
    print("🚀 TrendsQL Demo")
    print("=" * 60)
    print("This demo showcases the key features of TrendsQL")
    print("=" * 60)
    
    demos = [
        demo_sql_safety,
        demo_data_formatting,
        demo_pagination,
        demo_api_endpoints,
        demo_configuration
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"❌ Demo failed: {e}")
        
        print("\n" + "=" * 60)
    
    print("🎉 Demo complete!")
    print("\nTo get started:")
    print("1. Copy env.example to .env and add your OpenAI API key")
    print("2. Run 'make setup' to install dependencies and start database")
    print("3. Run 'make run' to start the application")
    print("4. Visit http://localhost:8000/docs for interactive API documentation")


if __name__ == "__main__":
    main()
