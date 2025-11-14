#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金融知识图谱系统 - 数据处理模块

负责文本数据的实体识别、关系抽取和事件提取。
采用混合策略：词典匹配 + 大模型分析，确保准确性和效率。
"""

import asyncio
import json
import logging
import re
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import jieba
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI


logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理器 - 核心业务逻辑"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据处理器
        
        Args:
            config: 配置信息，包含LLM配置
        """
        self.config = config
        self.llm_config = config.get('llm', {})
        self.cache_config = config.get('cache', {})
        
        # 初始化大模型
        try:
            self.llm = ChatOpenAI(
                model_name=self.llm_config.get('model_name', 'gpt-3.5-turbo'),
                openai_api_key=self.llm_config.get('api_key'),
                temperature=self.llm_config.get('temperature', 0.1),
                max_tokens=self.llm_config.get('max_tokens', 2000)
            )
        except Exception as e:
            logger.error(f"初始化大模型失败: {e}")
            self.llm = None
        
        # 导入缓存管理器
        from simple_cache import cache_manager
        
        # 金融词典初始化
        self._init_financial_dictionary()
        
        # 正则表达式模式
        self._init_patterns()
    
    def _init_financial_dictionary(self) -> None:
        """初始化金融词典"""
        
        # 公司类型词典
        self.company_types = [
            '有限公司', '股份有限公司', '集团有限公司', '科技公司', '投资公司',
            '银行', '证券公司', '保险公司', '基金公司', '信托公司',
            '股份有限公司', '有限责任公司', '股份公司', '集团公司',
            '科技股份有限公司', '投资集团有限公司', '实业公司'
        ]
        
        # 金融术语词典
        self.financial_terms = [
            '股票', '股价', '市值', '市盈率', '净资产收益率', 'ROE',
            'IPO', '上市', '退市', '停牌', '复牌', '涨停', '跌停',
            '财报', '业绩', '净利润', '营业收入', '利润', '收益',
            '分红', '配股', '增发', '回购', '重组', '并购', '收购',
            '投资', '融资', '基金', '债券', '期货', '外汇', '汇率',
            '央行', '货币政策', '利率', '通胀', 'GDP', '经济',
            '板块', '行业', '概念', '热点', '题材', '龙头', '白马',
            '庄家', '主力', '散户', '资金', '成交量', '成交额'
        ]
        
        # 机构类型词典
        self.institution_types = [
            '银行', '证券公司', '保险公司', '基金公司', '信托公司',
            '投资公司', '基金公司', '私募基金', '公募基金',
            '资产管理公司', '投资银行', '商业银行', '央行'
        ]
        
        # 职位词典
        self.position_words = [
            '董事长', '总裁', '总经理', 'CEO', 'CTO', 'CFO',
            '董事', '监事', '经理', '主管', '总监', '副院长',
            '行长', '副行长', '主任', '副主任', '部长', '副部长'
        ]
        
        # 添加到jieba分词词典
        for word in (self.company_types + self.financial_terms + 
                    self.institution_types + self.position_words):
            jieba.add_word(word)
    
    def _init_patterns(self) -> None:
        """初始化正则表达式模式"""
        
        # 公司名称模式
        self.company_pattern = re.compile(
            r'(?:(.{2,10}?(?:有限公司|股份有限公司|集团有限公司|科技公司|投资公司|'
            r'银行|证券公司|保险公司|基金公司|信托公司|实业公司|'
            r'股份公司|有限责任公司))))',
            re.UNICODE
        )
        
        # 人名模式（简化版）
        self.person_pattern = re.compile(
            r'(?:(?:[张李王刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程柴袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖邹熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段漕钱汤尹黎易常武乔贺赖龚文]))',
            re.UNICODE
        )
        
        # 数字模式（用于股价、百分比等）
        self.number_pattern = re.compile(
            r'(?:\d+(?:\.\d+)?%|\d+(?:,\d{3})*(?:\.\d+)?元|\d+(?:\.\d+)?[万亿]?|\d+(?:\.\d+)?[倍])',
            re.UNICODE
        )
        
        # 时间模式
        self.date_pattern = re.compile(
            r'(?:(\d{4})年(\d{1,2})月(\d{1,2})日|(\d{4})-(\d{1,2})-(\d{1,2})|'
            r'(\d{1,2})月(\d{1,2})日|(\d{1,2})/(\d{1,2}))',
            re.UNICODE
        )
    
    async def process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个文档
        
        Args:
            document: 源文档信息
            
        Returns:
            处理结果
        """
        try:
            text = document.get('content', '')
            title = document.get('title', '')
            
            # 合并标题和正文
            full_text = f"{title}\n\n{text}" if title else text
            
            # 提取实体
            entities = await self.extract_entities(full_text)
            
            # 提取关系
            relations = await self.extract_relations(full_text, entities)
            
            # 提取事件
            events = await self.extract_events(full_text, entities)
            
            result = {
                'document_id': document.get('id'),
                'url': document.get('url'),
                'entities': entities,
                'relations': relations,
                'events': events,
                'processed_at': datetime.now(),
                'status': 'success'
            }
            
            logger.info(f"文档处理完成: {document.get('url')}, "
                       f"实体: {len(entities)}, 关系: {len(relations)}, 事件: {len(events)}")
            
            return result
            
        except Exception as e:
            logger.error(f"文档处理失败: {e}")
            return {
                'document_id': document.get('id'),
                'url': document.get('url'),
                'entities': [],
                'relations': [],
                'events': [],
                'processed_at': datetime.now(),
                'status': 'error',
                'error': str(e)
            }
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        提取实体（公司、人名、金融术语等）
        
        Args:
            text: 输入文本
            
        Returns:
            实体列表
        """
        entities = []
        
        # 1. 基于词典的实体识别
        dict_entities = self._extract_entities_by_dict(text)
        entities.extend(dict_entities)
        
        # 2. 基于大模型的实体识别
        if self.llm:
            llm_entities = await self._extract_entities_by_llm(text)
            entities.extend(llm_entities)
        
        # 3. 去重和过滤
        entities = self._deduplicate_entities(entities)
        
        logger.debug(f"实体提取完成: {len(entities)} 个实体")
        return entities
    
    def _extract_entities_by_dict(self, text: str) -> List[Dict[str, Any]]:
        """基于词典的实体识别"""
        entities = []
        
        # 使用jieba分词
        words = jieba.cut(text)
        words_list = list(words)
        
        # 公司实体识别
        companies = []
        for match in self.company_pattern.finditer(text):
            company_name = match.group(1).strip()
            if 2 <= len(company_name) <= 20:  # 合理长度
                companies.append(company_name)
        
        # 去重
        companies = list(set(companies))
        
        for company in companies:
            entities.append({
                'name': company,
                'type': '公司',
                'confidence': 0.8,
                'source': 'dictionary',
                'context': text[max(0, text.find(company)-50):text.find(company)+50]
            })
        
        # 人名实体识别
        person_names = []
        for match in self.person_pattern.finditer(text):
            name = match.group(1)
            if 2 <= len(name) <= 4:  # 中文姓名长度
                person_names.append(name)
        
        # 去重
        person_names = list(set(person_names))
        
        for name in person_names:
            entities.append({
                'name': name,
                'type': '人名',
                'confidence': 0.7,
                'source': 'dictionary',
                'context': text[max(0, text.find(name)-30):text.find(name)+30]
            })
        
        # 金融术语识别
        terms = []
        for term in self.financial_terms:
            if term in text:
                terms.append(term)
        
        for term in terms:
            entities.append({
                'name': term,
                'type': '金融术语',
                'confidence': 0.9,
                'source': 'dictionary',
                'context': ''
            })
        
        return entities
    
    async def _extract_entities_by_llm(self, text: str) -> List[Dict[str, Any]]:
        """基于大模型的实体识别"""
        try:
            from simple_cache import get_cache
            
            # 生成缓存键
            cache = get_cache()
            cache_key = f"entity_extraction_{hash(text[:500])}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # 构建提示词
            system_prompt = """你是一个金融信息提取专家。请从金融新闻文本中提取实体，包括：
1. 公司名称（上市公司、企业等）
2. 金融机构（银行、证券公司、保险公司等）
3. 人名（高管姓名、分析师姓名等）
4. 重要的金融产品和概念

请以JSON格式返回结果：
{
    "entities": [
        {
            "name": "实体名称",
            "type": "实体类型（公司/金融机构/人名/金融术语）",
            "confidence": 0.0-1.0,
            "context": "上下文信息"
        }
    ]
}"""
            
            user_prompt = f"请提取以下文本中的金融实体：\n\n{text[:2000]}"
            
            # 调用大模型
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析响应
            try:
                result = json.loads(response.content)
                entities = result.get('entities', [])
                
                # 缓存结果
                cache.set(cache_key, json.dumps(entities))
                
                return entities
            except json.JSONDecodeError:
                logger.warning("LLM响应格式错误，无法解析实体")
                return []
                
        except Exception as e:
            logger.error(f"大模型实体识别失败: {e}")
            return []
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重实体列表"""
        seen = set()
        deduplicated = []
        
        for entity in entities:
            key = (entity['name'], entity['type'])
            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)
        
        # 按置信度排序
        deduplicated.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return deduplicated
    
    async def extract_relations(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取实体间关系
        
        Args:
            text: 输入文本
            entities: 实体列表
            
        Returns:
            关系列表
        """
        relations = []
        
        # 1. 基于规则的关系识别
        rule_relations = self._extract_relations_by_rules(text, entities)
        relations.extend(rule_relations)
        
        # 2. 基于大模型的关系识别
        if self.llm and entities:
            llm_relations = await self._extract_relations_by_llm(text, entities)
            relations.extend(llm_relations)
        
        # 3. 去重
        relations = self._deduplicate_relations(relations)
        
        logger.debug(f"关系提取完成: {len(relations)} 个关系")
        return relations
    
    def _extract_relations_by_rules(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于规则的关系识别"""
        relations = []
        
        # 常见的投资关系关键词
        investment_keywords = ['投资', '持股', '控股', '参股', '收购', '并购', '重组']
        
        # 合作关系关键词
        cooperation_keywords = ['合作', '联合', '携手', '达成', '签约', '战略合作']
        
        # 竞争关系关键词
        competition_keywords = ['竞争', '对手', '挑战', '超越', '领先', '落后']
        
        # 寻找包含这些关键词的句子
        sentences = re.split(r'[。！？\n]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 找到句子中的实体
            entities_in_sentence = []
            for entity in entities:
                if entity['name'] in sentence:
                    entities_in_sentence.append(entity)
            
            if len(entities_in_sentence) < 2:
                continue
            
            # 判断关系类型
            relation_type = None
            keyword = None
            
            if any(keyword in sentence for keyword in investment_keywords):
                relation_type = '投资关系'
                keyword = [k for k in investment_keywords if k in sentence][0]
            elif any(keyword in sentence for keyword in cooperation_keywords):
                relation_type = '合作关系'
                keyword = [k for k in cooperation_keywords if k in sentence][0]
            elif any(keyword in sentence for keyword in competition_keywords):
                relation_type = '竞争关系'
                keyword = [k for k in competition_keywords if k in sentence][0]
            
            if relation_type:
                # 创建实体间的关系
                for i in range(len(entities_in_sentence)):
                    for j in range(i + 1, len(entities_in_sentence)):
                        source_entity = entities_in_sentence[i]
                        target_entity = entities_in_sentence[j]
                        
                        relations.append({
                            'source_entity': source_entity['name'],
                            'target_entity': target_entity['name'],
                            'relation_type': relation_type,
                            'confidence': 0.7,
                            'context': sentence,
                            'keyword': keyword,
                            'evidence': sentence
                        })
        
        return relations
    
    async def _extract_relations_by_llm(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于大模型的关系识别"""
        try:
            from simple_cache import get_cache
            
            # 生成缓存键
            cache = get_cache()
            cache_key = f"relation_extraction_{hash(text[:500] + str(len(entities)))}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # 提取前20个最置信的实体
            top_entities = sorted(entities, key=lambda x: x.get('confidence', 0), reverse=True)[:20]
            
            # 构建提示词
            system_prompt = f"""你是一个金融关系提取专家。给定以下实体和文本，识别实体之间的关系。

提取的关系类型包括：
- 投资关系：投资、持股、控股、参股、收购、并购、重组
- 合作关系：合作、联合、携手、达成、签约、战略合作
- 竞争关系：竞争、对手、挑战、超越、领先
- 管理关系：担任、任职、离任、任命
- 财务关系：分红、配股、增发、回购

请以JSON格式返回结果：
{{
    "relations": [
        {{
            "source_entity": "实体1名称",
            "target_entity": "实体2名称",
            "relation_type": "关系类型",
            "confidence": 0.0-1.0,
            "context": "包含关系的上下文",
            "keyword": "关键词"
        }}
    ]
}}"""
            
            # 构建用户提示
            entity_list = "\n".join([f"- {e['name']} ({e['type']})" for e in top_entities])
            user_prompt = f"""已知实体：
{entity_list}

文本内容：
{text[:2000]}

请识别这些实体之间的关系。"""
            
            # 调用大模型
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析响应
            try:
                result = json.loads(response.content)
                relations = result.get('relations', [])
                
                # 缓存结果
                cache.set(cache_key, json.dumps(relations))
                
                return relations
            except json.JSONDecodeError:
                logger.warning("LLM响应格式错误，无法解析关系")
                return []
                
        except Exception as e:
            logger.error(f"大模型关系识别失败: {e}")
            return []
    
    def _deduplicate_relations(self, relations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重关系列表"""
        seen = set()
        deduplicated = []
        
        for relation in relations:
            key = (
                relation['source_entity'],
                relation['target_entity'],
                relation['relation_type']
            )
            if key not in seen:
                seen.add(key)
                deduplicated.append(relation)
        
        # 按置信度排序
        deduplicated.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return deduplicated
    
    async def extract_events(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        提取关键事件
        
        Args:
            text: 输入文本
            entities: 实体列表
            
        Returns:
            事件列表
        """
        events = []
        
        # 1. 基于模板的事件识别
        template_events = self._extract_events_by_template(text, entities)
        events.extend(template_events)
        
        # 2. 基于大模型的事件识别
        if self.llm:
            llm_events = await self._extract_events_by_llm(text, entities)
            events.extend(llm_events)
        
        # 3. 去重
        events = self._deduplicate_events(events)
        
        logger.debug(f"事件提取完成: {len(events)} 个事件")
        return events
    
    def _extract_events_by_template(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于模板的事件识别"""
        events = []
        
        # 事件模板
        event_patterns = [
            {
                'type': '公司公告',
                'patterns': [
                    r'(.*?)宣布(.*?)',
                    r'(.*?)发布(.*?)',
                    r'(.*?)公告(.*?)',
                ]
            },
            {
                'type': '投资事件',
                'patterns': [
                    r'(.*?)投资(.*?)',
                    r'(.*?)获得(.*?)投资',
                    r'(.*?)完成(.*?)轮融资',
                ]
            },
            {
                'type': '并购事件',
                'patterns': [
                    r'(.*?)收购(.*?)',
                    r'(.*?)并购(.*?)',
                    r'(.*?)被(.*?)收购',
                ]
            },
            {
                'type': '上市事件',
                'patterns': [
                    r'(.*?)上市',
                    r'(.*?)IPO',
                    r'(.*?)登陆资本市场',
                ]
            }
        ]
        
        for template in event_patterns:
            event_type = template['type']
            patterns = template['patterns']
            
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    # 找到相关的实体
                    related_entities = []
                    for entity in entities:
                        if (entity['name'] in match.group(0) or 
                            any(e_name in match.group(0) for e_name in [entity['name']])):
                            related_entities.append(entity['name'])
                    
                    if related_entities:
                        events.append({
                            'title': match.group(0).strip(),
                            'event_type': event_type,
                            'entities': related_entities[:5],  # 最多5个相关实体
                            'description': match.group(0).strip(),
                            'impact_level': '中等',
                            'confidence': 0.7,
                            'source': 'template'
                        })
        
        return events
    
    async def _extract_events_by_llm(self, text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于大模型的事件识别"""
        try:
            from simple_cache import get_cache
            
            # 生成缓存键
            cache = get_cache()
            cache_key = f"event_extraction_{hash(text[:500])}"
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # 构建提示词
            system_prompt = """你是一个金融事件提取专家。从金融新闻文本中提取重要的金融事件。

事件类型包括：
- 公司公告：财报发布、重大决策、战略调整
- 投资事件：融资、投资、收购
- 市场事件：股价变动、政策发布
- 监管事件：处罚、调查、许可
- 业绩事件：业绩预告、业绩发布

请以JSON格式返回结果：
{
    "events": [
        {
            "title": "事件标题",
            "event_type": "事件类型",
            "entities": ["相关实体1", "相关实体2"],
            "description": "事件描述",
            "impact_level": "影响级别(高/中/低)",
            "confidence": 0.0-1.0
        }
    ]
}"""
            
            user_prompt = f"请提取以下文本中的金融事件：\n\n{text[:2000]}"
            
            # 调用大模型
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 解析响应
            try:
                result = json.loads(response.content)
                events = result.get('events', [])
                
                # 缓存结果
                cache.set(cache_key, json.dumps(events))
                
                return events
            except json.JSONDecodeError:
                logger.warning("LLM响应格式错误，无法解析事件")
                return []
                
        except Exception as e:
            logger.error(f"大模型事件识别失败: {e}")
            return []
    
    def _deduplicate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重事件列表"""
        seen = set()
        deduplicated = []
        
        for event in events:
            key = (event['title'], event['event_type'])
            if key not in seen:
                seen.add(key)
                deduplicated.append(event)
        
        # 按置信度排序
        deduplicated.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return deduplicated


# 数据处理器工厂函数
def create_data_processor(config: Dict[str, Any]) -> DataProcessor:
    """创建数据处理器"""
    return DataProcessor(config)