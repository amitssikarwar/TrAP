import pytest
from unittest.mock import Mock, patch, MagicMock
from connectors.exploding import ExplodingTopicsConnector
from connectors.google_trends import GoogleTrendsConnector


class TestExplodingTopicsConnector:
    def test_init(self):
        """Test connector initialization."""
        config = {
            "provider": "exploding_topics",
            "fetch_mode": "csv",
            "csv_path": "./test.csv",
            "filters": {"min_growth_score": 50},
            "upsert": True
        }
        
        with patch('connectors.exploding.psycopg.connect'):
            connector = ExplodingTopicsConnector(config)
            
            assert connector.provider == "exploding_topics"
            assert connector.fetch_mode == "csv"
            assert connector.csv_path == "./test.csv"
            assert connector.filters["min_growth_score"] == 50
            assert connector.upsert == True
    
    def test_fetch_from_csv_missing_file(self):
        """Test CSV fetching when file doesn't exist."""
        config = {"csv_path": "./nonexistent.csv"}
        
        with patch('connectors.exploding.psycopg.connect'):
            connector = ExplodingTopicsConnector(config)
            data = connector._fetch_from_csv()
            
            # Should return sample data when file doesn't exist
            assert len(data) > 0
            assert all("topic" in row for row in data)
    
    def test_parse_date(self):
        """Test date parsing functionality."""
        config = {}
        with patch('connectors.exploding.psycopg.connect'):
            connector = ExplodingTopicsConnector(config)
            
            # Test valid dates
            assert connector._parse_date("2024-01-15") == "2024-01-15"
            assert connector._parse_date("01/15/2024") == "2024-01-15"
            
            # Test invalid dates
            assert connector._parse_date("invalid") is None
            assert connector._parse_date("") is None
    
    def test_parse_numeric(self):
        """Test numeric parsing functionality."""
        config = {}
        with patch('connectors.exploding.psycopg.connect'):
            connector = ExplodingTopicsConnector(config)
            
            # Test valid numbers
            assert connector._parse_numeric("85.5") == 85.5
            assert connector._parse_numeric("100") == 100.0
            
            # Test invalid numbers
            assert connector._parse_numeric("invalid") is None
            assert connector._parse_numeric("") is None
    
    def test_apply_filters(self):
        """Test filter application."""
        config = {
            "filters": {
                "min_growth_score": 80,
                "regions": ["US"],
                "categories": ["Technology"]
            }
        }
        
        with patch('connectors.exploding.psycopg.connect'):
            connector = ExplodingTopicsConnector(config)
            
            # Test passing row
            passing_row = {
                "growth_score": 85.5,
                "region": "US",
                "category": "Technology"
            }
            assert connector._apply_filters(passing_row) == True
            
            # Test failing rows
            failing_growth = {
                "growth_score": 75.0,
                "region": "US",
                "category": "Technology"
            }
            assert connector._apply_filters(failing_growth) == False
            
            failing_region = {
                "growth_score": 85.5,
                "region": "IN",
                "category": "Technology"
            }
            assert connector._apply_filters(failing_region) == False
    
    def test_map_csv_row(self):
        """Test CSV row mapping."""
        config = {}
        with patch('connectors.exploding.psycopg.connect'):
            connector = ExplodingTopicsConnector(config)
            
            csv_row = {
                "topic": "AI-powered pet care",
                "category": "Technology",
                "growth_score": "85.5",
                "popularity_score": "92.3",
                "region": "US",
                "first_seen_date": "2024-01-15",
                "url": "https://example.com"
            }
            
            mapped = connector._map_csv_row(csv_row)
            
            assert mapped["topic"] == "AI-powered pet care"
            assert mapped["category"] == "Technology"
            assert mapped["growth_score"] == 85.5
            assert mapped["popularity_score"] == 92.3
            assert mapped["region"] == "US"
            assert mapped["url"] == "https://example.com"


