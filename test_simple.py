from datetime import datetime

# Import the services directly to avoid circular imports
from kg.services.llm_service import LLMService

# Test just the LLM service first to make sure it works
llm_service = LLMService()

# Sample news content
content = "Apple today unveiled its highly anticipated iPhone 15 series at a special event held in Cupertino, California."

# Test entity extraction
print("Testing LLMService extract_entities...")
entities = llm_service.extract_entities(content)
print(f"Entities extracted: {entities}")

# Test relation extraction
print("Testing LLMService extract_relations...")
relations = llm_service.extract_relations(content, entities['entities'])
print(f"Relations extracted: {relations}")

# Test news summarization
print("Testing LLMService generate_news_summary...")
summary = llm_service.generate_news_summary(content)
print(f"Summary generated: {summary}")