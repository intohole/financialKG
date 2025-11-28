/**
 * 知识图谱通用UI组件
 * 包含通知、加载器、确认对话框等基础组件
 */

/**
 * 通知组件（简化版）
 */
class Notification {
    static show(message, type = 'info', duration = 3000) {
        const notification = new NotificationComponent(message, type, duration);
        notification.show();
        return notification;
    }

    static success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    static error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    static warning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }

    static info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }
}

/**
 * 通知组件内部类
 */
class NotificationComponent {
    constructor(message, type, duration) {
        this.message = message;
        this.type = type;
        this.duration = duration;
        this.element = null;
        this.timer = null;
    }

    /**
     * 显示通知
     */
    show() {
        this.createElement();
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
        this.element.className = `notification notification-${this.type}`;
        
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        const iconClass = iconMap[this.type] || 'fas fa-info-circle';
        
        this.element.innerHTML = `
            <div class="notification-content">
                <i class="${iconClass} notification-icon"></i>
                <div class="notification-message">${this.escapeHtml(this.message)}</div>
                <button class="notification-close" aria-label="关闭">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 隐藏通知
     */
    hide() {
        this.element.classList.remove('show');
        this.element.classList.add('hide');
        
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

/**
 * 加载器组件
 */
class Loading {
    static show(message = '加载中...', options = {}) {
        const loading = new LoadingComponent(message, options);
        loading.show();
        return loading;
    }

    static hide() {
        LoadingComponent.hideAll();
    }
}

/**
 * 加载器组件内部类
 */
class LoadingComponent {
    static instances = [];

    constructor(message, options) {
        this.message = message;
        this.options = {
            mask: true,
            closable: false,
            ...options
        };
        this.element = null;
        this.mask = null;
    }

    /**
     * 显示加载器
     */
    show() {
        this.createElement();
        document.body.appendChild(this.element);
        
        if (this.options.mask) {
            this.createMask();
            document.body.appendChild(this.mask);
        }
        
        LoadingComponent.instances.push(this);
    }

    /**
     * 创建元素
     */
    createElement() {
        this.element = document.createElement('div');
        this.element.className = 'loading-container';
        
        this.element.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner">
                    <i class="fas fa-spinner fa-spin"></i>
                </div>
                <div class="loading-message">${this.message}</div>
            </div>
        `;
    }

    /**
     * 创建遮罩层
     */
    createMask() {
        this.mask = document.createElement('div');
        this.mask.className = 'loading-mask';
        this.mask.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.3);
            z-index: 9999;
        `;
    }

    /**
     * 隐藏加载器
     */
    hide() {
        if (this.element) {
            this.element.remove();
        }
        
        if (this.mask) {
            this.mask.remove();
        }
        
        const index = LoadingComponent.instances.indexOf(this);
        if (index > -1) {
            LoadingComponent.instances.splice(index, 1);
        }
    }

    /**
     * 隐藏所有加载器
     */
    static hideAll() {
        LoadingComponent.instances.forEach(instance => instance.hide());
        LoadingComponent.instances = [];
    }
}

/**
 * 确认对话框组件
 */
class ConfirmDialog {
    static show(options) {
        const dialog = new ConfirmDialogComponent(options);
        dialog.show();
        return dialog;
    }
}

/**
 * 确认对话框组件内部类
 */
class ConfirmDialogComponent {
    constructor(options) {
        this.options = {
            title: '确认',
            message: '确定要执行此操作吗？',
            confirmText: '确定',
            cancelText: '取消',
            confirmType: 'primary',
            onConfirm: null,
            onCancel: null,
            ...options
        };
        this.element = null;
        this.mask = null;
        this.isOpen = false;
    }

    /**
     * 显示确认对话框
     */
    show() {
        this.createElement();
        this.attachEventListeners();
        document.body.appendChild(this.element);
        
        this.createMask();
        document.body.appendChild(this.mask);
        
        this.isOpen = true;
    }

    /**
     * 创建元素
     */
    createElement() {
        this.element = document.createElement('div');
        this.element.className = 'confirm-dialog';
        
        const confirmBtnClass = `btn btn-${this.options.confirmType}`;
        
        this.element.innerHTML = `
            <div class="confirm-dialog-content">
                <div class="confirm-dialog-header">
                    <h3 class="confirm-dialog-title">${this.options.title}</h3>
                    <button class="confirm-dialog-close" aria-label="关闭">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="confirm-dialog-body">
                    <div class="confirm-dialog-message">${this.options.message}</div>
                </div>
                <div class="confirm-dialog-footer">
                    <button class="btn btn-default confirm-dialog-cancel">${this.options.cancelText}</button>
                    <button class="${confirmBtnClass} confirm-dialog-confirm">${this.options.confirmText}</button>
                </div>
            </div>
        `;
    }

    /**
     * 创建遮罩层
     */
    createMask() {
        this.mask = document.createElement('div');
        this.mask.className = 'confirm-dialog-mask';
        this.mask.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 10000;
        `;
    }

    /**
     * 添加事件监听器
     */
    attachEventListeners() {
        // 关闭按钮
        const closeBtn = this.element.querySelector('.confirm-dialog-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.cancel());
        }
        
        // 取消按钮
        const cancelBtn = this.element.querySelector('.confirm-dialog-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.cancel());
        }
        
        // 确定按钮
        const confirmBtn = this.element.querySelector('.confirm-dialog-confirm');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this.confirm());
        }
        
        // 遮罩层点击
        this.mask.addEventListener('click', (e) => {
            if (e.target === this.mask) {
                this.cancel();
            }
        });
        
        // ESC键关闭
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.cancel();
            }
        });
    }

    /**
     * 确认操作
     */
    confirm() {
        if (this.options.onConfirm) {
            this.options.onConfirm();
        }
        this.close();
    }

    /**
     * 取消操作
     */
    cancel() {
        if (this.options.onCancel) {
            this.options.onCancel();
        }
        this.close();
    }

    /**
     * 关闭对话框
     */
    close() {
        if (!this.isOpen) return;
        
        this.isOpen = false;
        
        if (this.element) {
            this.element.remove();
        }
        
        if (this.mask) {
            this.mask.remove();
        }
    }
}

