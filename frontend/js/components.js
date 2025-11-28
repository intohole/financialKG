/**
 * 知识图谱前端UI组件库
 * 提供可复用的UI组件和工具函数
 */

/**
 * 工具函数集合
 */
class UIUtils {
    /**
     * 格式化日期
     */
    static formatDate(dateString, format = 'YYYY-MM-DD HH:mm') {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return dateString;

        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');

        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes);
    }

    /**
     * 生成实体类型颜色
     */
    static getEntityTypeColor(entityType) {
        const colors = {
            'organization': '#3498db',
            'person': '#e74c3c',
            'product': '#f39c12',
            'technology': '#9b59b6',
            'location': '#2ecc71',
            'event': '#e67e22',
            'company': '#34495e',
            'brand': '#1abc9c',
            'device': '#e91e63',
            'service': '#795548'
        };
        return colors[entityType] || '#95a5a6';
    }

    /**
     * 生成关系类型颜色
     */
    static getRelationTypeColor(relationType) {
        const colors = {
            'develops': '#3498db',
            'produces': '#2ecc71',
            'owns': '#f39c12',
            'acquired': '#e74c3c',
            'partnership': '#9b59b6',
            'competes': '#e67e22',
            'supplies': '#1abc9c',
            'uses': '#34495e',
            'creates': '#e91e63',
            'publishes': '#795548'
        };
        return colors[relationType] || '#95a5a6';
    }

    /**
     * 截断文本
     */
    static truncateText(text, maxLength = 100) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    /**
     * 创建加载指示器
     */
    static createLoader(text = '加载中...') {
        return `
            <div class="loader-container">
                <div class="loader-spinner"></div>
                <div class="loader-text">${text}</div>
            </div>
        `;
    }

    /**
     * 创建错误消息
     */
    static createErrorMessage(message, details = null) {
        return `
            <div class="error-message">
                <div class="error-icon">⚠️</div>
                <div class="error-content">
                    <div class="error-title">操作失败</div>
                    <div class="error-text">${message}</div>
                    ${details ? `<div class="error-details">${details}</div>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * 创建成功消息
     */
    static createSuccessMessage(message) {
        return `
            <div class="success-message">
                <div class="success-icon">✅</div>
                <div class="success-content">
                    <div class="success-title">操作成功</div>
                    <div class="success-text">${message}</div>
                </div>
            </div>
        `;
    }

    /**
     * 创建空状态
     */
    static createEmptyState(title, description, icon = '📭') {
        return `
            <div class="empty-state">
                <div class="empty-icon">${icon}</div>
                <div class="empty-title">${title}</div>
                <div class="empty-description">${description}</div>
            </div>
        `;
    }
}

/**
 * 实体卡片组件
 */
class EntityCard {
    constructor(entity) {
        this.entity = entity;
        this.element = this.createElement();
    }

    createElement() {
        const color = UIUtils.getEntityTypeColor(this.entity.entity_type);
        const createdAt = UIUtils.formatDate(this.entity.created_at);
        
        const card = document.createElement('div');
        card.className = 'entity-card';
        card.style.setProperty('--entity-color', color);
        
        card.innerHTML = `
            <div class="entity-card-header">
                <div class="entity-type-badge" style="background-color: ${color}">
                    ${this.entity.entity_type}
                </div>
                <div class="entity-actions">
                    <button class="entity-action-btn" data-action="view" title="查看详情">
                        👁️
                    </button>
                    <button class="entity-action-btn" data-action="network" title="查看网络">
                        🔗
                    </button>
                </div>
            </div>
            <div class="entity-card-body">
                <h3 class="entity-name">${this.entity.name}</h3>
                <p class="entity-description">${UIUtils.truncateText(this.entity.description, 120)}</p>
            </div>
            <div class="entity-card-footer">
                <div class="entity-stats">
                    <span class="entity-stat">
                        <span class="stat-icon">🔗</span>
                        <span class="stat-value">${this.entity.stats?.relation_count || 0}</span>
                    </span>
                    <span class="entity-stat">
                        <span class="stat-icon">📰</span>
                        <span class="stat-value">${this.entity.stats?.news_count || 0}</span>
                    </span>
                </div>
                <div class="entity-date">${createdAt}</div>
            </div>
        `;

        this.attachEventListeners(card);
        return card;
    }

