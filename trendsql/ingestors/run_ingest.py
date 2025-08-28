#!/usr/bin/env python3
"""
TrendSQL Data Ingestion CLI

Usage:
    python -m ingestors.run_ingest exploding --config config/exploding.yml
    python -m ingestors.run_ingest google --config config/google_trends.yml
"""

import argparse
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from connectors.exploding import ExplodingTopicsConnector
from connectors.google_trends import GoogleTrendsConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        logger.info(f"Loaded config from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file: {e}")
        sys.exit(1)


def run_exploding_ingest(config: Dict[str, Any]) -> bool:
    """Run exploding topics ingestion."""
    try:
        logger.info("Starting exploding topics ingestion...")
        connector = ExplodingTopicsConnector(config)
        
        result = connector.ingest_data()
        
        logger.info(f"Exploding topics ingestion complete:")
        logger.info(f"  - Inserted: {result['inserted']}")
        logger.info(f"  - Updated: {result['updated']}")
        
        connector.close()
        return True
        
    except Exception as e:
        logger.error(f"Error during exploding topics ingestion: {e}")
        return False


def run_google_trends_ingest(config: Dict[str, Any]) -> bool:
    """Run Google Trends ingestion."""
    try:
        logger.info("Starting Google Trends ingestion...")
        connector = GoogleTrendsConnector(config)
        
        result = connector.ingest_data()
        
        logger.info(f"Google Trends ingestion complete:")
        logger.info(f"  - Interest records inserted: {result['interest_inserted']}")
        logger.info(f"  - Interest records updated: {result['interest_updated']}")
        logger.info(f"  - Related topics inserted: {result['related_inserted']}")
        logger.info(f"  - Related topics updated: {result['related_updated']}")
        
        connector.close()
        return True
        
    except Exception as e:
        logger.error(f"Error during Google Trends ingestion: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TrendSQL Data Ingestion CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ingestors.run_ingest exploding --config config/exploding.yml
  python -m ingestors.run_ingest google --config config/google_trends.yml
        """
    )
    
    parser.add_argument(
        "provider",
        choices=["exploding", "google"],
        help="Data provider to ingest from"
    )
    
    parser.add_argument(
        "--config",
        required=True,
        help="Path to configuration YAML file"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = load_config(args.config)
    
    # Run ingestion based on provider
    success = False
    if args.provider == "exploding":
        success = run_exploding_ingest(config)
    elif args.provider == "google":
        success = run_google_trends_ingest(config)
    else:
        logger.error(f"Unknown provider: {args.provider}")
        sys.exit(1)
    
    # Exit with appropriate code
    if success:
        logger.info("Ingestion completed successfully")
        sys.exit(0)
    else:
        logger.error("Ingestion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
