#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金融知识图谱系统 - 数据库管理模块

负责数据库的初始化、连接管理、CRUD操作等核心功能。
遵循大厂数据库设计规范，确保数据一致性和性能。
"""

import aiosqlite
import logging
import sqlite3
from typing import List, Dict, Optional, Any
from datetime import datetime
import os


logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls, db_path: str = "data/knowledge_graph.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = "data/knowledge_graph.db"):
        if self._initialized:
            return
            
        self.db_path = db_path
        self._initialized = True
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self.init_database()
    
    async def init_database(self) -> None:
        """初始化数据库表结构"""
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)
            logger.info(f"数据库初始化完成: {self.db_path}")
    
    async def _create_tables(self, db: aiosqlite.Connection) -> None:
        """创建所有数据表"""
        
        # 实体表 - 存储识别的实体信息
        await db.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                industry TEXT,
                region TEXT,
                description TEXT,
                confidence REAL DEFAULT 0.0,
                source TEXT,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, type)
            )
        """)
        
        # 关系表 - 存储实体间关系
        await db.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_entity TEXT NOT NULL,
                target_entity TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                context TEXT,
                keyword TEXT,
                evidence TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_entity, target_entity, relation_type)
            )
        """)
        
        # 事件表 - 存储关键事件信息
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                event_type TEXT NOT NULL,
                entities TEXT,  -- JSON格式存储相关实体列表
                description TEXT,
                impact_level TEXT,
                source_url TEXT,
                published_date TIMESTAMP,
                confidence REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 源文档表 - 存储原始文档信息
        await db.execute("""
            CREATE TABLE IF NOT EXISTS source_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                content TEXT,
                content_hash TEXT,
                fetch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed BOOLEAN DEFAULT FALSE,
                processing_time REAL
            )
        """)
        
        # 缓存表 - 存储大模型API调用结果缓存
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        # 创建索引以提升查询性能
        await self._create_indexes(db)
        
        await db.commit()
    
    async def _create_indexes(self, db: aiosqlite.Connection) -> None:
        """创建性能索引"""
        
        # 实体表索引
        await db.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_entities_industry ON entities(industry)")
        
        # 关系表索引
        await db.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_entity)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_entity)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type)")
        
        # 事件表索引
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events(published_date)")
        
        # 源文档表索引
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_url ON source_documents(url)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_documents_processed ON source_documents(processed)")
        
        # 缓存表索引
        await db.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
    
    # =================== 实体管理 ===================
    
    async def insert_entity(self, entity: Dict[str, Any]) -> int:
        """插入实体记录"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT OR REPLACE INTO entities 
                    (name, type, industry, region, description, confidence, source, context, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity['name'],
                    entity['type'],
                    entity.get('industry'),
                    entity.get('region'),
                    entity.get('description'),
                    entity.get('confidence', 0.0),
                    entity.get('source'),
                    entity.get('context'),
                    datetime.now()
                ))
                await db.commit()
                entity_id = cursor.lastrowid
                logger.debug(f"实体插入成功: {entity['name']} (ID: {entity_id})")
                return entity_id
        except Exception as e:
            logger.error(f"插入实体失败: {e}")
            raise
    
    async def get_entities(self, entity_type: Optional[str] = None, 
                          industry: Optional[str] = None, 
                          limit: int = 100) -> List[Dict]:
        """获取实体列表"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                query = "SELECT * FROM entities WHERE 1=1"
                params = []
                
                if entity_type:
                    query += " AND type = ?"
                    params.append(entity_type)
                
                if industry:
                    query += " AND industry = ?"
                    params.append(industry)
                
                query += " ORDER BY confidence DESC, created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取实体列表失败: {e}")
            return []
    
    async def search_entities(self, keyword: str) -> List[Dict]:
        """搜索实体"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                cursor = await db.execute("""
                    SELECT * FROM entities 
                    WHERE name LIKE ? OR description LIKE ?
                    ORDER BY confidence DESC
                """, (f"%{keyword}%", f"%{keyword}%"))
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"搜索实体失败: {e}")
            return []
    
    # =================== 关系管理 ===================
    
    async def insert_relation(self, relation: Dict[str, Any]) -> int:
        """插入关系记录"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT OR REPLACE INTO relations 
                    (source_entity, target_entity, relation_type, confidence, context, keyword, evidence, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    relation['source_entity'],
                    relation['target_entity'],
                    relation['relation_type'],
                    relation.get('confidence', 0.0),
                    relation.get('context'),
                    relation.get('keyword'),
                    relation.get('evidence'),
                    datetime.now()
                ))
                await db.commit()
                relation_id = cursor.lastrowid
                logger.debug(f"关系插入成功: {relation['source_entity']} -> {relation['target_entity']} (ID: {relation_id})")
                return relation_id
        except Exception as e:
            logger.error(f"插入关系失败: {e}")
            raise
    
    async def get_relations(self, entity_name: Optional[str] = None,
                           relation_type: Optional[str] = None,
                           limit: int = 100) -> List[Dict]:
        """获取关系列表"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                query = "SELECT * FROM relations WHERE 1=1"
                params = []
                
                if entity_name:
                    query += " AND (source_entity = ? OR target_entity = ?)"
                    params.extend([entity_name, entity_name])
                
                if relation_type:
                    query += " AND relation_type = ?"
                    params.append(relation_type)
                
                query += " ORDER BY confidence DESC, created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取关系列表失败: {e}")
            return []
    
    # =================== 事件管理 ===================
    
    async def insert_event(self, event: Dict[str, Any]) -> int:
        """插入事件记录"""
        try:
            import json
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO events 
                    (title, event_type, entities, description, impact_level, 
                     source_url, published_date, confidence, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event['title'],
                    event['event_type'],
                    json.dumps(event.get('entities', [])),
                    event.get('description'),
                    event.get('impact_level'),
                    event.get('source_url'),
                    event.get('published_date'),
                    event.get('confidence', 0.0),
                    datetime.now()
                ))
                await db.commit()
                event_id = cursor.lastrowid
                logger.debug(f"事件插入成功: {event['title']} (ID: {event_id})")
                return event_id
        except Exception as e:
            logger.error(f"插入事件失败: {e}")
            raise
    
    async def get_events(self, event_type: Optional[str] = None,
                        limit: int = 50) -> List[Dict]:
        """获取事件列表"""
        try:
            import json
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                query = "SELECT * FROM events WHERE 1=1"
                params = []
                
                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type)
                
                query += " ORDER BY published_date DESC, created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                # 解析JSON字段
                result = []
                for row in rows:
                    row_dict = dict(row)
                    try:
                        row_dict['entities'] = json.loads(row_dict['entities'] or '[]')
                    except:
                        row_dict['entities'] = []
                    result.append(row_dict)
                
                return result
        except Exception as e:
            logger.error(f"获取事件列表失败: {e}")
            return []
    
    # =================== 源文档管理 ===================
    
    async def insert_source_document(self, doc: Dict[str, Any]) -> int:
        """插入源文档记录"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT OR REPLACE INTO source_documents 
                    (url, title, content, content_hash, fetch_time, processed, processing_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc['url'],
                    doc.get('title'),
                    doc.get('content'),
                    doc.get('content_hash'),
                    doc.get('fetch_time'),
                    doc.get('processed', False),
                    doc.get('processing_time')
                ))
                await db.commit()
                doc_id = cursor.lastrowid
                logger.debug(f"源文档插入成功: {doc['url']} (ID: {doc_id})")
                return doc_id
        except Exception as e:
            logger.error(f"插入源文档失败: {e}")
            raise
    
    async def get_unprocessed_documents(self, limit: int = 10) -> List[Dict]:
        """获取未处理的文档"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                cursor = await db.execute("""
                    SELECT * FROM source_documents 
                    WHERE processed = FALSE 
                    ORDER BY fetch_time ASC 
                    LIMIT ?
                """, (limit,))
                
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取未处理文档失败: {e}")
            return []
    
    async def mark_document_processed(self, doc_id: int, processing_time: float) -> None:
        """标记文档为已处理"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE source_documents 
                    SET processed = TRUE, processing_time = ?
                    WHERE id = ?
                """, (processing_time, doc_id))
                await db.commit()
        except Exception as e:
            logger.error(f"标记文档处理状态失败: {e}")
            raise
    
    # =================== 统计查询 ===================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                stats = {}
                
                # 实体统计
                cursor = await db.execute("SELECT COUNT(*) as count FROM entities")
                stats['entities_count'] = (await cursor.fetchone())['count']
                
                # 关系统计
                cursor = await db.execute("SELECT COUNT(*) as count FROM relations")
                stats['relations_count'] = (await cursor.fetchone())['count']
                
                # 事件统计
                cursor = await db.execute("SELECT COUNT(*) as count FROM events")
                stats['events_count'] = (await cursor.fetchone())['count']
                
                # 源文档统计
                cursor = await db.execute("SELECT COUNT(*) as count FROM source_documents")
                stats['documents_count'] = (await cursor.fetchone())['count']
                
                cursor = await db.execute("SELECT COUNT(*) as count FROM source_documents WHERE processed = TRUE")
                stats['processed_documents_count'] = (await cursor.fetchone())['count']
                
                # 实体类型分布
                cursor = await db.execute("""
                    SELECT type, COUNT(*) as count 
                    FROM entities 
                    GROUP BY type 
                    ORDER BY count DESC
                """)
                stats['entity_types'] = [dict(row) for row in await cursor.fetchall()]
                
                # 关系类型分布
                cursor = await db.execute("""
                    SELECT relation_type, COUNT(*) as count 
                    FROM relations 
                    GROUP BY relation_type 
                    ORDER BY count DESC
                """)
                stats['relation_types'] = [dict(row) for row in await cursor.fetchall()]
                
                return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    # =================== 缓存管理 ===================
    
    async def set_cache(self, key: str, value: str, ttl: int = 3600) -> None:
        """设置缓存"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                expires_at = datetime.fromtimestamp(datetime.now().timestamp() + ttl)
                await db.execute("""
                    INSERT OR REPLACE INTO cache (key, value, expires_at)
                    VALUES (?, ?, ?)
                """, (key, value, expires_at))
                await db.commit()
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
    
    async def get_cache(self, key: str) -> Optional[str]:
        """获取缓存"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT value FROM cache 
                    WHERE key = ? AND (expires_at IS NULL OR expires_at > ?)
                """, (key, datetime.now()))
                
                row = await cursor.fetchone()
                return row['value'] if row else None
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None
    
    async def cleanup_expired_cache(self) -> int:
        """清理过期缓存"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    DELETE FROM cache 
                    WHERE expires_at IS NOT NULL AND expires_at <= ?
                """, (datetime.now(),))
                await db.commit()
                deleted_count = cursor.rowcount
                logger.debug(f"清理过期缓存 {deleted_count} 条")
                return deleted_count
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0
    
    # =================== 工具方法 ===================
    
    async def close(self) -> None:
        """关闭数据库连接（如果有的话）"""
        # aiosqlite 使用上下文管理器，不需要显式关闭
        logger.info("数据库管理器已关闭")


# 全局数据库管理器实例
db_manager = DatabaseManager()