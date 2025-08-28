#!/usr/bin/env python3
"""
Simple test script to verify TrendsQL setup
"""

import os
import sys

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test app imports
        from app import models, sql_safety, schema_introspect, llm_sql, formatters, pagination, hints
        print("✅ App modules imported successfully")
        
        # Test connector imports
        from connectors import exploding, google_trends
        print("✅ Connector modules imported successfully")
        
        # Test ingestor imports
        from ingestors import run_ingest
        print("✅ Ingestor modules imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config_files():
    """Test that config files exist."""
    print("\nTesting config files...")
    
    config_files = [
        "config/exploding.yml",
        "config/google_trends.yml",
        "env.example",
        "requirements.txt"
    ]
    
    all_exist = True
    for file_path in config_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_database_files():
    """Test that database files exist."""
    print("\nTesting database files...")
    
    db_files = [
        "db/schema.sql",
        "db/seed.sql"
    ]
    
    all_exist = True
    for file_path in db_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_docker_files():
    """Test that Docker files exist."""
    print("\nTesting Docker files...")
    
    docker_files = [
        "Dockerfile",
        "docker-compose.yml",
        "Makefile"
    ]
    
    all_exist = True
    for file_path in docker_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("TrendsQL Setup Verification")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config_files,
        test_database_files,
        test_docker_files
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 40)
    print("Summary:")
    
    if all(results):
        print("✅ All tests passed! TrendsQL is ready to use.")
        print("\nNext steps:")
        print("1. Copy env.example to .env and add your OpenAI API key")
        print("2. Run 'make setup' to install dependencies and start database")
        print("3. Run 'make run' to start the application")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
