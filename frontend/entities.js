/**
 * 实体管理页面功能模块
 * 负责实体搜索、列表展示、分页和详情查看
 */

// 全局状态管理
const state = {
    currentPage: 1,
    pageSize: 10,
    totalItems: 0,
    entities: [],
    selectedEntity: null,
    loading: false
};

// 页面初始化
function initializePage() {
    if (typeof window.KGAPI === 'object') {
        loadEntities();
        setupEventListeners();
    } else {
        setTimeout(initializePage, 100);
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 搜索按钮点击事件
    const searchBtn = document.querySelector('.btn-primary');
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            state.currentPage = 1;
            loadEntities();
        });
    }

    // 重置按钮点击事件
    const resetBtn = document.querySelector('.btn-secondary');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            const searchInput = document.getElementById('searchKeyword');
            const typeSelect = document.getElementById('entityType');
            if (searchInput) searchInput.value = '';
            if (typeSelect) typeSelect.value = '';
            state.currentPage = 1;
            loadEntities();
        });
    }
    
    // 搜索框回车事件
    const searchInput = document.getElementById('searchKeyword');
    if (searchInput) {
        searchInput.addEventListener('keypress', handleEnter);
    }
}

// 加载实体列表
async function loadEntities() {
    if (state.loading) return;
    
    try {
        state.loading = true;
        showLoading();
        
        // 获取搜索参数
        const searchInput = document.getElementById('searchKeyword');
        const typeSelect = document.getElementById('entityType');
        
        const response = await window.KGAPI.getEntities({
            page: state.currentPage,
            page_size: state.pageSize,
            search: searchInput && searchInput.value ? searchInput.value : null,
            entity_type: typeSelect && typeSelect.value ? typeSelect.value : null
        });
        
        state.entities = response.items || [];
        state.totalItems = response.total || 0;
        
        renderEntities();
        renderPagination();
        
    } catch (error) {
        // 只在开发环境显示日志
        console.error('加载实体失败:', error);
        showError('加载实体失败: ' + error.message, 'error');
    } finally {
        state.loading = false;
        hideLoading();
    }
}

