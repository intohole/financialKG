/**
 * 知识图谱前端主应用
 * 整合所有功能模块，提供统一的用户界面
 */

class KGApplication {
    constructor() {
        this.currentPage = 'content';
        this.entitiesPage = 1;
        this.relationsPage = 1;
        this.searchQuery = '';
        this.selectedEntity = null;
        this.networkGraph = null;
        this.isLoading = false;
        
        this.init();
    }

    /**
     * 初始化应用
     */
    async init() {
        try {
            this.bindEvents();
            this.showContentPanel();
            this.updateNavigation();
            
            console.log('知识图谱应用初始化完成');
        } catch (error) {
            console.error('应用初始化失败:', error);
            this.showError('应用初始化失败，请刷新页面重试');
        }
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        // 导航事件
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = item.dataset.tab;
                this.switchPanel(tab);
            });
        });

        // 内容处理面板事件
        const processBtn = document.getElementById('process-content-btn');
        if (processBtn) {
            processBtn.addEventListener('click', () => {
                this.processContent();
            });
        }

        // 实体管理面板事件
        const entitySearchBox = document.getElementById('entity-search');
        if (entitySearchBox) {
            entitySearchBox.addEventListener('search:change', (e) => {
                this.searchQuery = e.detail.query;
                this.entitiesPage = 1;
                this.loadEntities();
            });
        }

        // 网络分析面板事件
        const networkSearchBox = document.getElementById('network-search');
        if (networkSearchBox) {
            networkSearchBox.addEventListener('search:change', (e) => {
                this.searchEntityForNetwork(e.detail.query);
            });
        }

        // 全局事件监听
        document.addEventListener('entity:view', (e) => {
            this.showEntityDetail(e.detail.entity);
        });

        document.addEventListener('entity:network', (e) => {
            this.showEntityNetwork(e.detail.entity);
        });

        document.addEventListener('node:click', (e) => {
            this.handleNodeClick(e.detail.node);
        });

        // 分页事件
        document.addEventListener('page:change', (e) => {
            const panel = e.target.closest('.tab-panel');
            if (panel) {
                if (panel.id === 'entities-tab') {
                    this.entitiesPage = e.detail.page;
                    this.loadEntities();
                } else if (panel.id === 'relations-tab') {
                    this.relationsPage = e.detail.page;
                    this.loadRelations();
                }
            }
        });
    }

    /**
     * 切换面板
     */
    switchPanel(panel) {
        if (this.currentPage === panel) return;

        this.currentPage = panel;
        this.updateNavigation();

        // 隐藏所有面板
        document.querySelectorAll('.tab-panel').forEach(p => {
            p.classList.remove('active');
        });

        // 显示目标面板
        const targetPanel = document.getElementById(`${panel}-tab`);
        if (targetPanel) {
            targetPanel.classList.add('active');
            
            // 加载对应数据
            switch (panel) {
                case 'content':
                    this.showContentPanel();
                    break;
                case 'entities':
                    this.showEntitiesPanel();
                    break;
                case 'relations':
                    this.showRelationsPanel();
                    break;
                case 'network':
                    this.showNetworkPanel();
                    break;
            }
        }
    }

    /**
     * 更新导航状态
     */
    updateNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.tab === this.currentPage);
        });
    }

    /**
     * 显示内容处理面板
     */
    showContentPanel() {
        const resultsContainer = document.getElementById('content-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = UIUtils.createEmptyState(
                '内容处理',
                '输入文本内容，系统将自动提取实体和关系，构建知识图谱',
                '📝'
            );
        }
    }

    /**
     * 显示实体管理面板
     */
    async showEntitiesPanel() {
        if (this.currentPage === 'entities') {
            await this.loadEntities();
        }
    }

    /**
     * 显示关系管理面板
     */
    async showRelationsPanel() {
        if (this.currentPage === 'relations') {
            await this.loadRelations();
        }
    }

    /**
     * 显示网络分析面板
     */
    showNetworkPanel() {
        if (this.currentPage === 'network') {
            this.initNetworkGraph();
        }
    }

    /**
     * 处理内容
     */
    async processContent() {
        const contentInput = document.getElementById('content-input');
        const resultsContainer = document.getElementById('content-results');
        
        if (!contentInput || !resultsContainer) return;

        const content = contentInput.value.trim();
        if (!content) {
            this.showWarning('请输入要处理的内容');
            return;
        }

        this.setLoading(true);
        resultsContainer.innerHTML = UIUtils.createLoader('正在处理内容，提取实体和关系...');

        try {
            const startTime = Date.now();
            const response = await kgAPI.processContent(content);
            const processingTime = Date.now() - startTime;

            console.log('内容处理结果:', response);
            
            this.displayContentResults(response, processingTime);
            this.showSuccess(`内容处理完成，耗时 ${processingTime}ms`);
            
        } catch (error) {
            console.error('内容处理失败:', error);
            resultsContainer.innerHTML = UIUtils.createErrorMessage(
                '内容处理失败',
                error.message || '请检查网络连接或稍后重试'
            );
            this.showError('内容处理失败');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * 显示内容处理结果
     */
    displayContentResults(data, processingTime) {
        const resultsContainer = document.getElementById('content-results');
        if (!resultsContainer) return;

        const processedData = APIResponseHandler.processKnowledgeGraph(data);
        
        resultsContainer.innerHTML = `
            <div class="content-results">
                <div class="results-header">
                    <h3>处理结果</h3>
                    <div class="processing-info">
                        <span class="processing-time">处理时间: ${processingTime}ms</span>
                        <span class="category-badge">${processedData.category}</span>
                    </div>
                </div>
                
                <div class="results-stats">
                    <div class="stat-card">
                        <div class="stat-number">${processedData.entities.length}</div>
                        <div class="stat-label">实体</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${processedData.relations.length}</div>
                        <div class="stat-label">关系</div>
                    </div>
                </div>

                <div class="results-content">
                    <div class="entities-section">
                        <h4>提取的实体</h4>
                        <div class="entities-grid">
                            ${processedData.entities.map(entity => {
                                const color = UIUtils.getEntityTypeColor(entity.entity_type);
                                return `
                                    <div class="entity-mini-card" style="--entity-color: ${color}">
                                        <div class="entity-type-badge">${entity.entity_type}</div>
                                        <div class="entity-name">${entity.name}</div>
                                        <div class="entity-description">${UIUtils.truncateText(entity.description, 50)}</div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>

                    <div class="relations-section">
                        <h4>提取的关系</h4>
                        <div class="relations-list">
                            ${processedData.relations.map(relation => {
                                const color = UIUtils.getRelationTypeColor(relation.relation_type);
                                return `
                                    <div class="relation-mini-item" style="--relation-color: ${color}">
                                        <div class="relation-type">${relation.relation_type}</div>
                                        <div class="relation-entities">
                                            ${relation.source_entity.name} → ${relation.target_entity.name}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 加载实体列表
     */
    async loadEntities() {
        const entitiesContainer = document.getElementById('entities-list');
        const paginationContainer = document.getElementById('entities-pagination');
        
        if (!entitiesContainer || !paginationContainer) return;

        entitiesContainer.innerHTML = UIUtils.createLoader('正在加载实体列表...');

        try {
            const params = {
                page: this.entitiesPage,
                page_size: 12,
                search: this.searchQuery
            };

            const response = await kgAPI.getEntities(params);
            const processedData = APIResponseHandler.processEntityList(response);
            
            this.displayEntities(processedData, entitiesContainer);
            
            // 渲染分页
            const pagination = new Pagination(paginationContainer);
            pagination.render(processedData);
            
        } catch (error) {
            console.error('加载实体失败:', error);
            entitiesContainer.innerHTML = UIUtils.createErrorMessage(
                '加载实体失败',
                error.message || '请检查网络连接或稍后重试'
            );
        }
    }

    /**
     * 显示实体列表
     */
    displayEntities(data, container) {
        if (data.items.length === 0) {
            container.innerHTML = UIUtils.createEmptyState(
                '未找到实体',
                this.searchQuery ? `未找到包含 "${this.searchQuery}" 的实体` : '暂无实体数据',
                '🔍'
            );
            return;
        }

        const entitiesGrid = document.createElement('div');
        entitiesGrid.className = 'entities-grid';

        data.items.forEach(entityData => {
            const entityCard = new EntityCard(entityData);
            entitiesGrid.appendChild(entityCard.render());
        });

        container.innerHTML = '';
        container.appendChild(entitiesGrid);
    }

    /**
     * 加载关系列表
     */
    async loadRelations() {
        const relationsContainer = document.getElementById('relations-list');
        const paginationContainer = document.getElementById('relations-pagination');
        
        if (!relationsContainer || !paginationContainer) return;

        relationsContainer.innerHTML = UIUtils.createLoader('正在加载关系列表...');

        try {
            const params = {
                page: this.relationsPage,
                page_size: 10
            };

            const response = await kgAPI.getRelations(params);
            
            this.displayRelations(response.items, relationsContainer);
            
            // 渲染分页
            const pagination = new Pagination(paginationContainer);
            pagination.render(response);
            
        } catch (error) {
            console.error('加载关系失败:', error);
            relationsContainer.innerHTML = UIUtils.createErrorMessage(
                '加载关系失败',
                error.message || '请检查网络连接或稍后重试'
            );
        }
    }

    /**
     * 显示关系列表
     */
    displayRelations(relations, container) {
        if (relations.length === 0) {
            container.innerHTML = UIUtils.createEmptyState(
                '未找到关系',
                '暂无关系数据',
                '🔗'
            );
            return;
        }

        const relationsList = document.createElement('div');
        relationsList.className = 'relations-list';

        relations.forEach(relationData => {
            const relationCard = new RelationCard(relationData);
            relationsList.appendChild(relationCard.render());
        });

        container.innerHTML = '';
        container.appendChild(relationsList);
    }

    /**
     * 初始化网络图
     */
    initNetworkGraph() {
        const networkContainer = document.getElementById('network-container');
        if (!networkContainer) return;

        // 创建搜索框
        const searchContainer = document.createElement('div');
        searchContainer.className = 'network-search-container';
        searchContainer.innerHTML = `
            <div class="search-box" id="network-search-box">
                <div class="search-input-container">
                    <input type="text" class="search-input" placeholder="搜索实体查看其关系网络...">
                    <button class="search-clear-btn" style="display: none;">✕</button>
                </div>
                <button class="search-btn">
                    <span class="search-icon">🔍</span>
                </button>
            </div>
        `;

        // 创建网络图容器
        const graphContainer = document.createElement('div');
        graphContainer.className = 'network-graph-wrapper';
        graphContainer.id = 'network-graph';

        networkContainer.innerHTML = '';
        networkContainer.appendChild(searchContainer);
        networkContainer.appendChild(graphContainer);

        // 初始化网络图组件
        this.networkGraph = new NetworkGraph(graphContainer, {
            width: 800,
            height: 600
        });

        // 绑定搜索事件
        const searchInput = searchContainer.querySelector('.search-input');
        const searchBtn = searchContainer.querySelector('.search-btn');
        const clearBtn = searchContainer.querySelector('.search-clear-btn');

        let searchTimeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            const query = searchInput.value.trim();
            clearBtn.style.display = query ? 'block' : 'none';
            
            if (query) {
                searchTimeout = setTimeout(() => {
                    this.searchEntityForNetwork(query);
                }, 500);
            }
        });

        searchBtn.addEventListener('click', () => {
            const query = searchInput.value.trim();
            if (query) {
                this.searchEntityForNetwork(query);
            }
        });

        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            clearBtn.style.display = 'none';
            this.clearNetworkGraph();
        });

        // 显示初始状态
        this.clearNetworkGraph();
    }

    /**
     * 搜索实体用于网络分析
     */
    async searchEntityForNetwork(query) {
        if (!query || !this.networkGraph) return;

        try {
            // 先搜索实体
            const searchResponse = await kgAPI.getEntities({
                search: query,
                page: 1,
                page_size: 5
            });

            if (searchResponse.items.length === 0) {
                this.showWarning(`未找到包含 "${query}" 的实体`);
                return;
            }

            // 获取第一个实体的网络数据
            const entity = searchResponse.items[0];
            await this.loadEntityNetwork(entity.id);
            
        } catch (error) {
            console.error('搜索实体网络失败:', error);
            this.showError('搜索实体网络失败');
        }
    }

    /**
     * 加载实体网络数据
     */
    async loadEntityNetwork(entityId) {
        if (!this.networkGraph) return;

        const networkContainer = document.getElementById('network-container');
        const graphWrapper = document.querySelector('.network-graph-wrapper');
        
        if (graphWrapper) {
            graphWrapper.innerHTML = UIUtils.createLoader('正在加载网络数据...');
        }

        try {
            const response = await kgAPI.getEntityNeighbors(entityId, {
                depth: 2,
                max_entities: 20
            });

            const processedData = APIResponseHandler.processNetworkData(response);
            
            if (processedData.nodes.length === 0) {
                if (graphWrapper) {
                    graphWrapper.innerHTML = UIUtils.createEmptyState(
                        '未找到相关实体',
                        '该实体暂无关联的其他实体',
                        '🔍'
                    );
                }
                return;
            }

            this.networkGraph.setData(processedData);
            
        } catch (error) {
            console.error('加载网络数据失败:', error);
            if (graphWrapper) {
                graphWrapper.innerHTML = UIUtils.createErrorMessage(
                    '加载网络数据失败',
                    error.message || '请检查网络连接或稍后重试'
                );
            }
        }
    }

    /**
     * 清空网络图
     */
    clearNetworkGraph() {
        if (this.networkGraph) {
            this.networkGraph.destroy();
            this.initNetworkGraph();
        }
    }

    /**
     * 显示实体详情
     */
    async showEntityDetail(entity) {
        const modal = new Modal({
            title: '实体详情',
            width: '800px',
            content: UIUtils.createLoader('正在加载实体详情...'),
            footerButtons: [
                { text: '查看网络', action: 'network', className: 'modal-btn modal-btn-primary' },
                { text: '关闭', action: 'close', className: 'modal-btn' }
            ]
        });

        modal.show();

        try {
            const detail = await kgAPI.getEntityDetail(entity.id);
            const processedDetail = APIResponseHandler.processEntityDetail(detail);
            
            const detailContent = this.createEntityDetailContent(processedDetail);
            modal.updateContent(detailContent);
            
        } catch (error) {
            console.error('加载实体详情失败:', error);
            modal.updateContent(UIUtils.createErrorMessage(
                '加载实体详情失败',
                error.message || '请检查网络连接或稍后重试'
            ));
        }

        // 绑定模态框事件
        modal.element.addEventListener('modal:button:click', (e) => {
            if (e.detail.action === 'network') {
                modal.close();
                this.switchPanel('network');
                setTimeout(() => {
                    this.searchEntityForNetwork(entity.name);
                }, 300);
            } else if (e.detail.action === 'close') {
                modal.close();
            }
        });
    }

    /**
     * 创建实体详情内容
     */
    createEntityDetailContent(entity) {
        const color = UIUtils.getEntityTypeColor(entity.entity_type);
        const createdAt = UIUtils.formatDate(entity.created_at);
        const updatedAt = UIUtils.formatDate(entity.updated_at);

        return `
            <div class="entity-detail">
                <div class="entity-detail-header">
                    <div class="entity-type-badge" style="background-color: ${color}">
                        ${entity.entity_type}
                    </div>
                    <div class="entity-name">${entity.name}</div>
                </div>
                
                <div class="entity-detail-body">
                    <div class="entity-description">
                        <h4>描述</h4>
                        <p>${entity.description || '暂无描述'}</p>
                    </div>
                    
                    <div class="entity-stats">
                        <div class="stat-item">
                            <span class="stat-label">关系数量:</span>
                            <span class="stat-value">${entity.stats.relation_count}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">新闻数量:</span>
                            <span class="stat-value">${entity.stats.news_count}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">属性数量:</span>
                            <span class="stat-value">${entity.stats.attribute_count}</span>
                        </div>
                    </div>
                    
                    <div class="entity-timestamps">
                        <div class="timestamp">
                            <span class="timestamp-label">创建时间:</span>
                            <span class="timestamp-value">${createdAt}</span>
                        </div>
                        <div class="timestamp">
                            <span class="timestamp-label">更新时间:</span>
                            <span class="timestamp-value">${updatedAt}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 显示实体网络
     */
    showEntityNetwork(entity) {
        this.switchPanel('network');
        setTimeout(() => {
            this.searchEntityForNetwork(entity.name);
        }, 300);
    }

    /**
     * 处理节点点击
     */
    handleNodeClick(node) {
        // 查找对应的实体数据
        const entityData = {
            id: node.id,
            name: node.name,
            entity_type: node.entity_type,
            description: node.description || '',
            stats: node.stats || { relation_count: 0, news_count: 0, attribute_count: 0 },
            created_at: node.created_at || new Date().toISOString(),
            updated_at: node.updated_at || new Date().toISOString()
        };

        this.showEntityDetail(entityData);
    }

    /**
     * 设置加载状态
     */
    setLoading(loading) {
        this.isLoading = loading;
        const processBtn = document.getElementById('process-content-btn');
        if (processBtn) {
            processBtn.disabled = loading;
            processBtn.textContent = loading ? '处理中...' : '处理内容';
        }
    }

    /**
     * 显示成功消息
     */
    showSuccess(message) {
        Notification.show(message, 'success', 3000);
    }

    /**
     * 显示错误消息
     */
    showError(message) {
        Notification.show(message, 'error', 5000);
    }

    /**
     * 显示警告消息
     */
    showWarning(message) {
        Notification.show(message, 'warning', 4000);
    }

    /**
     * 显示信息消息
     */
    showInfo(message) {
        Notification.show(message, 'info', 3000);
    }
}

/**
 * 应用初始化
 * 等待DOM加载完成后启动应用
 */
document.addEventListener('DOMContentLoaded', () => {
    // 检查必要的依赖
    if (typeof KGAPI === 'undefined') {
        console.error('KGAPI 未加载，请检查 api.js 文件');
        return;
    }

    if (typeof UIUtils === 'undefined') {
        console.error('UIUtils 未加载，请检查 components.js 文件');
        return;
    }

    // 创建全局应用实例
    window.kgApp = new KGApplication();
    
    console.log('知识图谱前端应用已启动');
});

/**
 * 全局错误处理
 */
window.addEventListener('error', (event) => {
    console.error('全局错误:', event.error);
    if (window.kgApp) {
        window.kgApp.showError('发生未知错误，请刷新页面重试');
    }
});

/**
 * 未处理的Promise拒绝
 */
window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason);
    if (window.kgApp) {
        window.kgApp.showError('操作失败，请稍后重试');
    }
});