/**
 * 图谱可视化页面功能模块
 * 负责知识图谱的展示、交互和数据管理
 */

// 全局状态管理
const state = {
    nodes: [],
    links: [],
    svg: null,
    simulation: null,
    width: 800,
    height: 600,
    selectedNode: null,
    loading: false
};

// 页面初始化
function initializePage() {
    try {
        if (typeof window.KGAPI !== 'object') {
            throw new Error('KGAPI未加载，请检查config.js和api.js是否正确加载');
        }
        
        if (typeof d3 === 'undefined') {
            throw new Error('D3.js库未加载，请检查网络连接');
        }
        
        const graphSvg = document.getElementById('graph-svg');
        
        if (!graphSvg) {
            throw new Error('图谱容器未找到');
        }
        
        setupGraph();
        setupEventListeners();
        loadGraphData();
        
    } catch (error) {
        showError('页面初始化失败: ' + error.message, 'error');
        
        if (error.message.includes('未加载')) {
            setTimeout(initializePage, 3000);
        }
    }
}

// 设置事件监听器
function setupEventListeners() {
    // 搜索表单
    document.getElementById('searchForm').addEventListener('submit', (e) => {
        e.preventDefault();
        searchEntities();
    });

    // 重置按钮
    document.getElementById('resetBtn').addEventListener('click', () => {
        document.getElementById('searchForm').reset();
        const depth = parseInt(document.getElementById('depth')?.value) || 2;
        loadGraphData(depth);
    });

    // 刷新按钮
    document.getElementById('refreshBtn').addEventListener('click', () => {
        const depth = parseInt(document.getElementById('depth')?.value) || 2;
        loadGraphData(depth);
    });

    // 重置视图按钮
    const resetViewBtn = document.getElementById('resetViewBtn');
    if (resetViewBtn) {
        resetViewBtn.addEventListener('click', resetView);
    }

    // 窗口大小变化
    window.addEventListener('resize', () => {
        setTimeout(resizeGraph, 300);
    });
}

// 设置图谱
function setupGraph() {
    const container = document.getElementById('graph-svg');
    
    if (!container) {
        throw new Error('图谱容器(graph-svg)未找到，请检查HTML结构');
    }
    
    const rect = container.getBoundingClientRect();
    state.width = rect.width - 40;
    state.height = rect.height - 40;

    try {
        state.svg = d3.select('#graph-svg')
            .append('svg')
            .attr('width', state.width)
            .attr('height', state.height);
            
        state.svg.call(d3.zoom()
                .scaleExtent([0.1, 10])
                .on('zoom', handleZoom));

        state.svg.append('g');

        state.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(state.width / 2, state.height / 2))
            .force('collision', d3.forceCollide().radius(30))
            .alphaDecay(0.05)
            .velocityDecay(0.3);
            
    } catch (error) {
        throw new Error(`创建图谱失败: ${error.message}`);
    }
}

// 加载图谱数据
async function loadGraphData(depth = 2) {
    if (state.loading) return;
    
    try {
        state.loading = true;
        showLoading(true, 'graph-svg');
        
        let entitiesRes;
        try {
            entitiesRes = await window.KGAPI.getEntities({
                page: 1,
                page_size: 50
            });
        } catch (apiError) {
            throw new Error(`获取实体列表失败: ${apiError.message}`);
        }
        
        if (!entitiesRes || !entitiesRes.items || entitiesRes.items.length === 0) {
            showError('暂无实体数据', 'info');
            return;
        }
        
        // 选择一个合适的实体作为中心（优先选择有邻居的实体）
        let centerEntity = entitiesRes.items[0];
        
        // 尝试找到第一个有关系的实体
        for (const entity of entitiesRes.items.slice(0, 5)) {
            try {
                const testNeighbors = await window.KGAPI.getEntityNeighbors(entity.id, {
                    depth: 1,
                    max_entities: 10
                });
                if (testNeighbors && testNeighbors.nodes && testNeighbors.nodes.length > 1) {
                    centerEntity = entity;
                    break;
                }
            } catch (e) {
                continue;
            }
        }
        
        let neighborsResponse;
        try {
            neighborsResponse = await window.KGAPI.getEntityNeighbors(centerEntity.id, {
                depth: depth,
                max_entities: 100
            });
        } catch (apiError) {
            throw new Error(`获取邻居网络失败: ${apiError.message}`);
        }
        
        if (!neighborsResponse || !neighborsResponse.nodes || !neighborsResponse.edges) {
            throw new Error('邻居网络数据格式不正确');
        }
        
        state.nodes = neighborsResponse.nodes || [];
        state.links = neighborsResponse.edges || [];
        
        if (state.nodes.length > 0) {
            renderGraph();
        } else {
            showError('暂无图谱数据', 'info');
        }
        
    } catch (error) {
        showError(`加载图谱失败: ${error.message}`, 'error');
    } finally {
        state.loading = false;
        hideLoading('graph-svg');
    }
}

