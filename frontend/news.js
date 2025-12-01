/**
 * 新闻管理页面功能模块
 * 负责新闻搜索、列表展示、分页和详情查看
 */

// 全局状态管理
const state = {
    currentPage: 1,
    pageSize: 10,
    totalNews: 0,
    news: [],
    selectedNews: null,
    loading: false,
    entityId: null // 从URL参数获取的实体ID
};

// 页面初始化
function initializePage() {
    if (typeof window.KGAPI === 'object') {
        // 获取URL参数
        const urlParams = new URLSearchParams(window.location.search);
        state.entityId = urlParams.get('entity_id');
        
        // 如果有实体ID但没有对应的输入框，忽略它
        if (state.entityId) {
            const entityFilter = document.getElementById('entityFilter');
            if (entityFilter) {
                entityFilter.value = state.entityId;
            }
        }
        
        setupEventListeners();
        loadNews();
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
            loadNews();
        });
    }

    // 重置按钮点击事件
    const resetBtn = document.querySelector('.btn-secondary');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            const searchInput = document.getElementById('searchKeyword');
            const timeSelect = document.getElementById('timeRange');
            if (searchInput) searchInput.value = '';
            if (timeSelect) timeSelect.value = '';
            state.currentPage = 1;
            state.entityId = null;
            loadNews();
        });
    }
}

// 加载新闻列表
async function loadNews() {
    if (state.loading) return;
    
    try {
        state.loading = true;
        showLoading();
        
        // 获取搜索参数
        const searchInput = document.getElementById('searchKeyword');
        
        let response;
        if (state.entityId) {
            // 如果有实体ID，获取该实体的新闻
            response = await window.KGAPI.getEntityNews(state.entityId, {
                page: state.currentPage,
                page_size: state.pageSize,
                search: searchInput && searchInput.value ? searchInput.value : null
            });
        } else {
            // 否则获取所有新闻
            response = await window.KGAPI.getNewsList({
                page: state.currentPage,
                page_size: state.pageSize,
                search: searchInput && searchInput.value ? searchInput.value : null
            });
        }
        
        state.news = response.items || [];
        state.totalNews = response.total || 0;
        
        renderNews();
        renderPagination();
        
    } catch (error) {
        // 只在开发环境显示日志
        console.error('加载新闻失败:', error);
        showError('加载新闻失败: ' + error.message, 'error');
    } finally {
        state.loading = false;
        hideLoading();
    }
}

// 渲染新闻列表
function renderNews() {
    const container = document.getElementById('news-container');
    
    if (!container) {
        // 只在开发环境显示日志
        console.error('news-container element not found');
        return;
    }
    
    if (state.news.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📰</div>
                <div class="empty-text">暂无新闻数据</div>
                <div class="empty-desc">您可以先添加一些新闻数据</div>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="news-grid">
            ${state.news.map(news => `
                <div class="news-card" onclick="showNewsDetails('${news.id}')">
                    <div class="news-header">
                        <div class="news-title">${escapeHtml(news.title)}</div>
                        <div class="news-date">${formatDate(news.published_at || news.created_at)}</div>
                    </div>
                    <div class="news-summary">${escapeHtml(truncateText(news.summary || news.content, 150))}</div>
                    <div class="news-meta">
                        <div class="news-source">来源: ${escapeHtml(news.source || '未知')}</div>
                        <div class="news-actions">
                            <button class="btn btn-sm btn-outline" onclick="event.stopPropagation(); showNewsEntities('${news.id}')">查看实体</button>
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
    if (!container) {
        // 只在开发环境显示日志
        console.error('pagination-container element not found');
        return;
    }
    
    const totalPages = Math.ceil(state.totalNews / state.pageSize);
    
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
    loadNews();
}

// 搜索新闻
function searchNews() {
    state.currentPage = 1;
    loadNews();
}

// 重置搜索
function resetSearch() {
    const searchInput = document.getElementById('searchKeyword');
    const timeSelect = document.getElementById('timeRange');
    if (searchInput) searchInput.value = '';
    if (timeSelect) timeSelect.value = '';
    state.currentPage = 1;
    state.entityId = null;
    loadNews();
}

// 处理回车键
function handleEnter(event) {
    if (event.key === 'Enter') {
        searchNews();
    }
}

// 显示新闻详情
async function showNewsDetails(newsId) {
    try {
        const news = state.news.find(n => n.id === newsId);
        if (!news) return;
        
        state.selectedNews = news;
        
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${escapeHtml(news.title)}</h3>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="detail-section">
                        <h4>基本信息</h4>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>来源:</label>
                                <span>${escapeHtml(news.source || '未知')}</span>
                            </div>
                            <div class="detail-item">
                                <label>发布时间:</label>
                                <span>${formatDate(news.published_at)}</span>
                            </div>
                            <div class="detail-item">
                                <label>创建时间:</label>
                                <span>${formatDate(news.created_at)}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>摘要</h4>
                        <div class="detail-content">${escapeHtml(news.summary || news.content || '暂无摘要')}</div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>内容</h4>
                        <div class="detail-content">${escapeHtml(news.content || '暂无内容')}</div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>相关实体</h4>
                        <div id="news-entities" class="entities-list"></div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 加载相关实体
        try {
            const entitiesRes = await window.KGAPI.getNewsEntities(newsId);
            const entitiesContainer = document.getElementById('news-entities');
            
            if (entitiesRes.entities && entitiesRes.entities.length > 0) {
                entitiesContainer.innerHTML = entitiesRes.entities.map(entity => `
                    <div class="entity-item">
                        <span class="entity-name">${escapeHtml(entity.name)}</span>
                        <span class="entity-type ${getEntityTypeClass(entity.type)}">${getEntityTypeLabel(entity.type)}</span>
                    </div>
                `).join('');
            } else {
                entitiesContainer.innerHTML = '<div class="empty-text">暂无相关实体</div>';
            }
        } catch (entitiesError) {
                // 只在开发环境显示日志
                console.error('加载实体失败:', entitiesError);
                document.getElementById('news-entities').innerHTML = '<div class="error-text">加载实体失败</div>';
            }
        
    } catch (error) {
        // 只在开发环境显示日志
        console.error('显示新闻详情失败:', error);
        showError('显示新闻详情失败: ' + error.message, 'error');
    }
}

// 显示新闻实体
function showNewsEntities(newsId) {
    window.location.href = `entities.html?news_id=${newsId}`;
}

// 工具函数
function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) modal.remove();
}

function showLoading() {
    const container = document.getElementById('news-container');
    if (container) {
        container.innerHTML = '<div class="loading-spinner"></div>';
    }
}

function hideLoading() {
    // 加载状态由renderNews处理
}

function showError(message, type) {
    // 显示错误消息
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
        errorContainer.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
        errorContainer.style.display = 'block';
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    } else {
        // 如果没有错误容器，使用alert
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

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}



// 页面初始化
function initNewsPage() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializePage);
    } else {
        // 确保DOM完全加载
        if (document.getElementById('news-container')) {
            initializePage();
        } else {
            setTimeout(initNewsPage, 100);
        }
    }
}

initNewsPage();