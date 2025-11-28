/**
 * 知识图谱UI组件库
 * 提供通用的UI组件
 */

/**
 * 分页组件
 */
class Pagination {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            currentPage: 1,
            totalPages: 1,
            pageSize: 10,
            totalItems: 0,
            maxButtons: 5,
            showInfo: true,
            showSizeChanger: true,
            pageSizeOptions: [10, 20, 50, 100],
            ...options
        };
        this.eventListeners = new Map();
    }

    /**
     * 渲染分页组件
     */
    render() {
        this.container.innerHTML = this.createPaginationHTML();
        this.attachEventListeners();
    }

    /**
     * 创建分页HTML
     */
    createPaginationHTML() {
        const { currentPage, totalPages, pageSize, totalItems, maxButtons, showInfo, showSizeChanger, pageSizeOptions } = this.options;
        
        let html = '<div class="pagination-container">';
        
        // 显示信息
        if (showInfo && totalItems > 0) {
            const start = (currentPage - 1) * pageSize + 1;
            const end = Math.min(currentPage * pageSize, totalItems);
            html += `
                <div class="pagination-info">
                    显示 ${start}-${end} 条，共 ${totalItems} 条
                </div>
            `;
        }
        
        html += '<div class="pagination-main">';
        
        // 上一页
        html += `
            <button class="pagination-btn pagination-prev ${currentPage <= 1 ? 'disabled' : ''}" 
                    data-page="${currentPage - 1}" ${currentPage <= 1 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i>
            </button>
        `;
        
        // 页码按钮
        const pageButtons = this.generatePageButtons();
        html += pageButtons;
        
        // 下一页
        html += `
            <button class="pagination-btn pagination-next ${currentPage >= totalPages ? 'disabled' : ''}" 
                    data-page="${currentPage + 1}" ${currentPage >= totalPages ? 'disabled' : ''}>
                <i class="fas fa-chevron-right"></i>
            </button>
        `;
        
        html += '</div>';
        
        // 每页显示条数选择器
        if (showSizeChanger) {
            html += '<div class="pagination-size-changer">';
            html += '<select class="pagination-size-select">';
            pageSizeOptions.forEach(size => {
                html += `<option value="${size}" ${size === pageSize ? 'selected' : ''}>${size} 条/页</option>`;
            });
            html += '</select>';
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    }

    /**
     * 生成页码按钮
     */
    generatePageButtons() {
        const { currentPage, totalPages, maxButtons } = this.options;
        let html = '';
        
        if (totalPages <= maxButtons) {
            // 页数较少，显示所有页码
            for (let i = 1; i <= totalPages; i++) {
                html += this.createPageButton(i, i === currentPage);
            }
        } else {
            // 页数较多，显示部分页码
            const halfButtons = Math.floor(maxButtons / 2);
            let startPage = Math.max(1, currentPage - halfButtons);
            let endPage = Math.min(totalPages, startPage + maxButtons - 1);
            
            if (endPage - startPage < maxButtons - 1) {
                startPage = Math.max(1, endPage - maxButtons + 1);
            }
            
            // 第一页
            if (startPage > 1) {
                html += this.createPageButton(1, false);
                if (startPage > 2) {
                    html += '<span class="pagination-ellipsis">...</span>';
                }
            }
            
            // 中间页码
            for (let i = startPage; i <= endPage; i++) {
                html += this.createPageButton(i, i === currentPage);
            }
            
            // 最后一页
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    html += '<span class="pagination-ellipsis">...</span>';
                }
                html += this.createPageButton(totalPages, false);
            }
        }
        
        return html;
    }

    /**
     * 创建单个页码按钮
     */
    createPageButton(page, isActive) {
        return `
            <button class="pagination-btn pagination-page ${isActive ? 'active' : ''}" data-page="${page}">
                ${page}
            </button>
        `;
    }

    /**
     * 添加事件监听器
     */
    attachEventListeners() {
        // 页码按钮点击
        this.container.querySelectorAll('.pagination-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                if (btn.disabled || btn.classList.contains('disabled')) return;
                
                const page = parseInt(btn.dataset.page);
                if (page > 0 && page <= this.options.totalPages) {
                    this.goToPage(page);
                }
            });
        });
        
        // 每页显示条数改变
        const sizeSelect = this.container.querySelector('.pagination-size-select');
        if (sizeSelect) {
            sizeSelect.addEventListener('change', (e) => {
                const newSize = parseInt(e.target.value);
                this.changePageSize(newSize);
            });
        }
    }

    /**
     * 跳转到指定页
     */
    goToPage(page) {
        if (page < 1 || page > this.options.totalPages) return;
        
        this.options.currentPage = page;
        this.render();
        
        // 触发事件
        this.emit('pageChange', {
            currentPage: page,
            pageSize: this.options.pageSize,
            totalPages: this.options.totalPages,
            totalItems: this.options.totalItems
        });
    }

    /**
     * 改变每页显示条数
     */
    changePageSize(newSize) {
        const oldPageSize = this.options.pageSize;
        this.options.pageSize = newSize;
        
        // 重新计算总页数
        this.options.totalPages = Math.ceil(this.options.totalItems / newSize);
        
        // 调整当前页码
        const currentStart = (this.options.currentPage - 1) * oldPageSize;
        this.options.currentPage = Math.floor(currentStart / newSize) + 1;
        
        // 确保当前页码有效
        if (this.options.currentPage > this.options.totalPages) {
            this.options.currentPage = this.options.totalPages;
        }
        if (this.options.currentPage < 1) {
            this.options.currentPage = 1;
        }
        
        this.render();
        
        // 触发事件
        this.emit('pageSizeChange', {
            currentPage: this.options.currentPage,
            pageSize: newSize,
            totalPages: this.options.totalPages,
            totalItems: this.options.totalItems
        });
    }

    /**
     * 更新数据
     */
    updateData(data) {
        this.options = { ...this.options, ...data };
        this.render();
    }

    /**
     * 获取当前页码
     */
    getCurrentPage() {
        return this.options.currentPage;
    }

    /**
     * 获取每页显示条数
     */
    getPageSize() {
        return this.options.pageSize;
    }

    /**
     * 获取总页数
     */
    getTotalPages() {
        return this.options.totalPages;
    }

    /**
     * 获取总条数
     */
    getTotalItems() {
        return this.options.totalItems;
    }

    /**
     * 触发事件
     */
    emit(eventName, data) {
        const event = new CustomEvent(`pagination:${eventName}`, {
            detail: data,
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }

    /**
     * 销毁分页组件
     */
    destroy() {
        this.container.innerHTML = '';
        this.eventListeners.clear();
    }
}

/**
 * 搜索组件
 */
class SearchBox {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            placeholder: '请输入搜索关键词...',
            searchButton: true,
            clearButton: true,
            debounceTime: 300,
            minLength: 1,
            maxLength: 100,
            caseSensitive: false,
            ...options
        };
        this.input = null;
        this.searchButton = null;
        this.clearButton = null;
        this.eventListeners = new Map();
        this.debounceTimer = null;
    }

    /**
     * 渲染搜索组件
     */
    render() {
        this.container.innerHTML = this.createSearchHTML();
        this.attachEventListeners();
    }

    /**
     * 创建搜索HTML
     */
    createSearchHTML() {
        const { placeholder, searchButton, clearButton } = this.options;
        
        let html = '<div class="search-container">';
        html += '<div class="search-input-wrapper">';
        
        // 搜索图标
        html += '<i class="fas fa-search search-icon"></i>';
        
        // 输入框
        html += `<input type="text" class="search-input" placeholder="${placeholder}" 
                        maxlength="${this.options.maxLength}">`;
        
        // 清除按钮
        if (clearButton) {
            html += '<button class="search-clear-btn" style="display: none;">';
            html += '<i class="fas fa-times"></i>';
            html += '</button>';
        }
        
        html += '</div>';
        
        // 搜索按钮
        if (searchButton) {
            html += '<button class="search-btn">';
            html += '<i class="fas fa-search"></i>';
            html += '</button>';
        }
        
        html += '</div>';
        return html;
    }

    /**
     * 添加事件监听器
     */
    attachEventListeners() {
        this.input = this.container.querySelector('.search-input');
        this.searchButton = this.container.querySelector('.search-btn');
        this.clearButton = this.container.querySelector('.search-clear-btn');
        
        // 输入事件（防抖）
        this.input.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });
        
        // 回车搜索
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch(this.input.value);
            }
        });
        
        // 搜索按钮点击
        if (this.searchButton) {
            this.searchButton.addEventListener('click', () => {
                this.handleSearch(this.input.value);
            });
        }
        
        // 清除按钮点击
        if (this.clearButton) {
            this.clearButton.addEventListener('click', () => {
                this.clear();
            });
        }
    }

    /**
     * 处理输入
     */
    handleInput(value) {
        // 显示/隐藏清除按钮
        if (this.clearButton) {
            this.clearButton.style.display = value ? 'block' : 'none';
        }
        
        // 防抖处理
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        if (value.length >= this.options.minLength || value.length === 0) {
            this.debounceTimer = setTimeout(() => {
                this.handleSearch(value);
            }, this.options.debounceTime);
        } else if (value.length > 0 && value.length < this.options.minLength) {
            // 输入长度不足时立即清除之前的结果
            this.emit('clear', { timestamp: Date.now() });
        }
    }

    /**
     * 处理搜索
     */
    handleSearch(keyword) {
        const searchTerm = this.options.caseSensitive ? keyword : keyword.toLowerCase();
        
        // 触发搜索事件
        this.emit('search', {
            keyword: searchTerm,
            originalKeyword: keyword,
            timestamp: Date.now()
        });
    }

    /**
     * 清除搜索
     */
    clear() {
        this.input.value = '';
        if (this.clearButton) {
            this.clearButton.style.display = 'none';
        }
        
        // 触发清除事件
        this.emit('clear', {
            timestamp: Date.now()
        });
    }

    /**
     * 获取搜索关键词
     */
    getValue() {
        return this.input ? this.input.value : '';
    }

    /**
     * 设置搜索关键词
     */
    setValue(value) {
        if (this.input) {
            this.input.value = value;
            this.handleInput(value);
        }
    }

    /**
     * 聚焦输入框
     */
    focus() {
        if (this.input) {
            this.input.focus();
        }
    }

    /**
     * 禁用搜索
     */
    disable() {
        if (this.input) {
            this.input.disabled = true;
        }
        if (this.searchButton) {
            this.searchButton.disabled = true;
        }
        if (this.clearButton) {
            this.clearButton.disabled = true;
        }
    }

    /**
     * 启用搜索
     */
    enable() {
        if (this.input) {
            this.input.disabled = false;
        }
        if (this.searchButton) {
            this.searchButton.disabled = false;
        }
        if (this.clearButton) {
            this.clearButton.disabled = false;
        }
    }

    /**
     * 触发事件
     */
    emit(eventName, data) {
        const event = new CustomEvent(`search:${eventName}`, {
            detail: data,
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }

    /**
     * 销毁搜索组件
     */
    destroy() {
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        this.container.innerHTML = '';
        this.eventListeners.clear();
    }
}

/**
 * 标签页组件
 */
class TabContainer {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            tabs: [],
            activeTab: 0,
            type: 'line', // line, card, pill
            position: 'top', // top, bottom, left, right
            ...options
        };
        this.activeTab = this.options.activeTab;
        this.eventListeners = new Map();
    }

    /**
     * 渲染标签页组件
     */
    render() {
        this.container.innerHTML = this.createTabHTML();
        this.attachEventListeners();
        this.showTab(this.activeTab);
    }

    /**
     * 创建标签页HTML
     */
    createTabHTML() {
        const { tabs, type, position } = this.options;
        const containerClass = `tab-container tab-${type} tab-${position}`;
        
        let html = `<div class="${containerClass}">`;
        
        // 标签头
        html += '<div class="tab-header">';
        tabs.forEach((tab, index) => {
            const tabClass = `tab-item ${index === this.activeTab ? 'active' : ''}`;
            html += `
                <div class="${tabClass}" data-tab-index="${index}">
                    ${tab.icon ? `<i class="${tab.icon}"></i>` : ''}
                    <span class="tab-title">${tab.title}</span>
                </div>
            `;
        });
        html += '</div>';
        
        // 标签内容
        html += '<div class="tab-content">';
        tabs.forEach((tab, index) => {
            const contentClass = `tab-panel ${index === this.activeTab ? 'active' : ''}`;
            html += `<div class="${contentClass}" data-tab-index="${index}">`;
            if (tab.content) {
                html += tab.content;
            }
            html += '</div>';
        });
        html += '</div>';
        
        html += '</div>';
        return html;
    }

    /**
     * 添加事件监听器
     */
    attachEventListeners() {
        const tabItems = this.container.querySelectorAll('.tab-item');
        tabItems.forEach((item, index) => {
            item.addEventListener('click', () => {
                this.switchTab(index);
            });
        });
    }

    /**
     * 切换标签页
     */
    switchTab(index) {
        if (index === this.activeTab || index < 0 || index >= this.options.tabs.length) {
            return;
        }
        
        const oldTab = this.activeTab;
        this.activeTab = index;
        
        // 更新标签头
        const tabItems = this.container.querySelectorAll('.tab-item');
        tabItems.forEach((item, i) => {
            item.classList.toggle('active', i === index);
        });
        
        // 切换内容
        this.showTab(index);
        this.hideTab(oldTab);
        
        // 触发事件
        this.emit('tabChange', {
            activeTab: index,
            previousTab: oldTab,
            tab: this.options.tabs[index]
        });
    }

    /**
     * 显示标签页内容
     */
    showTab(index) {
        const tabPanel = this.container.querySelector(`[data-tab-index="${index}"].tab-panel`);
        if (tabPanel) {
            tabPanel.classList.add('active');
        }
    }

    /**
     * 隐藏标签页内容
     */
    hideTab(index) {
        const tabPanel = this.container.querySelector(`[data-tab-index="${index}"].tab-panel`);
        if (tabPanel) {
            tabPanel.classList.remove('active');
        }
    }

    /**
     * 获取当前活动标签页
     */
    getActiveTab() {
        return this.activeTab;
    }

    /**
     * 获取标签页数据
     */
    getTab(index) {
        return this.options.tabs[index];
    }

    /**
     * 更新标签页内容
     */
    updateTabContent(index, content) {
        const tabPanel = this.container.querySelector(`[data-tab-index="${index}"].tab-panel`);
        if (tabPanel) {
            tabPanel.innerHTML = content;
        }
        this.options.tabs[index].content = content;
    }

    /**
     * 添加新标签页
     */
    addTab(tab) {
        this.options.tabs.push(tab);
        this.render();
    }

    /**
     * 删除标签页
     */
    removeTab(index) {
        if (index < 0 || index >= this.options.tabs.length) return;
        
        this.options.tabs.splice(index, 1);
        
        // 调整当前活动标签页
        if (this.activeTab >= this.options.tabs.length) {
            this.activeTab = this.options.tabs.length - 1;
        }
        if (this.activeTab < 0) {
            this.activeTab = 0;
        }
        
        this.render();
    }

    /**
     * 触发事件
     */
    emit(eventName, data) {
        const event = new CustomEvent(`tab:${eventName}`, {
            detail: data,
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }

    /**
     * 销毁标签页组件
     */
    destroy() {
        this.container.innerHTML = '';
        this.eventListeners.clear();
    }
}

/**
 * 模态框组件
 */
class Modal {
    constructor(options = {}) {
        this.options = {
            title: '',
            content: '',
            width: 500,
            closable: true,
            maskClosable: true,
            footer: null,
            centered: true,
            ...options
        };
        this.element = null;
        this.mask = null;
        this.eventListeners = new Map();
        this.isOpen = false;
    }

    /**
     * 创建模态框
     */
    create() {
        this.createMask();
        this.createModal();
        this.attachEventListeners();
    }

    /**
     * 创建遮罩层
     */
    createMask() {
        this.mask = document.createElement('div');
        this.mask.className = 'modal-mask';
        this.mask.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 1000;
            display: none;
        `;
        document.body.appendChild(this.mask);
    }

    /**
     * 创建模态框
     */
    createModal() {
        const { title, content, width, closable, footer, centered } = this.options;
        
        this.element = document.createElement('div');
        this.element.className = 'modal-container';
        this.element.style.cssText = `
            position: fixed;
            top: ${centered ? '50%' : '100px'};
            left: 50%;
            transform: translate(-50%, ${centered ? '-50%' : '0'});
            width: ${width}px;
            max-width: 90vw;
            max-height: 90vh;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 1001;
            display: none;
            overflow: hidden;
        `;
        
        let html = '<div class="modal-content">';
        
        // 头部
        if (title) {
            html += '<div class="modal-header">';
            html += `<h3 class="modal-title">${title}</h3>`;
            if (closable) {
                html += '<button class="modal-close" aria-label="关闭">';
                html += '<i class="fas fa-times"></i>';
                html += '</button>';
            }
            html += '</div>';
        }
        
        // 内容
        html += '<div class="modal-body">';
        html += content;
        html += '</div>';
        
        // 底部
        if (footer !== false) {
            html += '<div class="modal-footer">';
            if (footer) {
                html += footer;
            } else {
                html += '<button class="btn btn-default modal-cancel">取消</button>';
                html += '<button class="btn btn-primary modal-ok">确定</button>';
            }
            html += '</div>';
        }
        
        html += '</div>';
        this.element.innerHTML = html;
        document.body.appendChild(this.element);
    }

    /**
     * 添加事件监听器
     */
    attachEventListeners() {
        // 关闭按钮
        const closeBtn = this.element.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
        
        // 遮罩层点击
        if (this.options.maskClosable) {
            this.mask.addEventListener('click', (e) => {
                if (e.target === this.mask) {
                    this.close();
                }
            });
        }
        
        // ESC键关闭
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
        
        // 默认按钮
        const cancelBtn = this.element.querySelector('.modal-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.close());
        }
        
        const okBtn = this.element.querySelector('.modal-ok');
        if (okBtn) {
            okBtn.addEventListener('click', () => {
                this.emit('ok');
                this.close();
            });
        }
    }

    /**
     * 打开模态框
     */
    open() {
        if (this.isOpen) return;
        
        this.isOpen = true;
        this.mask.style.display = 'block';
        this.element.style.display = 'block';
        
        // 防止背景滚动
        document.body.style.overflow = 'hidden';
        
        this.emit('open');
    }

    /**
     * 关闭模态框
     */
    close() {
        if (!this.isOpen) return;
        
        this.isOpen = false;
        this.mask.style.display = 'none';
        this.element.style.display = 'none';
        
        // 恢复背景滚动
        document.body.style.overflow = '';
        
        this.emit('close');
    }

    /**
     * 更新内容
     */
    updateContent(content) {
        const body = this.element.querySelector('.modal-body');
        if (body) {
            body.innerHTML = content;
        }
    }

    /**
     * 更新标题
     */
    updateTitle(title) {
        const titleElement = this.element.querySelector('.modal-title');
        if (titleElement) {
            titleElement.textContent = title;
        }
    }

    /**
     * 触发事件
     */
    emit(eventName, data = {}) {
        const event = new CustomEvent(`modal:${eventName}`, {
            detail: { modal: this, ...data },
            bubbles: true
        });
        document.dispatchEvent(event);
    }

    /**
     * 销毁模态框
     */
    destroy() {
        this.close();
        
        if (this.mask) {
            this.mask.remove();
        }
        
        if (this.element) {
            this.element.remove();
        }
        
        this.eventListeners.clear();
    }
}

/**
 * 通知组件
 */
class Notification {
    static show(message, type = 'info', duration = 3000, options = {}) {
        const notification = new NotificationComponent(message, type, duration, options);
        notification.show();
        return notification;
    }

    static success(message, duration = 3000, options = {}) {
        return this.show(message, 'success', duration, options);
    }

    static error(message, duration = 5000, options = {}) {
        return this.show(message, 'error', duration, options);
    }

    static warning(message, duration = 4000, options = {}) {
        return this.show(message, 'warning', duration, options);
    }

    static info(message, duration = 3000, options = {}) {
        return this.show(message, 'info', duration, options);
    }
}

/**
 * 通知组件内部类
 */
class NotificationComponent {
    constructor(message, type, duration, options) {
        this.message = message;
        this.type = type;
        this.duration = duration;
        this.options = {
            closable: true,
            position: 'top-right',
            showIcon: true,
            ...options
        };
        this.element = null;
        this.timer = null;
    }

    /**
     * 显示通知
     */
    show() {
        this.createElement();
        this.attachEventListeners();
        document.body.appendChild(this.element);
        
        // 添加显示动画
        requestAnimationFrame(() => {
            this.element.classList.add('show');
        });
        
        // 自动关闭
        if (this.duration > 0) {
            this.timer = setTimeout(() => {
                this.hide();
            }, this.duration);
        }
    }

    /**
     * 创建元素
     */
    createElement() {
        this.element = document.createElement('div');
        this.element.className = `notification notification-${this.type} notification-${this.options.position}`;
        
        let html = '<div class="notification-content">';
        
        // 图标
        if (this.options.showIcon) {
            const iconClass = this.getIconClass();
            html += `<i class="${iconClass} notification-icon"></i>`;
        }
        
        // 消息
        html += '<div class="notification-message">';
        html += this.message;
        html += '</div>';
        
        // 关闭按钮
        if (this.options.closable) {
            html += '<button class="notification-close" aria-label="关闭">';
            html += '<i class="fas fa-times"></i>';
            html += '</button>';
        }
        
        html += '</div>';
        this.element.innerHTML = html;
    }

    /**
     * 获取图标类
     */
    getIconClass() {
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return iconMap[this.type] || 'fas fa-info-circle';
    }

    /**
     * 添加事件监听器
     */
    attachEventListeners() {
        // 关闭按钮
        const closeBtn = this.element.querySelector('.notification-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.hide();
            });
        }
        
        // 鼠标悬停时暂停自动关闭
        if (this.duration > 0) {
            this.element.addEventListener('mouseenter', () => {
                if (this.timer) {
                    clearTimeout(this.timer);
                }
            });
            
            this.element.addEventListener('mouseleave', () => {
                this.timer = setTimeout(() => {
                    this.hide();
                }, this.duration);
            });
        }
    }

    /**
     * 隐藏通知
     */
    hide() {
        this.element.classList.remove('show');
        this.element.classList.add('hide');
        
        // 动画结束后移除元素
        this.element.addEventListener('transitionend', () => {
            this.destroy();
        });
        
        // 如果动画不支持，直接移除
        setTimeout(() => {
            this.destroy();
        }, 300);
    }

    /**
     * 销毁通知
     */
    destroy() {
        if (this.timer) {
            clearTimeout(this.timer);
        }
        
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

// 导出UI组件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        Pagination, 
        SearchBox, 
        TabContainer, 
        Modal, 
        Notification 
    };
} else {
    // 浏览器环境，挂载到全局对象
    window.Pagination = Pagination;
    window.SearchBox = SearchBox;
    window.TabContainer = TabContainer;
    window.Modal = Modal;
    window.Notification = Notification;
}