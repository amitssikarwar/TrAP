# TrendsQL-KG

**Knowledge Graph + Agentic RAG for Trend Analysis**

TrendsQL-KG is a production-ready Python 3.11 project that ingests Exploding-style topics and Google Trends data, stores them in PostgreSQL, mirrors key entities into Neo4j as a Knowledge Graph, and exposes FastAPI endpoints for Text-to-SQL and Agentic RAG capabilities.

## 🚀 Features

### Core Capabilities
- **Text-to-SQL**: Natural language to SQL conversion with OpenAI
- **Agentic RAG**: Intelligent routing between SQL, Knowledge Graph, and Vector search
- **Knowledge Graph**: Neo4j integration with entity relationships and summaries
- **Data Ingestion**: Config-driven ingestion from Exploding Topics and Google Trends
- **Safe SQL**: Comprehensive SQL safety validation (SELECT only)
- **Pagination**: Built-in pagination and result limiting
- **Multiple Formats**: HTML tables, CSV export, JSON responses

### Agentic RAG Routing
- **SQL_ONLY**: Numeric aggregations, "top N by", date windows
- **KG_ONLY**: Relations/explanations, "how are X and Y related?"
- **HYBRID**: Combines SQL and Knowledge Graph for complex queries
- **VECTOR_FALLBACK**: Semantic search over node summaries

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │     Neo4j       │
│                 │    │                 │    │                 │
│ • Text-to-SQL   │◄──►│ • Trend Data    │◄──►│ • Knowledge     │
│ • Agentic RAG   │    │ • Node Summaries│    │   Graph         │
│ • API Endpoints │    │ • Vector Search │    │ • Relationships │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   RAG System    │    │   Vector Store  │
│                 │    │                 │    │                 │
│ • Exploding     │    │ • Planner       │    │ • Embeddings    │
│ • Google Trends │    │ • Retrievers    │    │ • Similarity    │
└─────────────────┘    │ • Synthesizer   │    │   Search        │
                       └─────────────────┘    └─────────────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- OpenAI API key

### Quick Start

1. **Clone and setup**:
```bash
git clone <repository>
cd trendsql_kg
make setup
```

2. **Configure environment**:
```bash
cp env.example .env
# Edit .env with your OpenAI API key and other settings
```

3. **Start services**:
```bash
make quick-start
```

4. **Access the application**:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

