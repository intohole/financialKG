from datetime import datetime
from kg.services.data_services import KnowledgeGraphService
from kg.services.news_processing_service import NewsProcessingService

# Initialize services
kg_service = KnowledgeGraphService()
news_processing_service = NewsProcessingService(kg_service)

# Sample news data
title = "Apple Unveils New iPhone 15 Series"
content = "Apple today unveiled its highly anticipated iPhone 15 series at a special event held in Cupertino, California. The new lineup includes four models: iPhone 15, iPhone 15 Plus, iPhone 15 Pro, and iPhone 15 Pro Max. Key features include USB-C connectivity, improved cameras, and faster A17 Pro chips for the Pro models. Tim Cook, Apple's CEO, emphasized the company's commitment to sustainability with all new iPhones using 100% recycled rare earth elements in their magnets. The iPhone 15 series is set to go on sale starting September 22, with pre-orders beginning on September 15."
source = "TechCrunch"
publish_time = datetime.now()
author = "John Doe"

print("Testing NewsProcessingService...")
print(f"News Title: {title}")
print(f"Source: {source}")
print(f"Publish Time: {publish_time}")
print(f"Author: {author}")
print("\n" + "="*50 + "\n")

# Process and store news
result = news_processing_service.process_and_store_news(
    title=title,
    content=content,
    source=source,
    publish_time=publish_time,
    author=author
)

print("Processing Result:")
print(f"News ID: {result['news_id']}")
print(f"Summary: {result['summary']}")
print(f"Entities Extracted: {len(result['entities'])}")
for entity in result['entities']:
    print(f"  - {entity.name} ({entity.entity_type})")
print(f"Relations Extracted: {len(result['relations'])}")
for relation in result['relations']:
    # Get entity names for better display
    source_entity = [e for e in result['entities'] if e.id == relation.source_entity_id][0]
    target_entity = [e for e in result['entities'] if e.id == relation.target_entity_id][0]
    print(f"  - {source_entity.name} {relation.relation_type} {target_entity.name}")

print("\n" + "="*50 + "\n")
print("Test completed successfully!")
