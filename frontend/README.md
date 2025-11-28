# 知识图谱可视化前端

基于知识图谱API构建的轻量级可视化前端，提供实体管理、关系分析和网络可视化功能。

## 功能特性

### 📝 内容处理
- **智能文本分析**: 自动提取文本中的实体和关系
- **实时处理反馈**: 显示处理进度和结果统计
- **分类识别**: 自动识别内容类别（科技、商业等）

### 🔍 实体管理
- **实体搜索**: 支持按名称、类型搜索实体
- **实体卡片**: 美观的实体展示卡片，包含类型、描述和统计信息
- **实体详情**: 点击查看实体详细信息，包括关联统计
- **分页浏览**: 支持分页浏览大量实体数据

### 🔗 关系分析
- **关系列表**: 展示实体间的关联关系
- **关系类型**: 支持多种关系类型展示（开发、生产、拥有等）
- **置信度显示**: 显示关系抽取的置信度
- **时间排序**: 按创建时间排序关系

### 🌐 网络可视化
- **交互式网络图**: 基于SVG的力导向图可视化
- **实体网络**: 展示实体间的复杂关联网络
- **节点交互**: 支持节点点击、悬停高亮
- **动态布局**: 自动计算最优节点布局

## 技术架构

### 前端技术栈
- **原生JavaScript**: 无需框架依赖，轻量级实现
- **模块化设计**: 采用ES6类模块化组织代码
- **响应式布局**: 适配移动端和桌面端
- **现代CSS**: 使用CSS变量和现代布局技术

### 核心组件

#### API封装层 (`js/api.js`)
```javascript
// API请求封装
class KGAPI {
    async processContent(content) // 处理内容
    async getEntities(params)    // 获取实体列表
    async getEntityDetail(id)    // 获取实体详情
    async getRelations(params)   // 获取关系列表
    async getEntityNeighbors(id) // 获取实体邻居网络
}
```

#### UI组件库 (`js/components.js`)
```javascript
// 核心UI组件
class EntityCard      // 实体卡片组件
class RelationCard    // 关系卡片组件
class NetworkGraph    // 网络图组件
class Pagination      // 分页组件
class SearchBox       // 搜索框组件
class Modal           // 模态框组件
class Notification    // 通知组件
```

#### 主应用 (`js/app.js`)
```javascript
// 应用主类
class KGApplication {
    switchPanel(panel)     // 面板切换
    processContent()      // 内容处理
    loadEntities()        // 实体加载
    loadRelations()       // 关系加载
    showEntityNetwork()   // 网络展示
}
```

## 文件结构

```
frontend/
├── index.html              # 主页面
├── css/
│   ├── main.css           # 主样式
│   ├── components.css      # 组件样式
│   └── responsive.css     # 响应式样式
├── js/
│   ├── api.js             # API封装
│   ├── components.js      # UI组件
│   └── app.js             # 主应用逻辑
└── README.md              # 文档
```

## 快速开始

### 1. 启动后端服务
确保后端API服务运行在 `http://localhost:8001`

### 2. 打开前端页面
使用现代浏览器直接打开 `index.html` 文件，或使用本地服务器：

```bash
# 使用Python简单HTTP服务器
cd frontend
python -m http.server 8080

# 或使用Node.js http-server
npx http-server -p 8080
```

### 3. 访问应用
打开浏览器访问 `http://localhost:8080`

## 使用指南

### 内容处理
1. 在"内容处理"面板输入文本内容
2. 点击"处理内容"按钮
3. 查看提取的实体和关系结果

### 实体管理
1. 切换到"实体管理"面板
2. 使用搜索框搜索特定实体
3. 点击实体卡片查看详情
4. 点击"查看网络"按钮查看实体关系网络

### 网络分析
1. 切换到"网络分析"面板
2. 在搜索框输入实体名称
3. 查看实体的关联网络图
4. 点击节点查看实体详情

## API接口

前端与后端通过以下API接口通信：

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/kg/process-content` | POST | 处理内容，提取实体和关系 |
| `/api/kg/entities` | GET | 获取实体列表 |
| `/api/kg/entities/{id}` | GET | 获取实体详情 |
| `/api/kg/relations` | GET | 获取关系列表 |
| `/api/kg/entities/{id}/neighbors` | GET | 获取实体邻居网络 |

## 设计规范

### 大厂前端规范遵循
- **组件化**: 高度模块化的组件设计
- **一致性**: 统一的视觉风格和交互模式
- **可维护性**: 清晰的代码结构和注释
- **性能优化**: 防抖、缓存、请求队列优化
- **错误处理**: 完善的错误处理和用户反馈

### 响应式设计
- **移动端优先**: 基于移动设备设计，向上适配
- **弹性布局**: 使用Flexbox和Grid布局
- **断点设计**: 针对平板、桌面、大屏的适配
- **触摸优化**: 适配触摸操作的交互设计

### 性能优化
- **防抖处理**: 搜索输入防抖优化
- **请求缓存**: API响应缓存机制
- **请求队列**: 防止重复请求
- **懒加载**: 按需加载数据和组件

## 浏览器兼容性

- Chrome 60+
- Firefox 55+
- Safari 11+
- Edge 79+

## 开发说明

### 扩展组件
按照以下模式创建新组件：

```javascript
class NewComponent {
    constructor(options = {}) {
        this.options = { ...options };
        this.element = this.createElement();
    }
    
    createElement() {
        // 创建DOM元素
    }
    
    render() {
        return this.element;
    }
}
```

### 添加新面板
1. 在HTML中添加面板结构
2. 在CSS中添加对应样式
3. 在JS中添加面板逻辑
4. 更新导航和路由处理

### 自定义样式
使用CSS变量进行主题定制：

```css
:root {
    --primary-color: #3498db;
    --secondary-color: #2ecc71;
    --danger-color: #e74c3c;
    --warning-color: #f39c12;
    --info-color: #9b59b6;
}
```

## 贡献指南

1. 遵循现有代码风格和结构
2. 添加必要的注释和文档
3. 测试所有功能模块
4. 确保响应式兼容性
5. 优化性能和用户体验

## 许可证

MIT License - 详见项目根目录LICENSE文件