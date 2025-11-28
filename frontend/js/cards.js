/**
 * 知识图谱卡片组件库
 * 提供实体卡片和关系卡片组件
 */

/**
 * 实体卡片组件
 */
class EntityCard {
    constructor(entity, options = {}) {
        this.entity = entity;
        this.options = {
            showActions: true,
            showRelations: true,
            showProperties: true,
            compact: false,
            ...options
        };
        this.element = null;
        this.eventListeners = new Map();
    }

    /**
     * 创建卡片元素
     */
    createElement() {
        const card = document.createElement('div');
        card.className = 'entity-card';
        card.dataset.entityId = this.entity.id;
        
        // 设置实体类型颜色
        const typeColor = UIUtils.getEntityTypeColor(this.entity.type);
        card.style.borderLeftColor = typeColor;
        
        // 创建卡片内容
        card.innerHTML = this.createCardContent();
        
        // 添加事件监听器
        this.attachEventListeners(card);
        
        this.element = card;
        return card;
    }

    /**
     * 创建卡片内容
     */
    createCardContent() {
        const { showActions, showRelations, showProperties, compact } = this.options;
        
        return `
            <div class="entity-card-header">
                <div class="entity-type-badge" style="background-color: ${UIUtils.getEntityTypeColor(this.entity.type)}">
                    ${this.entity.type}
                </div>
                <div class="entity-actions">
                    ${showActions ? this.createActions() : ''}
                </div>
            </div>
            
            <div class="entity-card-body">
                <h3 class="entity-name">${this.entity.name}</h3>
                ${this.entity.description ? `<p class="entity-description">${UIUtils.truncateText(this.entity.description, 150)}</p>` : ''}
                
                ${showProperties && this.entity.properties ? this.createProperties() : ''}
                ${showRelations && this.entity.relations ? this.createRelations() : ''}
            </div>
            
            <div class="entity-card-footer">
                <div class="entity-meta">
                    <span class="entity-id">ID: ${this.entity.id}</span>
                    <span class="entity-timestamp">${UIUtils.formatDate(this.entity.created_at || new Date())}</span>
                </div>
            </div>
        `;
    }

    /**
     * 创建操作按钮
     */
    createActions() {
        return `
            <button class="btn btn-sm btn-outline entity-edit-btn" data-action="edit" title="编辑">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-outline entity-view-btn" data-action="view" title="查看详情">
                <i class="fas fa-eye"></i>
            </button>
            <button class="btn btn-sm btn-outline entity-relations-btn" data-action="relations" title="查看关系">
                <i class="fas fa-project-diagram"></i>
            </button>
        `;
    }

    /**
     * 创建属性列表
     */
    createProperties() {
        const properties = this.entity.properties || {};
        const propertyEntries = Object.entries(properties).slice(0, 3); // 只显示前3个属性
        
        if (propertyEntries.length === 0) return '';
        
        return `
            <div class="entity-properties">
                <h4 class="properties-title">属性</h4>
                <div class="properties-list">
                    ${propertyEntries.map(([key, value]) => `
                        <div class="property-item">
                            <span class="property-key">${key}:</span>
                            <span class="property-value">${this.formatPropertyValue(value)}</span>
                        </div>
                    `).join('')}
                    ${Object.keys(properties).length > 3 ? '<div class="property-more">...</div>' : ''}
                </div>
            </div>
        `;
    }

    /**
     * 格式化属性值
     */
    formatPropertyValue(value) {
        if (value === null || value === undefined) return '';
        if (typeof value === 'boolean') return value ? '是' : '否';
        if (typeof value === 'number') return value.toString();
        if (typeof value === 'string') {
            // 如果是JSON字符串，尝试解析
            if (value.startsWith('{') && value.endsWith('}')) {
                try {
                    const parsed = JSON.parse(value);
                    return this.formatPropertyValue(parsed);
                } catch (e) {
                    return value;
                }
            }
            return value;
        }
        if (Array.isArray(value)) {
            return `[${value.length}项]`;
        }
        if (typeof value === 'object') {
            return Object.keys(value).join(', ');
        }
        return String(value);
    }

    /**
     * 创建关系列表
     */
    createRelations() {
        const relations = this.entity.relations || [];
        const relationCount = relations.length;
        
        if (relationCount === 0) return '';
        
        return `
            <div class="entity-relations">
                <h4 class="relations-title">关系 (${relationCount})</h4>
                <div class="relations-list">
                    ${relations.slice(0, 2).map(relation => `
                        <div class="relation-item">
                            <span class="relation-type">${relation.type}</span>
                            <span class="relation-target">${relation.target_name || relation.target_id}</span>
                        </div>
                    `).join('')}
                    ${relationCount > 2 ? `<div class="relation-more">还有 ${relationCount - 2} 个关系</div>` : ''}
                </div>
            </div>
        `;
    }

