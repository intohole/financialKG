# 性能优化策略

## 7. 性能优化策略

### 7.1 数据处理效率优化

#### 7.1.1 并行处理机制

**文档处理并行化**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict, Any
import multiprocessing as mp

class ParallelDocumentProcessor:
    """并行文档处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_workers = config.get('max_workers', mp.cpu_count())
        self.chunk_size = config.get('chunk_size', 10)
        
        # 线程池用于I/O密集型任务
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers * 2)
        
        # 进程池用于CPU密集型任务
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
    
    async def process_documents_batch(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理文档"""
        # 将文档分成块
        chunks = [documents[i:i + self.chunk_size] 
                 for i in range(0, len(documents), self.chunk_size)]
        
        # 并发处理每个块
        tasks = [self._process_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        all_results = []
        for result in results:
            if isinstance(result, Exception):
                # 记录异常但不中断整体处理
                logger.error(f"Chunk processing failed: {result}")
            else:
                all_results.extend(result)
        
        return all_results
    
    async def _process_chunk(self, chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理单个文档块"""
        # 使用信号量限制并发数
        semaphore = asyncio.Semaphore(self.config.get('max_concurrent', 10))
        
        async def process_with_limit(doc: Dict[str, Any]):
            async with semaphore:
                return await self._process_single_document(doc)
        
        tasks = [process_with_limit(doc) for doc in chunk]
        return await asyncio.gather(*tasks)
    
    async def _process_single_document(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个文档"""
        try:
            # 步骤1: 文档加载（I/O密集型）
            loaded_doc = await self._load_document_async(doc)
            
            # 步骤2: 文本提取（CPU密集型）
            text = await self._extract_text_parallel(loaded_doc)
            
            # 步骤3: 文本分块（CPU密集型）
            chunks = await self._split_text_parallel(text)
            
            # 步骤4: 并行处理每个块
            processed_chunks = await self._process_chunks_parallel(chunks)
            
            return {
                'document_id': doc['id'],
                'status': 'success',
                'chunks_processed': len(processed_chunks),
                'processing_time': self._calculate_processing_time(),
                'chunks': processed_chunks
            }
            
        except Exception as e:
            return {
                'document_id': doc['id'],
                'status': 'failed',
                'error': str(e),
                'processing_time': self._calculate_processing_time()
            }
    
    async def _load_document_async(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """异步加载文档"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.thread_pool, 
            self._sync_load_document, 
            doc
        )
    
    async def _extract_text_parallel(self, doc: Dict[str, Any]) -> str:
        """并行提取文本"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.process_pool,
            self._sync_extract_text,
            doc
        )
    
    async def _split_text_parallel(self, text: str) -> List[str]:
        """并行分割文本"""
        # 将大文本分成多个部分进行并行处理
        text_parts = self._divide_text(text, self.max_workers)
        
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.process_pool, self._sync_split_text, part)
            for part in text_parts
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 合并结果
        all_chunks = []
        for chunks in results:
            all_chunks.extend(chunks)
        
        return all_chunks
    
    async def _process_chunks_parallel(self, chunks: List[str]) -> List[Dict[str, Any]]:
        """并行处理文本块"""
        # 分批处理以避免内存溢出
        batch_size = self.config.get('chunk_batch_size', 50)
        results = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            batch_results = await self._process_batch_async(batch)
            results.extend(batch_results)
        
        return results
```

#### 7.1.2 任务调度策略

**优先级队列调度**
```python
import asyncio
from asyncio import PriorityQueue
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Optional
import time

class TaskPriority(IntEnum):
    """任务优先级"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0

@dataclass
class ProcessingTask:
    """处理任务"""
    priority: TaskPriority
    task_id: str
    task_type: str
    data: Any
    created_at: float
    max_retries: int = 3
    current_retry: int = 0
    timeout: int = 300  # 5分钟
    
    def __lt__(self, other):
        # 优先级数值越小，优先级越高
        if self.priority != other.priority:
            return self.priority < other.priority
        # 相同优先级，先创建的先处理
        return self.created_at < other.created_at

class PriorityTaskScheduler:
    """优先级任务调度器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.task_queue = PriorityQueue()
        self.workers = []
        self.max_workers = config.get('max_workers', 5)
        self.running = False
        self.task_stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'retried_tasks': 0
        }
    
    async def start(self):
        """启动调度器"""
        self.running = True
        
        # 创建工作进程
        for i in range(self.max_workers):
            worker = asyncio.create_task(
                self._worker_loop(f"worker_{i}")
            )
            self.workers.append(worker)
        
        logger.info(f"Started {self.max_workers} workers")
    
    async def stop(self):
        """停止调度器"""
        self.running = False
        
        # 等待所有工作进程完成
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Task scheduler stopped")
    
    async def submit_task(self, task: ProcessingTask) -> str:
        """提交任务"""
        await self.task_queue.put(task)
        self.task_stats['total_tasks'] += 1
        
        logger.info(f"Task submitted: {task.task_id} (priority: {task.priority.name})")
        return task.task_id
    
    async def _worker_loop(self, worker_id: str):
        """工作进程循环"""
        while self.running:
            try:
                # 获取任务（带超时）
                task = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=1.0
                )
                
                # 处理任务
                await self._process_task(task, worker_id)
                
            except asyncio.TimeoutError:
                # 队列为空，继续循环
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
    
    async def _process_task(self, task: ProcessingTask, worker_id: str):
        """处理单个任务"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing task {task.task_id} on {worker_id}")
            
            # 检查任务是否超时
            if time.time() - task.created_at > task.timeout:
                raise TimeoutError(f"Task {task.task_id} timed out")
            
            # 执行任务
            result = await self._execute_task(task)
            
            # 更新统计
            self.task_stats['completed_tasks'] += 1
            
            processing_time = time.time() - start_time
            logger.info(f"Task {task.task_id} completed in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            
            # 重试逻辑
            if task.current_retry < task.max_retries:
                task.current_retry += 1
                self.task_stats['retried_tasks'] += 1
                
                # 指数退避延迟
                retry_delay = min(
                    2 ** task.current_retry,
                    self.config.get('max_retry_delay', 60)
                )
                
                await asyncio.sleep(retry_delay)
                await self.submit_task(task)
            else:
                self.task_stats['failed_tasks'] += 1
                await self._handle_task_failure(task, e)
    
    async def _execute_task(self, task: ProcessingTask) -> Any:
        """执行任务逻辑"""
        # 根据任务类型调用不同的处理器
        if task.task_type == 'document_processing':
            return await self._process_document_task(task)
        elif task.task_type == 'knowledge_extraction':
            return await self._extract_knowledge_task(task)
        elif task.task_type == 'vector_embedding':
            return await self._generate_embedding_task(task)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取调度统计"""
        queue_size = self.task_queue.qsize()
        
        return {
            'queue_size': queue_size,
            'worker_count': len(self.workers),
            'is_running': self.running,
            'statistics': self.task_stats,
            'performance': {
                'throughput': self._calculate_throughput(),
                'average_processing_time': self._calculate_avg_time()
            }
        }
