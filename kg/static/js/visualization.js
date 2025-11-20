// Knowledge Graph Visualization JavaScript

// Global variables for graph visualization
let network = null;
let graphData = null;
let nodes = [];
let edges = [];
let currentLayout = 'forceDirected';

// Initialize the Visualization page
function initVisualizationPage() {
    console.log('Visualization page initialized');
    
    // Set up event listeners
    setupVisualizationEvents();
    
    // Load initial graph data
    loadGraphData();
}

// Set up event listeners for Visualization functions
function setupVisualizationEvents() {
    // Search form
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            searchGraph();
        });
    }
    
    // Filter form
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', (e) => {
            e.preventDefault();
            filterGraph();
        });
    }
    
    // Layout controls
    const layoutSelect = document.getElementById('layout-select');
    if (layoutSelect) {
        layoutSelect.addEventListener('change', (e) => {
            changeLayout(e.target.value);
        });
    }
    
    // Refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadGraphData();
        });
    }
    
    // Clear button
    const clearBtn = document.getElementById('clear-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            clearFilter();
        });
    }
    
    // Statistics button
    const statsBtn = document.getElementById('stats-btn');
    if (statsBtn) {
        statsBtn.addEventListener('click', () => {
            showGraphStatistics();
        });
    }
}

// Load graph data from API
async function loadGraphData() {
    const loadingContainer = document.getElementById('graph-loading');
    const graphContainer = document.getElementById('graph-container');
    const errorContainer = document.getElementById('graph-error');
    
    try {
        showLoading(true, loadingContainer);
        showError(false, errorContainer);
        graphContainer.innerHTML = '<div class="d-flex justify-content-center align-items-center h-100"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Load initial graph data
        const result = await apiRequest('/api/v1/visualize/graph-data', 'GET');
        
        if (result && result.success) {
            graphData = result;
            renderGraph(result.nodes, result.edges, graphContainer);
            updateGraphStats(result.stats);
        } else {
            throw new Error('Failed to load graph data');
        }
        
    } catch (error) {
        console.error('Error loading graph data:', error);
        showError(true, errorContainer, 'Failed to load graph data. Please try again.');
        graphContainer.innerHTML = '';
    } finally {
        showLoading(false, loadingContainer);
    }
}

// Render the graph using vis-network
function renderGraph(nodesData, edgesData, container) {
    // Check if container exists
    if (!container) {
        console.error('Graph container not found');
        return;
    }
    
    // Create nodes and edges arrays
    nodes = new vis.DataSet(nodesData);
    edges = new vis.DataSet(edgesData);
    
    // Create network data
    const data = {
        nodes: nodes,
        edges: edges
    };
    
    // Configuration options
    const options = {
        nodes: {
            shape: 'circle',
            size: 25,
            font: {
                size: 12,
                color: '#ffffff'
            },
            color: {
                background: '#4caf50',
                border: '#388e3c'
            },
            shadow: {
                enabled: true,
                color: 'rgba(0, 0, 0, 0.3)',
                size: 5
            },
            scaling: {
                min: 15,
                max: 50
            }
        },
        edges: {
            width: 2,
            color: {
                color: '#9e9e9e',
                highlight: '#2196f3'
            },
            font: {
                size: 10,
                align: 'middle'
            },
            arrowStrikethrough: false,
            selectionWidth: 3
        },
        interaction: {
            dragNodes: true,
            zoomView: true,
            panView: true,
            selectable: true,
            selectConnectedEdges: true
        },
        layout: {
            randomSeed: 42,
            improvedLayout: true,
            hierarchical: {
                enabled: false,
                levelSeparation: 150,
                nodeSpacing: 100,
                parentCentralization: true,
                direction: 'UD', // UD, DU, LR, RL
                sortMethod: 'hubsize' // hubsize, directed
            },
            forceAtlas2Based: {
                gravitationalConstant: -50,
                centralGravity: 0.01,
                springLength: 100,
                springConstant: 0.08,
                damping: 0.4
            }
        },
        physics: {
            enabled: true,
            solver: 'forceAtlas2Based',
            stabilization: {
                enabled: true,
                iterations: 100
            }
        }
    };
    
    // Initialize network
    network = new vis.Network(container, data, options);
    
    // Set up network event listeners
    network.on('selectNode', handleNodeSelect);
    network.on('selectEdge', handleEdgeSelect);
    network.on('click', handleGraphClick);
    network.on('stabilized', () => {
        console.log('Graph stabilized');
    });
}

