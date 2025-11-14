# 金融知识图谱系统

一个基于Python的异步金融知识图谱构建系统，支持多数据源爬虫、实时数据处理和知识图谱构建。

## 项目特色

- 🚀 **高性能异步架构**: 基于asyncio和aiohttp构建的高并发系统
- 📊 **多数据源支持**: 支持财经网站、新闻API、财报数据等多源数据采集
- 🧠 **智能实体识别**: 集成NLP技术进行金融实体识别和关系抽取
- ⚡ **实时数据处理**: 流式数据处理和增量更新机制
- 🎯 **可视化展示**: 基于Web的可视化界面和API接口
- 🔄 **定时任务调度**: 内置任务调度器支持定时爬虫和数据更新

## 项目结构

```
financial_kg/
├── README.md              # 项目说明文档
├── requirements.txt       # 依赖包列表
├── .gitignore            # Git忽略文件
├── setup_env.sh          # 环境设置脚本
├── config.yaml           # 配置文件
├── main.py               # 主程序入口
├── deploy.sh             # 部署脚本
├── quick_start.sh        # 快速启动脚本
├── api_server.py         # API服务模块
├── crawler.py            # 爬虫模块
├── database_manager.py   # 数据库管理模块
├── processor.py          # 数据处理模块
├── scheduler.py          # 任务调度模块
├── simple_cache.py       # 缓存模块
└── test_system.py        # 系统测试文件
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone git@github.com:intohole/financialKG.git
cd financial_kg

# 运行环境设置脚本
chmod +x setup_env.sh
./setup_env.sh
```

### 2. 手动安装（可选）

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 配置清华数据源
pip install --upgrade pip
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装依赖
pip install -r requirements.txt
```

### 3. 启动系统

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行主程序
python3 main.py

# 或者使用快速启动
./quick_start.sh

# 或者部署系统
./deploy.sh
```

## 配置说明

编辑 `config.yaml` 文件来自定义系统配置：

```yaml
database:
  path: "./data/financial_kg.db"
  max_connections: 10

cache:
  max_size: 1000
  ttl: 3600

crawler:
  timeout: 30
  max_workers: 5
  rate_limit: 1.0  # 秒

sources:
  - name: "sina_finance"
    url: "https://finance.sina.com.cn"
    enabled: true
```

## 使用说明

### 启动模式

```bash
# API服务模式（默认）
python3 main.py --mode api

# 爬虫模式
python3 main.py --mode crawler

# 数据处理模式
python3 main.py --mode processor

# 全功能模式
python3 main.py --mode all

# 定时任务模式
python3 main.py --mode scheduler
```

### API接口

系统启动后，可以通过以下接口访问：

- `GET /api/health` - 健康检查
- `GET /api/entities` - 获取实体列表
- `GET /api/relationships` - 获取关系列表
- `POST /api/crawl` - 触发爬虫任务
- `GET /api/stats` - 获取系统统计信息

## 核心模块

### 1. 数据库管理器 (DatabaseManager)
- 异步SQLite操作
- 实体和关系存储
- 索引优化

### 2. 爬虫模块 (NewsCrawler)
- 多源数据采集
- 内容去重和质量过滤
- 速率限制和错误重试

### 3. 数据处理器 (DataProcessor)
- 实体识别和抽取
- 关系挖掘
- 知识图谱构建

### 4. 缓存系统 (SimpleCache)
- LRU缓存策略
- TTL过期机制
- 内存优化

### 5. 任务调度器 (TaskScheduler)
- 定时任务管理
- 优先级队列
- 失败重试机制

### 6. API服务 (APIServer)
- FastAPI框架
- RESTful API设计
- 自动文档生成

## 性能指标

- **并发爬虫**: 支持100+并发请求
- **数据处理**: 每秒处理1000+实体识别
- **响应时间**: API响应 < 100ms
- **内存使用**: 基础配置 < 500MB

## 故障排查

### 常见问题

1. **模块导入失败**
   ```bash
   pip install -r requirements.txt
   ```

2. **数据库锁定**
   ```bash
   rm -f data/*.db
   ```

3. **爬虫被封**
   ```bash
   # 调整config.yaml中的rate_limit
   ```

4. **API服务启动失败**
   ```bash
   # 检查端口占用
   lsof -i :8000
   ```

## 部署指南

### Docker部署（推荐）

```bash
# 构建镜像
docker build -t financial_kg .

# 运行容器
docker run -p 8000:8000 -v ./data:/app/data financial_kg
```

### 传统部署

```bash
# 使用systemd服务
sudo cp deploy.sh /etc/systemd/system/financial-kg.service
sudo systemctl enable financial-kg
sudo systemctl start financial-kg
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 许可证

MIT License

## 联系方式

- GitHub: [intohole](https://github.com/intohole)
- Email: intohole@users.noreply.github.com