```

### 7.2 查询响应速度优化

#### 7.2.1 多级缓存策略

**缓存架构设计**
```python
import asyncio
import aioredis
from typing import Any, Optional, Dict, List
import json
import hashlib
from datetime import datetime, timedelta
import pickle

class CacheManager:
    """多级缓存管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # L1缓存：内存缓存
        self.l1_cache = {}
        self.l1_max_size = config.get('l1_max_size', 1000)
        self.l1_ttl = config.get('l1_ttl', 300)  # 5分钟
        
        # L2缓存：Redis缓存
        self.redis_url = config.get('redis_url', 'redis://localhost:6379')
        self.redis_client = None
        self.l2_ttl = config.get('l2_ttl', 3600)  # 1小时
        
        # L3缓存：数据库查询缓存
        self.l3_ttl = config.get('l3_ttl', 86400)  # 24小时
        
        # 缓存统计
        self.stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'l3_hits': 0,
            'l3_misses': 0
        }
    
    async def initialize(self):
        """初始化缓存管理器"""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # 测试Redis连接
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}, using memory cache only")
            self.redis_client = None
    
    async def get(self, key: str, level: int = 1) -> Optional[Any]:
        """获取缓存值"""
        # L1缓存查找
        if level <= 1:
            value = self._get_l1(key)
            if value is not None:
                self.stats['l1_hits'] += 1
                return value
            self.stats['l1_misses'] += 1
        
        # L2缓存查找
        if level <= 2 and self.redis_client:
            value = await self._get_l2(key)
            if value is not None:
                # 回写到L1缓存
                self._set_l1(key, value)
                self.stats['l2_hits'] += 1
                return value
            self.stats['l2_misses'] += 1
        
        # L3缓存（数据库）查找
        if level <= 3:
            value = await self._get_l3(key)
            if value is not None:
                # 回写到L1和L2缓存
                self._set_l1(key, value)
                if self.redis_client:
                    await self._set_l2(key, value)
                self.stats['l3_hits'] += 1
                return value
            self.stats['l3_misses'] += 1
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, level: int = 1) -> bool:
        """设置缓存值"""
        try:
            # L1缓存
            if level <= 1:
                self._set_l1(key, value, ttl)
            
            # L2缓存
            if level <= 2 and self.redis_client:
                await self._set_l2(key, value, ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    async def delete(self, key: str, level: int = 3) -> bool:
        """删除缓存"""
        try:
            # L1缓存删除
            if level >= 1:
                self._delete_l1(key)
            
            # L2缓存删除
            if level >= 2 and self.redis_client:
                await self._delete_l2(key)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    def _get_l1(self, key: str) -> Optional[Any]:
        """L1缓存获取"""
        if key not in self.l1_cache:
            return None
        
        entry = self.l1_cache[key]
        
        # 检查过期时间
        if entry['expires_at'] and datetime.now() > entry['expires_at']:
            del self.l1_cache[key]
            return None
        
        return entry['value']
    
    def _set_l1(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """L1缓存设置"""
        # 检查缓存大小限制
        if len(self.l1_cache) >= self.l1_max_size:
            # 使用LRU策略删除最久未使用的缓存
            self._evict_lru_l1()
        
        expires_at = None
        if ttl:
            expires_at = datetime.now() + timedelta(seconds=ttl)
        elif self.l1_ttl:
            expires_at = datetime.now() + timedelta(seconds=self.l1_ttl)
        
        self.l1_cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'accessed_at': datetime.now()
        }
    
    def _delete_l1(self, key: str) -> None:
        """L1缓存删除"""
        self.l1_cache.pop(key, None)
    
    def _evict_lru_l1(self) -> None:
        """LRU缓存淘汰"""
        if not self.l1_cache:
            return
        
        # 找到最久未使用的缓存项
        oldest_key = min(
            self.l1_cache.keys(),
            key=lambda k: self.l1_cache[k]['accessed_at']
        )
        
        del self.l1_cache[oldest_key]
    
    async def _get_l2(self, key: str) -> Optional[Any]:
        """L2缓存获取"""
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(f"cache:l2:{key}")
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"L2 cache get failed: {e}")
        
        return None
    
    async def _set_l2(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """L2缓存设置"""
        if not self.redis_client:
            return
        
        try:
            ttl = ttl or self.l2_ttl
            serialized_value = json.dumps(value, default=str)
            
            await self.redis_client.setex(
                f"cache:l2:{key}",
                ttl,
                serialized_value
            )
        except Exception as e:
            logger.error(f"L2 cache set failed: {e}")
    
    async def _delete_l2(self, key: str) -> None:
        """L2缓存删除"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.delete(f"cache:l2:{key}")
        except Exception as e:
            logger.error(f"L2 cache delete failed: {e}")
    
    async def _get_l3(self, key: str) -> Optional[Any]:
        """L3缓存获取（数据库查询）"""
        # 这里应该实现数据库查询逻辑
        # 为了演示，返回None
        return None
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 构建键的组成部分
        key_parts = [prefix]
        
        # 添加位置参数
        for arg in args:
            key_parts.append(str(arg))
        
        # 添加关键字参数（排序以确保一致性）
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        # 连接键部分
        key_string = ":".join(key_parts)
        
        # 生成哈希（避免键过长）
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            key_string = f"{prefix}:hash:{key_hash}"
        
        return key_string