    /**
     * 添加事件监听器
     */
    attachEventListeners(card) {
        // 编辑按钮
        const editBtn = card.querySelector('.entity-edit-btn');
        if (editBtn) {
            const editHandler = (e) => {
                e.stopPropagation();
                this.emit('edit', this.entity);
            };
            editBtn.addEventListener('click', editHandler);
            this.eventListeners.set('edit', editHandler);
        }

        // 查看按钮
        const viewBtn = card.querySelector('.entity-view-btn');
        if (viewBtn) {
            const viewHandler = (e) => {
                e.stopPropagation();
                this.emit('view', this.entity);
            };
            viewBtn.addEventListener('click', viewHandler);
            this.eventListeners.set('view', viewHandler);
        }

        // 关系按钮
        const relationsBtn = card.querySelector('.entity-relations-btn');
        if (relationsBtn) {
            const relationsHandler = (e) => {
                e.stopPropagation();
                this.emit('relations', this.entity);
            };
            relationsBtn.addEventListener('click', relationsHandler);
            this.eventListeners.set('relations', relationsHandler);
        }

        // 卡片点击
        const clickHandler = (e) => {
            if (!e.target.closest('.entity-actions')) {
                this.emit('click', this.entity);
            }
        };
        card.addEventListener('click', clickHandler);
        this.eventListeners.set('click', clickHandler);
    }

    /**
     * 触发事件
     */
    emit(eventName, data) {
        const event = new CustomEvent(`entity:${eventName}`, {
            detail: { entity: data, card: this },
            bubbles: true
        });
        this.element.dispatchEvent(event);
    }

    /**
     * 更新实体数据
     */
    updateEntity(entity) {
        this.entity = { ...this.entity, ...entity };
        if (this.element) {
            this.element.innerHTML = this.createCardContent();
            this.attachEventListeners(this.element);
        }
    }

