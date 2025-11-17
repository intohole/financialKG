#!/usr/bin/env python3
"""Async test script for NewsProcessingService"""

import sys
import asyncio
from datetime import datetime
from kg.services.news_processing_service import NewsProcessingService
from kg.services.data_services import KnowledgeGraphService
from kg.database.connection import db_session

async def test_news_processing():
    """Test the news processing service with async calls"""
    print("Initializing services...")
    
    # Get a database session using the context manager
    async with db_session() as session:
        # Create the services with the session
        knowledge_graph_service = KnowledgeGraphService(session=session)
        news_processing_service = NewsProcessingService(
            knowledge_graph_service
        )
        
        print("Services initialized successfully.")
        
        # Test data with unique URL
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        news_data = {
            "title": "Test News Article",
            "content": "This is a test news article about AI and machine learning technologies.",
            "source_url": f"http://example.com/test-news-{timestamp}",
            "publish_date": datetime.fromisoformat("2023-10-01T12:00:00Z"),
            "source": "test_source"
        }
        
        print(f"Testing with news data: {news_data}")
        
        try:
            # Call the async method
            news_result = await news_processing_service.process_and_store_news(news_data)
            print(f"Processing completed successfully: {news_result}")
            return True
        except Exception as e:
            print(f"Error during processing: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("Starting async test for NewsProcessingService...")
    
    # Run the async test
    success = asyncio.run(test_news_processing())
    
    if success:
        print("✅ Async test passed!")
        sys.exit(0)
    else:
        print("❌ Async test failed!")
        sys.exit(1)