# 缓存装饰器
class CacheDecorator:
    """缓存装饰器"""
    
    def __init__(self, cache_manager: CacheManager, ttl: int = 3600, key_prefix: str = ""):
        self.cache_manager = cache_manager
        self.ttl = ttl
        self.key_prefix = key_prefix
    
    def __call__(self, func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = self.cache_manager.generate_cache_key(
                self.key_prefix or func.__name__,
                *args,
                **kwargs
            )
            
            # 尝试从缓存获取
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            await self.cache_manager.set(cache_key, result, self.ttl)
            
            return result
        
        return wrapper
```

#### 7.2.2 查询优化策略

**数据库查询优化**
```python
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload
import asyncio
from typing import List, Dict, Any, Optional

class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enable_query_cache = config.get('enable_query_cache', True)
        self.max_query_cache_size = config.get('max_query_cache_size', 1000)
        self.query_cache = {}
    
    async def optimize_entity_query(self, query_params: Dict[str, Any]) -> select:
        """优化实体查询"""
        # 基础查询
        stmt = select(Entity)
        
        # 条件过滤
        conditions = []
        
        if 'name' in query_params:
            conditions.append(Entity.name.ilike(f"%{query_params['name']}%"))
        
        if 'type' in query_params:
            conditions.append(Entity.type == query_params['type'])
        
        if 'confidence_min' in query_params:
            conditions.append(Entity.confidence >= query_params['confidence_min'])
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 预加载关联数据
        if query_params.get('include_relations'):
            stmt = stmt.options(
                selectinload(Entity.as_subject),
                selectinload(Entity.as_object)
            )
        
        if query_params.get('include_attributes'):
            stmt = stmt.options(selectinload(Entity.attributes))
        
        # 排序
        if 'sort' in query_params:
            sort_field = query_params['sort']
            if sort_field.startswith('-'):
                stmt = stmt.order_by(getattr(Entity, sort_field[1:]).desc())
            else:
                stmt = stmt.order_by(getattr(Entity, sort_field).asc())
        
        # 分页
        page = query_params.get('page', 1)
        size = min(query_params.get('size', 20), 100)
        offset = (page - 1) * size
        
        stmt = stmt.offset(offset).limit(size)
        
        return stmt
    
    async def optimize_relation_query(self, query_params: Dict[str, Any]) -> select:
        """优化关系查询"""
        # 基础查询
        stmt = select(Relation)
        
        # 条件过滤
        conditions = []
        
        if 'subject_id' in query_params:
            conditions.append(Relation.subject_id == query_params['subject_id'])
        
        if 'object_id' in query_params:
            conditions.append(Relation.object_id == query_params['object_id'])
        
        if 'predicate' in query_params:
            conditions.append(Relation.predicate == query_params['predicate'])
        
        if 'confidence_min' in query_params:
            conditions.append(Relation.confidence >= query_params['confidence_min'])
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 预加载关联实体
        stmt = stmt.options(
            joinedload(Relation.subject),
            joinedload(Relation.object)
        )
        
        # 排序和分页
        if 'sort' in query_params:
            sort_field = query_params['sort']
            if sort_field.startswith('-'):
                stmt = stmt.order_by(getattr(Relation, sort_field[1:]).desc())
            else:
                stmt = stmt.order_by(getattr(Relation, sort_field).asc())
        
        page = query_params.get('page', 1)
        size = min(query_params.get('size', 20), 100)
        offset = (page - 1) * size
        
        stmt = stmt.offset(offset).limit(size)
        
        return stmt
    
    async def optimize_graph_traversal(self, start_entity_id: int, end_entity_id: int, 
                                     max_depth: int = 3) -> List[List[Dict[str, Any]]]:
        """优化图遍历查询"""
        # 使用递归CTE进行路径查找
        paths_cte = """
        WITH RECURSIVE paths AS (
            -- 基础情况：直接连接
            SELECT 
                r.subject_id as start_id,
                r.object_id as end_id,
                r.predicate as path,
                1 as depth,
                r.confidence as total_confidence,
                r.id as relation_ids
            FROM relations r
            WHERE r.subject_id = :start_id
            
            UNION ALL
            
            -- 递归情况：扩展路径
            SELECT 
                p.start_id,
                r.object_id as end_id,
                p.path || '->' || r.predicate as path,
                p.depth + 1,
                p.total_confidence * r.confidence as total_confidence,
                p.relation_ids || ',' || r.id::text as relation_ids
            FROM paths p
            JOIN relations r ON p.end_id = r.subject_id
            WHERE p.depth < :max_depth AND p.end_id != :end_id
        )
        SELECT * FROM paths
        WHERE end_id = :end_id AND depth <= :max_depth
        ORDER BY total_confidence DESC
        """
        
        # 执行查询
        result = await self._execute_query(
            paths_cte,
            {
                'start_id': start_entity_id,
                'end_id': end_entity_id,
                'max_depth': max_depth
            }
        )
        
        return result
    
    async def optimize_vector_search(self, query_vector: List[float], 
                                   collection_name: str, top_k: int = 10,
                                   filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """优化向量搜索"""
        # 使用Chroma的查询优化
        
        # 构建查询参数
        query_params = {
            'query_embeddings': [query_vector],
            'n_results': top_k,
            'include': ['metadatas', 'documents', 'distances']
        }
        
        # 添加过滤条件
        if filters:
            where_clause = self._build_where_clause(filters)
            query_params['where'] = where_clause
        
        # 执行向量搜索
        results = await self._execute_vector_query(
            collection_name, 
            query_params
        )
        
        # 后处理和优化
        optimized_results = await self._post_process_vector_results(results)
        
        return optimized_results
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """构建查询过滤条件"""
        where_clause = {}
        
        for key, value in filters.items():
            if isinstance(value, dict):
                # 范围查询
                if 'min' in value and 'max' in value:
                    where_clause[key] = {
                        "$gte": value['min'],
                        "$lte": value['max']
                    }
                elif 'in' in value:
                    where_clause[key] = {"$in": value['in']}
            else:
                # 等值查询
                where_clause[key] = value
        
        return where_clause
    
    async def _post_process_vector_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """后处理向量搜索结果"""
        processed_results = []
        
        # 提取结果
        ids = results.get('ids', [[]])[0]
        distances = results.get('distances', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        documents = results.get('documents', [[]])[0]
        
        # 构建标准化结果
        for i, doc_id in enumerate(ids):
            result = {
                'id': doc_id,
                'score': 1 - distances[i],  # 转换为相似度分数
                'distance': distances[i],
                'metadata': metadatas[i] if i < len(metadatas) else {},
                'content': documents[i] if i < len(documents) else ""
            }
            
            processed_results.append(result)
        
        # 按分数排序
        processed_results.sort(key=lambda x: x['score'], reverse=True)
        
        return processed_results
```

### 7.3 资源占用优化

#### 7.3.1 内存管理策略

**对象池和连接池**
```python
import weakref
import gc
from typing import Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager

class ObjectPool:
    """对象池管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pools = {}
        self.object_stats = {}
        
        # 垃圾回收配置
        self.gc_threshold = config.get('gc_threshold', 1000)
        self.enable_auto_gc = config.get('enable_auto_gc', True)
    
    def register_pool(self, pool_name: str, factory_func, max_size: int = 100):
        """注册对象池"""
        self.pools[pool_name] = {
            'factory': factory_func,
            'max_size': max_size,
            'available': [],
            'in_use': weakref.WeakSet(),
            'stats': {
                'created': 0,
                'borrowed': 0,
                'returned': 0,
                'destroyed': 0
            }
        }
        
        self.object_stats[pool_name] = {
            'total_objects': 0,
            'active_objects': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }
    
    @asynccontextmanager
    async def get_object(self, pool_name: str):
        """获取池化对象"""
        if pool_name not in self.pools:
            raise ValueError(f"Pool {pool_name} not registered")
        
        pool = self.pools[pool_name]
        obj = None
        
        try:
            # 从可用对象池中获取
            if pool['available']:
                obj = pool['available'].pop()
                self.object_stats[pool_name]['pool_hits'] += 1
            else:
                # 创建新对象
                if self._can_create_object(pool_name):
                    obj = await self._create_object(pool_name)
                    self.object_stats[pool_name]['pool_misses'] += 1
                else:
                    raise RuntimeError(f"Pool {pool_name} exhausted")
            
            # 标记为使用中
            pool['in_use'].add(obj)
            pool['stats']['borrowed'] += 1
            self.object_stats[pool_name]['active_objects'] += 1
            
            yield obj
            
        finally:
            # 归还对象到池中
            if obj is not None:
                await self._return_object(pool_name, obj)
    
    async def _create_object(self, pool_name: str):
        """创建新对象"""
        pool = self.pools[pool_name]
        
        # 调用工厂函数创建对象
        obj = await pool['factory']()
        
        pool['stats']['created'] += 1
        self.object_stats[pool_name]['total_objects'] += 1
        
        return obj
    
    async def _return_object(self, pool_name: str, obj: Any):
        """归还对象到池中"""
        pool = self.pools[pool_name]
        
        # 清理对象状态
        await self._cleanup_object(obj)
        
        # 从使用集合中移除
        pool['in_use'].discard(obj)
        
        # 归还到可用池
        if len(pool['available']) < pool['max_size']:
            pool['available'].append(obj)
        else:
            # 池已满，销毁对象
            await self._destroy_object(pool_name, obj)
        
        pool['stats']['returned'] += 1
        self.object_stats[pool_name]['active_objects'] -= 1
    
    def _can_create_object(self, pool_name: str) -> bool:
        """检查是否可以创建新对象"""
        pool = self.pools[pool_name]
        total_objects = len(pool['available']) + len(pool['in_use'])
        return total_objects < pool['max_size']
    
    async def _cleanup_object(self, obj: Any):
        """清理对象状态"""
        # 这里可以根据对象类型进行特定的清理操作
        if hasattr(obj, 'reset'):
            obj.reset()
        elif hasattr(obj, 'cleanup'):
            await obj.cleanup()
    
    async def _destroy_object(self, pool_name: str, obj: Any):
        """销毁对象"""
        pool = self.pools[pool_name]
        
        # 调用对象的销毁方法
        if hasattr(obj, 'destroy'):
            await obj.destroy()
        elif hasattr(obj, '__del__'):
            obj.__del__()
        
        pool['stats']['destroyed'] += 1
        self.object_stats[pool_name]['total_objects'] -= 1
    
    async def perform_maintenance(self):
        """执行池维护"""
        for pool_name, pool in self.pools.items():
            # 清理过期对象
            await self._cleanup_expired_objects(pool_name)
            
            # 调整池大小
            await self._adjust_pool_size(pool_name)
            
            # 执行垃圾回收
            if self.enable_auto_gc:
                self._perform_garbage_collection()
    
    async def _cleanup_expired_objects(self, pool_name: str):
        """清理过期对象"""
        # 这里可以实现对象的过期检查逻辑
        pass
    
    async def _adjust_pool_size(self, pool_name: str):
        """根据使用情况调整池大小"""
        stats = self.object_stats[pool_name]
        pool = self.pools[pool_name]
        
        # 根据命中率和活跃对象数调整池大小
        hit_rate = stats['pool_hits'] / (stats['pool_hits'] + stats['pool_misses'] + 1)
        
        if hit_rate < 0.8 and stats['active_objects'] > pool['max_size'] * 0.8:
            # 增加池大小
            pool['max_size'] = min(pool['max_size'] * 2, self.config.get('max_pool_size', 1000))
        elif hit_rate > 0.95 and stats['active_objects'] < pool['max_size'] * 0.3:
            # 减少池大小
            pool['max_size'] = max(pool['max_size'] // 2, self.config.get('min_pool_size', 10))
    
    def _perform_garbage_collection(self):
        """执行垃圾回收"""
        total_objects = sum(stats['total_objects'] for stats in self.object_stats.values())
        
        if total_objects > self.gc_threshold:
            gc.collect()
            logger.info(f"Performed garbage collection, total objects: {total_objects}")

class ConnectionPool:
    """数据库连接池"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool_size = config.get('pool_size', 20)
        self.max_overflow = config.get('max_overflow', 10)
        self.pool_timeout = config.get('pool_timeout', 30)
        self.pool_recycle = config.get('pool_recycle', 3600)
        
        self.engine = None
        self.async_engine = None
    
    async def initialize(self):
        """初始化连接池"""
        from sqlalchemy.ext.asyncio import create_async_engine
        
        # 异步引擎配置
        self.async_engine = create_async_engine(
            self.config['database_url'],
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,  # 连接健康检查
            echo=self.config.get('echo', False)
        )
        
        logger.info(f"Database connection pool initialized: size={self.pool_size}")
    
    @asynccontextmanager
    async def get_connection(self):
        """获取数据库连接"""
        async with self.async_engine.begin() as conn:
            try:
                yield conn
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                raise
            finally:
                # 连接会自动归还到池中
                pass
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取连接池统计"""
        if not self.async_engine:
            return {}
        
        pool = self.async_engine.pool
        
        return {
            'size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'total_connections': pool.total(),
            'timeout': self.pool_timeout,
            'recycle_time': self.pool_recycle
        }
```

#### 7.3.2 内存监控和优化

**内存使用监控**
```python
import psutil
import os
from typing import Dict, Any
import threading
import time
from collections import deque

class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.check_interval = config.get('check_interval', 60)  # 秒
        self.memory_threshold = config.get('memory_threshold', 0.8)  # 80%
        self.max_memory_usage = config.get('max_memory_usage', 4 * 1024 * 1024 * 1024)  # 4GB
        
        # 历史数据
        self.memory_history = deque(maxlen=1000)
        self.monitoring = False
        self.monitor_thread = None
        
        # 告警回调
        self.alert_callbacks = []
    
    def start_monitoring(self):
        """开始内存监控"""
        if not self.enabled:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 获取当前内存使用情况
                memory_info = self._get_memory_info()
                
                # 记录历史数据
                self.memory_history.append({
                    'timestamp': time.time(),
                    'memory_info': memory_info
                })
                
                # 检查是否超过阈值
                if self._is_memory_high(memory_info):
                    self._handle_high_memory(memory_info)
                
                # 检查是否超过最大限制
                if self._is_memory_critical(memory_info):
                    self._handle_critical_memory(memory_info)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.check_interval)
    
    def _get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            'process_memory': {
                'rss': memory_info.rss,  # 常驻内存
                'vms': memory_info.vms,  # 虚拟内存
                'percent': process.memory_percent()
            },
            'system_memory': {
                'total': system_memory.total,
                'available': system_memory.available,
                'percent': system_memory.percent,
                'used': system_memory.used
            },
            'timestamp': time.time()
        }
    
    def _is_memory_high(self, memory_info: Dict[str, Any]) -> bool:
        """检查内存是否过高"""
        process_percent = memory_info['process_memory']['percent']
        system_percent = memory_info['system_memory']['percent']
        
        return (process_percent > self.memory_threshold * 100 or 
                system_percent > self.memory_threshold * 100)
    
    def _is_memory_critical(self, memory_info: Dict[str, Any]) -> bool:
        """检查内存是否达到临界状态"""
        process_rss = memory_info['process_memory']['rss']
        system_percent = memory_info['system_memory']['percent']
        
        return (process_rss > self.max_memory_usage or 
                system_percent > 0.95)  # 系统内存使用超过95%
    
    def _handle_high_memory(self, memory_info: Dict[str, Any]):
        """处理高内存使用"""
        logger.warning(f"High memory usage detected: {memory_info}")
        
        # 触发告警回调
        for callback in self.alert_callbacks:
            try:
                callback('high_memory', memory_info)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        # 执行内存优化
        self._perform_memory_optimization()
    
    def _handle_critical_memory(self, memory_info: Dict[str, Any]):
        """处理临界内存使用"""
        logger.critical(f"Critical memory usage detected: {memory_info}")
        
        # 触发紧急告警
        for callback in self.alert_callbacks:
            try:
                callback('critical_memory', memory_info)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        # 执行紧急内存释放
        self._perform_emergency_cleanup()
    
    def _perform_memory_optimization(self):
        """执行内存优化"""
        # 1. 触发垃圾回收
        gc.collect()
        
        # 2. 清理缓存
        # 这里可以调用缓存管理器的清理方法
        
        # 3. 释放大对象
        # 这里可以调用对象池的清理方法
        
        logger.info("Memory optimization performed")
    
    def _perform_emergency_cleanup(self):
        """执行紧急内存清理"""
        # 1. 强制垃圾回收
        gc.collect(2)  # 最彻底的垃圾回收
        
        # 2. 清理所有缓存
        # 这里可以清空所有缓存
        
        # 3. 释放所有池化对象
        # 这里可以清空所有对象池
        
        # 4. 重启工作进程（如果需要）
        # 这里可以实现进程重启逻辑
        
        logger.info("Emergency memory cleanup performed")
    
    def add_alert_callback(self, callback):
        """添加告警回调"""
        self.alert_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取内存统计"""
        if not self.memory_history:
            return {}
        
        current_memory = self._get_memory_info()
        
        # 计算趋势
        recent_samples = list(self.memory_history)[-10:]
        memory_trend = self._calculate_memory_trend(recent_samples)
        
        return {
            'current_memory': current_memory,
            'memory_trend': memory_trend,
            'samples_collected': len(self.memory_history),
            'monitoring_enabled': self.enabled,
            'thresholds': {
                'memory_threshold': self.memory_threshold,
                'max_memory_usage': self.max_memory_usage
            }
        }
    
    def _calculate_memory_trend(self, samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算内存使用趋势"""
        if len(samples) < 2:
            return {'trend': 'stable', 'change_rate': 0}
        
        memory_values = [
            sample['memory_info']['process_memory']['rss']
            for sample in samples
        ]
        
        # 计算线性回归斜率
        n = len(memory_values)
        x_sum = sum(range(n))
        y_sum = sum(memory_values)
        xy_sum = sum(i * memory_values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        # 确定趋势
        if slope > 1024 * 1024:  # 每秒增加1MB以上
            trend = 'increasing'
        elif slope < -1024 * 1024:  # 每秒减少1MB以上
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_rate': slope,
            'slope': slope
        }
```

### 7.4 网络传输优化

#### 7.4.1 数据压缩策略

**智能压缩管理器**
```python
import gzip
import zlib
import brotli
from typing import Dict, Any, Optional, Union
import json

class CompressionManager:
    """压缩管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.min_size = config.get('min_compression_size', 1024)  # 1KB
        self.compression_threshold = config.get('compression_threshold', 0.8)
        
        # 压缩算法配置
        self.algorithms = {
            'gzip': {
                'compress': self._gzip_compress,
                'decompress': self._gzip_decompress,
                'level': config.get('gzip_level', 6)
            },
            'deflate': {
                'compress': self._deflate_compress,
                'decompress': self._deflate_decompress,
                'level': config.get('deflate_level', 6)
            },
            'brotli': {
                'compress': self._brotli_compress,
                'decompress': self._brotli_decompress,
                'level': config.get('brotli_level', 6)
            }
        }
        
        self.preferred_algorithm = config.get('preferred_algorithm', 'gzip')
    
    def compress_data(self, data: Union[str, bytes, Dict], 
                     algorithm: Optional[str] = None) -> Dict[str, Any]:
        """压缩数据"""
        if not self.enabled:
            return {
                'compressed': False,
                'data': data,
                'original_size': len(data) if isinstance(data, (str, bytes)) else len(json.dumps(data)),
                'compressed_size': len(data) if isinstance(data, (str, bytes)) else len(json.dumps(data))
            }
        
        # 序列化数据
        if isinstance(data, dict):
            serialized_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        elif isinstance(data, str):
            serialized_data = data.encode('utf-8')
        else:
            serialized_data = data
        
        original_size = len(serialized_data)
        
        # 检查是否需要压缩
        if original_size < self.min_size:
            return {
                'compressed': False,
                'data': data,
                'original_size': original_size,
                'compressed_size': original_size
            }
        
        # 选择压缩算法
        algorithm = algorithm or self.preferred_algorithm
        if algorithm not in self.algorithms:
            algorithm = 'gzip'
        
        # 执行压缩
        try:
            compressor = self.algorithms[algorithm]['compress']
            compressed_data = compressor(serialized_data)
            
            compressed_size = len(compressed_data)
            compression_ratio = compressed_size / original_size
            
            # 检查压缩效果
            if compression_ratio > self.compression_threshold:
                # 压缩效果不佳，返回原始数据
                return {
                    'compressed': False,
                    'data': data,
                    'original_size': original_size,
                    'compressed_size': original_size,
                    'reason': 'poor_compression_ratio'
                }
            
            return {
                'compressed': True,
                'data': compressed_data,
                'algorithm': algorithm,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio
            }
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return {
                'compressed': False,
                'data': data,
                'original_size': original_size,
                'compressed_size': original_size,
                'error': str(e)
            }
    
    def decompress_data(self, compressed_data: Dict[str, Any]) -> Any:
        """解压缩数据"""
        if not compressed_data.get('compressed'):
            return compressed_data.get('data')
        
        algorithm = compressed_data.get('algorithm', 'gzip')
        data = compressed_data.get('data')
        
        if algorithm not in self.algorithms:
            raise ValueError(f"Unknown compression algorithm: {algorithm}")
        
        try:
            decompressor = self.algorithms[algorithm]['decompress']
            decompressed_data = decompressor(data)
            
            # 如果是JSON数据，尝试反序列化
            try:
                return json.loads(decompressed_data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 返回原始字节数据或字符串
                return decompressed_data.decode('utf-8')
                
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            raise
    
    def _gzip_compress(self, data: bytes) -> bytes:
        """Gzip压缩"""
        return gzip.compress(data, compresslevel=self.algorithms['gzip']['level'])
    
    def _gzip_decompress(self, data: bytes) -> bytes:
        """Gzip解压缩"""
        return gzip.decompress(data)
    
    def _deflate_compress(self, data: bytes) -> bytes:
        """Deflate压缩"""
        return zlib.compress(data, level=self.algorithms['deflate']['level'])
    
    def _deflate_decompress(self, data: bytes) -> bytes:
        """Deflate解压缩"""
        return zlib.decompress(data)
    
    def _brotli_compress(self, data: bytes) -> bytes:
        """Brotli压缩"""
        return brotli.compress(data, quality=self.algorithms['brotli']['level'])
    
    def _brotli_decompress(self, data: bytes) -> bytes:
        """Brotli解压缩"""
        return brotli.decompress(data)
    
    def select_algorithm(self, data_size: int, data_type: str) -> str:
        """选择最优压缩算法"""
        # 基于数据大小和类型选择算法
        
        if data_size < 1024:  # 小于1KB
            return 'deflate'  # 快速压缩
        elif data_size < 10240:  # 小于10KB
            return 'gzip'  # 平衡性能和压缩率
        else:  # 大于10KB
            return 'brotli'  # 最高压缩率
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """获取压缩统计"""
        return {
            'enabled': self.enabled,
            'algorithms': list(self.algorithms.keys()),
            'preferred_algorithm': self.preferred_algorithm,
            'min_compression_size': self.min_size,
            'compression_threshold': self.compression_threshold
        }

# 响应压缩中间件
class CompressionMiddleware:
    """压缩中间件"""
    
    def __init__(self, compression_manager: CompressionManager):
        self.compression_manager = compression_manager
    
    async def __call__(self, request, call_next):
        """中间件调用"""
        response = await call_next(request)
        
        # 检查是否需要压缩
        if not self._should_compress(request, response):
            return response
        
        # 获取响应内容
        content = await response.body()
        
        # 压缩内容
        compressed_result = self.compression_manager.compress_data(content)
        
        if compressed_result['compressed']:
            # 更新响应
            response.body = compressed_result['data']
            response.headers['Content-Encoding'] = compressed_result['algorithm']
            response.headers['Content-Length'] = str(compressed_result['compressed_size'])
            response.headers['X-Compression-Ratio'] = str(compressed_result['compression_ratio'])
        
        return response
    
    def _should_compress(self, request, response) -> bool:
        """检查是否应该压缩响应"""
        # 检查客户端是否支持压缩
        accept_encoding = request.headers.get('accept-encoding', '')
        if 'gzip' not in accept_encoding and 'deflate' not in accept_encoding:
            return False
        
        # 检查内容类型
        content_type = response.headers.get('content-type', '')
        compressible_types = [
            'text/',
            'application/json',
            'application/xml',
            'application/javascript',
            'application/octet-stream'
        ]
        
        if not any(content_type.startswith(ct) for ct in compressible_types):
            return False
        
        # 检查内容长度
        content_length = response.headers.get('content-length')
        if content_length:
            try:
                if int(content_length) < self.compression_manager.min_size:
                    return False
            except ValueError:
                pass
        
        return True
```

#### 7.4.2 批量处理优化

**批量API请求处理**
```python
from typing import List, Dict, Any, Optional
import asyncio
from dataclasses import dataclass
import aiohttp

@dataclass
class BatchRequest:
    """批量请求"""
    request_id: str
    method: str
    endpoint: str
    data: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None

@dataclass
class BatchResponse:
    """批量响应"""
    request_id: str
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_batch_size = config.get('max_batch_size', 100)
        self.batch_timeout = config.get('batch_timeout', 30)
        self.max_concurrent_batches = config.get('max_concurrent_batches', 5)
        
        # 批处理队列
        self.batch_queue = asyncio.Queue(maxsize=self.max_batch_size * 2)
        self.processing = False
        self.batch_stats = {
            'total_batches': 0,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_batch_size': 0
        }
    
    async def start(self):
        """启动批处理器"""
        self.processing = True
        
        # 启动批处理循环
        self.batch_task = asyncio.create_task(self._batch_processing_loop())
        
        logger.info("Batch processor started")
    
    async def stop(self):
        """停止批处理器"""
        self.processing = False
        
        if self.batch_task:
            await self.batch_task
        
        logger.info("Batch processor stopped")
    
    async def submit_request(self, request: BatchRequest) -> BatchResponse:
        """提交批量请求"""
        # 创建响应future
        response_future = asyncio.Future()
        
        # 包装请求
        batch_item = {
            'request': request,
            'response_future': response_future,
            'submitted_at': time.time()
        }
        
        # 添加到队列
        await self.batch_queue.put(batch_item)
        self.batch_stats['total_requests'] += 1
        
        # 等待响应
        return await response_future
    
    async def _batch_processing_loop(self):
        """批处理循环"""
        while self.processing:
            try:
                # 收集批量请求
                batch = await self._collect_batch_requests()
                
                if batch:
                    # 处理批量请求
                    await self._process_batch(batch)
                    
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
                await asyncio.sleep(1)
    
    async def _collect_batch_requests(self) -> List[Dict[str, Any]]:
        """收集批量请求"""
        batch = []
        deadline = time.time() + self.batch_timeout
        
        # 等待第一个请求
        try:
            first_item = await asyncio.wait_for(
                self.batch_queue.get(),
                timeout=1.0
            )
            batch.append(first_item)
        except asyncio.TimeoutError:
            return batch
        
        # 收集更多请求直到批次满或超时
        while (len(batch) < self.max_batch_size and 
               time.time() < deadline and 
               self.processing):
            
            try:
                item = await asyncio.wait_for(
                    self.batch_queue.get(),
                    timeout=0.1
                )
                batch.append(item)
            except asyncio.TimeoutError:
                break
        
        return batch
    
    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """处理批量请求"""
        start_time = time.time()
        batch_size = len(batch)
        
        logger.info(f"Processing batch of {batch_size} requests")
        
        try:
            # 按端点分组请求
            grouped_requests = self._group_requests_by_endpoint(batch)
            
            # 并发处理不同端点的请求组
            tasks = [
                self._process_endpoint_group(endpoint, group)
                for endpoint, group in grouped_requests.items()
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 更新统计
            self.batch_stats['total_batches'] += 1
            self.batch_stats['average_batch_size'] = (
                (self.batch_stats['average_batch_size'] * (self.batch_stats['total_batches'] - 1) + batch_size) /
                self.batch_stats['total_batches']
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Batch processed in {processing_time:.2f}s, size: {batch_size}")
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            
            # 标记所有请求为失败
            for item in batch:
                if not item['response_future'].done():
                    item['response_future'].set_exception(e)
    
    def _group_requests_by_endpoint(self, batch: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按端点分组请求"""
        grouped = {}
        
        for item in batch:
            request = item['request']
            endpoint = request.endpoint
            
            if endpoint not in grouped:
                grouped[endpoint] = []
            
            grouped[endpoint].append(item)
        
        return grouped
    
    async def _process_endpoint_group(self, endpoint: str, group: List[Dict[str, Any]]):
        """处理端点请求组"""
        # 根据端点类型选择不同的处理策略
        if endpoint.startswith('/api/v1/documents'):
            await self._process_document_requests(endpoint, group)
        elif endpoint.startswith('/api/v1/entities'):
            await self._process_entity_requests(endpoint, group)
        elif endpoint.startswith('/api/v1/relations'):
            await self._process_relation_requests(endpoint, group)
        else:
            await self._process_generic_requests(endpoint, group)
    
    async def _process_document_requests(self, endpoint: str, group: List[Dict[str, Any]]):
        """处理文档请求"""
        # 批量查询数据库
        document_ids = [
            item['request'].params.get('id') 
            for item in group 
            if item['request'].params and 'id' in item['request'].params
        ]
        
        if document_ids:
            # 执行批量查询
            batch_results = await self._batch_query_documents(document_ids)
            
            # 分发结果
            for item in group:
                request_id = item['request'].request_id
                result = batch_results.get(request_id)
                
                if result:
                    response = BatchResponse(
                        request_id=request_id,
                        status_code=200,
                        data=result
                    )
                    item['response_future'].set_result(response)
                    self.batch_stats['successful_requests'] += 1
                else:
                    error_response = BatchResponse(
                        request_id=request_id,
                        status_code=404,
                        error="Document not found"
                    )
                    item['response_future'].set_result(error_response)
                    self.batch_stats['failed_requests'] += 1
    
    async def _batch_query_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """批量查询文档"""
        # 这里实现具体的数据库查询逻辑
        # 返回文档ID到文档数据的映射
        
        # 模拟批量查询
        results = {}
        for doc_id in document_ids:
            results[f"req_{doc_id}"] = {
                'id': doc_id,
                'filename': f'document_{doc_id}.pdf',
                'status': 'processed'
            }
        
        return results
    
    async def _process_generic_requests(self, endpoint: str, group: List[Dict[str, Any]]):
        """处理通用请求"""
        # 并发处理每个请求
        tasks = []
        
        for item in group:
            task = asyncio.create_task(self._process_single_request(item))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_request(self, item: Dict[str, Any]):
        """处理单个请求"""
        try:
            request = item['request']
            
            # 模拟API调用
            result = await self._simulate_api_call(request)
            
            response = BatchResponse(
                request_id=request.request_id,
                status_code=200,
                data=result
            )
            
            item['response_future'].set_result(response)
            self.batch_stats['successful_requests'] += 1
            
        except Exception as e:
            error_response = BatchResponse(
                request_id=item['request'].request_id,
                status_code=500,
                error=str(e)
            )
            
            item['response_future'].set_result(error_response)
            self.batch_stats['failed_requests'] += 1
    
    async def _simulate_api_call(self, request: BatchRequest) -> Dict[str, Any]:
        """模拟API调用"""
        # 这里实现具体的API调用逻辑
        await asyncio.sleep(0.1)  # 模拟延迟
        
        return {
            'request_id': request.request_id,
            'method': request.method,
            'endpoint': request.endpoint,
            'processed_at': time.time()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取批处理统计"""
        return {
            'statistics': self.batch_stats,
            'configuration': {
                'max_batch_size': self.max_batch_size,
                'batch_timeout': self.batch_timeout,
                'max_concurrent_batches': self.max_concurrent_batches
            },
            'queue_size': self.batch_queue.qsize(),
            'is_processing': self.processing
        }
```