    attachEventListeners(card) {
        const actionButtons = card.querySelectorAll('[data-action]');
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = button.dataset.action;
                this.handleAction(action);
            });
        });

        card.addEventListener('click', (e) => {
            if (!e.target.closest('.entity-actions')) {
                this.handleAction('view');
            }
        });
    }

    handleAction(action) {
        const event = new CustomEvent(`entity:${action}`, {
            detail: { entity: this.entity },
            bubbles: true
        });
        this.element.dispatchEvent(event);
    }

    render() {
        return this.element;
    }
}

/**
 * 关系卡片组件
 */
class RelationCard {
    constructor(relation) {
        this.relation = relation;
        this.element = this.createElement();
    }

    createElement() {
        const color = UIUtils.getRelationTypeColor(this.relation.relation_type);
        
        const card = document.createElement('div');
        card.className = 'relation-card';
        card.style.setProperty('--relation-color', color);
        
        card.innerHTML = `
            <div class="relation-header">
                <div class="relation-type-badge" style="background-color: ${color}">
                    ${this.relation.relation_type}
                </div>
                <div class="relation-confidence">
                    ${this.formatConfidence(this.relation.confidence)}
                </div>
            </div>
            <div class="relation-body">
                <div class="relation-entities">
                    <div class="relation-entity">
                        <div class="entity-name">${this.relation.source_entity.name}</div>
                        <div class="entity-type">${this.relation.source_entity.entity_type}</div>
                    </div>
                    <div class="relation-arrow">
                        <div class="arrow-line"></div>
                        <div class="arrow-head"></div>
                    </div>
                    <div class="relation-entity">
                        <div class="entity-name">${this.relation.target_entity.name}</div>
                        <div class="entity-type">${this.relation.target_entity.entity_type}</div>
                    </div>
                </div>
                ${this.relation.description ? `<div class="relation-description">${this.relation.description}</div>` : ''}
            </div>
            <div class="relation-footer">
                <div class="relation-date">${UIUtils.formatDate(this.relation.created_at)}</div>
                <div class="relation-actions">
                    <button class="relation-action-btn" data-action="view" title="查看详情">👁️</button>
                </div>
            </div>
        `;

        this.attachEventListeners(card);
        return card;
    }

    formatConfidence(confidence) {
        if (typeof confidence !== 'number') return '';
        const percentage = Math.round(confidence * 100);
        return `置信度: ${percentage}%`;
    }

    attachEventListeners(card) {
        const actionButton = card.querySelector('[data-action]');
        if (actionButton) {
            actionButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleAction('view');
            });
        }
    }

    handleAction(action) {
        const event = new CustomEvent(`relation:${action}`, {
            detail: { relation: this.relation },
            bubbles: true
        });
        this.element.dispatchEvent(event);
    }

    render() {
        return this.element;
    }
}

/**
 * 网络图组件
 */
