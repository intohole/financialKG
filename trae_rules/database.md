# SQLite + SQLAlchemy 精炼开发指南

## 依赖包
- `SQLAlchemy`: 数据库 ORM 框架
- `asyncio-sqlalchemy`: 异步 SQLAlchemy 扩展
- `pytest-asyncio`: 异步测试框架
- `pytest`: 测试框架
- `sqlalchemy-utils`: 数据库工具库

## 数据库设计规则
- 所有表都必须有一个主键列，命名为 `id`，类型为 `Integer`，自增。
- 所有表都必须有一个 `created_at` 列，类型为 `DateTime`，默认值为当前时间。
- 所有表都必须有一个 `updated_at` 列，类型为 `DateTime`，默认值为当前时间，每次更新时自动更新为当前时间。

## 数据库默认值
- 所有表的 `created_at` 和 `updated_at` 列默认值均为中国本地时间。
