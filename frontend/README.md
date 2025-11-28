# 知识图谱管理系统前端

基于现代Web技术构建的轻量级知识图谱管理前端应用，采用国内CDN加速的开源库，确保在中国网络环境下的良好访问体验。

## 🚀 技术栈

### 核心框架
- **Vue.js 3** - 渐进式JavaScript框架
- **Element Plus** - Vue 3组件库，提供丰富的UI组件
- **Tailwind CSS** - 实用优先的CSS框架

### 数据可视化
- **D3.js v7** - 强大的数据可视化库，用于图网络展示

### HTTP通信
- **Axios** - 基于Promise的HTTP客户端

### 国内CDN资源
所有外部依赖均使用国内可访问的CDN资源：
- unpkg.com (全球CDN，国内访问稳定)
- cdn.tailwindcss.com (官方CDN)
- d3js.org (官方CDN)

## 📁 项目结构

```
frontend/
├── index.html          # 主页面
├── app.js             # Vue应用主脚本
├── styles.css         # 自定义样式
└── README.md          # 项目文档
```

## 🎯 核心功能

### 1. 内容处理与知识图谱构建
- 支持文本内容输入和处理
- 自动提取实体和关系
- 实时展示处理结果

### 2. 实体管理与查询
- 实体列表展示和搜索
- 支持按类型过滤
- 实体详情查看
- 相关新闻展示

### 3. 知识图谱可视化
- 交互式图网络展示
- 支持拖拽和缩放
- 不同实体类型颜色区分
- 关系类型标注

### 4. 响应式设计
- 适配桌面端和移动端
- 优雅的交互体验
- 加载状态提示

## 🔧 快速开始

### 环境要求
- 现代浏览器（Chrome、Firefox、Safari、Edge）
- 后端API服务运行在 `http://localhost:8001`

### 部署步骤

1. **启动后端服务**
   ```bash
   cd /Users/intoblack/workspace/graph
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
   ```

2. **启动前端服务**
   ```bash
   cd frontend
   python3 -m http.server 8081
   ```

3. **访问应用**
   打开浏览器访问 `http://localhost:8081`

### 开发模式

由于使用了CDN资源，无需安装npm包，直接编辑文件即可看到效果：

```bash
# 启动本地开发服务器
cd frontend
python3 -m http.server 8081

# 或者使用Node.js的http-server
npx http-server -p 8081
```

## 📋 API接口说明

前端应用与后端API的交互接口：

### 内容处理
- `POST /api/kg/process-content` - 处理文本内容并构建知识图谱

### 实体管理
- `GET /api/kg/entities` - 获取实体列表（支持分页、搜索、过滤）
- `GET /api/kg/entities/{id}` - 获取实体详细信息
- `GET /api/kg/entities/{id}/news` - 获取实体关联的新闻
- `GET /api/kg/entities/{id}/neighbors` - 获取实体邻居网络

### 关系管理
- `GET /api/kg/relations` - 获取关系列表

### 统计分析
- `GET /api/kg/statistics/overview` - 获取知识图谱概览统计

## 🎨 设计特点

### 用户体验
- 简洁直观的界面设计
- 清晰的功能分区
- 实时反馈和状态提示
- 错误处理和恢复机制

### 性能优化
- 虚拟滚动处理大量数据
- 懒加载和分页机制
- CDN加速资源加载
- 防抖和节流优化

### 可访问性
- 语义化HTML结构
- 键盘导航支持
- 屏幕阅读器友好
- 高对比度颜色方案

## 🔍 浏览器兼容性

| 浏览器 | 最低版本 | 备注 |
|--------|----------|------|
| Chrome | 80+ | 推荐使用 |
| Firefox | 75+ | 完全支持 |
| Safari | 13+ | 完全支持 |
| Edge | 80+ | 完全支持 |

## 📱 移动端适配

- 响应式布局设计
- 触摸友好的交互
- 适配小屏幕显示
- 优化的移动端性能

## 🔒 安全考虑

- 所有外部资源使用HTTPS
- 输入验证和XSS防护
- API请求超时处理
- 错误信息脱敏

## 🐛 常见问题

### Q: 后端API连接失败怎么办？
A: 确保后端服务已启动并运行在 `http://localhost:8001`，检查网络连接和防火墙设置。

### Q: 图可视化显示异常？
A: 清除浏览器缓存，检查浏览器控制台是否有错误信息，确保D3.js库正确加载。

### Q: 如何处理大量数据？
A: 应用内置了分页和懒加载机制，对于超大数据集可以调整分页参数或使用服务器端分页。

## 📚 相关资源

- [Vue.js 3 官方文档](https://v3.cn.vuejs.org/)
- [Element Plus 组件库](https://element-plus.org/zh-CN/)
- [D3.js 数据可视化](https://d3js.org/)
- [Tailwind CSS 框架](https://tailwindcss.com/)

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目。在提交前请确保：

1. 代码符合项目规范
2. 通过基本功能测试
3. 更新相关文档
4. 遵循开源协议

## 📄 许可证

本项目采用MIT许可证，详见项目根目录的LICENSE文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至项目维护者

---

**注意**: 本项目为演示性质，生产环境使用前请进行充分的测试和安全评估。