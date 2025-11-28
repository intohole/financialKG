/**
 * 知识图谱API封装层
 * 提供统一的API调用接口和错误处理
 */

class KGAPI {
    constructor(baseURL = 'http://localhost:8001') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    /**
     * 统一的请求方法
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const error = await this.parseError(response);
                throw new Error(error.message || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API请求失败 [${endpoint}]:`, error);
            throw this.enhanceError(error, endpoint);
        }
    }

    /**
     * 解析错误响应
     */
    async parseError(response) {
        try {
            const data = await response.json();
            return {
                status: response.status,
                message: data.detail || data.message || '未知错误',
                data: data
            };
        } catch {
            return {
                status: response.status,
                message: `${response.status} ${response.statusText}`,
                data: null
            };
        }
    }

    /**
     * 增强错误信息
     */
    enhanceError(error, endpoint) {
        const enhancedError = new Error(error.message);
        enhancedError.endpoint = endpoint;
        enhancedError.timestamp = new Date().toISOString();
        enhancedError.originalError = error;
        return enhancedError;
    }

    /**
     * 处理内容并构建知识图谱
     */
    async processContent(content, contentId = null) {
        const payload = {
            content: content,
            content_id: contentId
        };

        return await this.request('/api/kg/process-content', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * 获取实体列表
     */
    async getEntities(params = {}) {
        const queryParams = new URLSearchParams();
        
        // 添加分页参数
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        
        // 添加搜索和过滤参数
        if (params.search) queryParams.append('search', params.search);
        if (params.entity_type) queryParams.append('entity_type', params.entity_type);
        if (params.sort_by) queryParams.append('sort_by', params.sort_by);
        if (params.sort_order) queryParams.append('sort_order', params.sort_order);

        const endpoint = `/api/kg/entities${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        return await this.request(endpoint);
    }

    /**
     * 获取实体详情
     */
    async getEntityDetail(entityId) {
        return await this.request(`/api/kg/entities/${entityId}`);
    }

    /**
     * 获取关系列表
     */
    async getRelations(params = {}) {
        const queryParams = new URLSearchParams();
        
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        if (params.entity_id) queryParams.append('entity_id', params.entity_id);
        if (params.relation_type) queryParams.append('relation_type', params.relation_type);
        if (params.search) queryParams.append('search', params.search);

        const endpoint = `/api/kg/relations${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        return await this.request(endpoint);
    }

    /**
     * 获取实体邻居网络
     */
    async getEntityNeighbors(entityId, params = {}) {
        const queryParams = new URLSearchParams();
        
        if (params.depth) queryParams.append('depth', params.depth);
        if (params.relation_types) {
            params.relation_types.forEach(type => {
                queryParams.append('relation_types', type);
            });
        }
        if (params.max_entities) queryParams.append('max_entities', params.max_entities);

        const endpoint = `/api/kg/entities/${entityId}/neighbors${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        return await this.request(endpoint);
    }

    /**
     * 获取实体关联的新闻
     */
    async getEntityNews(entityId, params = {}) {
        const queryParams = new URLSearchParams();
        
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        if (params.start_date) queryParams.append('start_date', params.start_date);
        if (params.end_date) queryParams.append('end_date', params.end_date);

        const endpoint = `/api/kg/entities/${entityId}/news${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
        return await this.request(endpoint);
    }
}

/**
 * API响应处理器
 * 统一处理API响应数据格式
 */
class APIResponseHandler {
    /**
     * 处理实体列表数据
     */
    static processEntityList(response) {
        return {
            items: response.items || [],
            total: response.total || 0,
            page: response.page || 1,
            page_size: response.page_size || 20,
            total_pages: response.total_pages || 0,
            has_next: response.page < response.total_pages,
            has_prev: response.page > 1
        };
    }

    /**
     * 处理实体详情数据
     */
    static processEntityDetail(response) {
        return {
            id: response.id,
            name: response.name,
            entity_type: response.entity_type,
            description: response.description,
            created_at: response.created_at,
            updated_at: response.updated_at,
            stats: response.stats || {
                relation_count: 0,
                news_count: 0,
                attribute_count: 0
            }
        };
    }

    /**
     * 处理知识图谱数据
     */
    static processKnowledgeGraph(response) {
        return {
            entities: response.entities || [],
            relations: response.relations || [],
            category: response.category || 'unknown',
            metadata: response.metadata || {},
            processing_time: response.processing_time
        };
    }

    /**
     * 处理网络数据
     */
    static processNetworkData(response) {
        return {
            nodes: response.nodes || [],
            edges: response.edges || [],
            metadata: response.metadata || {
                total_entities: 0,
                total_relations: 0,
                max_depth: 0
            }
        };
    }

    /**
     * 处理错误响应
     */
    static processError(error) {
        const errorInfo = {
            message: '未知错误',
            type: 'unknown',
            details: null,
            timestamp: new Date().toISOString()
        };

        if (error.message) {
            errorInfo.message = error.message;
        }

        if (error.endpoint) {
            errorInfo.endpoint = error.endpoint;
        }

        if (error.originalError) {
            errorInfo.originalError = error.originalError;
        }

        // 根据错误消息判断错误类型
        if (error.message.includes('timeout')) {
            errorInfo.type = 'timeout';
            errorInfo.message = '请求超时，请稍后重试';
        } else if (error.message.includes('404')) {
            errorInfo.type = 'not_found';
            errorInfo.message = '请求的资源不存在';
        } else if (error.message.includes('400')) {
            errorInfo.type = 'bad_request';
            errorInfo.message = '请求参数错误';
        } else if (error.message.includes('500')) {
            errorInfo.type = 'server_error';
            errorInfo.message = '服务器内部错误';
        }

        return errorInfo;
    }
}

/**
 * 缓存管理器
 * 提供简单的缓存机制减少API请求
 */
class APICache {
    constructor(defaultTTL = 5 * 60 * 1000) { // 默认5分钟
        this.cache = new Map();
        this.defaultTTL = defaultTTL;
    }

    /**
     * 生成缓存键
     */
    generateKey(endpoint, params = {}) {
        const sortedParams = Object.keys(params).sort().reduce((acc, key) => {
            acc[key] = params[key];
            return acc;
        }, {});
        return `${endpoint}:${JSON.stringify(sortedParams)}`;
    }

    /**
     * 获取缓存
     */
    get(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;

        if (Date.now() > cached.expiresAt) {
            this.cache.delete(key);
            return null;
        }

        return cached.data;
    }

    /**
     * 设置缓存
     */
    set(key, data, ttl = this.defaultTTL) {
        this.cache.set(key, {
            data: data,
            expiresAt: Date.now() + ttl
        });
    }

    /**
     * 清除缓存
     */
    clear() {
        this.cache.clear();
    }

    /**
     * 清除特定端点的缓存
     */
    clearEndpoint(endpoint) {
        for (const [key, value] of this.cache.entries()) {
            if (key.startsWith(endpoint)) {
                this.cache.delete(key);
            }
        }
    }
}

/**
 * 请求队列管理器
 * 防止重复请求和并发控制
 */
class RequestQueue {
    constructor() {
        this.pendingRequests = new Map();
    }

    /**
     * 执行请求，避免重复
     */
    async execute(key, requestFn) {
        // 如果已有相同请求在进行中，返回已有的Promise
        if (this.pendingRequests.has(key)) {
            return await this.pendingRequests.get(key);
        }

        // 创建新的请求Promise
        const requestPromise = requestFn().finally(() => {
            // 请求完成后从队列中移除
            this.pendingRequests.delete(key);
        });

        this.pendingRequests.set(key, requestPromise);
        return await requestPromise;
    }

    /**
     * 清除所有挂起的请求
     */
    clear() {
        this.pendingRequests.clear();
    }
}

// 创建全局API实例
const kgAPI = new KGAPI();
const apiCache = new APICache();
const requestQueue = new RequestQueue();

// 导出API相关类和实例
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        KGAPI,
        APIResponseHandler,
        APICache,
        RequestQueue,
        kgAPI,
        apiCache,
        requestQueue
    };
} else {
    // 浏览器环境，挂载到全局对象
    window.KGAPI = KGAPI;
    window.APIResponseHandler = APIResponseHandler;
    window.APICache = APICache;
    window.RequestQueue = RequestQueue;
    window.kgAPI = kgAPI;
    window.apiCache = apiCache;
    window.requestQueue = requestQueue;
}