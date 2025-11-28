/**
 * 知识图谱前端工具函数库
 * 提供通用的工具函数和辅助方法
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
 * 通用工具函数
 */
class Utils {
    /**
     * 防抖函数
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 节流函数
     */
    static throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * 深拷贝对象
     */
    static deepClone(obj) {
        if (obj === null || typeof obj !== 'object') return obj;
        if (obj instanceof Date) return new Date(obj.getTime());
        if (obj instanceof Array) return obj.map(item => this.deepClone(item));
        if (typeof obj === 'object') {
            const cloned = {};
            for (const key in obj) {
                if (obj.hasOwnProperty(key)) {
                    cloned[key] = this.deepClone(obj[key]);
                }
            }
            return cloned;
        }
    }

    /**
     * 生成唯一ID
     */
    static generateId(prefix = 'id') {
        return `${prefix}_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    }

    /**
     * 格式化数字（添加千位分隔符）
     */
    static formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    /**
     * 将字符串转换为驼峰命名
     */
    static toCamelCase(str) {
        return str.replace(/[-_](.)/g, (_, char) => char.toUpperCase());
    }

    /**
     * 将驼峰命名转换为短横线命名
     */
    static toKebabCase(str) {
        return str.replace(/([A-Z])/g, '-$1').toLowerCase().replace(/^-/, '');
    }

    /**
     * 获取URL参数
     */
    static getUrlParams(url = window.location.href) {
        const params = {};
        const urlObj = new URL(url);
        urlObj.searchParams.forEach((value, key) => {
            params[key] = value;
        });
        return params;
    }

    /**
     * 设置URL参数
     */
    static setUrlParams(params, url = window.location.href) {
        const urlObj = new URL(url);
        Object.keys(params).forEach(key => {
            if (params[key] === null || params[key] === undefined) {
                urlObj.searchParams.delete(key);
            } else {
                urlObj.searchParams.set(key, params[key]);
            }
        });
        return urlObj.toString();
    }

    /**
     * 本地存储操作
     */
    static storage = {
        /**
         * 设置本地存储
         */
        set(key, value, expireTime = null) {
            try {
                const data = { value, expireTime };
                localStorage.setItem(key, JSON.stringify(data));
                return true;
            } catch (error) {
                console.error('本地存储设置失败:', error);
                return false;
            }
        },

        /**
         * 获取本地存储
         */
        get(key) {
            try {
                const data = localStorage.getItem(key);
                if (!data) return null;
                
                const parsed = JSON.parse(data);
                
                // 检查过期时间
                if (parsed.expireTime && Date.now() > parsed.expireTime) {
                    localStorage.removeItem(key);
                    return null;
                }
                
                return parsed.value;
            } catch (error) {
                console.error('本地存储获取失败:', error);
                return null;
            }
        },

        /**
         * 删除本地存储
         */
        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (error) {
                console.error('本地存储删除失败:', error);
                return false;
            }
        },

        /**
         * 清空本地存储
         */
        clear() {
            try {
                localStorage.clear();
                return true;
            } catch (error) {
                console.error('本地存储清空失败:', error);
                return false;
            }
        }
    };

    /**
     * 事件总线
     */
    static eventBus = {
        events: {},

        /**
         * 监听事件
         */
        on(event, callback) {
            if (!this.events[event]) {
                this.events[event] = [];
            }
            this.events[event].push(callback);
        },

        /**
         * 触发事件
         */
        emit(event, data) {
            if (this.events[event]) {
                this.events[event].forEach(callback => {
                    try {
                        callback(data);
                    } catch (error) {
                        console.error(`事件 ${event} 处理失败:`, error);
                    }
                });
            }
        },

        /**
         * 移除事件监听
         */
        off(event, callback) {
            if (this.events[event]) {
                this.events[event] = this.events[event].filter(cb => cb !== callback);
            }
        },

        /**
         * 清空所有事件
         */
        clear() {
            this.events = {};
        }
    };
}

// 导出工具函数
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { UIUtils, Utils };
} else {
    // 浏览器环境，挂载到全局对象
    window.UIUtils = UIUtils;
    window.Utils = Utils;
}