// 渲染图谱
function renderGraph() {
    if (!state.svg) return;
    
    const g = state.svg.select('g');
    g.selectAll('*').remove();

    // 确保连线数据中的source和target是节点对象引用
    const linksWithReferences = state.links.map(link => {
        const sourceNode = state.nodes.find(n => n.id === link.source);
        const targetNode = state.nodes.find(n => n.id === link.target);
        return {
            ...link,
            source: sourceNode || link.source,
            target: targetNode || link.target
        };
    });

    // 创建连线
    const link = g.append('g')
        .selectAll('line')
        .data(linksWithReferences)
        .enter().append('line')
        .attr('class', 'graph-link')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.strength || 1));

    // 创建节点 - 根据层级调整大小和颜色深度
    const node = g.append('g')
        .selectAll('circle')
        .data(state.nodes)
        .enter().append('circle')
        .attr('class', d => `graph-node level-${d.level || 0}`)
        .attr('r', d => {
            if (d.is_center) return 25;
            const level = d.level || 1;
            return Math.max(15, 25 - level * 3);
        })
        .attr('fill', d => {
            const baseColor = getNodeColor(d.entity_type);
            const level = d.level || 0;
            const opacity = Math.max(0.6, 1 - level * 0.15);
            return d3.color(baseColor).copy({opacity: opacity});
        })
        .attr('class', d => {
            const levelClass = `level-${d.level || 0}`;
            return `graph-node ${levelClass}`;
        })
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended))
        .on('click', handleNodeClick)
        .on('mouseover', handleNodeMouseOver)
        .on('mouseout', handleNodeMouseOut);

    // 添加标签
    const label = g.append('g')
        .selectAll('text')
        .data(state.nodes)
        .enter().append('text')
        .attr('class', 'node-label')
        .attr('text-anchor', 'middle')
        .attr('dy', '.35em')
        .style('font-size', '12px')
        .style('fill', '#333')
        .text(d => d.name);

    // 更新力导向图
    try {
        if (!state.nodes || state.nodes.length === 0) {
            return;
        }
        
        state.simulation.nodes(state.nodes);
        
        state.simulation.force('link')
            .links(linksWithReferences)
            .distance(150);
            
        state.simulation.force('charge')
            .strength(-500);
            
        state.simulation.alpha(1).restart();
        
    } catch (error) {
        throw error;
    }

    // 更新位置
    state.simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);

        label
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    // 渲染图例和统计信息
    renderLegend();
    renderStats();
}

// 搜索实体
async function searchEntities() {
    const formData = new FormData(document.getElementById('searchForm'));
    const name = formData.get('name');
    const type = formData.get('type');
    const depth = parseInt(formData.get('depth')) || 2;
    
    if (!name && !type) {
        loadGraphData(depth);
        return;
    }
    
    showLoading(true, 'graph-svg');

    try {
        const response = await window.KGAPI.getEntities({
            page: 1,
            page_size: 50,
            search: name || null,
            entity_type: type || null
        });
        
        if (response.items.length === 0) {
            showError('未找到匹配的实体', 'info');
            hideLoading('graph-svg');
            return;
        }
        
        // 只显示搜索结果和它们的邻居
        const centerEntity = response.items[0];
        
        // 获取实体邻居网络
        const neighborsResponse = await window.KGAPI.getEntityNeighbors(centerEntity.id, {
            depth: depth,
            max_entities: 100
        });
        
        // 直接使用后端返回的节点和边数据，保持is_center和level信息
        state.nodes = neighborsResponse.nodes || [];
        state.links = neighborsResponse.edges || [];
        
        renderGraph();
        
    } catch (error) {
        showError('搜索失败，请检查网络连接或稍后重试', 'error');
    } finally {
        hideLoading('graph-svg');
    }
}

