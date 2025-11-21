#!/usr/bin/env python3

import asyncio
import logging
from app.core.content_processor import ContentProcessor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_enhanced():
    processor = ContentProcessor()
    
    # Test text
    text = "苹果公司发布了新的iPhone产品，采用了最新的A17芯片技术。"
    
    # Complex category config
    complex_config = {
        'custom_tech': {
            'name': '自定义科技',
            'description': '用户自定义的科技类别，包含特定的技术产品'
        },
        'financial': {
            'name': '金融财经',
            'description': '金融、财经、股票、证券等相关内容'
        }
    }
    
    try:
        # Get the raw response first
        from app.llm.prompt_manager import PromptManager
        prompt_manager = PromptManager()
        prompt_template = prompt_manager.get_prompt('content_classification_enhanced')
        
        category_info_parts = []
        for category_key, category_data in complex_config.items():
            name = category_data.get('name', category_key)
            description = category_data.get('description', '')
            category_info_parts.append(f"{category_key}({name}): {description}")
        category_info = "; ".join(category_info_parts)
        
        formatted_prompt = prompt_template.format(text=text, categories=category_info)
        print("=== PROMPT ===")
        print(formatted_prompt)
        print("=== END PROMPT ===")
        
        # Get raw response
        from app.llm.llm_service import LLMService
        llm_service = LLMService()
        response_obj = await llm_service.async_generate(formatted_prompt)
        response = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)
        
        print("=== RAW RESPONSE ===")
        print(repr(response))  # Use repr to see exact format
        print("=== END RAW RESPONSE ===")
        
        # Write to file for detailed inspection
        with open('debug_response.txt', 'w', encoding='utf-8') as f:
            f.write("=== PROMPT ===\n")
            f.write(formatted_prompt)
            f.write("\n=== END PROMPT ===\n\n")
            f.write("=== RAW RESPONSE ===\n")
            f.write(response)
            f.write("\n=== END RAW RESPONSE ===\n")
        print("Response written to debug_response.txt")
        
        # Try to extract JSON
        processor = ContentProcessor()
        data = processor.extract_json_from_response(response)
        print("=== EXTRACTED JSON ===")
        print(data)
        print("=== END EXTRACTED JSON ===")
        
    except Exception as e:
        logger.error(f"Debug failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(debug_enhanced())