class TestGoogleTrendsConnector:
    def test_init(self):
        """Test connector initialization."""
        config = {
            "keywords": ["AI", "Machine Learning"],
            "timeframe": "today 3-m",
            "geo": "US",
            "category": 0,
            "gprop": "",
            "tz_offset_minutes": 0,
            "fetch_related_topics": True
        }
        
        with patch('connectors.google_trends.psycopg.connect'):
            connector = GoogleTrendsConnector(config)
            
            assert connector.keywords == ["AI", "Machine Learning"]
            assert connector.timeframe == "today 3-m"
            assert connector.geo == "US"
            assert connector.category == 0
            assert connector.fetch_related_topics == True
    
    def test_fetch_data_empty_keywords(self):
        """Test fetching data with empty keywords."""
        config = {"keywords": []}
        
        with patch('connectors.google_trends.psycopg.connect'):
            connector = GoogleTrendsConnector(config)
            data = connector.fetch_data()
            
            assert data["interest_over_time"] == []
            assert data["related_topics"] == []
    
    @patch('connectors.google_trends.pd')
    def test_process_interest_data(self, mock_pd):
        """Test interest data processing."""
        config = {}
        with patch('connectors.google_trends.psycopg.connect'):
            connector = GoogleTrendsConnector(config)
            
            # Mock DataFrame
            mock_df = Mock()
            mock_df.iterrows.return_value = [
                ("2024-01-15", {"AI": 85}),
                ("2024-01-16", {"AI": 87}),
            ]
            
            data = connector._process_interest_data(mock_df, "AI")
            
            assert len(data) == 2
            assert data[0]["keyword"] == "AI"
            assert data[0]["interest"] == 85
            assert data[1]["interest"] == 87
    
    def test_process_related_topics(self):
        """Test related topics processing."""
        config = {}
        with patch('connectors.google_trends.psycopg.connect'):
            connector = GoogleTrendsConnector(config)
            
            # Mock related topics data
            related_dict = {
                'top': Mock(),
                'rising': Mock()
            }
            
            # Mock top topics DataFrame
            top_df = Mock()
            top_df.iterrows.return_value = [
                (0, {"topic_title": "Machine Learning", "value": 95}),
                (1, {"topic_title": "Deep Learning", "value": 85}),
            ]
            related_dict['top'] = top_df
            
            # Mock rising topics DataFrame
            rising_df = Mock()
            rising_df.iterrows.return_value = [
                (0, {"topic_title": "ChatGPT", "value": 100}),
            ]
            related_dict['rising'] = rising_df
            
            data = connector._process_related_topics(related_dict, "AI")
            
            assert len(data) == 3
            assert any(topic["type"] == "top" and topic["related_topic"] == "Machine Learning" for topic in data)
            assert any(topic["type"] == "rising" and topic["related_topic"] == "ChatGPT" for topic in data)


class TestIngestionIntegration:
    @patch('connectors.exploding.psycopg.connect')
    def test_exploding_ingestion_flow(self, mock_connect):
        """Test complete exploding topics ingestion flow."""
        config = {
            "fetch_mode": "csv",
            "csv_path": "./nonexistent.csv",  # Will use sample data
            "upsert": True
        }
        
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = ExplodingTopicsConnector(config)
        result = connector.ingest_data()
        
        # Verify result structure
        assert "inserted" in result
        assert "updated" in result
        assert result["inserted"] >= 0
        assert result["updated"] >= 0
        
        # Verify database calls were made
        assert mock_cursor.execute.called
        assert mock_conn.commit.called
    
    @patch('connectors.google_trends.psycopg.connect')
    @patch('connectors.google_trends.TrendReq')
    def test_google_trends_ingestion_flow(self, mock_trendreq, mock_connect):
        """Test complete Google Trends ingestion flow."""
        config = {
            "keywords": ["AI"],
            "timeframe": "today 3-m",
            "geo": "US",
            "fetch_related_topics": True
        }
        
        # Mock pytrends
        mock_pytrends = Mock()
        mock_trendreq.return_value = mock_pytrends
        
        # Mock interest over time data
        mock_interest_df = Mock()
        mock_interest_df.empty = False
        mock_interest_df.iterrows.return_value = [
            ("2024-01-15", {"AI": 85}),
        ]
        mock_pytrends.interest_over_time.return_value = mock_interest_df
        
        # Mock related topics data
        mock_pytrends.related_topics.return_value = {"AI": {}}
        
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        connector = GoogleTrendsConnector(config)
        result = connector.ingest_data()
        
        # Verify result structure
        assert "interest_inserted" in result
        assert "interest_updated" in result
        assert "related_inserted" in result
        assert "related_updated" in result
        
        # Verify database calls were made
        assert mock_cursor.execute.called
        assert mock_conn.commit.called