// Handle node selection
function handleNodeSelect(params) {
    const nodeId = params.nodes[0];
    const node = nodes.get(nodeId);
    
    if (node) {
        // Display node details
        showNodeDetails(node);
        
        // Highlight connected nodes and edges
        highlightConnected(nodeId);
    }
}

// Handle edge selection
function handleEdgeSelect(params) {
    const edgeId = params.edges[0];
    const edge = edges.get(edgeId);
    
    if (edge) {
        // Display edge details
        showEdgeDetails(edge);
    }
}

// Handle graph click
function handleGraphClick(params) {
    if (params.nodes.length === 0 && params.edges.length === 0) {
        // Clear selection
        clearSelection();
    }
}

// Search graph
async function searchGraph() {
    const searchInput = document.getElementById('search-query');
    const searchType = document.getElementById('search-type');
    
    if (!searchInput || !searchType) {
        return;
    }
    
    const query = searchInput.value.trim();
    const type = searchType.value;
    
    if (!query) {
        showAlert('error', 'Please enter a search query');
        return;
    }
    
    try {
        // 由于后端暂未实现搜索API，使用前端过滤实现搜索功能
        // 在现有图数据中进行前端搜索
        const filteredNodes = graphData.nodes.filter(node => 
            (type === 'all' || node.group === type) && 
            node.label.toLowerCase().includes(query.toLowerCase())
        );
        const filteredEdges = graphData.edges.filter(edge => 
            filteredNodes.some(node => node.id === edge.from_id || node.id === edge.to_id) ||
            edge.label.toLowerCase().includes(query.toLowerCase())
        );
        const result = { success: true, nodes: filteredNodes, edges: filteredEdges };
        
        if (result && result.success) {
            // Highlight search results
            highlightSearchResults(result.nodes, result.edges);
            
            // Center on search results
            if (result.nodes.length > 0) {
                network.focus(result.nodes, { animation: true });
            }
            
            showAlert('success', `Found ${result.nodes.length} nodes and ${result.edges.length} edges`);
        }
        
    } catch (error) {
        console.error('Error searching graph:', error);
        showAlert('error', 'Failed to search graph. Please try again.');
    }
}

// Filter graph
async function filterGraph() {
    const entityTypeFilter = document.getElementById('entity-type-filter');
    const relationTypeFilter = document.getElementById('relation-type-filter');
    const depthFilter = document.getElementById('depth-filter');
    
    if (!entityTypeFilter || !relationTypeFilter || !depthFilter) {
        return;
    }
    
    const entityType = entityTypeFilter.value;
    const relationType = relationTypeFilter.value;
    const depth = parseInt(depthFilter.value) || 1;
    
    try {
        // 由于后端暂未实现过滤API，使用前端过滤实现过滤功能
        // 在现有图数据中进行前端过滤
        let filteredNodes = [...graphData.nodes];
        let filteredEdges = [...graphData.edges];
        
        // 根据实体类型过滤
        if (entityType) {
            filteredNodes = filteredNodes.filter(node => node.group === entityType);
        }
        
        // 根据关系类型过滤
        if (relationType) {
            filteredEdges = filteredEdges.filter(edge => edge.label === relationType);
        }
        
        // 过滤出与过滤后节点相关的边
        const nodeIds = new Set(filteredNodes.map(node => node.id));
        filteredEdges = filteredEdges.filter(edge => 
            nodeIds.has(edge.from_id) && nodeIds.has(edge.to_id)
        );
        
        const result = { success: true, nodes: filteredNodes, edges: filteredEdges };
        
        if (result && result.success) {
            // Update graph with filtered data
            nodes.clear();
            edges.clear();
            nodes.add(result.nodes);
            edges.add(result.edges);
            
            showAlert('success', `Filtered to ${result.nodes.length} nodes and ${result.edges.length} edges`);
        }
        
    } catch (error) {
        console.error('Error filtering graph:', error);
        showAlert('error', 'Failed to filter graph. Please try again.');
    }
}