/**
 * 工具提示组件
 */
class Tooltip {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            content: '',
            position: 'top',
            trigger: 'hover',
            delay: 100,
            ...options
        };
        this.tooltipElement = null;
        this.timer = null;
        this.isVisible = false;
    }

    /**
     * 初始化工具提示
     */
    init() {
        this.attachEventListeners();
    }

    /**
     * 添加事件监听器
     */
    attachEventListeners() {
        const { trigger } = this.options;
        
        if (trigger === 'hover') {
            this.element.addEventListener('mouseenter', () => this.show());
            this.element.addEventListener('mouseleave', () => this.hide());
        } else if (trigger === 'click') {
            this.element.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggle();
            });
        } else if (trigger === 'focus') {
            this.element.addEventListener('focus', () => this.show());
            this.element.addEventListener('blur', () => this.hide());
        }
    }

    /**
     * 显示工具提示
     */
    show() {
        if (this.isVisible) return;
        
        if (this.timer) {
            clearTimeout(this.timer);
        }
        
        this.timer = setTimeout(() => {
            this.createElement();
            document.body.appendChild(this.tooltipElement);
            this.position();
            this.isVisible = true;
        }, this.options.delay);
    }

    /**
     * 隐藏工具提示
     */
    hide() {
        if (!this.isVisible) return;
        
        if (this.timer) {
            clearTimeout(this.timer);
        }
        
        this.timer = setTimeout(() => {
            this.destroy();
            this.isVisible = false;
        }, this.options.delay);
    }

    /**
     * 切换工具提示
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * 创建元素
     */
    createElement() {
        this.tooltipElement = document.createElement('div');
        this.tooltipElement.className = `tooltip tooltip-${this.options.position}`;
        this.tooltipElement.innerHTML = `
            <div class="tooltip-content">${this.options.content}</div>
            <div class="tooltip-arrow"></div>
        `;
    }

    /**
     * 定位工具提示
     */
    position() {
        if (!this.tooltipElement) return;
        
        const rect = this.element.getBoundingClientRect();
        const tooltipRect = this.tooltipElement.getBoundingClientRect();
        const { position } = this.options;
        
        let top = 0;
        let left = 0;
        
        switch (position) {
            case 'top':
                top = rect.top - tooltipRect.height - 8;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'bottom':
                top = rect.bottom + 8;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                break;
            case 'left':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.left - tooltipRect.width - 8;
                break;
            case 'right':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.right + 8;
                break;
        }
        
        // 确保不超出视窗
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };
        
        if (left < 0) left = 8;
        if (left + tooltipRect.width > viewport.width) {
            left = viewport.width - tooltipRect.width - 8;
        }
        if (top < 0) top = 8;
        if (top + tooltipRect.height > viewport.height) {
            top = viewport.height - tooltipRect.height - 8;
        }
        
        this.tooltipElement.style.cssText = `
            position: fixed;
            top: ${top}px;
            left: ${left}px;
            z-index: 9999;
        `;
    }

    /**
     * 销毁工具提示
     */
    destroy() {
        if (this.tooltipElement && this.tooltipElement.parentNode) {
            this.tooltipElement.parentNode.removeChild(this.tooltipElement);
        }
        this.tooltipElement = null;
    }

    /**
     * 更新内容
     */
    updateContent(content) {
        this.options.content = content;
        if (this.tooltipElement) {
            const contentElement = this.tooltipElement.querySelector('.tooltip-content');
            if (contentElement) {
                contentElement.textContent = content;
            }
        }
    }
}

// 导出通用UI组件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { 
        Notification,
        Loading,
        ConfirmDialog,
        Tooltip
    };
} else {
    // 浏览器环境，挂载到全局对象
    window.Notification = Notification;
    window.Loading = Loading;
    window.ConfirmDialog = ConfirmDialog;
    window.Tooltip = Tooltip;
}