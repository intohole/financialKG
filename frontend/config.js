/**
 * 前端统一配置文件
 * 所有API请求的基础配置都在这里设置
 */

// API基础配置
const API_CONFIG = {
    BASE_URL: 'http://localhost:8066',
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
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            lastError = error;
            console.warn(`请求失败 (尝试 ${i + 1}/${API_CONFIG.RETRY_COUNT}):`, error.message);
            if (i < API_CONFIG.RETRY_COUNT - 1) {
                await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
            }
        }
    }
    throw lastError;
}

// 导出给全局使用
window.API_CONFIG = API_CONFIG;
window.apiRequest = apiRequest;