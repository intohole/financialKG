/**
 * 知识图谱组件库主入口文件
 * 整合所有模块化的组件
 */

// 浏览器环境，假设各个模块已经通过script标签加载
if (typeof module === 'undefined') {
    // 如果某些模块不存在，创建空对象作为后备
    if (typeof window.UIUtils === 'undefined') {
        window.UIUtils = class {};
    }
    
    if (typeof window.Utils === 'undefined') {
        window.Utils = class {};
    }
    
    if (typeof window.EntityCard === 'undefined') {
        window.EntityCard = class {};
    }
    
    if (typeof window.RelationCard === 'undefined') {
        window.RelationCard = class {};
    }
    
    if (typeof window.NetworkGraph === 'undefined') {
        window.NetworkGraph = class {};
    }
    
    if (typeof window.Pagination === 'undefined') {
        window.Pagination = class {};
    }
    
    if (typeof window.SearchBox === 'undefined') {
        window.SearchBox = class {};
    }
    
    if (typeof window.Notification === 'undefined') {
        window.Notification = {
            show: function(message, type = 'info', duration = 3000) {
                console.log(`[${type.toUpperCase()}] ${message}`);
            },
            success: function(message, duration = 3000) {
                this.show(message, 'success', duration);
            },
            error: function(message, duration = 5000) {
                this.show(message, 'error', duration);
            },
            warning: function(message, duration = 4000) {
                this.show(message, 'warning', duration);
            },
            info: function(message, duration = 3000) {
                this.show(message, 'info', duration);
            }
        };
    }
    
    if (typeof window.Loading === 'undefined') {
        window.Loading = {
            show: function(message = '加载中...') {
                console.log(`[LOADING] ${message}`);
                return {
                    hide: function() {
                        console.log('[LOADING] 隐藏加载器');
                    }
                };
            },
            hide: function() {
                console.log('[LOADING] 隐藏所有加载器');
            }
        };
    }
}

// Node.js环境，需要引入各个模块
if (typeof module !== 'undefined' && module.exports) {
    const { UIUtils, Utils } = require('./utils.js');
    const { EntityCard, RelationCard } = require('./cards.js');
    const { NetworkGraph } = require('./network.js');
    const { Pagination, SearchBox, Modal } = require('./ui_components.js');
    
    module.exports = {
        // 工具函数
        UIUtils,
        Utils,
        
        // 卡片组件
        EntityCard,
        RelationCard,
        
        // 网络图组件
        NetworkGraph,
        
        // UI组件
        Pagination,
        SearchBox,
        Modal
    };
}