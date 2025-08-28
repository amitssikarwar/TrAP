import os
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import psycopg

logger = logging.getLogger(__name__)


class ExplodingTopicsConnector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider = config.get("provider", "exploding_topics")
        self.fetch_mode = config.get("fetch_mode", "csv")
        self.csv_path = config.get("csv_path", "./data/exploding_topics.csv")
        self.api_config = config.get("api", {})
        self.filters = config.get("filters", {})
        self.upsert = config.get("upsert", True)
        
        # Database connection
        self.db_conn = psycopg.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "trendsql"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres")
        )
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch data based on configured mode."""
        if self.fetch_mode == "csv":
            return self._fetch_from_csv()
        elif self.fetch_mode == "api":
            return self._fetch_from_api()
        else:
            raise ValueError(f"Unsupported fetch_mode: {self.fetch_mode}")
    
    def _fetch_from_csv(self) -> List[Dict[str, Any]]:
        """Fetch data from CSV file."""
        if not os.path.exists(self.csv_path):
            logger.warning(f"CSV file not found: {self.csv_path}")
            logger.info("Using sample data instead")
            return self._get_sample_data()
        
        data = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Map CSV columns to our schema
                    mapped_row = self._map_csv_row(row)
                    if self._apply_filters(mapped_row):
                        data.append(mapped_row)
            
            logger.info(f"Loaded {len(data)} rows from CSV")
            return data
            
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            logger.info("Using sample data instead")
            return self._get_sample_data()
    
    def _fetch_from_api(self) -> List[Dict[str, Any]]:
        """Fetch data from API (stub implementation)."""
        logger.warning("API mode not implemented yet - using sample data")
        return self._get_sample_data()
    
    def _map_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Map CSV row to our schema."""
        return {
            "topic": row.get("topic", ""),
            "category": row.get("category", ""),
            "source": row.get("source", "exploding"),
            "first_seen_date": self._parse_date(row.get("first_seen_date", "")),
            "growth_score": self._parse_numeric(row.get("growth_score", "")),
            "popularity_score": self._parse_numeric(row.get("popularity_score", "")),
            "region": row.get("region", ""),
            "url": row.get("url", "")
        }
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        
        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def _parse_numeric(self, value: str) -> Optional[float]:
        """Parse numeric string to float."""
        if not value:
            return None
        
        try:
            return float(value)
        except ValueError:
            return None
    
    def _apply_filters(self, row: Dict[str, Any]) -> bool:
        """Apply configured filters to row."""
        # Min growth score filter
        min_growth = self.filters.get("min_growth_score", 0)
        if row.get("growth_score") is not None and row["growth_score"] < min_growth:
            return False
        
        # Region filter
        regions = self.filters.get("regions", [])
        if regions and row.get("region") and row["region"] not in regions:
            return False
        
        # Category filter
        categories = self.filters.get("categories", [])
        if categories and row.get("category") and row["category"] not in categories:
            return False
        
        return True
    
    def _get_sample_data(self) -> List[Dict[str, Any]]:
        """Get sample data for testing."""
        return [
            {
                "topic": "AI-powered pet care",
                "category": "Technology",
                "source": "exploding",
                "first_seen_date": date(2024, 1, 15),
                "growth_score": 85.5,
                "popularity_score": 92.3,
                "region": "US",
                "url": "https://example.com/ai-pet-care"
            },
            {
                "topic": "Sustainable fashion trends",
                "category": "Fashion",
                "source": "exploding",
                "first_seen_date": date(2024, 1, 10),
                "growth_score": 78.2,
                "popularity_score": 88.7,
                "region": "US",
                "url": "https://example.com/sustainable-fashion"
            },
            {
                "topic": "Ayurvedic skincare",
                "category": "Beauty",
                "source": "exploding",
                "first_seen_date": date(2024, 1, 5),
                "growth_score": 82.3,
                "popularity_score": 87.9,
                "region": "IN",
                "url": "https://example.com/ayurvedic-skincare"
            }
        ]
    
    def ingest_data(self) -> Dict[str, int]:
        """Ingest data into database."""
        data = self.fetch_data()
        
        if not data:
            logger.warning("No data to ingest")
            return {"inserted": 0, "updated": 0}
        
        inserted = 0
        updated = 0
        
        try:
            with self.db_conn.cursor() as cursor:
                for row in data:
                    if self.upsert:
                        # Use upsert (INSERT ... ON CONFLICT)
                        result = self._upsert_row(cursor, row)
                        if result == "inserted":
                            inserted += 1
                        else:
                            updated += 1
                    else:
                        # Simple insert
                        self._insert_row(cursor, row)
                        inserted += 1
            
            self.db_conn.commit()
            logger.info(f"Ingestion complete: {inserted} inserted, {updated} updated")
            
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Error during ingestion: {e}")
            raise
        
        return {"inserted": inserted, "updated": updated}
    
    def _upsert_row(self, cursor, row: Dict[str, Any]) -> str:
        """Upsert a row into exploding_topics table."""
        query = """
        INSERT INTO exploding_topics 
        (topic, category, source, first_seen_date, growth_score, popularity_score, region, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (topic, COALESCE(region, ''))
        DO UPDATE SET
            category = EXCLUDED.category,
            source = EXCLUDED.source,
            first_seen_date = EXCLUDED.first_seen_date,
            growth_score = EXCLUDED.growth_score,
            popularity_score = EXCLUDED.popularity_score,
            url = EXCLUDED.url,
            created_at = NOW()
        RETURNING (xmax = 0) as is_insert
        """
        
        cursor.execute(query, (
            row["topic"],
            row["category"],
            row["source"],
            row["first_seen_date"],
            row["growth_score"],
            row["popularity_score"],
            row["region"],
            row["url"]
        ))
        
        result = cursor.fetchone()
        return "inserted" if result[0] else "updated"
    
    def _insert_row(self, cursor, row: Dict[str, Any]):
        """Insert a row into exploding_topics table."""
        query = """
        INSERT INTO exploding_topics 
        (topic, category, source, first_seen_date, growth_score, popularity_score, region, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            row["topic"],
            row["category"],
            row["source"],
            row["first_seen_date"],
            row["growth_score"],
            row["popularity_score"],
            row["region"],
            row["url"]
        ))
    
    def close(self):
        """Close database connection."""
        if self.db_conn and not self.db_conn.closed:
            self.db_conn.close()