// Change graph layout
function changeLayout(layoutType) {
    if (!network) {
        return;
    }
    
    currentLayout = layoutType;
    let options = {};
    
    if (layoutType === 'hierarchical') {
        options = {
            layout: {
                hierarchical: {
                    enabled: true
                },
                forceAtlas2Based: {
                    enabled: false
                }
            },
            physics: {
                enabled: true,
                solver: 'hierarchicalRepulsion',
                hierarchicalRepulsion: {
                    nodeDistance: 120,
                    centralGravity: 0.01,
                    springLength: 100,
                    springConstant: 0.01,
                    damping: 0.09
                }
            }
        };
    } else {
        // Force directed layout
        options = {
            layout: {
                hierarchical: {
                    enabled: false
                },
                forceAtlas2Based: {
                    enabled: true
                }
            },
            physics: {
                enabled: true,
                solver: 'forceAtlas2Based'
            }
        };
    }
    
    network.setOptions(options);
    showAlert('info', `Layout changed to ${layoutType}`);
}

// Highlight connected nodes and edges
function highlightConnected(nodeId) {
    if (!network || !nodeId) {
        return;
    }
    
    // Get connected edges
    const connectedEdges = network.getConnectedEdges(nodeId);
    const connectedNodes = [];
    
    // Get connected nodes
    connectedEdges.forEach(edgeId => {
        const edge = edges.get(edgeId);
        if (edge) {
            connectedNodes.push(edge.from);
            connectedNodes.push(edge.to);
        }
    });
    
    // Remove duplicates
    const uniqueConnectedNodes = [...new Set(connectedNodes)];
    
    // Highlight nodes and edges
    network.setSelection({ nodes: uniqueConnectedNodes, edges: connectedEdges }, { unselectAll: true });
}

// Highlight search results
function highlightSearchResults(nodeIds, edgeIds) {
    if (!network) {
        return;
    }
    
    network.setSelection({ nodes: nodeIds, edges: edgeIds }, { unselectAll: true });
}

// Show node details
function showNodeDetails(node) {
    const detailsContainer = document.getElementById('node-details');
    
    if (!detailsContainer) {
        return;
    }
    
    const html = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Node Details</h5>
                <table class="table table-sm">
                    <tbody>
                        <tr><th>ID</th><td>${node.id}</td></tr>
                        <tr><th>Name</th><td>${node.label}</td></tr>
                        <tr><th>Type</th><td>${node.type}</td></tr>
                        <tr><th>Label</th><td>${node.label}</td></tr>
                        <tr><th>Description</th><td>${node.description || '-'}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    detailsContainer.innerHTML = html;
}

// Show edge details
function showEdgeDetails(edge) {
    const detailsContainer = document.getElementById('edge-details');
    
    if (!detailsContainer) {
        return;
    }
    
    const html = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Edge Details</h5>
                <table class="table table-sm">
                    <tbody>
                        <tr><th>ID</th><td>${edge.id}</td></tr>
                        <tr><th>From</th><td>${edge.from}</td></tr>
                        <tr><th>To</th><td>${edge.to}</td></tr>
                        <tr><th>Type</th><td>${edge.label}</td></tr>
                        <tr><th>Description</th><td>${edge.description || '-'}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    detailsContainer.innerHTML = html;
}

