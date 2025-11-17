from kg.services.llm.langchain_config import LangChainConfig
from kg.services.llm_service import LLMService

# Test LangChainConfig
print("Testing LangChainConfig...")
config = LangChainConfig()
print(f"Model: {config.model}")
print(f"API Key: {'Set' if config.api_key else 'Not set'}")
print(f"Base URL: {config.base_url}")
print(f"Temperature: {config.temperature}")
print(f"Max Tokens: {config.max_tokens}")

# Test LLMService initialization
print("\nTesting LLMService initialization...")
service = LLMService()
print("LLMService initialized successfully")
print("All services loaded:")
print(f"- Entity Extraction: {service.entity_extraction}")
print(f"- Relation Extraction: {service.relation_extraction}")
print(f"- News Summarization: {service.news_summarization}")
print(f"- Entity Aggregation: {service.entity_aggregation}")
print(f"- Relation Aggregation: {service.relation_aggregation}")

print("\nTest completed successfully")