// 事件处理函数
function handleZoom(event) {
    d3.select('#graph-svg svg g').attr('transform', event.transform);
}

async function handleNodeClick(event, d) {
    event.stopPropagation();
    state.selectedNode = d;
    showNodeDetails(d);
    
    // 显示节点详情面板
    const detailsContainer = document.getElementById('node-details');
    if (detailsContainer) {
        detailsContainer.style.display = 'block';
    }
    
    // 双击节点时重新以该节点为中心加载邻居网络
    if (event.detail === 2) { // 双击
        const depth = parseInt(document.getElementById('depth')?.value) || 2;
        try {
            showLoading(true, 'graph-svg');
            const neighborsResponse = await window.KGAPI.getEntityNeighbors(d.id, {
                depth: depth,
                max_entities: 100
            });
            
            state.nodes = neighborsResponse.nodes || [];
            state.links = neighborsResponse.edges || [];
            
            renderGraph();
            
        } catch (error) {
            showError('重新加载邻居网络失败', 'error');
        } finally {
            hideLoading();
        }
    }
}

function handleNodeMouseOver(event, d) {
    // 根据层级动态调整悬停效果，保留层级信息
    const originalRadius = d.is_center ? 25 : Math.max(15, 25 - (d.level || 1) * 3);
    d3.select(event.target)
        .attr('r', originalRadius + 3) // 增加3px半径
        .style('stroke-width', 3); // 增加边框宽度
}

function handleNodeMouseOut(event, d) {
    // 恢复原始的动态计算值
    const originalRadius = d.is_center ? 25 : Math.max(15, 25 - (d.level || 1) * 3);
    d3.select(event.target)
        .attr('r', originalRadius) // 恢复原始半径
        .style('stroke-width', null); // 移除内联样式，恢复CSS默认
}

function dragstarted(event, d) {
    if (!event.active) state.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) state.simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

// 显示节点详情
function hideNodeDetails() {
    const detailsContainer = document.getElementById('node-details');
    if (detailsContainer) {
        detailsContainer.style.display = 'none';
    }
}

function showNodeDetails(node) {
    const detailsContainer = document.getElementById('node-details');
    detailsContainer.innerHTML = `
        <div class="detail-header">
            <h3 class="detail-title">${escapeHtml(node.name)}</h3>
            <button class="detail-close" onclick="hideNodeDetails()">&times;</button>
        </div>
        <div class="detail-content">
            <div class="detail-section">
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>类型:</label>
                        <span>${getEntityTypeLabel(node.entity_type)}</span>
                    </div>
                    <div class="detail-item">
                        <label>描述:</label>
                        <span>${escapeHtml(node.description || '暂无描述')}</span>
                    </div>
                    <div class="detail-item">
                        <label>创建时间:</label>
                        <span>${formatDate(node.created_at)}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h4>相关关系</h4>
                <div id="node-relations"></div>
            </div>
        </div>
    `;
    
    // 显示相关关系 - 修复：处理link.source和link.target可能是ID而不是对象的情况
    const relations = state.links.filter(link => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
        return sourceId === node.id || targetId === node.id;
    });
    
    const relationsContainer = document.getElementById('node-relations');
    if (relations.length > 0) {
        relationsContainer.innerHTML = relations.map(relation => {
            // 处理source和target可能是ID的情况
            const sourceId = typeof relation.source === 'object' ? relation.source.id : relation.source;
            const targetId = typeof relation.target === 'object' ? relation.target.id : relation.target;
            
            const isSource = sourceId === node.id;
            
            // 获取相关节点对象
            let sourceNode, targetNode;
            if (typeof relation.source === 'object') {
                sourceNode = relation.source;
            } else {
                sourceNode = state.nodes.find(n => n.id === sourceId) || { id: sourceId, name: `实体${sourceId}` };
            }
            
            if (typeof relation.target === 'object') {
                targetNode = relation.target;
            } else {
                targetNode = state.nodes.find(n => n.id === targetId) || { id: targetId, name: `实体${targetId}` };
            }
            
            const otherNode = isSource ? targetNode : sourceNode;
            const direction = isSource ? '→' : '←';
            
            // 获取关系类型（处理不同字段名）
            const relationType = relation.relation_type || relation.relationship || '关联';
            
            return `
                <div class="relation-item">
                    <span class="relation-entity">${escapeHtml(node.name)}</span>
                    <span class="relation-arrow">${direction}</span>
                    <span class="relation-type">${escapeHtml(relationType)}</span>
                    <span class="relation-arrow">${direction}</span>
                    <span class="relation-entity">${escapeHtml(otherNode.name)}</span>
                </div>
            `;
        }).join('');
    } else {
        relationsContainer.innerHTML = '<div class="empty-text">暂无相关关系</div>';
    }
}