    /**
     * 销毁卡片
     */
    destroy() {
        // 移除所有事件监听器
        this.eventListeners.forEach((handler, event) => {
            this.element.removeEventListener(event, handler);
        });
        this.eventListeners.clear();
        
        // 移除DOM元素
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

/**
 * 关系卡片组件
 */
class RelationCard {
    constructor(relation, options = {}) {
        this.relation = relation;
        this.options = {
            showActions: true,
            showProperties: true,
            compact: false,
            ...options
        };
        this.element = null;
        this.eventListeners = new Map();
    }

    /**
     * 创建卡片元素
     */
    createElement() {
        const card = document.createElement('div');
        card.className = 'relation-card';
        card.dataset.relationId = this.relation.id;
        
        // 设置关系类型颜色
        const typeColor = UIUtils.getRelationTypeColor(this.relation.type);
        card.style.borderLeftColor = typeColor;
        
        // 创建卡片内容
        card.innerHTML = this.createCardContent();
        
        // 添加事件监听器
        this.attachEventListeners(card);
        
        this.element = card;
        return card;
    }

    /**
     * 创建卡片内容
     */
    createCardContent() {
        const { showActions, showProperties, compact } = this.options;
        
        return `
            <div class="relation-card-header">
                <div class="relation-type-badge" style="background-color: ${UIUtils.getRelationTypeColor(this.relation.type)}">
                    ${this.relation.type}
                </div>
                <div class="relation-actions">
                    ${showActions ? this.createActions() : ''}
                </div>
            </div>
            
            <div class="relation-card-body">
                <div class="relation-entities">
                    <div class="relation-entity source-entity">
                        <div class="entity-avatar" style="background-color: ${UIUtils.getEntityTypeColor(this.relation.source_type)}">
                            ${this.relation.source_name.charAt(0).toUpperCase()}
                        </div>
                        <div class="entity-info">
                            <div class="entity-name">${this.relation.source_name}</div>
                            <div class="entity-type">${this.relation.source_type}</div>
                        </div>
                    </div>
                    
                    <div class="relation-arrow">
                        <i class="fas fa-arrow-right"></i>
                    </div>
                    
                    <div class="relation-entity target-entity">
                        <div class="entity-avatar" style="background-color: ${UIUtils.getEntityTypeColor(this.relation.target_type)}">
                            ${this.relation.target_name.charAt(0).toUpperCase()}
                        </div>
                        <div class="entity-info">
                            <div class="entity-name">${this.relation.target_name}</div>
                            <div class="entity-type">${this.relation.target_type}</div>
                        </div>
                    </div>
                </div>
                
                ${this.relation.description ? `<p class="relation-description">${UIUtils.truncateText(this.relation.description, 100)}</p>` : ''}
                
                ${showProperties && this.relation.properties ? this.createProperties() : ''}
            </div>
            
            <div class="relation-card-footer">
                <div class="relation-meta">
                    <span class="relation-id">ID: ${this.relation.id}</span>
                    <span class="relation-timestamp">${UIUtils.formatDate(this.relation.created_at || new Date())}</span>
                </div>
            </div>
        `;
    }

    /**
     * 创建操作按钮
     */
    createActions() {
        return `
            <button class="btn btn-sm btn-outline relation-edit-btn" data-action="edit" title="编辑">
                <i class="fas fa-edit"></i>
            </button>
            <button class="btn btn-sm btn-outline relation-view-btn" data-action="view" title="查看详情">
                <i class="fas fa-eye"></i>
            </button>
        `;
    }

    /**
     * 创建属性列表
     */
    createProperties() {
        const properties = this.relation.properties || {};
        const propertyEntries = Object.entries(properties).slice(0, 3); // 只显示前3个属性
        
        if (propertyEntries.length === 0) return '';
        
        return `
            <div class="relation-properties">
                <h4 class="properties-title">属性</h4>
                <div class="properties-list">
                    ${propertyEntries.map(([key, value]) => `
                        <div class="property-item">
                            <span class="property-key">${key}:</span>
                            <span class="property-value">${this.formatPropertyValue(value)}</span>
                        </div>
                    `).join('')}
                    ${Object.keys(properties).length > 3 ? '<div class="property-more">...</div>' : ''}
                </div>
            </div>
        `;
    }

    /**
     * 格式化属性值
     */
    formatPropertyValue(value) {
        if (value === null || value === undefined) return '';
        if (typeof value === 'boolean') return value ? '是' : '否';
        if (typeof value === 'number') return value.toString();
        if (typeof value === 'string') {
            // 如果是JSON字符串，尝试解析
            if (value.startsWith('{') && value.endsWith('}')) {
                try {
                    const parsed = JSON.parse(value);
                    return this.formatPropertyValue(parsed);
                } catch (e) {
                    return value;
                }
            }
            return value;
        }
        if (Array.isArray(value)) {
            return `[${value.length}项]`;
        }
        if (typeof value === 'object') {
            return Object.keys(value).join(', ');
        }
        return String(value);
    }

    /**
     * 添加事件监听器
     */
    attachEventListeners(card) {
        // 编辑按钮
        const editBtn = card.querySelector('.relation-edit-btn');
        if (editBtn) {
            const editHandler = (e) => {
                e.stopPropagation();
                this.emit('edit', this.relation);
            };
            editBtn.addEventListener('click', editHandler);
            this.eventListeners.set('edit', editHandler);
        }

        // 查看按钮
        const viewBtn = card.querySelector('.relation-view-btn');
        if (viewBtn) {
            const viewHandler = (e) => {
                e.stopPropagation();
                this.emit('view', this.relation);
            };
            viewBtn.addEventListener('click', viewHandler);
            this.eventListeners.set('view', viewHandler);
        }

        // 卡片点击
        const clickHandler = (e) => {
            if (!e.target.closest('.relation-actions')) {
                this.emit('click', this.relation);
            }
        };
        card.addEventListener('click', clickHandler);
        this.eventListeners.set('click', clickHandler);
    }

    /**
     * 触发事件
     */
    emit(eventName, data) {
        const event = new CustomEvent(`relation:${eventName}`, {
            detail: { relation: data, card: this },
            bubbles: true
        });
        this.element.dispatchEvent(event);
    }

    /**
     * 更新关系数据
     */
    updateRelation(relation) {
        this.relation = { ...this.relation, ...relation };
        if (this.element) {
            this.element.innerHTML = this.createCardContent();
            this.attachEventListeners(this.element);
        }
    }

    /**
     * 销毁卡片
     */
    destroy() {
        // 移除所有事件监听器
        this.eventListeners.forEach((handler, event) => {
            this.element.removeEventListener(event, handler);
        });
        this.eventListeners.clear();
        
        // 移除DOM元素
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

// 导出卡片组件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EntityCard, RelationCard };
} else {
    // 浏览器环境，挂载到全局对象
    window.EntityCard = EntityCard;
    window.RelationCard = RelationCard;
}