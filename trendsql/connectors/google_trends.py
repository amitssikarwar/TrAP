import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import psycopg
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)


class GoogleTrendsConnector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.keywords = config.get("keywords", [])
        self.timeframe = config.get("timeframe", "today 3-m")
        self.geo = config.get("geo", "")
        self.category = config.get("category", 0)
        self.gprop = config.get("gprop", "")
        self.tz_offset_minutes = config.get("tz_offset_minutes", 0)
        self.fetch_related_topics = config.get("fetch_related_topics", True)
        
        # Initialize pytrends
        self.pytrends = TrendReq(tz=self.tz_offset_minutes)
        
        # Database connection
        self.db_conn = psycopg.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "trendsql"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres")
        )
    
    def fetch_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch Google Trends data for all keywords."""
        if not self.keywords:
            logger.warning("No keywords configured")
            return {"interest_over_time": [], "related_topics": []}
        
        interest_data = []
        related_data = []
        
        for keyword in self.keywords:
            logger.info(f"Fetching data for keyword: {keyword}")
            
            try:
                # Build payload
                self.pytrends.build_payload(
                    kw_list=[keyword],
                    cat=self.category,
                    timeframe=self.timeframe,
                    geo=self.geo,
                    gprop=self.gprop
                )
                
                # Fetch interest over time
                interest_df = self.pytrends.interest_over_time()
                if not interest_df.empty:
                    keyword_interest = self._process_interest_data(interest_df, keyword)
                    interest_data.extend(keyword_interest)
                
                # Fetch related topics if requested
                if self.fetch_related_topics:
                    try:
                        related_topics = self.pytrends.related_topics()
                        if keyword in related_topics:
                            keyword_related = self._process_related_topics(related_topics[keyword], keyword)
                            related_data.extend(keyword_related)
                    except Exception as e:
                        logger.warning(f"Error fetching related topics for {keyword}: {e}")
                
                # Rate limiting - be nice to Google
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching data for keyword {keyword}: {e}")
                continue
        
        return {
            "interest_over_time": interest_data,
            "related_topics": related_data
        }
    
    def _process_interest_data(self, df, keyword: str) -> List[Dict[str, Any]]:
        """Process interest over time DataFrame."""
        data = []
        
        for date_str, row in df.iterrows():
            # Skip the 'isPartial' column
            if date_str == 'isPartial':
                continue
            
            interest_value = row[keyword]
            if pd.isna(interest_value):
                continue
            
            data.append({
                "keyword": keyword,
                "date": date_str.date() if hasattr(date_str, 'date') else date_str,
                "interest": int(interest_value),
                "geo": self.geo,
                "category": self.category,
                "gprop": self.gprop
            })
        
        return data
    
    def _process_related_topics(self, related_dict, keyword: str) -> List[Dict[str, Any]]:
        """Process related topics data."""
        data = []
        
        # Process top related topics
        if 'top' in related_dict and related_dict['top'] is not None:
            for _, row in related_dict['top'].iterrows():
                data.append({
                    "keyword": keyword,
                    "related_topic": row['topic_title'],
                    "type": "top",
                    "value": int(row['value']),
                    "geo": self.geo
                })
        
        # Process rising related topics
        if 'rising' in related_dict and related_dict['rising'] is not None:
            for _, row in related_dict['rising'].iterrows():
                data.append({
                    "keyword": keyword,
                    "related_topic": row['topic_title'],
                    "type": "rising",
                    "value": int(row['value']),
                    "geo": self.geo
                })
        
        return data
    
    def ingest_data(self) -> Dict[str, int]:
        """Ingest Google Trends data into database."""
        data = self.fetch_data()
        
        interest_inserted = 0
        interest_updated = 0
        related_inserted = 0
        related_updated = 0
        
        try:
            with self.db_conn.cursor() as cursor:
                # Ingest interest over time data
                for row in data["interest_over_time"]:
                    result = self._upsert_interest_row(cursor, row)
                    if result == "inserted":
                        interest_inserted += 1
                    else:
                        interest_updated += 1
                
                # Ingest related topics data
                for row in data["related_topics"]:
                    result = self._upsert_related_row(cursor, row)
                    if result == "inserted":
                        related_inserted += 1
                    else:
                        related_updated += 1
            
            self.db_conn.commit()
            logger.info(f"Ingestion complete: {interest_inserted} interest records inserted, {interest_updated} updated")
            logger.info(f"Related topics: {related_inserted} inserted, {related_updated} updated")
            
        except Exception as e:
            self.db_conn.rollback()
            logger.error(f"Error during ingestion: {e}")
            raise
        
        return {
            "interest_inserted": interest_inserted,
            "interest_updated": interest_updated,
            "related_inserted": related_inserted,
            "related_updated": related_updated
        }
    
    def _upsert_interest_row(self, cursor, row: Dict[str, Any]) -> str:
        """Upsert interest over time row."""
        query = """
        INSERT INTO gt_interest_over_time 
        (keyword, date, interest, geo, category, gprop)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (keyword, date, COALESCE(geo, ''), COALESCE(gprop, ''), COALESCE(category, 0))
        DO UPDATE SET
            interest = EXCLUDED.interest,
            created_at = NOW()
        RETURNING (xmax = 0) as is_insert
        """
        
        cursor.execute(query, (
            row["keyword"],
            row["date"],
            row["interest"],
            row["geo"],
            row["category"],
            row["gprop"]
        ))
        
        result = cursor.fetchone()
        return "inserted" if result[0] else "updated"
    
    def _upsert_related_row(self, cursor, row: Dict[str, Any]) -> str:
        """Upsert related topics row."""
        query = """
        INSERT INTO gt_related_topics 
        (keyword, related_topic, type, value, geo)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (keyword, related_topic, type, COALESCE(geo, ''))
        DO UPDATE SET
            value = EXCLUDED.value,
            created_at = NOW()
        RETURNING (xmax = 0) as is_insert
        """
        
        cursor.execute(query, (
            row["keyword"],
            row["related_topic"],
            row["type"],
            row["value"],
            row["geo"]
        ))
        
        result = cursor.fetchone()
        return "inserted" if result[0] else "updated"
    
    def close(self):
        """Close database connection."""
        if self.db_conn and not self.db_conn.closed:
            self.db_conn.close()


# Import pandas for DataFrame handling
try:
    import pandas as pd
except ImportError:
    logger.warning("pandas not available - Google Trends functionality may be limited")
    pd = None