class NetworkGraph {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            width: 800,
            height: 600,
            nodeRadius: 25,
            linkDistance: 150,
            chargeStrength: -300,
            ...options
        };
        this.svg = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.init();
    }

    init() {
        this.container.innerHTML = '';
        this.container.className = 'network-graph-container';
        
        this.svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        this.svg.setAttribute('width', '100%');
        this.svg.setAttribute('height', '100%');
        this.svg.setAttribute('viewBox', `0 0 ${this.options.width} ${this.options.height}`);
        this.svg.className = 'network-graph';
        
        this.container.appendChild(this.svg);
        
        // 创建SVG组
        this.linkGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        this.linkGroup.className = 'links';
        this.svg.appendChild(this.linkGroup);
        
        this.nodeGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        this.nodeGroup.className = 'nodes';
        this.svg.appendChild(this.nodeGroup);
    }

    /**
     * 设置数据并渲染
     */
    setData(data) {
        this.nodes = data.nodes.map(d => ({ ...d }));
        this.links = data.edges.map(d => ({ ...d }));
        this.render();
    }

    /**
     * 渲染网络图
     */
    render() {
        this.renderLinks();
        this.renderNodes();
        this.startSimulation();
    }

    /**
     * 渲染连线
     */
    renderLinks() {
        // 清除现有连线
        this.linkGroup.innerHTML = '';
        
        this.links.forEach(link => {
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.className = 'link-group';
            
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.className = 'link';
            line.setAttribute('stroke', UIUtils.getRelationTypeColor(link.relation_type));
            line.setAttribute('stroke-width', '2');
            
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.className = 'link-label';
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dy', '0.35em');
            text.setAttribute('font-size', '12px');
            text.setAttribute('fill', '#666');
            text.textContent = link.relation_type;
            
            g.appendChild(line);
            g.appendChild(text);
            this.linkGroup.appendChild(g);
            
            link.element = g;
            link.line = line;
            link.text = text;
        });
    }

    /**
     * 渲染节点
     */
    renderNodes() {
        // 清除现有节点
        this.nodeGroup.innerHTML = '';
        
        this.nodes.forEach(node => {
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.className = 'node-group';
            g.style.cursor = 'pointer';
            
            const color = UIUtils.getEntityTypeColor(node.entity_type);
            
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.className = 'node';
            circle.setAttribute('r', this.options.nodeRadius);
            circle.setAttribute('fill', color);
            circle.setAttribute('stroke', '#fff');
            circle.setAttribute('stroke-width', '2');
            
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.className = 'node-label';
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dy', '0.35em');
            text.setAttribute('font-size', '12px');
            text.setAttribute('fill', '#fff');
            text.setAttribute('font-weight', 'bold');
            text.textContent = UIUtils.truncateText(node.name, 10);
            
            g.appendChild(circle);
            g.appendChild(text);
            this.nodeGroup.appendChild(g);
            
            node.element = g;
            node.circle = circle;
            node.text = text;
            
            // 添加事件监听
            g.addEventListener('click', () => {
                this.handleNodeClick(node);
            });
            
            g.addEventListener('mouseenter', () => {
                this.highlightNode(node);
            });
            
            g.addEventListener('mouseleave', () => {
                this.unhighlightNode(node);
            });
        });
    }

    /**
     * 启动力导向仿真
     */
    startSimulation() {
        // 简化的力导向算法实现
        const centerX = this.options.width / 2;
        const centerY = this.options.height / 2;
        
        // 初始化节点位置
        this.nodes.forEach((node, i) => {
            if (!node.x || !node.y) {
                const angle = (i / this.nodes.length) * 2 * Math.PI;
                node.x = centerX + Math.cos(angle) * 100;
                node.y = centerY + Math.sin(angle) * 100;
            }
        });

        // 简单的迭代算法
        const iterations = 100;
        for (let iter = 0; iter < iterations; iter++) {
            this.applyForces();
            this.updatePositions();
        }
        
        this.updateVisuals();
    }

    /**
     * 应用力
     */
    applyForces() {
        // 排斥力
        for (let i = 0; i < this.nodes.length; i++) {
            for (let j = i + 1; j < this.nodes.length; j++) {
                const nodeA = this.nodes[i];
                const nodeB = this.nodes[j];
                
                const dx = nodeB.x - nodeA.x;
                const dy = nodeB.y - nodeA.y;
                const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                
                const force = this.options.chargeStrength / (distance * distance);
                const fx = (dx / distance) * force;
                const fy = (dy / distance) * force;
                
                nodeA.vx = (nodeA.vx || 0) - fx;
                nodeA.vy = (nodeA.vy || 0) - fy;
                nodeB.vx = (nodeB.vx || 0) + fx;
                nodeB.vy = (nodeB.vy || 0) + fy;
            }
        }
        
        // 吸引力（连线）
        this.links.forEach(link => {
            const source = this.nodes.find(n => n.id === link.source);
            const target = this.nodes.find(n => n.id === link.target);
            
            if (source && target) {
                const dx = target.x - source.x;
                const dy = target.y - source.y;
                const distance = Math.sqrt(dx * dx + dy * dy) || 1;
                
                const force = (distance - this.options.linkDistance) * 0.1;
                const fx = (dx / distance) * force;
                const fy = (dy / distance) * force;
                
                source.vx = (source.vx || 0) + fx;
                source.vy = (source.vy || 0) + fy;
                target.vx = (target.vx || 0) - fx;
                target.vy = (target.vy || 0) - fy;
            }
        });
        
        // 中心引力
        const centerX = this.options.width / 2;
        const centerY = this.options.height / 2;
        
        this.nodes.forEach(node => {
            const dx = centerX - node.x;
            const dy = centerY - node.y;
            const distance = Math.sqrt(dx * dx + dy * dy) || 1;
            
            const force = distance * 0.01;
            node.vx = (node.vx || 0) + (dx / distance) * force;
            node.vy = (node.vy || 0) + (dy / distance) * force;
        });
    }

    /**
     * 更新位置
     */
    updatePositions() {
        this.nodes.forEach(node => {
            node.vx = (node.vx || 0) * 0.9; // 阻尼
            node.vy = (node.vy || 0) * 0.9;
            
            node.x += node.vx || 0;
            node.y += node.vy || 0;
            
            // 边界检查
            const radius = this.options.nodeRadius;
            node.x = Math.max(radius, Math.min(this.options.width - radius, node.x));
            node.y = Math.max(radius, Math.min(this.options.height - radius, node.y));
        });
    }

    /**
     * 更新视觉效果
     */
    updateVisuals() {
        // 更新连线
        this.links.forEach(link => {
            const source = this.nodes.find(n => n.id === link.source);
            const target = this.nodes.find(n => n.id === link.target);
            
            if (source && target && link.line && link.text) {
                link.line.setAttribute('x1', source.x);
                link.line.setAttribute('y1', source.y);
                link.line.setAttribute('x2', target.x);
                link.line.setAttribute('y2', target.y);
                
                link.text.setAttribute('x', (source.x + target.x) / 2);
                link.text.setAttribute('y', (source.y + target.y) / 2);
            }
        });
        
        // 更新节点
        this.nodes.forEach(node => {
            if (node.element) {
                node.element.setAttribute('transform', `translate(${node.x}, ${node.y})`);
            }
        });
    }

    /**
     * 处理节点点击
     */
    handleNodeClick(node) {
        const event = new CustomEvent('node:click', {
            detail: { node: node },
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }

    /**
     * 高亮节点
     */
    highlightNode(node) {
        if (node.circle) {
            node.circle.setAttribute('r', this.options.nodeRadius * 1.2);
            node.circle.style.filter = 'drop-shadow(0 0 10px rgba(0,0,0,0.3))';
        }
    }

    /**
     * 取消高亮节点
     */
    unhighlightNode(node) {
        if (node.circle) {
            node.circle.setAttribute('r', this.options.nodeRadius);
            node.circle.style.filter = 'none';
        }
    }

    /**
     * 销毁组件
     */
    destroy() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

/**
 * 分页组件
 */
class Pagination {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            currentPage: 1,
            totalPages: 1,
            maxButtons: 7,
            showInfo: true,
            ...options
        };
        this.element = null;
    }

    render(data) {
        this.options.currentPage = data.page;
        this.options.totalPages = data.total_pages;
        
        this.container.innerHTML = '';
        
        const pagination = document.createElement('div');
        pagination.className = 'pagination';
        
        // 上一页按钮
        const prevBtn = this.createButton('上一页', data.has_prev, () => {
            this.goToPage(this.options.currentPage - 1);
        });
        pagination.appendChild(prevBtn);
        
        // 页码按钮
        const pageButtons = this.createPageButtons();
        pageButtons.forEach(btn => pagination.appendChild(btn));
        
        // 下一页按钮
        const nextBtn = this.createButton('下一页', data.has_next, () => {
            this.goToPage(this.options.currentPage + 1);
        });
        pagination.appendChild(nextBtn);
        
        // 信息展示
        if (this.options.showInfo) {
            const info = this.createInfo(data);
            pagination.appendChild(info);
        }
        
        this.container.appendChild(pagination);
        this.element = pagination;
    }

    createButton(text, enabled, onClick) {
        const button = document.createElement('button');
        button.className = 'pagination-btn';
        button.textContent = text;
        button.disabled = !enabled;
        
        if (enabled) {
            button.addEventListener('click', onClick);
        }
        
        return button;
    }

    createPageButtons() {
        const buttons = [];
        const { currentPage, totalPages, maxButtons } = this.options;
        
        let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(totalPages, startPage + maxButtons - 1);
        
        if (endPage - startPage + 1 < maxButtons) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }
        
        // 第一页
        if (startPage > 1) {
            buttons.push(this.createPageButton(1, currentPage === 1));
            if (startPage > 2) {
                buttons.push(this.createEllipsis());
            }
        }
        
        // 中间页码
        for (let i = startPage; i <= endPage; i++) {
            buttons.push(this.createPageButton(i, currentPage === i));
        }
        
        // 最后一页
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                buttons.push(this.createEllipsis());
            }
            buttons.push(this.createPageButton(totalPages, currentPage === totalPages));
        }
        
        return buttons;
    }

    createPageButton(page, isActive) {
        const button = document.createElement('button');
        button.className = `pagination-btn ${isActive ? 'active' : ''}`;
        button.textContent = page;
        
        if (!isActive) {
            button.addEventListener('click', () => {
                this.goToPage(page);
            });
        }
        
        return button;
    }

    createEllipsis() {
        const span = document.createElement('span');
        span.className = 'pagination-ellipsis';
        span.textContent = '...';
        return span;
    }

    createInfo(data) {
        const info = document.createElement('div');
        info.className = 'pagination-info';
        info.textContent = `第 ${data.page} 页，共 ${data.total_pages} 页，${data.total} 条记录`;
        return info;
    }

    goToPage(page) {
        const event = new CustomEvent('page:change', {
            detail: { page: page },
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }
}

/**
 * 搜索框组件
 */
class SearchBox {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            placeholder: '搜索...',
            debounceDelay: 300,
            showClearButton: true,
            ...options
        };
        this.element = null;
        this.input = null;
        this.searchTimeout = null;
        this.init();
    }

    init() {
        this.render();
    }

    render() {
        this.container.innerHTML = '';
        
        const searchBox = document.createElement('div');
        searchBox.className = 'search-box';
        
        searchBox.innerHTML = `
            <div class="search-input-container">
                <input type="text" class="search-input" placeholder="${this.options.placeholder}">
                ${this.options.showClearButton ? '<button class="search-clear-btn" style="display: none;">✕</button>' : ''}
            </div>
            <button class="search-btn">
                <span class="search-icon">🔍</span>
            </button>
        `;
        
        this.container.appendChild(searchBox);
        this.element = searchBox;
        this.input = searchBox.querySelector('.search-input');
        this.clearBtn = searchBox.querySelector('.search-clear-btn');
        this.searchBtn = searchBox.querySelector('.search-btn');
        
        this.attachEventListeners();
    }

    attachEventListeners() {
        // 输入事件
        this.input.addEventListener('input', () => {
            this.handleInput();
        });
        
        // 回车事件
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });
        
        // 清除按钮
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => {
                this.clear();
            });
        }
        
        // 搜索按钮
        this.searchBtn.addEventListener('click', () => {
            this.handleSearch();
        });
    }

    handleInput() {
        const value = this.input.value.trim();
        
        // 显示/隐藏清除按钮
        if (this.clearBtn) {
            this.clearBtn.style.display = value ? 'block' : 'none';
        }
        
        // 防抖搜索
        clearTimeout(this.searchTimeout);
        if (value) {
            this.searchTimeout = setTimeout(() => {
                this.handleSearch();
            }, this.options.debounceDelay);
        }
    }

    handleSearch() {
        const value = this.input.value.trim();
        const event = new CustomEvent('search:change', {
            detail: { query: value },
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }

    clear() {
        this.input.value = '';
        if (this.clearBtn) {
            this.clearBtn.style.display = 'none';
        }
        this.handleSearch();
    }

    getValue() {
        return this.input.value.trim();
    }

    setValue(value) {
        this.input.value = value;
        this.handleInput();
    }
}

/**
 * 标签页组件
 */
class TabPanel {
    constructor(container, tabs, options = {}) {
        this.container = container;
        this.tabs = tabs;
        this.options = {
            activeTab: 0,
            ...options
        };
        this.element = null;
        this.activeTab = this.options.activeTab;
        this.init();
    }

    init() {
        this.render();
    }

    render() {
        this.container.innerHTML = '';
        
        const tabPanel = document.createElement('div');
        tabPanel.className = 'tab-panel';
        
        // 标签头
        const tabHeaders = document.createElement('div');
        tabHeaders.className = 'tab-headers';
        
        this.tabs.forEach((tab, index) => {
            const tabHeader = document.createElement('button');
            tabHeader.className = `tab-header ${index === this.activeTab ? 'active' : ''}`;
            tabHeader.textContent = tab.title;
            tabHeader.dataset.tabIndex = index;
            
            tabHeader.addEventListener('click', () => {
                this.switchTab(index);
            });
            
            tabHeaders.appendChild(tabHeader);
        });
        
        // 标签内容
        const tabContents = document.createElement('div');
        tabContents.className = 'tab-contents';
        
        this.tabs.forEach((tab, index) => {
            const tabContent = document.createElement('div');
            tabContent.className = `tab-content ${index === this.activeTab ? 'active' : ''}`;
            tabContent.dataset.tabIndex = index;
            
            if (typeof tab.content === 'string') {
                tabContent.innerHTML = tab.content;
            } else if (tab.content instanceof HTMLElement) {
                tabContent.appendChild(tab.content);
            }
            
            tabContents.appendChild(tabContent);
        });
        
        tabPanel.appendChild(tabHeaders);
        tabPanel.appendChild(tabContents);
        
        this.container.appendChild(tabPanel);
        this.element = tabPanel;
    }

    switchTab(index) {
        if (index === this.activeTab) return;
        
        // 更新标签头
        const headers = this.element.querySelectorAll('.tab-header');
        headers.forEach((header, i) => {
            header.classList.toggle('active', i === index);
        });
        
        // 更新标签内容
        const contents = this.element.querySelectorAll('.tab-content');
        contents.forEach((content, i) => {
            content.classList.toggle('active', i === index);
        });
        
        this.activeTab = index;
        
        // 触发事件
        const event = new CustomEvent('tab:switch', {
            detail: { tabIndex: index, tab: this.tabs[index] },
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }

    getActiveTab() {
        return this.activeTab;
    }
}

/**
 * 模态框组件
 */
class Modal {
    constructor(options = {}) {
        this.options = {
            title: '模态框',
            content: '',
            showClose: true,
            showFooter: true,
            footerButtons: [],
            width: '600px',
            ...options
        };
        this.element = null;
        this.backdrop = null;
        this.init();
    }

    init() {
        this.createModal();
    }

    createModal() {
        // 创建背景
        this.backdrop = document.createElement('div');
        this.backdrop.className = 'modal-backdrop';
        
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.width = this.options.width;
        
        modal.innerHTML = `
            <div class="modal-header">
                <h3 class="modal-title">${this.options.title}</h3>
                ${this.options.showClose ? '<button class="modal-close">✕</button>' : ''}
            </div>
            <div class="modal-body">
                ${typeof this.options.content === 'string' ? this.options.content : ''}
            </div>
            ${this.options.showFooter ? this.createFooter() : ''}
        `;
        
        // 添加自定义内容
        if (this.options.content instanceof HTMLElement) {
            const modalBody = modal.querySelector('.modal-body');
            modalBody.innerHTML = '';
            modalBody.appendChild(this.options.content);
        }
        
        this.element = modal;
        
        // 添加事件监听
        this.attachEventListeners();
        
        // 添加到背景
        this.backdrop.appendChild(modal);
    }

    createFooter() {
        let footerHTML = '<div class="modal-footer">';
        
        this.options.footerButtons.forEach(button => {
            const btnClass = button.className || 'modal-btn';
            const btnText = button.text || '按钮';
            footerHTML += `<button class="${btnClass}" data-action="${button.action || ''}">${btnText}</button>`;
        });
        
        footerHTML += '</div>';
        return footerHTML;
    }

    attachEventListeners() {
        // 关闭按钮
        const closeBtn = this.element.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.close();
            });
        }
        
        // 背景点击关闭
        this.backdrop.addEventListener('click', (e) => {
            if (e.target === this.backdrop) {
                this.close();
            }
        });
        
        // 底部按钮
        const footerButtons = this.element.querySelectorAll('.modal-footer button');
        footerButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const action = e.target.dataset.action;
                this.handleButtonClick(action, e);
            });
        });
        
        // ESC键关闭
        document.addEventListener('keydown', this.handleKeyDown);
    }

    handleKeyDown = (e) => {
        if (e.key === 'Escape') {
            this.close();
        }
    }

    handleButtonClick(action, event) {
        const customEvent = new CustomEvent('modal:button:click', {
            detail: { action: action, event: event },
            bubbles: true
        });
        this.element.dispatchEvent(customEvent);
    }

    show() {
        document.body.appendChild(this.backdrop);
        document.body.classList.add('modal-open');
        
        // 触发自定义事件
        const event = new CustomEvent('modal:show', {
            detail: { modal: this },
            bubbles: true
        });
        this.element.dispatchEvent(event);
    }

    close() {
        if (this.backdrop.parentNode) {
            this.backdrop.parentNode.removeChild(this.backdrop);
        }
        document.body.classList.remove('modal-open');
        document.removeEventListener('keydown', this.handleKeyDown);
        
        // 触发自定义事件
        const event = new CustomEvent('modal:close', {
            detail: { modal: this },
            bubbles: true
        });
        this.element.dispatchEvent(event);
    }

    updateContent(content) {
        const modalBody = this.element.querySelector('.modal-body');
        if (modalBody) {
            if (typeof content === 'string') {
                modalBody.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                modalBody.innerHTML = '';
                modalBody.appendChild(content);
            }
        }
    }
}

/**
 * 通知组件
 */
class Notification {
    static show(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌'
        };
        
        notification.innerHTML = `
            <div class="notification-icon">${icons[type]}</div>
            <div class="notification-content">${message}</div>
            <button class="notification-close">✕</button>
        `;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 添加事件监听
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            this.hide(notification);
        });
        
        // 自动隐藏
        if (duration > 0) {
            setTimeout(() => {
                this.hide(notification);
            }, duration);
        }
        
        // 显示动画
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
    }

    static hide(notification) {
        notification.classList.add('hide');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
}

// 导出组件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        UIUtils,
        EntityCard,
        RelationCard,
        NetworkGraph,
        Pagination,
        SearchBox,
        TabPanel,
        Modal,
        Notification
    };
} else {
    // 浏览器环境，挂载到全局对象
    window.UIUtils = UIUtils;
    window.EntityCard = EntityCard;
    window.RelationCard = RelationCard;
    window.NetworkGraph = NetworkGraph;
    window.Pagination = Pagination;
    window.SearchBox = SearchBox;
    window.TabPanel = TabPanel;
    window.Modal = Modal;
    window.Notification = Notification;
}