/**
 * 前端统一配置文件
 * 所有API请求的基础配置都在这里设置
 */

// API基础配置
const API_CONFIG = {
    BASE_URL: 'http://localhost:8066/api/kg',
    TIMEOUT: 30000,
    RETRY_COUNT: 3
};

// 统一请求函数
async function apiRequest(endpoint, options = {}) {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        timeout: API_CONFIG.TIMEOUT
    };

    const finalOptions = { ...defaultOptions, ...options };
    
    let lastError;
    for (let i = 0; i < API_CONFIG.RETRY_COUNT; i++) {
        try {
            const response = await fetch(url, finalOptions);
            if (!response.ok) {
                // 创建包含response对象的错误
                const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
                error.response = response;
                error.status = response.status;
                error.statusText = response.statusText;
                
                // 尝试获取错误详情
                try {
                    const errorData = await response.json();
                    error.data = errorData;
                } catch {
                    // 如果无法解析JSON，不影响错误对象
                }
                
                throw error;
            }
            return await response.json();
        } catch (error) {
            lastError = error;
            if (i < API_CONFIG.RETRY_COUNT - 1) {
                await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
            }
        }
    }
    throw lastError;
}

// 统一的错误处理函数
function showError(message, type = 'error') {
    const div = document.createElement('div');
    Object.assign(div.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: '1000',
        minWidth: '200px',
        padding: '12px 16px',
        borderRadius: '6px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        backgroundColor: type === 'error' ? '#fee' : type === 'success' ? '#efe' : '#eef',
        color: type === 'error' ? '#c00' : type === 'success' ? '#060' : '#006',
        border: `1px solid ${type === 'error' ? '#fcc' : type === 'success' ? '#cfc' : '#ccf'}`
    });
    div.textContent = message;
    document.body.appendChild(div);
    setTimeout(() => div.remove(), 3000);
}

// 统一的加载状态管理
function showLoading(show = true, containerId = null) {
    if (containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            if (show) {
                container.innerHTML = '<div class="loading">正在加载数据...</div>';
            }
        }
    }
}

// 导出给全局使用
window.API_CONFIG = API_CONFIG;
window.apiRequest = apiRequest;
window.showError = showError;
window.showLoading = showLoading;