## 🔧 Configuration

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Database Configuration
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=trendsql_kg
DB_USER=postgres
DB_PASSWORD=postgres

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j
```

### Configuration Files
- `config/exploding.yml`: Exploding Topics ingestion settings
- `config/google_trends.yml`: Google Trends parameters
- `config/kg.yml`: Knowledge Graph projection settings
- `config/rag.yml`: RAG planner and retrieval configuration

## 📊 Database Schema

### PostgreSQL Tables
```sql
-- Exploding Topics
CREATE TABLE exploding_topics (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    category TEXT,
    growth_score NUMERIC,
    popularity_score NUMERIC,
    region TEXT,
    url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Google Trends Interest
CREATE TABLE gt_interest_over_time (
    id BIGSERIAL PRIMARY KEY,
    keyword TEXT NOT NULL,
    date DATE NOT NULL,
    interest INT NOT NULL,
    geo TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge Graph Summaries
CREATE TABLE kg_node_summaries (
    id BIGSERIAL PRIMARY KEY,
    node_id TEXT NOT NULL,
    node_label TEXT NOT NULL,
    summary TEXT NOT NULL,
    embedding VECTOR(3072),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Neo4j Knowledge Graph
```cypher
// Nodes
(:Topic {topic, category, region, growth_score, popularity_score})
(:Keyword {name, geo, gprop})
(:Category {name})
(:Region {code})

// Relationships
(:Topic)-[:BELONGS_TO]->(:Category)
(:Topic)-[:SEEN_IN]->(:Region)
(:Keyword)-[:ALSO_RELATES_TO {type, value}]->(:Keyword)
(:Topic)-[:MENTIONS]->(:Keyword)
(:Topic)-[:CO_TRENDS_WITH {window, corr}]->(:Topic)
```

## 🚀 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /schema` - Database schema information
- `POST /generate-sql` - Generate and execute SQL from natural language
- `POST /generate-html` - Generate HTML tables from SQL
- `POST /download-csv` - Download CSV from SQL query

### RAG Endpoints
- `POST /rag/answer` - Agentic RAG question answering

### Knowledge Graph Endpoints
- `POST /kg/ingest` - Trigger data ingestion
- `POST /kg/build` - Build/refresh knowledge graph
- `GET /kg/subgraph` - Get knowledge graph subgraph

## 💡 Usage Examples

### Text-to-SQL
```bash
curl -X POST "http://localhost:8000/generate-sql" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show top 10 trending topics in India by growth score",
    "execute": true,
    "page": 1,
    "page_size": 10
  }'
```

### Agentic RAG
```bash
curl -X POST "http://localhost:8000/rag/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How are Ayurveda for dogs and pet anxiety related in India?",
    "mode": "auto",
    "page": 1,
    "page_size": 50
  }'
```

### Knowledge Graph Subgraph
```bash
curl -X GET "http://localhost:8000/kg/subgraph?topic=Ayurveda%20for%20dogs&depth=2&limit=50"
```

## 🔄 Data Ingestion

### Exploding Topics
```bash
make ingest-exp
```

### Google Trends
```bash
make ingest-gt
```

### Build Knowledge Graph
```bash
make kg-build
```

## 🧪 Testing

### Run Tests
```bash
make test
```

### Health Check
```bash
make health
```

## 🐳 Docker Deployment

### Start All Services
```bash
make docker-up
```

### Start Only Databases
```bash
make db-up
```

### View Logs
```bash
make docker-logs
```

### Stop Services
```bash
make docker-down
```

## 🔍 Monitoring

### Service Status
```bash
make monitor
```

### Database Backup
```bash
make backup
```

### Database Restore
```bash
make restore
```

## 🛠️ Development

### Development Setup
```bash
make dev-setup
```

### Development Run
```bash
make dev-run
```

### Code Formatting
```bash
make format
```

### Linting
```bash
make lint
```

### Security Check
```bash
make security-check
```

## 📁 Project Structure

```
trendsql_kg/
├── app/                    # FastAPI application
│   ├── app.py             # Main FastAPI app
│   ├── models.py          # Pydantic models
│   ├── sql_safety.py      # SQL safety validation
│   ├── schema_introspect.py # Database schema introspection
│   ├── llm_sql.py         # OpenAI SQL generation
│   ├── pagination.py      # Pagination utilities
│   ├── formatters.py      # HTML/CSV formatters
│   └── hints.py           # Error hints and suggestions
├── rag/                   # Agentic RAG system
│   ├── planner.py         # Query routing planner
│   ├── retrievers.py      # SQL/KG/Vector retrievers
│   ├── synthesize.py      # Answer synthesis
│   ├── citations.py       # Citation handling
│   └── prompts/           # LLM prompts
├── kg/                    # Knowledge Graph
│   ├── neo4j_client.py    # Neo4j driver
│   ├── build_graph.py     # ETL from Postgres to Neo4j
│   ├── schema.cypher      # Neo4j schema
│   ├── mapping.py         # Relational to graph mapping
│   └── summarize.py       # Node summarization
├── connectors/            # Data source connectors
│   ├── exploding.py       # Exploding Topics connector
│   └── google_trends.py   # Google Trends connector
├── ingestors/             # Data ingestion tools
│   ├── run_ingest.py      # CLI for data ingestion
│   └── run_build_kg.py    # CLI for KG building
├── config/                # Configuration files
│   ├── exploding.yml      # Exploding Topics config
│   ├── google_trends.yml  # Google Trends config
│   ├── kg.yml            # Knowledge Graph config
│   └── rag.yml           # RAG configuration
├── db/                    # Database files
│   └── schema.sql        # PostgreSQL schema
├── tests/                 # Test suite
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose stack
├── Makefile              # Development commands
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🔒 Security

### SQL Safety
- Only SELECT queries are allowed
- Comprehensive keyword blocking
- Injection attack prevention
- Input sanitization

### API Security
- Environment-based secrets
- Input validation
- Error message sanitization
- Rate limiting (configurable)

## 📈 Performance

### Optimizations
- Database connection pooling
- Query result caching
- Pagination for large datasets
- Efficient vector search
- Background task processing

### Monitoring
- Health checks for all services
- Performance metrics
- Error tracking and logging
- Resource usage monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

**Database Connection Failed**
```bash
# Check if databases are running
make health

# Restart databases
make db-reset
```

**OpenAI API Errors**
```bash
# Check API key in .env file
cat .env | grep OPENAI_API_KEY

# Test API connection
curl -X GET "http://localhost:8000/health"
```

**Neo4j Connection Issues**
```bash
# Check Neo4j status
docker-compose ps neo4j

# View Neo4j logs
make logs-neo4j
```

### Getting Help
- Check the API documentation at http://localhost:8000/docs
- Review the logs: `make docker-logs`
- Check service health: `make health`
- Open an issue on GitHub

## 🎯 Roadmap

### Phase 1 (Current)
- ✅ Core FastAPI application
- ✅ Text-to-SQL functionality
- ✅ Database schema and safety
- ✅ Basic Docker setup

### Phase 2 (Next)
- 🔄 Knowledge Graph ETL
- 🔄 Neo4j integration
- 🔄 Node summarization
- 🔄 Basic RAG system

### Phase 3 (Future)
- 📋 Advanced Agentic RAG
- 📋 Vector search optimization
- 📋 Real-time data ingestion
- 📋 Advanced analytics
- 📋 Web UI dashboard

---

**TrendsQL-KG** - Transform your trend data into actionable insights with the power of Knowledge Graphs and Agentic RAG! 🚀