// 工具函数
function getNodeColor(type) {
    const colors = {
        '人物': '#3b82f6',
        '公司': '#10b981',
        '组织': '#10b981',
        '地点': '#f59e0b',
        '事件': '#ef4444',
        '产品': '#8b5cf6',
        '概念': '#06b6d4',
        '其他': '#6b7280'
    };
    return colors[type] || colors['其他'];
}

function getEntityTypeLabel(type) {
    // API返回的是中文类型，直接返回或提供默认值
    return type || '未知';
}



function resizeGraph() {
    if (state.svg) {
        const container = document.getElementById('graph-svg');
        if (!container) return;
        
        const rect = container.getBoundingClientRect();
        state.width = rect.width - 40;
        state.height = rect.height - 40;
        
        state.svg
            .attr('width', state.width)
            .attr('height', state.height);
        
        if (state.simulation) {
            state.simulation
                .force('center', d3.forceCenter(state.width / 2, state.height / 2))
                .alpha(0.3).restart();
        }
    }
}

function showLoading(show = true, containerId = 'graph-svg') {
    if (!show) return;
    
    const container = document.getElementById(containerId);
    if (container) {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.innerHTML = '正在加载数据...';
        container.appendChild(loadingDiv);
    }
}

function hideLoading(containerId = 'graph-svg') {
    const container = document.getElementById(containerId);
    if (container && container.querySelector('.loading')) {
        const loadingElement = container.querySelector('.loading');
        if (loadingElement) {
            loadingElement.remove();
        }
    }
}

function showError(message, type = 'error') {
    // 只在开发环境显示日志
    console.error('Error:', message);
    alert(message);
}

// 修复缺失的控制函数
function resetGraph() {
    if (state.simulation) {
        state.simulation.alpha(1).restart();
    }
}

function toggleLabels() {
    const labels = document.querySelectorAll('.link-label');
    labels.forEach(label => {
        label.style.display = label.style.display === 'none' ? 'block' : 'none';
    });
}

function toggleAnimation() {
    if (state.simulation) {
        if (state.simulation.alpha() > 0) {
            state.simulation.stop();
        } else {
            state.simulation.restart();
        }
    }
}

function exportGraph() {
    if (!state.svg) return;
    
    const svgElement = state.svg.node();
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svgElement);
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    canvas.width = state.width;
    canvas.height = state.height;
    
    img.onload = function() {
        ctx.drawImage(img, 0, 0);
        const link = document.createElement('a');
        link.download = 'knowledge-graph.png';
        link.href = canvas.toDataURL();
        link.click();
    };
    
    img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgString)));
}

function resetView() {
    if (state.svg) {
        state.svg.transition().duration(750).call(
            d3.zoom().transform,
            d3.zoomIdentity
        );
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '未知时间';
    try {
        // 处理不同格式的日期字符串
        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
            return '未知时间';
        }
        return date.toLocaleString('zh-CN');
    } catch {
        return '未知时间';
    }
}

// 渲染图例
function renderLegend() {
    const legendContainer = document.getElementById('legend');
    if (!legendContainer) return;
    
    const entityTypes = [
        { type: '人物', label: '人物', color: '#3b82f6' },
        { type: '公司', label: '公司', color: '#10b981' },
        { type: '组织', label: '组织', color: '#10b981' },
        { type: '地点', label: '地点', color: '#f59e0b' },
        { type: '事件', label: '事件', color: '#ef4444' },
        { type: '产品', label: '产品', color: '#8b5cf6' },
        { type: '概念', label: '概念', color: '#06b6d4' },
        { type: '其他', label: '其他', color: '#6b7280' }
    ];
    
    legendContainer.innerHTML = `
        <h4>图例</h4>
        ${entityTypes.map(item => `
            <div class="legend-item">
                <div class="legend-color" style="background-color: ${item.color}"></div>
                <span class="legend-label">${item.label}</span>
            </div>
        `).join('')}
    `;
}

