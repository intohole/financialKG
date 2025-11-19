// News Management JavaScript

// Global variables
let newsData = [];

// Initialize News Management page
function initNewsPage() {
    console.log('News Management page initialized');
    
    // Set up event listeners
    setupNewsEvents();
    
    // Load initial data
    loadNews();
}

// Set up event listeners for News Management
function setupNewsEvents() {
    // Refresh button
    const refreshBtn = document.getElementById('btn-refresh-news');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadNews);
    }
}

// Load news from API
function loadNews() {
    const newsTableBody = document.getElementById('news-table-body');
    
    // Show loading state
    newsTableBody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div> 加载新闻列表...</td></tr>';
    
    apiRequest('/api/v1/news/', 'GET')
        .then(data => {
            newsData = data.news || [];
            renderNews(newsData);
        })
        .catch(error => {
            console.error('Error loading news:', error);
            showAlert('error', '加载新闻失败: ' + error.message);
            newsTableBody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">加载失败，请稍后重试</td></tr>';
        });
}

// Render news list
function renderNews(news) {
    const newsTableBody = document.getElementById('news-table-body');
    
    if (news.length === 0) {
        newsTableBody.innerHTML = '<tr><td colspan="6" class="text-center">暂无新闻数据</td></tr>';
        return;
    }
    
    const rows = news.map(item => `
        <tr>
            <td>${item.id}</td>
            <td><a href="#" onclick="viewNews(${item.id})">${item.title}</a></td>
            <td>${item.source}</td>
            <td>${item.category || '-'}</td>
            <td>${item.publish_time || '-'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="viewNews(${item.id})" title="查看详情">
                    <i class="fa fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteNews(${item.id})" title="删除">
                    <i class="fa fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    newsTableBody.innerHTML = rows;
}

// View news details
function viewNews(newsId) {
    const news = newsData.find(item => item.id === newsId);
    
    if (news) {
        // Create modal or detail view
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'news-detail-modal';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${news.title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <strong>来源:</strong> ${news.source}
                        </div>
                        <div class="mb-3">
                            <strong>分类:</strong> ${news.category || '未分类'}
                        </div>
                        <div class="mb-3">
                            <strong>发布时间:</strong> ${news.publish_time || '未知'}
                        </div>
                        <div class="mb-3">
                            <strong>内容:</strong>
                            <p>${news.content || '无内容'}</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Remove modal after hidden
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }
}

// Delete news
function deleteNews(newsId) {
    if (confirm('确定要删除这条新闻吗？')) {
        apiRequest(`/api/v1/news/${newsId}`, 'DELETE')
            .then(() => {
                showAlert('success', '新闻删除成功');
                loadNews();
            })
            .catch(error => {
                console.error('Error deleting news:', error);
                showAlert('error', '删除新闻失败: ' + error.message);
            });
    }
}

// Initialize the page when it's loaded
window.initNewsPage = initNewsPage;
