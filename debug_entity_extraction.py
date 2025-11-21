#!/usr/bin/env python3

import asyncio
import logging
from app.llm.prompt_manager import PromptManager
from app.llm.llm_service import LLMService

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_entity_extraction():
    prompt_manager = PromptManager()
    llm_service = LLMService()
    
    # Test text
    text = "腾讯公司投资了京东集团，双方建立了战略合作关系"
    
    # Custom entity and relation types
    entity_types_info = "公司, 人物, 品牌"
    relation_types_info = "投资, 合作, 竞争"
    
    try:
        # Get the prompt template - use knowledge_graph_extraction for custom types
        prompt_template = prompt_manager.get_prompt('knowledge_graph_extraction')
        
        # Format the prompt
        formatted_prompt = prompt_template.format(
            text=text,
            entity_types=entity_types_info,
            relation_types=relation_types_info
        )
        
        print("=== PROMPT ===")
        print(formatted_prompt)
        print("=== END PROMPT ===")
        
        # Get the response
        response_obj = await llm_service.async_generate(formatted_prompt)
        response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
        
        print("=== RAW RESPONSE ===")
        print(repr(response))
        print("=== END RAW RESPONSE ===")
        
        # Write to file for detailed inspection
        with open('debug_entity_response.txt', 'w', encoding='utf-8') as f:
            f.write("=== PROMPT ===\n")
            f.write(formatted_prompt)
            f.write("\n=== END PROMPT ===\n\n")
            f.write("=== RAW RESPONSE ===\n")
            f.write(response)
            f.write("\n=== END RAW RESPONSE ===\n")
        print("Response written to debug_entity_response.txt")
        
    except Exception as e:
        logger.error(f"Debug failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(debug_entity_extraction())