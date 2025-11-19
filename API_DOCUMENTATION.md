# API 文档

## 实体列表接口 - 分页功能

### 1. 接口概述
获取实体列表，支持分页、搜索、排序和筛选功能。

### 2. 接口路径
```
GET /api/entities
```

### 3. 请求参数

| 参数名       | 类型    | 位置   | 描述                                                         | 可选  | 默认值 |
|-------------|---------|--------|--------------------------------------------------------------|-------|--------|
| name        | string  | query  | 搜索关键词，匹配实体名称或规范名称                           | 是    | -      |
| entity_type | string  | query  | 实体类型筛选                                                 | 是    | -      |
| page        | integer | query  | 页码，从1开始                                                | 是    | 1      |
| page_size   | integer | query  | 每页大小，最大支持100                                        | 是    | 20     |
| sort_by     | string  | query  | 排序字段，可选值：id, name, type, created_at, updated_at     | 是    | updated_at |
| sort_desc   | boolean | query  | 是否降序排序                                                 | 是    | true   |

### 4. 响应结构

```json
{
  "code": 200,
  "message": "请求成功",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "示例实体",
        "canonical_name": "示例实体",
        "type": "人物",
        "properties": {},
        "confidence_score": 0.85,
        "source": "test",
        "created_at": "2023-05-20T12:34:56",
        "updated_at": "2023-05-21T09:12:34"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 156,
      "total_pages": 8,
      "has_prev": false,
      "has_next": true
    }
  }
}
```

### 5. 代码实现细节

#### 5.1 后端实现
- **接口路由**：`kg/api/entities_router.py`
- **服务层**：`kg/services/database/entity_service.py`
- **数据层**：`kg/database/repositories.py`

#### 5.2 分页逻辑
```python
# 计算偏移量
if page and page_size:
    offset = (page - 1) * page_size
    stmt = stmt.limit(page_size).offset(offset)
```

#### 5.3 排序逻辑
```python
# 应用排序
if order_by:
    column = getattr(Entity, order_by, None)
    if column:
        stmt = stmt.order_by(desc(column) if sort_desc else column)
else:
    # 默认按更新时间降序
    stmt = stmt.order_by(desc(Entity.updated_at))
```

### 6. 使用示例

#### 6.1 基本使用
```bash
curl -X GET "http://localhost:8000/api/entities?page=1&page_size=20"
```

#### 6.2 带搜索条件
```bash
curl -X GET "http://localhost:8000/api/entities?name=示例&page=1&page_size=10"
```

#### 6.3 带筛选和排序
```bash
curl -X GET "http://localhost:8000/api/entities?entity_type=人物&sort_by=name&sort_desc=false&page=1&page_size=20"
```

### 7. 前端实现

在 `static/js/entity.js` 中实现了分页功能，包括：
- 页码导航（上一页/下一页/页码按钮）
- 每页大小选择器
- 省略号逻辑（只显示当前页附近的页码）

```javascript
// 分页控件渲染
function renderPagination(currentPage, totalPages, currentPageSize, totalItems) {
    // 实现分页控件渲染逻辑
}

// 页大小选择器事件
pageSizeSelector.addEventListener('change', function() {
    currentPageSize = parseInt(this.value);
    currentPage = 1;
    fetchEntities();
});
```

### 8. 性能优化

- 数据库查询使用 `limit` 和 `offset` 实现分页
- 只查询必要的字段
- 对经常搜索的字段（如 `name`）添加了索引

# 其他API接口

## 1. 实体详情接口
```
GET /api/entities/{entity_id}
```

## 2. 创建实体接口
```
POST /api/entities
```

## 3. 更新实体接口
```
PUT /api/entities/{entity_id}
```

## 4. 删除实体接口
```
DELETE /api/entities/{entity_id}
```

## 5. 实体邻居接口
```
GET /api/entities/{entity_id}/neighbors
```

## 6. 新闻列表接口
```
GET /api/news
```

## 7. 关系列表接口
```
GET /api/relations
```

## 8. 自动知识图谱生成接口
```
POST /api/autokg/generate
```

## 9. 实体去重接口
```
POST /api/deduplication/entities
```

## 10. 可视化数据接口
```
GET /api/visualization/entities
```
