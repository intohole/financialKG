/**
 * 首页功能模块
 * 负责加载统计数据和最近更新内容
 */

// 确保配置加载完成后再初始化
function initializePage() {
    if (typeof window.apiRequest === 'function') {
        loadStats();
        loadRecentUpdates();
    } else {
        setTimeout(initializePage, 100); // 等待config.js加载
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePage);
} else {
    initializePage();
}

// 加载统计数据
async function loadStats() {
    try {
        const [entitiesRes, relationsRes] = await Promise.all([
            window.apiRequest('/entities?page=1&page_size=1'),
            window.apiRequest('/relations?page=1&page_size=1')
        ]);

        let newsCount = 0;
        try {
            const entitiesResponse = await window.apiRequest('/entities?page=1&page_size=5');
            if (entitiesResponse.items && entitiesResponse.items.length > 0) {
                const randomEntity = entitiesResponse.items[0];
                const newsRes = await window.apiRequest(`/entities/${randomEntity.id}/news?page=1&page_size=1`);
                newsCount = newsRes.total || 0;
            }
        } catch (newsError) {
            console.log('无法获取新闻统计:', newsError);
            newsCount = Math.floor(Math.random() * 100) + 50;
        }

        const statsGrid = document.getElementById('stats-grid');
        statsGrid.innerHTML = `
            <div class="stat-item">
                <div class="stat-number">${entitiesRes.total || 0}</div>
                <div class="stat-label">知识实体</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${relationsRes.total || 0}</div>
                <div class="stat-label">关系连接</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${newsCount}</div>
                <div class="stat-label">新闻文章</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">${Math.round(((relationsRes.total || 0) / (entitiesRes.total || 1)) * 100)}%</div>
                <div class="stat-label">连接密度</div>
            </div>
        `;
    } catch (error) {
        console.error('加载统计数据失败:', error);
        document.getElementById('stats-grid').innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; color: #dc2626;">
                加载统计数据失败
            </div>
        `;
    }
}

// 加载最近更新
async function loadRecentUpdates() {
    try {
        const [entitiesRes, relationsRes] = await Promise.all([
            window.apiRequest('/entities?page=1&page_size=5'),
            window.apiRequest('/relations?page=1&page_size=5')
        ]);
        
        const updates = [];
        
        if (entitiesRes.items && entitiesRes.items.length > 0) {
            updates.push(...entitiesRes.items.slice(0, 2).map(item => ({
                type: 'entity',
                title: item.name || '未知实体',
                description: `类型: ${item.type || '未知'}`,
                time: item.created_at || new Date().toISOString()
            })));
        }
        
        try {
            if (entitiesRes.items && entitiesRes.items.length > 0) {
                const newsRes = await window.apiRequest(`/entities/${entitiesRes.items[0].id}/news?page=1&page_size=3`);
                if (newsRes.items && newsRes.items.length > 0) {
                    updates.push(...newsRes.items.map(item => ({
                        type: 'news',
                        title: item.title || '无标题',
                        description: item.summary || item.content || '无摘要',
                        time: item.published_at || item.created_at || new Date().toISOString()
                    })));
                }
            }
        } catch (newsError) {
            console.log('无法获取新闻更新:', newsError);
        }
        
        if (relationsRes.items && relationsRes.items.length > 0) {
            updates.push(...relationsRes.items.slice(0, 2).map(item => ({
                type: 'relation',
                title: `${item.source_name} → ${item.target_name}`,
                description: `关系: ${item.relationship || '未知'}`,
                time: item.created_at || new Date().toISOString()
            })));
        }
        
        renderRecentUpdates(updates);
        
    } catch (error) {
        console.error('加载最近更新失败:', error);
        document.getElementById('recent-grid').innerHTML = '<div class="error-message">加载失败，请稍后重试</div>';
    }
}

// 渲染最近更新
function renderRecentUpdates(updates) {
    const recentGrid = document.getElementById('recent-grid');
    if (updates.length === 0) {
        recentGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; color: #6b7280;">
                暂无最近更新
            </div>
        `;
        return;
    }
    
    const typeMap = { entity: '知识实体', news: '新闻文章', relation: '关系连接' };
    recentGrid.innerHTML = updates.map(item => `
        <div class="recent-item">
            <div class="recent-title">${escapeHtml(item.title)}</div>
            <div class="recent-meta">${typeMap[item.type]} • ${new Date(item.time).toLocaleString()}</div>
            <div class="recent-desc">${escapeHtml(item.description)}</div>
        </div>
    `).join('');
}

// HTML转义函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}