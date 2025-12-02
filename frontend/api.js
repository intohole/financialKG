/**
 * 知识图谱API封装
 * 
 * 统一封装所有后端API调用，提供简洁的前端调用接口
 * 依赖于config.js中的API_CONFIG和apiRequest函数
 */

// 确保config.js已加载
if (typeof API_CONFIG === 'undefined' || typeof apiRequest === 'undefined') {
    throw new Error('config.js must be loaded before api.js');
}

// API封装对象
const KGAPI = {
    // ==================== 内容处理API ====================
    /**
     * 处理文本内容并构建知识图谱
     * @param {string} content - 要处理的文本内容
     * @returns {Promise<Object>} 构建的知识图谱
     */
    processContent: async (content) => {
        return await apiRequest('/process-content', {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    },

    // ==================== 实体相关API ====================
    /**
     * 获取实体列表
     * @param {Object} params - 查询参数
     * @param {number} params.page - 页码，从1开始
     * @param {number} params.page_size - 每页数量
     * @param {string|null} params.search - 搜索关键词
     * @param {string|null} params.entity_type - 实体类型过滤
     * @param {string} params.sort_by - 排序字段
     * @param {string} params.sort_order - 排序方向（asc/desc）
     * @returns {Promise<Object>} 分页的实体列表
     */
    getEntities: async (params = {}) => {
        const defaultParams = {
            page: 1,
            page_size: 20,
            search: null,
            entity_type: null,
            sort_by: 'created_at',
            sort_order: 'desc'
        };
        
        const finalParams = { ...defaultParams, ...params };
        const queryParams = new URLSearchParams();
        
        // 只添加非null、非undefined的参数
        Object.entries(finalParams).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                queryParams.append(key, value);
            }
        });
        
        const queryString = queryParams.toString();
        return await apiRequest(`/entities?${queryString}`);
    },

    /**
     * 获取实体详细信息
     * @param {number} entity_id - 实体ID
     * @returns {Promise<Object>} 实体详细信息
     */
    getEntityDetail: async (entity_id) => {
        return await apiRequest(`/entities/${entity_id}`);
    },

    /**
     * 获取实体邻居网络
     * @param {number} entity_id - 实体ID
     * @param {Object} params - 查询参数
     * @param {number} params.depth - 遍历深度
     * @param {Array<string>|null} params.relation_types - 关系类型过滤
     * @param {number} params.max_entities - 最大实体数量
     * @returns {Promise<Object>} 实体邻居网络数据
     */
    getEntityNeighbors: async (entity_id, params = {}) => {
        const defaultParams = {
            depth: 2,
            relation_types: null,
            max_entities: 100
        };
        
        const finalParams = { ...defaultParams, ...params };
        const queryParams = new URLSearchParams();
        
        // 只添加非null、非undefined的参数
        Object.entries(finalParams).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                queryParams.append(key, value);
            }
        });
        
        const queryString = queryParams.toString();
        return await apiRequest(`/entities/${entity_id}/neighbors?${queryString}`);
    },

    /**
     * 获取实体关联的新闻
     * @param {number} entity_id - 实体ID
     * @param {Object} params - 查询参数
     * @param {number} params.page - 页码
     * @param {number} params.page_size - 每页数量
     * @param {string|null} params.start_date - 开始日期
     * @param {string|null} params.end_date - 结束日期
     * @returns {Promise<Object>} 分页的新闻列表
     */
    getEntityNews: async (entity_id, params = {}) => {
        const defaultParams = {
            page: 1,
            page_size: 10,
            start_date: null,
            end_date: null
        };
        
        const finalParams = { ...defaultParams, ...params };
        const queryParams = new URLSearchParams();
        
        // 只添加非null、非undefined的参数
        Object.entries(finalParams).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                queryParams.append(key, value);
            }
        });
        
        const queryString = queryParams.toString();
        return await apiRequest(`/entities/${entity_id}/news?${queryString}`);
    },

    /**
     * 获取多个实体的共同新闻
     * @param {Array<number>} entity_ids - 实体ID列表
     * @param {Object} params - 查询参数
     * @param {number} params.page - 页码
     * @param {number} params.page_size - 每页数量
     * @returns {Promise<Object>} 分页的共同新闻列表
     */
    getCommonNewsForEntities: async (entity_ids, params = {}) => {
        const defaultParams = {
            page: 1,
            page_size: 10
        };
        
        const finalParams = { ...defaultParams, ...params, entity_ids };
        const queryParams = new URLSearchParams();
        
        // 只添加非null、非undefined的参数
        Object.entries(finalParams).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                queryParams.append(key, value);
            }
        });
        
        const queryString = queryParams.toString();
        return await apiRequest(`/entities/common-news?${queryString}`);
    },

    // ==================== 关系相关API ====================
    /**
     * 获取关系列表
     * @param {Object} params - 查询参数
     * @param {number} params.page - 页码
     * @param {number} params.page_size - 每页数量
     * @param {number|null} params.entity_id - 实体ID过滤
     * @param {string|null} params.relation_type - 关系类型过滤
     * @param {string|null} params.search - 搜索关键词
     * @returns {Promise<Object>} 分页的关系列表
     */
    getRelations: async (params = {}) => {
        const defaultParams = {
            page: 1,
            page_size: 20,
            entity_id: null,
            relation_type: null,
            search: null
        };
        
        const finalParams = { ...defaultParams, ...params };
        const queryParams = new URLSearchParams();
        
        // 只添加非null、非undefined的参数
        Object.entries(finalParams).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                queryParams.append(key, value);
            }
        });
        
        const queryString = queryParams.toString();
        return await apiRequest(`/relations?${queryString}`);
    },

    // ==================== 新闻相关API ====================
    /**
     * 获取新闻列表
     * @param {Object} params - 查询参数
     * @param {number} params.page - 页码
     * @param {number} params.page_size - 每页数量
     * @param {string|null} params.search - 搜索关键词
     * @param {string|null} params.source - 新闻来源过滤
     * @param {string|null} params.start_date - 开始日期
     * @param {string|null} params.end_date - 结束日期
     * @param {string} params.sort_by - 排序字段
     * @param {string} params.sort_order - 排序方向
     * @returns {Promise<Object>} 分页的新闻列表
     */
    getNewsList: async (params = {}) => {
        const defaultParams = {
            page: 1,
            page_size: 20,
            search: null,
            source: null,
            start_date: null,
            end_date: null,
            sort_by: 'publish_time',
            sort_order: 'desc'
        };
        
        const finalParams = { ...defaultParams, ...params };
        const queryParams = new URLSearchParams();
        
        // 只添加非null、非undefined的参数
        Object.entries(finalParams).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                queryParams.append(key, value);
            }
        });
        
        const queryString = queryParams.toString();
        return await apiRequest(`/news?${queryString}`);
    },

    /**
     * 搜索新闻（向量搜索）
     * @param {string} query - 搜索查询词
     * @param {Object} params - 查询参数
     * @param {number} params.top_k - 返回结果数量
     * @param {string|null} params.start_date - 开始日期
     * @param {string|null} params.end_date - 结束日期
     * @returns {Promise<Object>} 搜索结果
     */
    searchNews: async (query, params = {}) => {
        const defaultParams = {
            top_k: 20,
            start_date: null,
            end_date: null
        };
        
        const finalParams = { ...defaultParams, ...params, query };
        const queryParams = new URLSearchParams();
        
        // 只添加非null、非undefined的参数
        Object.entries(finalParams).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                queryParams.append(key, value);
            }
        });
        
        const queryString = queryParams.toString();
        return await apiRequest(`/news/search?${queryString}`);
    },

    /**
     * 获取新闻相关的实体
     * @param {number} news_id - 新闻ID
     * @param {Object} params - 查询参数
     * @param {string|null} params.entity_type - 实体类型过滤
     * @param {number} params.limit - 返回实体数量限制
     * @returns {Promise<Object>} 新闻相关的实体列表
     */
    getNewsEntities: async (news_id, params = {}) => {
        const defaultParams = {
            entity_type: null,
            limit: 50
        };
        
        const finalParams = { ...defaultParams, ...params };
        const queryParams = new URLSearchParams();
        
        // 只添加非null、非undefined的参数
        Object.entries(finalParams).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                queryParams.append(key, value);
            }
        });
        
        const queryString = queryParams.toString();
        return await apiRequest(`/news/${news_id}/entities?${queryString}`);
    },

    // ==================== 统计分析API ====================
    /**
     * 获取知识图谱概览统计
     * @returns {Promise<Object>} 统计信息
     */
    getStatistics: async () => {
        return await apiRequest('/statistics/overview');
    }
};

// 导出到全局
window.KGAPI = KGAPI;

// 导出为ES模块（如果支持）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KGAPI;
}
