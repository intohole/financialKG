/**
 * 知识图谱网络图组件库
 * 提供网络图可视化组件
 */

/**
 * 网络图组件
 */
class NetworkGraph {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            width: 800,
            height: 600,
            nodeRadius: 20,
            linkDistance: 100,
            chargeStrength: -300,
            centerForce: 0.05,
            showLabels: true,
            showTooltips: true,
            enableZoom: true,
            enableDrag: true,
            ...options
        };
        
        this.svg = null;
        this.g = null;
        this.simulation = null;
        this.nodes = [];
        this.links = [];
        this.nodeElements = null;
        this.linkElements = null;
        this.labelElements = null;
        this.tooltip = null;
        this.zoom = null;
        this.eventListeners = new Map();
        
        this.init();
    }

    /**
     * 初始化网络图
     */
    init() {
        // 创建SVG容器
        this.createSVG();
        
        // 创建提示框
        if (this.options.showTooltips) {
            this.createTooltip();
        }
        
        // 创建力导向图模拟
        this.createSimulation();
        
        // 绑定事件
        this.bindEvents();
    }

    /**
     * 创建SVG容器
     */
    createSVG() {
        // 设置容器样式
        this.container.style.position = 'relative';
        this.container.style.width = `${this.options.width}px`;
        this.container.style.height = `${this.options.height}px`;
        this.container.style.overflow = 'hidden';
        
        // 创建SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height);
        
        // 创建主要的g元素
        this.g = this.svg.append('g');
        
        // 启用缩放
        if (this.options.enableZoom) {
            this.zoom = d3.zoom()
                .scaleExtent([0.1, 10])
                .on('zoom', (event) => {
                    this.g.attr('transform', event.transform);
                });
            
            this.svg.call(this.zoom);
        }
    }

    /**
     * 创建提示框
     */
    createTooltip() {
        this.tooltip = d3.select('body')
            .append('div')
            .attr('class', 'network-tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('z-index', '1000');
    }

    /**
     * 创建力导向图模拟
     */
    createSimulation() {
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(this.options.linkDistance))
            .force('charge', d3.forceManyBody().strength(this.options.chargeStrength))
            .force('center', d3.forceCenter(this.options.width / 2, this.options.height / 2))
            .force('collision', d3.forceCollide().radius(this.options.nodeRadius + 5));
    }

    /**
     * 渲染网络图
     */
    render(data) {
        if (!data) return;
        
        this.nodes = data.nodes || [];
        this.links = data.links || [];
        
        // 更新模拟
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        
        // 渲染连线
        this.renderLinks();
        
        // 渲染节点
        this.renderNodes();
        
        // 渲染标签
        if (this.options.showLabels) {
            this.renderLabels();
        }
        
        // 启动模拟
        this.simulation.alpha(1).restart();
    }

    /**
     * 渲染连线
     */
    renderLinks() {
        this.linkElements = this.g.selectAll('.link')
            .data(this.links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => Math.sqrt(d.value || 1));
    }

    /**
     * 渲染节点
     */
    renderNodes() {
        this.nodeElements = this.g.selectAll('.node')
            .data(this.nodes)
            .enter()
            .append('circle')
            .attr('class', 'node')
            .attr('r', d => d.radius || this.options.nodeRadius)
            .attr('fill', d => UIUtils.getEntityTypeColor(d.type))
            .attr('stroke', '#fff')
            .attr('stroke-width', 2)
            .call(d3.drag()
                .on('start', (event, d) => this.dragstarted(event, d))
                .on('drag', (event, d) => this.dragged(event, d))
                .on('end', (event, d) => this.dragended(event, d)));
        
        // 添加鼠标事件
        if (this.options.showTooltips) {
            this.nodeElements
                .on('mouseover', (event, d) => this.showTooltip(event, d))
                .on('mouseout', () => this.hideTooltip());
        }
        
        // 添加点击事件
        this.nodeElements
            .on('click', (event, d) => this.handleNodeClick(event, d));

        // 添加双击事件
        this.nodeElements
            .on('dblclick', (event, d) => this.handleNodeDoubleClick(event, d));
    }

    /**
     * 渲染标签
     */
    renderLabels() {
        this.labelElements = this.g.selectAll('.label')
            .data(this.nodes)
            .enter()
            .append('text')
            .attr('class', 'label')
            .attr('text-anchor', 'middle')
            .attr('dy', '.35em')
            .attr('font-size', '12px')
            .attr('fill', '#333')
            .text(d => d.name);
    }

    /**
     * 显示提示框
     */
    showTooltip(event, d) {
        this.tooltip.transition()
            .duration(200)
            .style('opacity', .9);
        
        this.tooltip.html(`
            <div><strong>${d.name}</strong></div>
            <div>类型: ${d.type}</div>
            <div>ID: ${d.id}</div>
        `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px');
    }

    /**
     * 隐藏提示框
     */
    hideTooltip() {
        this.tooltip.transition()
            .duration(500)
            .style('opacity', 0);
    }

    /**
     * 处理节点点击
     */
    handleNodeClick(event, d) {
        event.stopPropagation();
        
        // 触发事件
        this.emit('node:click', {
            node: d,
            event: event
        });
    }

    /**
     * 处理节点双击
     */
    handleNodeDoubleClick(event, d) {
        event.stopPropagation();
        
        // 触发事件
        this.emit('node:dblclick', {
            node: d,
            event: event
        });
    }

    /**
     * 拖拽开始
     */
    dragstarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    /**
     * 拖拽中
     */
    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    /**
     * 拖拽结束
     */
    dragended(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    /**
     * 更新位置
     */
    tick() {
        if (this.linkElements) {
            this.linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
        }
        
        if (this.nodeElements) {
            this.nodeElements
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
        }
        
        if (this.labelElements) {
            this.labelElements
                .attr('x', d => d.x)
                .attr('y', d => d.y);
        }
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        this.simulation.on('tick', () => this.tick());
    }

    /**
     * 添加节点
     */
    addNode(node) {
        this.nodes.push(node);
        this.simulation.nodes(this.nodes);
        this.render({ nodes: this.nodes, links: this.links });
    }

    /**
     * 添加连线
     */
    addLink(link) {
        this.links.push(link);
        this.simulation.force('link').links(this.links);
        this.render({ nodes: this.nodes, links: this.links });
    }

    /**
     * 移除节点
     */
    removeNode(nodeId) {
        this.nodes = this.nodes.filter(node => node.id !== nodeId);
        this.links = this.links.filter(link => link.source.id !== nodeId && link.target.id !== nodeId);
        this.simulation.nodes(this.nodes);
        this.simulation.force('link').links(this.links);
        this.render({ nodes: this.nodes, links: this.links });
    }

    /**
     * 移除连线
     */
    removeLink(linkId) {
        this.links = this.links.filter(link => link.id !== linkId);
        this.simulation.force('link').links(this.links);
        this.render({ nodes: this.nodes, links: this.links });
    }

    /**
     * 高亮节点
     */
    highlightNode(nodeId) {
        if (this.nodeElements) {
            this.nodeElements
                .attr('opacity', d => d.id === nodeId ? 1 : 0.3)
                .attr('stroke-width', d => d.id === nodeId ? 4 : 2);
        }
        
        if (this.linkElements) {
            this.linkElements
                .attr('opacity', d => (d.source.id === nodeId || d.target.id === nodeId) ? 1 : 0.1)
                .attr('stroke-width', d => (d.source.id === nodeId || d.target.id === nodeId) ? 3 : 1);
        }
    }

    /**
     * 取消高亮
     */
    unhighlightAll() {
        if (this.nodeElements) {
            this.nodeElements
                .attr('opacity', 1)
                .attr('stroke-width', 2);
        }
        
        if (this.linkElements) {
            this.linkElements
                .attr('opacity', 0.6)
                .attr('stroke-width', d => Math.sqrt(d.value || 1));
        }
    }

    /**
     * 清空网络图
     */
    clear() {
        this.nodes = [];
        this.links = [];
        
        if (this.g) {
            this.g.selectAll('*').remove();
        }
        
        this.simulation.nodes([]);
        this.simulation.force('link').links([]);
        this.simulation.alpha(1).restart();
    }

    /**
     * 重置缩放
     */
    resetZoom() {
        if (this.zoom && this.svg) {
            this.svg.transition()
                .duration(750)
                .call(this.zoom.transform, d3.zoomIdentity);
        }
    }

    /**
     * 调整大小
     */
    resize(width, height) {
        this.options.width = width;
        this.options.height = height;
        
        this.container.style.width = `${width}px`;
        this.container.style.height = `${height}px`;
        
        if (this.svg) {
            this.svg.attr('width', width).attr('height', height);
        }
        
        if (this.simulation) {
            this.simulation.force('center', d3.forceCenter(width / 2, height / 2));
            this.simulation.alpha(1).restart();
        }
    }

    /**
     * 销毁网络图
     */
    destroy() {
        // 停止模拟
        if (this.simulation) {
            this.simulation.stop();
        }
        
        // 移除提示框
        if (this.tooltip) {
            this.tooltip.remove();
        }
        
        // 清空SVG
        if (this.svg) {
            this.svg.remove();
        }
        
        this.eventListeners.clear();
    }
}

/**
 * 网络图控制器
 */
class NetworkGraphController {
    constructor(container, options = {}) {
        this.container = container;
        this.graph = new NetworkGraph(container, options);
        this.selectedNode = null;
        this.selectedLink = null;
        this.eventListeners = new Map();
        
        this.init();
    }

    /**
     * 初始化控制器
     */
    init() {
        // 监听网络图事件
        this.container.addEventListener('node:click', (e) => {
            this.handleNodeClick(e.detail.node);
        });
        
        // 创建控制面板
        this.createControlPanel();
    }

    /**
     * 创建控制面板
     */
    createControlPanel() {
        const panel = document.createElement('div');
        panel.className = 'network-control-panel';
        panel.innerHTML = `
            <div class="control-group">
                <button class="btn btn-sm btn-outline" id="reset-zoom-btn">
                    <i class="fas fa-search-minus"></i> 重置缩放
                </button>
                <button class="btn btn-sm btn-outline" id="center-graph-btn">
                    <i class="fas fa-crosshairs"></i> 居中显示
                </button>
            </div>
            <div class="control-group">
                <label>
                    <input type="checkbox" id="show-labels-checkbox" checked> 显示标签
                </label>
                <label>
                    <input type="checkbox" id="show-tooltips-checkbox" checked> 显示提示
                </label>
            </div>
        `;
        
        this.container.appendChild(panel);
        
        // 绑定控制事件
        this.bindControlEvents();
    }

    /**
     * 绑定控制事件
     */
    bindControlEvents() {
        // 重置缩放
        document.getElementById('reset-zoom-btn').addEventListener('click', () => {
            this.graph.resetZoom();
        });
        
        // 居中显示
        document.getElementById('center-graph-btn').addEventListener('click', () => {
            this.centerGraph();
        });
        
        // 显示标签
        document.getElementById('show-labels-checkbox').addEventListener('change', (e) => {
            this.toggleLabels(e.target.checked);
        });
        
        // 显示提示
        document.getElementById('show-tooltips-checkbox').addEventListener('change', (e) => {
            this.toggleTooltips(e.target.checked);
        });
    }

    /**
     * 处理节点点击
     */
    handleNodeClick(node) {
        if (this.selectedNode && this.selectedNode.id === node.id) {
            // 取消选择
            this.selectedNode = null;
            this.graph.unhighlightAll();
            this.emit('node:deselect', { node });
        } else {
            // 选择新节点
            this.selectedNode = node;
            this.graph.highlightNode(node.id);
            this.emit('node:select', { node });
        }
    }

    /**
     * 居中显示
     */
    centerGraph() {
        if (this.graph.nodes.length > 0) {
            this.graph.resetZoom();
        }
    }

    /**
     * 切换标签显示
     */
    toggleLabels(show) {
        if (show) {
            this.graph.renderLabels();
        } else {
            if (this.graph.labelElements) {
                this.graph.labelElements.remove();
                this.graph.labelElements = null;
            }
        }
    }

    /**
     * 切换提示显示
     */
    toggleTooltips(show) {
        if (show) {
            this.graph.createTooltip();
            if (this.graph.nodeElements) {
                this.graph.nodeElements
                    .on('mouseover', (event, d) => this.graph.showTooltip(event, d))
                    .on('mouseout', () => this.graph.hideTooltip());
            }
        } else {
            if (this.graph.tooltip) {
                this.graph.tooltip.remove();
                this.graph.tooltip = null;
            }
            if (this.graph.nodeElements) {
                this.graph.nodeElements
                    .on('mouseover', null)
                    .on('mouseout', null);
            }
        }
    }

    /**
     * 触发事件
     */
    emit(eventName, data) {
        const event = new CustomEvent(eventName, {
            detail: data,
            bubbles: true
        });
        this.container.dispatchEvent(event);
    }

    /**
     * 获取选中的节点
     */
    getSelectedNode() {
        return this.selectedNode;
    }

    /**
     * 清空选择
     */
    clearSelection() {
        this.selectedNode = null;
        this.selectedLink = null;
        this.graph.unhighlightAll();
    }

    /**
     * 销毁控制器
     */
    destroy() {
        this.graph.destroy();
        this.eventListeners.clear();
    }
}

// 导出网络图组件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NetworkGraph, NetworkGraphController };
} else {
    // 浏览器环境，挂载到全局对象
    window.NetworkGraph = NetworkGraph;
    window.NetworkGraphController = NetworkGraphController;
}