// 渲染实体列表
function renderEntities() {
    const container = document.getElementById('entities-container');
    
    if (state.entities.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📊</div>
                <div class="empty-text">暂无实体数据</div>
                <div class="empty-desc">您可以先添加一些实体数据</div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="entities-grid">
            ${state.entities.map(entity => `
                <div class="entity-card" onclick="showEntityDetails('${entity.id}')">
                    <div class="entity-header">
                        <div class="entity-name">${escapeHtml(entity.name)}</div>
                        <span class="entity-type ${getEntityTypeClass(entity.type)}">${getEntityTypeLabel(entity.type)}</span>
                    </div>
                    <div class="entity-description">${escapeHtml(entity.description || '暂无描述')}</div>
                    <div class="entity-meta">
                        <div class="entity-time">创建于 ${formatDate(entity.created_at)}</div>
                        <div class="entity-actions">
                            <button class="btn btn-sm btn-outline" onclick="event.stopPropagation(); showEntityNews('${entity.id}')">查看新闻</button>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// 渲染分页
function renderPagination() {
    const container = document.getElementById('pagination-container');
    const totalPages = Math.ceil(state.totalItems / state.pageSize);
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '<div class="pagination">';
    
    // 上一页
    if (state.currentPage > 1) {
        html += `<button class="page-btn" onclick="goToPage(${state.currentPage - 1})">上一页</button>`;
    }
    
    // 页码
    const startPage = Math.max(1, state.currentPage - 2);
    const endPage = Math.min(totalPages, state.currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === state.currentPage ? 'active' : '';
        html += `<button class="page-btn ${activeClass}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    // 下一页
    if (state.currentPage < totalPages) {
        html += `<button class="page-btn" onclick="goToPage(${state.currentPage + 1})">下一页</button>`;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// 跳转到指定页面
function goToPage(page) {
    state.currentPage = page;
    loadEntities();
}

// 显示实体详情
async function showEntityDetails(entityId) {
    try {
        const entity = state.entities.find(e => e.id === entityId);
        if (!entity) return;
        
        state.selectedEntity = entity;
        
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${escapeHtml(entity.name)}</h3>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="detail-section">
                        <h4>基本信息</h4>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>类型:</label>
                                <span class="entity-type ${getEntityTypeClass(entity.type)}">${getEntityTypeLabel(entity.type)}</span>
                            </div>
                            <div class="detail-item">
                                <label>创建时间:</label>
                                <span>${formatDate(entity.created_at)}</span>
                            </div>
                            <div class="detail-item">
                                <label>更新时间:</label>
                                <span>${formatDate(entity.updated_at)}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>描述</h4>
                        <div class="detail-content">${escapeHtml(entity.description || '暂无描述')}</div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>相关新闻</h4>
                        <div id="entity-news" class="news-list"></div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 加载相关新闻
        try {
            const newsRes = await window.KGAPI.getEntityNews(entityId, {
                page: 1,
                page_size: 5
            });
            const newsContainer = document.getElementById('entity-news');
            
            if (newsRes.items && newsRes.items.length > 0) {
                newsContainer.innerHTML = newsRes.items.map(news => `
                    <div class="news-item">
                        <div class="news-title">${escapeHtml(news.title)}</div>
                        <div class="news-date">${formatDate(news.published_at)}</div>
                    </div>
                `).join('');
            } else {
                newsContainer.innerHTML = '<div class="empty-text">暂无相关新闻</div>';
            }
        } catch (newsError) {
                // 只在开发环境显示日志
                console.error('加载新闻失败:', newsError);
                document.getElementById('entity-news').innerHTML = '<div class="error-text">加载新闻失败</div>';
            }
        
    } catch (error) {
        // 只在开发环境显示日志
        console.error('显示实体详情失败:', error);
        showError('显示实体详情失败: ' + error.message, 'error');
    }
}

// 显示实体新闻
function showEntityNews(entityId) {
    window.location.href = `news.html?entity_id=${entityId}`;
}

// 工具函数
function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) modal.remove();
}

function showLoading() {
    const container = document.getElementById('entities-container');
    container.innerHTML = '<div class="loading-spinner"></div>';
}

function hideLoading() {
    // 加载状态由renderEntities处理
}

function showError(message, type) {
    // 直接使用config.js中定义的window.showError，避免递归
    if (typeof window.showError === 'function') {
        // 保存原始函数引用，避免递归
        const originalShowError = window.showError;
        originalShowError(message, type);
    } else {
        // 只在开发环境显示日志
        console.error('Error:', message);
        alert(message);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function getEntityTypeLabel(type) {
    const labels = {
        person: '人物',
        organization: '组织',
        location: '地点',
        event: '事件',
        product: '产品',
        concept: '概念',
        other: '其他'
    };
    return labels[type] || type || '未知';
}

function getEntityTypeClass(type) {
    const classes = {
        person: 'type-person',
        organization: 'type-organization',
        location: 'type-location',
        event: 'type-event',
        product: 'type-product',
        concept: 'type-concept',
        other: 'type-other'
    };
    return classes[type] || 'type-other';
}

function formatDate(dateString) {
    if (!dateString) return '未知时间';
    try {
        return new Date(dateString).toLocaleString('zh-CN');
    } catch {
        return '未知时间';
    }
}

// 搜索和重置函数
function searchEntities() {
    state.currentPage = 1;
    loadEntities();
}

function resetSearch() {
    const searchInput = document.getElementById('searchKeyword');
    const typeSelect = document.getElementById('entityType');
    if (searchInput) searchInput.value = '';
    if (typeSelect) typeSelect.value = '';
    state.currentPage = 1;
    loadEntities();
}

// 回车事件处理
function handleEnter(event) {
    if (event.key === 'Enter') {
        searchEntities();
    }
}

// 页面初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePage);
} else {
    initializePage();
}