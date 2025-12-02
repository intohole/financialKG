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
    if (typeof window.KGAPI === 'object' && typeof d3 !== 'undefined') {
        setupGraph();
        loadGraphData();
        setupEventListeners();
    } else {
        setTimeout(initializePage, 100);
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

    // 窗口大小变化
    window.addEventListener('resize', () => {
        setTimeout(resizeGraph, 300);
    });
}

// 设置图谱
function setupGraph() {
    const container = document.getElementById('graph-svg');
    
    if (!container) {
        // 只在开发环境显示日志
        console.error('图谱容器未找到');
        return;
    }
    
    // 获取容器尺寸
    const rect = container.getBoundingClientRect();
    state.width = rect.width - 40;
    state.height = rect.height - 40;

    // 创建SVG
    state.svg = d3.select('#graph-svg')
        .append('svg')
        .attr('width', state.width)
        .attr('height', state.height)
        .call(d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', handleZoom));

    // 创建主容器
    const g = state.svg.append('g');

    // 创建力导向图
    state.simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(state.width / 2, state.height / 2))
        .force('collision', d3.forceCollide().radius(30));
}

// 加载图谱数据
async function loadGraphData(depth = 2) {
    if (state.loading) return;
    
    try {
        state.loading = true;
        showLoading(true, 'graph-svg');
        
        // 获取实体数据
        const entitiesRes = await window.KGAPI.getEntities({
            page: 1,
            page_size: 50
        });
        
        if (entitiesRes.items.length === 0) {
            showError('暂无实体数据', 'info');
            state.loading = false;
            hideLoading();
            return;
        }
        
        // 选择第一个实体作为中心，获取其邻居网络
        const centerEntity = entitiesRes.items[0];
        console.log(`获取实体 ${centerEntity.id} 的邻居网络，深度: ${depth}`);
        const neighborsResponse = await window.KGAPI.getEntityNeighbors(centerEntity.id, {
            depth: depth,
            max_entities: 100
        });
        
        console.log(`获取到 ${neighborsResponse.nodes?.length || 0} 个节点，${neighborsResponse.edges?.length || 0} 条边`);
        state.nodes = neighborsResponse.nodes || [];
        state.links = neighborsResponse.edges || [];
        
        if (state.nodes.length > 0) {
            renderGraph();
        } else {
            showError('暂无图谱数据', 'info');
        }
        
    } catch (error) {
        // 只在开发环境显示日志
        console.error('加载图谱失败:', error);
        showError('加载图谱失败，请稍后重试', 'error');
    } finally {
        state.loading = false;
        hideLoading();
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

    // 创建节点
    const node = g.append('g')
        .selectAll('circle')
        .data(state.nodes)
        .enter().append('circle')
        .attr('class', 'graph-node')
        .attr('r', 20)
        .attr('fill', d => getNodeColor(d.entity_type))
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
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
    state.simulation.nodes(state.nodes);
    state.simulation.force('link')
        .links(linksWithReferences)
        .distance(150); // 增加连线距离，确保深度为2的邻居能正确显示
    state.simulation.force('charge')
        .strength(-500); // 增加排斥力，确保节点不会重叠
    state.simulation.alpha(1).restart();

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

    try {
        showLoading();
        
        const response = await window.KGAPI.getEntities({
            page: 1,
            page_size: 50,
            search: name || null,
            entity_type: type || null
        });
        
        if (response.items.length === 0) {
            showError('未找到匹配的实体', 'info');
            hideLoading();
            return;
        }
        
        // 只显示搜索结果和它们的邻居
        const centerEntity = response.items[0];
        
        // 获取实体邻居网络
        console.log(`获取实体 ${centerEntity.id} 的邻居网络，深度: ${depth}`);
        const neighborsResponse = await window.KGAPI.getEntityNeighbors(centerEntity.id, {
            depth: depth,
            max_entities: 100
        });
        
        console.log(`获取到 ${neighborsResponse.nodes?.length || 0} 个节点，${neighborsResponse.edges?.length || 0} 条边`);
        state.nodes = neighborsResponse.nodes || [];
        state.links = neighborsResponse.edges || [];
        renderGraph();
        
    } catch (error) {
        // 只在开发环境显示日志
        console.error('搜索失败:', error);
        showError('搜索失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// 事件处理函数
function handleZoom(event) {
    d3.select('#graph-svg svg g').attr('transform', event.transform);
}

function handleNodeClick(event, d) {
    event.stopPropagation();
    state.selectedNode = d;
    showNodeDetails(d);
    
    // 显示节点详情面板
    const detailsContainer = document.getElementById('node-details');
    if (detailsContainer) {
        detailsContainer.style.display = 'block';
    }
}

function handleNodeMouseOver(event, d) {
    d3.select(event.target)
        .attr('r', 25)
        .attr('stroke-width', 3);
}

function handleNodeMouseOut(event, d) {
    d3.select(event.target)
        .attr('r', 20)
        .attr('stroke-width', 2);
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
                        <span>${getEntityTypeLabel(node.type)}</span>
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
    
    // 显示相关关系
    const relations = state.links.filter(link => 
        link.source.id === node.id || link.target.id === node.id
    );
    
    const relationsContainer = document.getElementById('node-relations');
    if (relations.length > 0) {
        relationsContainer.innerHTML = relations.map(relation => {
            const isSource = relation.source.id === node.id;
            const otherNode = isSource ? relation.target : relation.source;
            const direction = isSource ? '→' : '←';
            
            return `
                <div class="relation-item">
                    <span class="relation-entity">${escapeHtml(node.name)}</span>
                    <span class="relation-arrow">${direction}</span>
                    <span class="relation-type">${escapeHtml(relation.relationship)}</span>
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
        person: '#3b82f6',
        organization: '#10b981',
        location: '#f59e0b',
        event: '#ef4444',
        product: '#8b5cf6',
        concept: '#06b6d4',
        other: '#6b7280'
    };
    return colors[type] || colors.other;
}

function getEntityTypeLabel(type) {
    const labels = {
        person: '人物',
        organization: '组织',
        location: '地点',
        event: '事件',
        product: '产品',
        concept: '概念',
        company: '公司',
        business: '企业',
        technology: '科技公司',
        brand: '品牌',
        institution: '机构',
        government: '政府',
        school: '学校',
        hospital: '医院',
        city: '城市',
        country: '国家',
        province: '省份',
        other: '其他'
    };
    return labels[type] || type || '未知';
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

function showLoading() {
    // 加载状态由CSS处理
}

function hideLoading() {
    const container = document.getElementById('graph-svg');
    if (container && container.querySelector('.loading-spinner')) {
        container.innerHTML = '';
    }
    if (state.nodes.length > 0) {
        renderGraph();
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
        return new Date(dateString).toLocaleString('zh-CN');
    } catch {
        return '未知时间';
    }
}

// 渲染图例
function renderLegend() {
    const legendContainer = document.getElementById('legend');
    if (!legendContainer) return;
    
    const entityTypes = [
        { type: 'person', label: '人物', color: '#3b82f6' },
        { type: 'organization', label: '组织', color: '#10b981' },
        { type: 'location', label: '地点', color: '#f59e0b' },
        { type: 'event', label: '事件', color: '#ef4444' },
        { type: 'product', label: '产品', color: '#8b5cf6' },
        { type: 'concept', label: '概念', color: '#06b6d4' },
        { type: 'other', label: '其他', color: '#6b7280' }
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
        const type = node.type || 'other';
        typeCounts[type] = (typeCounts[type] || 0) + 1;
    });
    
    const entityTypes = [
        { type: 'person', label: '人物' },
        { type: 'organization', label: '组织' },
        { type: 'location', label: '地点' },
        { type: 'event', label: '事件' },
        { type: 'product', label: '产品' },
        { type: 'concept', label: '概念' },
        { type: 'other', label: '其他' }
    ];
    
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

// 页面初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePage);
} else {
    initializePage();
}