// Clear selection
function clearSelection() {
    const nodeDetails = document.getElementById('node-details');
    const edgeDetails = document.getElementById('edge-details');
    
    if (nodeDetails) {
        nodeDetails.innerHTML = '';
    }
    
    if (edgeDetails) {
        edgeDetails.innerHTML = '';
    }
    
    if (network) {
        network.unselectAll();
    }
}

// Clear filter and show full graph
function clearFilter() {
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.reset();
    }
    
    loadGraphData();
    showAlert('info', 'Filter cleared, showing full graph');
}

// Update graph statistics
function updateGraphStats(stats) {
    const statsContainer = document.getElementById('graph-stats');
    
    if (!statsContainer || !stats) {
        return;
    }
    
    const html = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Graph Statistics</h5>
                <div class="row">
                    <div class="col-md-3 col-sm-6">
                        <div class="stat-card">
                            <div class="stat-number">${stats.total_nodes}</div>
                            <div class="stat-label">Total Nodes</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6">
                        <div class="stat-card">
                            <div class="stat-number">${stats.total_edges}</div>
                            <div class="stat-label">Total Edges</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6">
                        <div class="stat-card">
                            <div class="stat-number">${stats.node_types || '-'}</div>
                            <div class="stat-label">Node Types</div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6">
                        <div class="stat-card">
                            <div class="stat-number">${stats.edge_types || '-'}</div>
                            <div class="stat-label">Edge Types</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    statsContainer.innerHTML = html;
}

// Show graph statistics in modal
function showGraphStatistics() {
    if (!graphData || !graphData.stats) {
        return;
    }
    
    const stats = graphData.stats;
    const modalBody = document.getElementById('stats-modal-body');
    
    if (!modalBody) {
        return;
    }
    
    const html = `
        <div class="row">
            <div class="col-md-6">
                <h6>Node Statistics</h6>
                <table class="table table-sm">
                    <tbody>
                        <tr><th>Total Nodes</th><td>${stats.total_nodes}</td></tr>
                        <tr><th>Node Types</th><td>${stats.node_types || '-'}</td></tr>
                        ${stats.top_node_types ? `
                            <tr>
                                <th>Top Node Types</th>
                                <td>
                                    ${stats.top_node_types.map(type => `<span class="badge bg-primary me-1">${type}</span>`).join('')}
                                </td>
                            </tr>
                        ` : ''}
                    </tbody>
                </table>
            </div>
            <div class="col-md-6">
                <h6>Edge Statistics</h6>
                <table class="table table-sm">
                    <tbody>
                        <tr><th>Total Edges</th><td>${stats.total_edges}</td></tr>
                        <tr><th>Edge Types</th><td>${stats.edge_types || '-'}</td></tr>
                        ${stats.top_edge_types ? `
                            <tr>
                                <th>Top Edge Types</th>
                                <td>
                                    ${stats.top_edge_types.map(type => `<span class="badge bg-success me-1">${type}</span>`).join('')}
                                </td>
                            </tr>
                        ` : ''}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="mt-3">
            <h6>Graph Metrics</h6>
            <table class="table table-sm">
                <tbody>
                    <tr><th>Average Degree</th><td>${stats.average_degree || '-'}</td></tr>
                    <tr><th>Density</th><td>${stats.density || '-'}</td></tr>
                </tbody>
            </table>
        </div>
    `;
    
    modalBody.innerHTML = html;
    
    // Show modal
    const statsModal = document.getElementById('stats-modal');
    if (statsModal) {
        statsModal.showModal();
    }
}

// Show loading state
function showLoading(show, container) {
    if (!container) {
        return;
    }
    
    if (show) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

// Show error message
function showError(show, container, message) {
    if (!container) {
        return;
    }
    
    if (show) {
        container.innerHTML = `<div class="alert alert-danger">${message}</div>`;
        container.style.display = 'block';
    } else {
        container.innerHTML = '';
        container.style.display = 'none';
    }
}

// Initialize the page when it's loaded
window.initVisualizationPage = initVisualizationPage;
