#!/usr/bin/env python3
"""
TrendsQL-KG Demo Script
Demonstrates the core functionality of the TrendsQL-KG system
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_section(title):
    """Print a formatted section"""
    print(f"\n--- {title} ---")

def demo_health_check():
    """Demo health check endpoint"""
    print_section("Health Check")
    
    # Simulate health check response
    health_response = {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": True,
            "openai": True,
            "neo4j": True
        }
    }
    
    print("Health Check Response:")
    print(json.dumps(health_response, indent=2))
    
    if health_response["ok"]:
        print("✅ All services are healthy!")
    else:
        print("❌ Some services are not responding")

def demo_schema_introspection():
    """Demo schema introspection"""
    print_section("Database Schema")
    
    # Simulate schema response
    schema_response = {
        "schemas": {
            "public": {
                "tables": [
                    {
                        "name": "exploding_topics",
                        "columns": [
                            {"name": "id", "type": "bigint", "nullable": False},
                            {"name": "topic", "type": "text", "nullable": False},
                            {"name": "category", "type": "text", "nullable": True},
                            {"name": "growth_score", "type": "numeric", "nullable": True},
                            {"name": "popularity_score", "type": "numeric", "nullable": True},
                            {"name": "region", "type": "text", "nullable": True},
                            {"name": "url", "type": "text", "nullable": True}
                        ]
                    },
                    {
                        "name": "gt_interest_over_time",
                        "columns": [
                            {"name": "id", "type": "bigint", "nullable": False},
                            {"name": "keyword", "type": "text", "nullable": False},
                            {"name": "date", "type": "date", "nullable": False},
                            {"name": "interest", "type": "integer", "nullable": False},
                            {"name": "geo", "type": "text", "nullable": True}
                        ]
                    }
                ]
            }
        },
        "tables": ["exploding_topics", "gt_interest_over_time"],
        "version": "1.0.0"
    }
    
    print("Available Tables:")
    for table in schema_response["tables"]:
        print(f"  📊 {table}")
    
    print("\nTable Details:")
    for table_info in schema_response["schemas"]["public"]["tables"]:
        print(f"\n  Table: {table_info['name']}")
        for column in table_info["columns"]:
            nullable = "NULL" if column["nullable"] else "NOT NULL"
            print(f"    - {column['name']}: {column['type']} {nullable}")

def demo_text_to_sql():
    """Demo Text-to-SQL functionality"""
    print_section("Text-to-SQL Generation")
    
    # Example prompts
    prompts = [
        "Show me the top 10 trending topics in India",
        "What are the most popular pet health topics?",
        "List topics with growth score above 80",
        "Show trending topics from the last 30 days"
    ]
    
    # Simulate SQL generation
    for i, prompt in enumerate(prompts, 1):
        print(f"\n{i}. Prompt: {prompt}")
        
        # Simulate generated SQL
        if "top 10" in prompt.lower() and "india" in prompt.lower():
            sql = """
            SELECT topic, growth_score, popularity_score, region
            FROM exploding_topics
            WHERE region = 'IN'
            ORDER BY growth_score DESC
            LIMIT 10
            """
        elif "pet health" in prompt.lower():
            sql = """
            SELECT topic, category, growth_score
            FROM exploding_topics
            WHERE category ILIKE '%pet%' OR category ILIKE '%health%'
            ORDER BY popularity_score DESC
            LIMIT 20
            """
        elif "growth score above 80" in prompt.lower():
            sql = """
            SELECT topic, growth_score, region
            FROM exploding_topics
            WHERE growth_score > 80
            ORDER BY growth_score DESC
            """
        else:
            sql = """
            SELECT topic, first_seen_date, growth_score
            FROM exploding_topics
            WHERE first_seen_date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY growth_score DESC
            """
        
        print(f"   Generated SQL:")
        print(f"   {sql.strip()}")
        
        # Simulate execution results
        print(f"   ✅ SQL generated and validated successfully")

def demo_rag_routing():
    """Demo RAG routing functionality"""
    print_section("Agentic RAG Routing")
    
    # Example questions
    questions = [
        {
            "question": "Show me the top 10 trending topics in India by growth score",
            "expected_route": "SQL_ONLY",
            "explanation": "This is a quantitative query asking for top N results with specific metrics"
        },
        {
            "question": "How are Ayurveda for dogs and pet anxiety related?",
            "expected_route": "KG_ONLY", 
            "explanation": "This is asking about relationships and connections between concepts"
        },
        {
            "question": "Which Ayurveda topics in India grew fastest and how are they connected?",
            "expected_route": "HYBRID",
            "explanation": "This combines quantitative analysis (growth) with relationship exploration"
        },
        {
            "question": "Tell me about natural pet care remedies",
            "expected_route": "VECTOR_FALLBACK",
            "explanation": "This is a semantic search for information about a topic"
        }
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. Question: {q['question']}")
        print(f"   Expected Route: {q['expected_route']}")
        print(f"   Explanation: {q['explanation']}")
        
        # Simulate routing decision
        print(f"   🤖 Router Analysis: Detected {q['expected_route']} signals")
        print(f"   ✅ Route selected: {q['expected_route']}")

def demo_knowledge_graph():
    """Demo Knowledge Graph functionality"""
    print_section("Knowledge Graph")
    
    # Simulate KG nodes
    nodes = [
        {
            "id": "Topic:Ayurveda for dogs",
            "label": "Topic",
            "properties": {
                "topic": "Ayurveda for dogs",
                "category": "Pet Health",
                "region": "IN",
                "growth_score": 85.5,
                "popularity_score": 72.3
            }
        },
        {
            "id": "Topic:Dog anxiety",
            "label": "Topic", 
            "properties": {
                "topic": "Dog anxiety",
                "category": "Pet Health",
                "region": "US",
                "growth_score": 67.2,
                "popularity_score": 89.1
            }
        },
        {
            "id": "Category:Pet Health",
            "label": "Category",
            "properties": {
                "name": "Pet Health"
            }
        }
    ]
    
    # Simulate relationships
    relationships = [
        {
            "source": "Topic:Ayurveda for dogs",
            "target": "Category:Pet Health",
            "type": "BELONGS_TO"
        },
        {
            "source": "Topic:Ayurveda for dogs",
            "target": "Topic:Dog anxiety",
            "type": "CO_TRENDS_WITH",
            "properties": {
                "correlation": 0.75,
                "window": "90 days"
            }
        }
    ]
    
    print("Knowledge Graph Nodes:")
    for node in nodes:
        print(f"  🟢 {node['label']}: {node['id']}")
        for key, value in node['properties'].items():
            print(f"    - {key}: {value}")
    
    print("\nKnowledge Graph Relationships:")
    for rel in relationships:
        print(f"  🔗 {rel['source']} -[{rel['type']}]-> {rel['target']}")
        if 'properties' in rel:
            for key, value in rel['properties'].items():
                print(f"    - {key}: {value}")

def demo_citations():
    """Demo citation generation"""
    print_section("Citations and Provenance")
    
    # Simulate citations
    citations = [
        {
            "type": "sql",
            "source": "exploding_topics",
            "identifier": "row_123",
            "url": "https://explodingtopics.com/topic/ayurveda-for-dogs",
            "confidence": 0.95
        },
        {
            "type": "kg",
            "source": "neo4j",
            "identifier": "Topic:Ayurveda for dogs",
            "url": None,
            "confidence": 0.88
        },
        {
            "type": "vector",
            "source": "node_summaries",
            "identifier": "summary_456",
            "url": None,
            "confidence": 0.82
        }
    ]
    
    print("Generated Citations:")
    for citation in citations:
        print(f"  📄 {citation['type'].upper()}: {citation['source']}")
        print(f"    - ID: {citation['identifier']}")
        if citation['url']:
            print(f"    - URL: {citation['url']}")
        print(f"    - Confidence: {citation['confidence']:.2f}")

def demo_api_endpoints():
    """Demo API endpoints"""
    print_section("API Endpoints")
    
    endpoints = [
        {"method": "GET", "path": "/health", "description": "Health check"},
        {"method": "GET", "path": "/schema", "description": "Database schema"},
        {"method": "POST", "path": "/generate-sql", "description": "Text-to-SQL generation"},
        {"method": "POST", "path": "/generate-html", "description": "HTML table generation"},
        {"method": "POST", "path": "/download-csv", "description": "CSV download"},
        {"method": "POST", "path": "/rag/answer", "description": "Agentic RAG question answering"},
        {"method": "POST", "path": "/kg/ingest", "description": "Data ingestion"},
        {"method": "POST", "path": "/kg/build", "description": "Knowledge Graph building"},
        {"method": "GET", "path": "/kg/subgraph", "description": "Knowledge Graph subgraph"}
    ]
    
    print("Available API Endpoints:")
    for endpoint in endpoints:
        print(f"  {endpoint['method']:<6} {endpoint['path']:<20} - {endpoint['description']}")

def demo_usage_examples():
    """Demo usage examples"""
    print_section("Usage Examples")
    
    examples = [
        {
            "title": "Text-to-SQL Query",
            "curl": '''curl -X POST "http://localhost:8000/generate-sql" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Show top 10 trending topics in India by growth score",
    "execute": true,
    "page": 1,
    "page_size": 10
  }' ''',
            "description": "Generate and execute SQL from natural language"
        },
        {
            "title": "RAG Question Answering",
            "curl": '''curl -X POST "http://localhost:8000/rag/answer" \\
  -H "Content-Type: application/json" \\
  -d '{
    "question": "How are Ayurveda for dogs and pet anxiety related in India?",
    "mode": "auto",
    "page": 1,
    "page_size": 50
  }' ''',
            "description": "Get intelligent answers with citations"
        },
        {
            "title": "Knowledge Graph Subgraph",
            "curl": '''curl -X GET "http://localhost:8000/kg/subgraph?topic=Ayurveda%20for%20dogs&depth=2&limit=50"''',
            "description": "Explore relationships in the knowledge graph"
        }
    ]
    
    for example in examples:
        print(f"\n📋 {example['title']}")
        print(f"   {example['description']}")
        print(f"   Command:")
        print(f"   {example['curl']}")

def main():
    """Main demo function"""
    print_header("TrendsQL-KG Demo")
    print("Welcome to TrendsQL-KG - Knowledge Graph + Agentic RAG for Trend Analysis!")
    print("\nThis demo showcases the core functionality of the system.")
    
    # Run demos
    demo_health_check()
    demo_schema_introspection()
    demo_text_to_sql()
    demo_rag_routing()
    demo_knowledge_graph()
    demo_citations()
    demo_api_endpoints()
    demo_usage_examples()
    
    print_header("Demo Complete")
    print("🎉 Demo completed successfully!")
    print("\nTo get started with TrendsQL-KG:")
    print("1. Run 'make setup' to install dependencies")
    print("2. Configure your .env file with API keys")
    print("3. Run 'make quick-start' to start all services")
    print("4. Visit http://localhost:8000/docs for interactive API documentation")
    print("\nHappy analyzing! 🚀")

if __name__ == "__main__":
    main()
