/**
 * 内容处理页面功能模块
 * 负责处理文本内容，提取实体和关系
 */

// 全局状态管理
const state = {
    processing: false,
    lastResult: null
};

// 加载示例文本
function loadExampleText() {
    const exampleText = `苹果公司今天宣布，将在下个月发布新款iPhone 15系列手机。这款手机将采用全新的A17芯片，支持5G网络，并配备更先进的摄像头系统。苹果公司CEO蒂姆·库克表示，这将是苹果历史上最重要的产品发布之一。

据悉，iPhone 15系列将包括iPhone 15、iPhone 15 Plus、iPhone 15 Pro和iPhone 15 Pro Max四款机型。新机型将在美国加州库比蒂诺的苹果总部正式发布，并将在全球范围内销售。`;
    
    document.getElementById('contentText').value = exampleText;
    showMessage('示例文本已加载', 'success');
}

// 处理内容
async function processContent() {
    const contentId = document.getElementById('contentId').value.trim();
    const contentText = document.getElementById('contentText').value.trim();
    
    if (!contentText) {
        showMessage('请输入要处理的文本内容', 'error');
        return;
    }

    if (state.processing) return;
    
    try {
        state.processing = true;
        showLoading();
        
        const response = await window.KGAPI.processContent(contentText, contentId || null);
        
        if (response.status === 'success') {
            state.lastResult = response.data;
            displayResult(response.data);
            showMessage(response.message, 'success');
        } else {
            showMessage(response.message, 'error');
        }
        
    } catch (error) {
        showMessage('处理失败: ' + error.message, 'error');
    } finally {
        state.processing = false;
        hideLoading();
    }
}

// 显示处理结果
function displayResult(result) {
    const container = document.getElementById('result-container');
    
    let html = `
        <div class="result-section">
            <div class="result-header">
                <h2 class="result-title">处理结果</h2>
                <button class="btn btn-secondary" onclick="clearResult()">清除结果</button>
            </div>
    `;

    // 显示实体信息
    if (result.entities && result.entities.length > 0) {
        html += `
            <div class="form-group">
                <h3 class="form-label">识别到的实体</h3>
                <div class="entities-grid">
                    ${result.entities.map(entity => `
                        <div class="entity-item">
                            <div class="entity-name">${escapeHtml(entity.name)}</div>
                            <span class="entity-type">${getEntityTypeLabel(entity.type)}</span>
                            <div class="entity-desc">${escapeHtml(entity.description || '暂无描述')}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 显示关系信息
    if (result.relations && result.relations.length > 0) {
        html += `
            <div class="form-group">
                <h3 class="form-label">识别的关系</h3>
                <div class="relations-list">
                    ${result.relations.map(relation => `
                        <div class="relation-item">
                            <div class="relation-entities">
                                <span>${escapeHtml(relation.source_entity)}</span>
                                <span class="relation-arrow">→</span>
                                <span class="relation-type">${escapeHtml(relation.relation_type)}</span>
                                <span class="relation-arrow">→</span>
                                <span>${escapeHtml(relation.target_entity)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // 显示原始JSON
    html += `
        <div class="form-group">
            <h3 class="form-label">原始数据</h3>
            <div class="result-content">${escapeHtml(JSON.stringify(result, null, 2))}</div>
        </div>
    `;

    html += '</div>';
    container.innerHTML = html;
    showMessage('内容处理完成', 'success');
}

// 清空内容
function clearContent() {
    document.getElementById('contentId').value = '';
    document.getElementById('contentText').value = '';
    showMessage('内容已清空', 'info');
}

// 清除结果
function clearResult() {
    document.getElementById('result-container').innerHTML = '';
    state.lastResult = null;
    showMessage('结果已清除', 'info');
}

// 工具函数
function showLoading() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <p>正在处理内容，请稍候...</p>
        </div>
    `;
    document.body.appendChild(overlay);
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) overlay.remove();
}

function showMessage(message, type = 'info') {
    window.showError(message, type);
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