// 渲染统计信息
function renderStats() {
    const statsContainer = document.getElementById('stats');
    if (!statsContainer) return;
    
    const nodes = state.nodes || [];
    const links = state.links || [];
    
    // 统计各类实体数量
    const typeCounts = {};
    nodes.forEach(node => {
        const type = node.entity_type || '其他';
        typeCounts[type] = (typeCounts[type] || 0) + 1;
    });
    
    // 统计层级分布
    const levelCounts = {};
    nodes.forEach(node => {
        const level = node.level || 0;
        levelCounts[level] = (levelCounts[level] || 0) + 1;
    });
    
    const entityTypes = [
        { type: '人物', label: '人物' },
        { type: '公司', label: '公司' },
        { type: '组织', label: '组织' },
        { type: '地点', label: '地点' },
        { type: '事件', label: '事件' },
        { type: '产品', label: '产品' },
        { type: '概念', label: '概念' },
        { type: '其他', label: '其他' }
    ];
    
    let levelStatsHtml = '';
    if (Object.keys(levelCounts).length > 1) {
        levelStatsHtml = '<h5>层级分布</h5>';
        Object.keys(levelCounts).sort((a, b) => parseInt(a) - parseInt(b)).forEach(level => {
            const levelName = level === '0' ? '中心节点' : `第${level}层`;
            levelStatsHtml += `
                <div class="stats-item">
                    <span class="stats-label">${levelName}:</span>
                    <span class="stats-value">${levelCounts[level]}</span>
                </div>
            `;
        });
    }
    
    statsContainer.innerHTML = `
        <h4>统计信息</h4>
        <div class="stats-item">
            <span class="stats-label">总实体数:</span>
            <span class="stats-value">${nodes.length}</span>
        </div>
        <div class="stats-item">
            <span class="stats-label">总关系数:</span>
            <span class="stats-value">${links.length}</span>
        </div>
        <div class="stats-item">
            <span class="stats-label">连接密度:</span>
            <span class="stats-value">${nodes.length > 0 ? Math.round((links.length / nodes.length) * 100) / 100 : 0}</span>
        </div>
        ${levelStatsHtml}
        <h5>实体类型</h5>
        ${entityTypes.map(item => {
            const count = typeCounts[item.type] || 0;
            return count > 0 ? `
                <div class="stats-item">
                    <span class="stats-label">${item.label}:</span>
                    <span class="stats-value">${count}</span>
                </div>
            ` : '';
        }).join('')}
    `;
}
// 页面初始化函数
function initGraphPage() {
    console.log('开始检查依赖项...');
    
    // 检查所有必需的依赖
    const dependencies = {
        'd3': typeof d3 !== 'undefined',
        'KGAPI': typeof window.KGAPI === 'object',
        'axios': typeof axios !== 'undefined',
        'ElementPlus': typeof ElementPlus !== 'undefined'
    };
    
    console.log('依赖项状态:', dependencies);
    
    // 检查是否有缺失的依赖
    const missingDeps = Object.keys(dependencies).filter(key => !dependencies[key]);
    
    if (missingDeps.length > 0) {
        console.warn(`等待依赖加载: ${missingDeps.join(', ')}`);
        setTimeout(initGraphPage, 200);
        return;
    }
    
    console.log('所有依赖项已加载，开始初始化页面');
    try {
        initializePage();
    } catch (error) {
        console.error('页面初始化失败:', error);
        showError('页面初始化失败: ' + error.message, 'error');
    }
}

// 页面加载完成后初始化 - 使用更可靠的加载方式
window.addEventListener('load', function() {
    console.log('页面load事件触发，开始初始化');
    setTimeout(initGraphPage, 100); // 给CDN资源一点加载时间
});

// 如果页面已经加载完成，立即初始化
if (document.readyState === 'complete') {
    console.log('页面已加载完成，立即初始化');
    setTimeout(initGraphPage, 100);
}

