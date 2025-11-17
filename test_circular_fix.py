from datetime import datetime

# Import DataServices first
data_services = None
try:
    from kg.services.data_services import DataServices
    data_services = DataServices()
    print("✅ Successfully imported DataServices")
except Exception as e:
    print(f"❌ Failed to import DataServices: {e}")
    import traceback
    traceback.print_exc()

# Now import NewsProcessingService
news_processing_service = None
if data_services:
    try:
        from kg.services.news_processing_service import NewsProcessingService
        news_processing_service = NewsProcessingService(data_services)
        print("✅ Successfully imported NewsProcessingService")
    except Exception as e:
        print(f"❌ Failed to import NewsProcessingService: {e}")
        import traceback
        traceback.print_exc()

# Test if everything works
if news_processing_service:
    print("\n✅ All services imported successfully!")
    
    # Sample news data
    title = "Apple Unveils New iPhone 15 Series"
    content = "Apple today unveiled its highly anticipated iPhone 15 series at a special event held in Cupertino, California."
    source = "TechCrunch"
    
    try:
        # Process news
        result = news_processing_service.process_and_store_news(title, content, source)
        print(f"\n✅ News processed successfully!")
        print(f"   News ID: {result['news_id']}")
        print(f"   Summary: {result['summary']}")
        print(f"   Entities: {len(result['entities'])}")
        print(f"   Relations: {len(result['relations'])}")
    except Exception as e:
        print(f"❌ Error processing news: {e}")
        import traceback
        traceback.print_exc()
