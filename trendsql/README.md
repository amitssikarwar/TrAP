# TrendsQL

A production-ready FastAPI microservice that provides a **Text-to-SQL** API for trend data analysis. TrendsQL ingests exploding topics and Google Trends data, stores them in PostgreSQL, and allows natural language queries to generate safe SQL.

## Features

- **Text-to-SQL Generation**: Convert natural language to safe SELECT queries using OpenAI
- **Data Ingestion**: Support for Exploding Topics and Google Trends data
- **SQL Safety**: Comprehensive protection against DDL/DML operations
- **Pagination**: Built-in pagination and result limiting
- **Multiple Output Formats**: JSON, HTML tables, and CSV streaming
- **Error Hints**: Intelligent error messages with suggestions
- **Docker Support**: Complete containerization with Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Docker & Docker Compose (optional)
- OpenAI API key

### 1. Clone and Setup

```bash
git clone <repository-url>
cd trendsql

# Copy environment file
cp env.example .env

# Edit .env with your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 2. Database Setup

#### Option A: Using Docker (Recommended)

```bash
# Start PostgreSQL with Docker
make db-up

# Initialize schema and seed data
make db-init
```

#### Option B: Local PostgreSQL

```bash
# Create database
createdb trendsql

# Apply schema
psql -d trendsql -f db/schema.sql
psql -d trendsql -f db/seed.sql
```

### 3. Install Dependencies

```bash
# Install Python dependencies
make install

# Or for development
make dev
```

### 4. Run the Application

```bash
# Start the FastAPI server
make run

# Or with Docker Compose
make docker-up
```

The API will be available at `http://localhost:8000`

## Data Ingestion

### Exploding Topics

```bash
# Ingest exploding topics data
make ingest-exploding

# Or manually
python -m ingestors.run_ingest exploding --config config/exploding.yml
```

### Google Trends

```bash
# Ingest Google Trends data
make ingest-google

# Or manually
python -m ingestors.run_ingest google --config config/google_trends.yml
```

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
# {"ok": true}
```

### Generate SQL from Natural Language

```bash
curl -X POST http://localhost:8000/generate-sql \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show the top 10 exploding topics in IN by growth_score this month",
    "execute": true,
    "page": 1,
    "page_size": 10,
    "include_total": true
  }'
```

### Generate HTML Table

```bash
curl -X POST http://localhost:8000/generate-html \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Show trending topics with growth score above 80",
    "page": 1,
    "page_size": 20
  }'
```

### Execute Custom SQL

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT topic, growth_score FROM exploding_topics WHERE region = '\''IN'\'' ORDER BY growth_score DESC LIMIT 5",
    "page": 1,
    "page_size": 10
  }'
```

### Download CSV

```bash
curl -X POST http://localhost:8000/download-csv \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Export all AI-related topics",
    "max_rows": 1000
  }' \
  --output results.csv
```

### Chat Interface

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the most popular topics in India?",
    "page": 1,
    "page_size": 10
  }'
```

## Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Database Configuration
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=trendsql
DB_USER=postgres
DB_PASSWORD=postgres
```

### Exploding Topics Config (`config/exploding.yml`)

```yaml
provider: exploding_topics
fetch_mode: csv  # or 'api'
csv_path: ./data/exploding_topics.csv

filters:
  min_growth_score: 0
  regions: ["US", "IN"]
  categories: []

upsert: true
```

### Google Trends Config (`config/google_trends.yml`)

```yaml
keywords: ["AI", "Machine Learning", "ChatGPT"]
timeframe: "today 3-m"
geo: "US"
category: 0
gprop: ""
tz_offset_minutes: 0
fetch_related_topics: true
```

## Database Schema

### Tables

- **`exploding_topics`**: Main exploding topics data
- **`exploding_topic_history`**: Historical time series data
- **`gt_interest_over_time`**: Google Trends interest data
- **`gt_related_topics`**: Google Trends related topics

### Key Indexes

- Topic/keyword lookups
- Date-based queries
- Geographic filtering
- Score-based sorting

## Development

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_sql_safety.py -v
```

### Development Commands

```bash
# Show all available commands
make help

# Clean up temporary files
make clean

# Reset everything (database + data)
make reset

# View Docker logs
make docker-logs
```

### Project Structure

```
trendsql/
├── app/                    # FastAPI application
│   ├── app.py             # Main API endpoints
│   ├── models.py          # Pydantic models
│   ├── sql_safety.py      # SQL safety checks
│   ├── schema_introspect.py # Database introspection
│   ├── llm_sql.py         # OpenAI integration
│   ├── formatters.py      # HTML/CSV formatting
│   ├── pagination.py      # Pagination logic
│   └── hints.py           # Error hints
├── connectors/             # Data connectors
│   ├── exploding.py       # Exploding topics connector
│   └── google_trends.py   # Google Trends connector
├── ingestors/             # Data ingestion
│   └── run_ingest.py      # CLI ingestion tool
├── config/                # Configuration files
├── db/                    # Database schema
├── tests/                 # Test files
└── requirements.txt       # Python dependencies
```

## Security Features

### SQL Safety

- **Whitelist Approach**: Only SELECT, WITH, and EXPLAIN statements allowed
- **Keyword Blocking**: Blocks INSERT, UPDATE, DELETE, DROP, CREATE, etc.
- **Injection Protection**: Prevents UNION-based attacks
- **Comment Removal**: Strips SQL comments
- **Multiple Statement Blocking**: Prevents chained statements

### Error Handling

- **Intelligent Hints**: Suggests similar column names
- **Query Improvements**: Recommends optimizations
- **Clear Messages**: User-friendly error descriptions

## Performance

### Optimizations

- **Connection Pooling**: Efficient database connections
- **Pagination**: Limits result sets
- **Indexing**: Optimized database queries
- **Caching**: LLM response caching (configurable)
- **Rate Limiting**: Google Trends API rate limiting

### Limits

- **Page Size**: Maximum 1000 rows per page
- **CSV Export**: Maximum 50,000 rows
- **Query Timeout**: 30 seconds per query
- **Concurrent Requests**: Configurable

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
make docker-up

# Or build manually
docker build -t trendsql .
docker-compose up -d
```

### Production Considerations

- **Environment Variables**: Use proper secrets management
- **Database**: Use managed PostgreSQL service
- **Monitoring**: Add health checks and logging
- **Scaling**: Use load balancer for multiple instances
- **Backup**: Regular database backups

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify connection parameters in `.env`
   - Ensure database exists

2. **OpenAI API Errors**
   - Verify API key is correct
   - Check API quota and billing
   - Ensure model name is valid

3. **Google Trends Rate Limiting**
   - Add delays between requests
   - Reduce number of keywords
   - Use longer timeframes

4. **CSV File Not Found**
   - Check file path in config
   - Ensure file has correct permissions
   - Verify CSV format matches expected schema

### Logs

```bash
# View application logs
docker-compose logs api

# View database logs
docker-compose logs db

# Follow logs in real-time
make docker-logs
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information
4. Include logs and configuration details
