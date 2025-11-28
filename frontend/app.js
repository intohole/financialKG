/**
 * 知识图谱前端应用主脚本
 * 
 * 功能特点：
 * 1. 内容处理与知识图谱构建
 * 2. 实体管理与查询
 * 3. 关系网络可视化
 * 4. 基于国内CDN的开源库集成
 */

const { createApp, ref, reactive, onMounted, nextTick } = Vue;
const { ElMessage } = ElementPlus;

// 引入统一配置
const API_CONFIG = {
    baseURL: window.API_CONFIG ? window.API_CONFIG.BASE_URL : 'http://localhost:8066',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
};

// 创建axios实例
const api = axios.create(API_CONFIG);

// 响应拦截器
api.interceptors.response.use(
    response => response.data,
    error => {
        console.error('API请求错误:', error);
        const message = error.response?.data?.detail || error.message || '请求失败';
        ElMessage.error(message);
        return Promise.reject(error);
    }
);

// 颜色映射配置
const ENTITY_COLORS = {
    '人物': '#409eff',
    '组织': '#67c23a', 
    '地点': '#e6a23c',
    '事件': '#f56c6c',
    'default': '#909399'
};

// 主应用
const app = createApp({
    setup() {
        // 状态管理
        const currentTab = ref('content');
        const processing = ref(false);
        const graphLoading = ref(false);
        const entityDialogVisible = ref(false);
        
        // 表单数据
        const contentForm = reactive({
            content: '',
            contentId: ''
        });
        
        const searchForm = reactive({
            search: '',
            entityType: ''
        });
        
        const graphForm = reactive({
            centerEntity: '',
            depth: 2,
            maxEntities: 100
        });
        
        // 数据存储
        const processResult = ref(null);
        const entities = ref([]);
        const selectedEntity = ref(null);
        const entityNews = ref([]);
        const pagination = reactive({
            page: 1,
            pageSize: 20,
            total: 0
        });
        
        // 图可视化相关
        let svg = null;
        let simulation = null;
        const graphData = ref({ nodes: [], edges: [] });
        
        /**
         * 内容处理功能
         */
        const processContent = async () => {
            if (!contentForm.content.trim()) {
                ElMessage.warning('请输入要处理的文本内容');
                return;
            }
            
            processing.value = true;
            try {
                const requestData = {
                    content: contentForm.content.trim(),
                    content_id: contentForm.contentId || undefined
                };
                
                const result = await api.post('/api/kg/process-content', requestData);
                processResult.value = result;
                
                ElMessage.success('内容处理成功！');
                console.log('处理结果:', result);
                
            } catch (error) {
                console.error('内容处理失败:', error);
            } finally {
                processing.value = false;
            }
        };
        
        const clearContentForm = () => {
            contentForm.content = '';
            contentForm.contentId = '';
            processResult.value = null;
        };
        
        /**
         * 实体查询功能
         */
        const searchEntities = async () => {
            try {
                const params = {
                    page: pagination.page,
                    page_size: pagination.pageSize,
                    search: searchForm.search || undefined,
                    entity_type: searchForm.entityType || undefined
                };
                
                const result = await api.get('/api/kg/entities', { params });
                entities.value = result.items;
                pagination.total = result.total;
                
                console.log('实体查询结果:', result);
                
            } catch (error) {
                console.error('实体查询失败:', error);
            }
        };
        
        const resetSearchForm = () => {
            searchForm.search = '';
            searchForm.entityType = '';
            pagination.page = 1;
            searchEntities();
        };
        
        const handlePageChange = (page) => {
            pagination.page = page;
            searchEntities();
        };
        
        /**
         * 实体详情功能
         */
        const showEntityDetail = async (entity) => {
            try {
                selectedEntity.value = entity;
                entityDialogVisible.value = true;
                
                // 获取实体详情
                const detail = await api.get(`/api/kg/entities/${entity.id}`);
                selectedEntity.value = { ...entity, ...detail };
                
                // 获取相关新闻
                const newsResult = await api.get(`/api/kg/entities/${entity.id}/news`, {
                    params: { page: 1, page_size: 10 }
                });
                entityNews.value = newsResult.items || [];
                
            } catch (error) {
                console.error('获取实体详情失败:', error);
            }
        };
        
        /**
         * 图网络可视化功能
         */
        const loadGraphData = async () => {
            if (!graphForm.centerEntity) {
                ElMessage.warning('请输入中心实体名称');
                return;
            }
            
            graphLoading.value = true;
            try {
                // 这里需要根据实体名称查找实体ID，简化处理直接使用ID 1
                const entityId = 1; // 实际应用中需要根据名称查找
                
                const result = await api.get(`/api/kg/entities/${entityId}/neighbors`, {
                    params: {
                        depth: graphForm.depth,
                        max_entities: graphForm.maxEntities
                    }
                });
                
                graphData.value = {
                    nodes: result.nodes || [],
                    edges: result.edges || []
                };
                
                renderGraph();
                ElMessage.success('图谱数据加载成功！');
                
            } catch (error) {
                console.error('加载图谱数据失败:', error);
            } finally {
                graphLoading.value = false;
            }
        };
        
        const renderGraph = () => {
            if (!graphData.value.nodes.length) return;
            
            // 清空现有图形
            d3.select("#graph-container").select("svg").remove();
            
            const container = document.getElementById('graph-container');
            const width = container.clientWidth;
            const height = 600;
            
            // 创建SVG
            svg = d3.select("#graph-container")
                .append("svg")
                .attr("width", width)
                .attr("height", height);
            
            // 创建力导向图
            simulation = d3.forceSimulation(graphData.value.nodes)
                .force("link", d3.forceLink(graphData.value.edges).id(d => d.id).distance(100))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collision", d3.forceCollide().radius(30));
            
            // 创建连线
            const link = svg.append("g")
                .selectAll("line")
                .data(graphData.value.edges)
                .enter().append("line")
                .attr("class", "link")
                .attr("stroke-width", 1.5);
            
            // 创建连线标签
            const linkLabel = svg.append("g")
                .selectAll("text")
                .data(graphData.value.edges)
                .enter().append("text")
                .attr("class", "link-label")
                .text(d => d.relation_type || d.type || '');
            
            // 创建节点
            const node = svg.append("g")
                .selectAll("circle")
                .data(graphData.value.nodes)
                .enter().append("circle")
                .attr("class", "node-circle")
                .attr("r", 15)
                .attr("fill", d => ENTITY_COLORS[d.type] || ENTITY_COLORS.default)
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            // 创建节点标签
            const nodeLabel = svg.append("g")
                .selectAll("text")
                .data(graphData.value.nodes)
                .enter().append("text")
                .attr("class", "node-text")
                .attr("dy", 25)
                .text(d => d.name);
            
            // 添加节点点击事件
            node.on("click", function(event, d) {
                console.log("点击节点:", d);
                // 这里可以扩展为显示节点详情
            });
            
            // 更新位置
            simulation.on("tick", () => {
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                linkLabel
                    .attr("x", d => (d.source.x + d.target.x) / 2)
                    .attr("y", d => (d.source.y + d.target.y) / 2);
                
                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
                
                nodeLabel
                    .attr("x", d => d.x)
                    .attr("y", d => d.y);
            });
            
            // 拖拽函数
            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }
            
            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }
            
            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
        };
        
        const clearGraph = () => {
            graphData.value = { nodes: [], edges: [] };
            d3.select("#graph-container").select("svg").remove();
        };
        
        /**
         * 工具函数
         */
        const formatDate = (dateString) => {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('zh-CN');
        };
        
        /**
         * 生命周期
         */
        onMounted(() => {
            // 初始化数据
            searchEntities();
            
            // 监听窗口大小变化
            window.addEventListener('resize', () => {
                if (graphData.value.nodes.length > 0) {
                    nextTick(() => {
                        renderGraph();
                    });
                }
            });
        });
        
        return {
            // 状态
            currentTab,
            processing,
            graphLoading,
            entityDialogVisible,
            
            // 表单
            contentForm,
            searchForm,
            graphForm,
            
            // 数据
            processResult,
            entities,
            selectedEntity,
            entityNews,
            pagination,
            graphData,
            
            // 方法
            processContent,
            clearContentForm,
            searchEntities,
            resetSearchForm,
            handlePageChange,
            showEntityDetail,
            loadGraphData,
            clearGraph,
            formatDate,
            
            // 工具
            JSON
        };
    }
});

// 使用Element Plus
app.use(ElementPlus);

// 挂载应用
app.mount('#app');