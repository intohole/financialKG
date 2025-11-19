"""
知识图谱数据库模型定义

定义知识图谱的核心数据模型，包括实体、关系、新闻及其关联关系
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Entity(Base):
    """
    实体表 - 存储知识图谱中的实体节点

    解决实体重复问题：
    - 通过entity_group_id关联相似实体
    - canonical_name作为实体的规范名称
    """

    __tablename__ = "entity"

    # 主键ID
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    # 实体原始名称（从文本中提取的名称）
    name = sa.Column(sa.String(500), nullable=False, index=True)

    # 实体类型（如：人物、公司、地点等）
    type = sa.Column(sa.String(100), nullable=False, index=True)

    # 实体规范名称（标准化后的名称）
    canonical_name = sa.Column(sa.String(500), nullable=True, index=True)

    # 实体分组ID，用于标识相似实体
    entity_group_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("entity_group.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 实体来源（如：新闻、报告等）
    source = sa.Column(sa.String(100), nullable=True)

    # 实体属性（JSON格式存储其他属性）
    properties = sa.Column(sa.Text, nullable=True)

    # 实体置信度分数
    confidence_score = sa.Column(sa.Float, default=0.0)

    # 创建时间
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    # 更新时间
    updated_at = sa.Column(
        sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 索引优化查询性能
    __table_args__ = (
        Index("idx_entity_type_name", "type", "name"),
        Index("idx_entity_group", "entity_group_id"),
        Index("idx_entity_canonical", "canonical_name"),
        Index("idx_entity_name_type", "name", "type"),  # 复合索引用于查找
        Index("idx_entity_name", "name"),  # 单个name字段索引，用于name IN查询
        Index("idx_entity_updated_at", sa.desc("updated_at")),  # 索引用于按更新时间排序
        Index("idx_entity_type_updated_at", "type", sa.desc("updated_at")),  # 复合索引用于按类型过滤并按更新时间排序
        sa.UniqueConstraint(
            "name", "type", "source", name="_entity_name_type_source_uc"
        ),  # 防止重复实体
    )


class Relation(Base):
    """
    关系表 - 存储实体之间的关系

    解决关系重复问题：
    - 通过relation_group_id关联相似关系
    - canonical_relation作为关系的规范名称
    """

    __tablename__ = "relation"

    # 主键ID
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    # 源实体ID（外键）
    source_entity_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 目标实体ID（外键）
    target_entity_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 关系类型原始名称（如：妻子、老婆等）
    relation_type = sa.Column(sa.String(200), nullable=False, index=True)

    # 关系规范名称（标准化后的关系类型）
    canonical_relation = sa.Column(sa.String(200), nullable=True, index=True)

    # 关系分组ID，用于标识相似关系
    relation_group_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("relation_group.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 关系权重/置信度
    weight = sa.Column(sa.Float, default=1.0)

    # 关系来源
    source = sa.Column(sa.String(100), nullable=True)

    # 关系属性（JSON格式存储其他属性）
    properties = sa.Column(sa.Text, nullable=True)

    # 创建时间
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    # 更新时间
    updated_at = sa.Column(
        sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 索引优化查询性能
    __table_args__ = (
        Index("idx_relation_source_target", "source_entity_id", "target_entity_id"),
        Index("idx_relation_type", "relation_type"),
        Index("idx_relation_group", "relation_group_id"),
        Index("idx_relation_canonical", "canonical_relation"),
        Index(
            "idx_relation_target_source", "target_entity_id", "source_entity_id"
        ),  # 反向查询索引
        sa.UniqueConstraint(
            "source_entity_id",
            "target_entity_id",
            "relation_type",
            "source",
            name="_relation_unique_uc",
        ),  # 防止重复关系
    )


class News(Base):
    """
    新闻表 - 存储原始新闻数据
    """

    __tablename__ = "news"

    # 主键ID
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    # 新闻标题
    title = sa.Column(sa.String(1000), nullable=False, index=True)

    # 新闻内容
    content = sa.Column(sa.Text, nullable=False)

    # 新闻URL
    url = sa.Column(sa.String(2000), nullable=True, index=True, unique=True)

    # 新闻发布时间
    publish_time = sa.Column(sa.DateTime, nullable=True, index=True)

    # 新闻来源
    source = sa.Column(sa.String(100), nullable=True, index=True)

    # 新闻类别
    category = sa.Column(sa.String(100), nullable=True, index=True)

    # 提取状态（是否已提取实体和关系）
    extraction_status = sa.Column(sa.String(50), default="pending", index=True)

    # 提取时间
    extracted_at = sa.Column(sa.DateTime, nullable=True)

    # 创建时间
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    # 更新时间
    updated_at = sa.Column(
        sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # 索引优化查询性能
    __table_args__ = (
        Index("idx_news_time_source", "publish_time", "source"),
        Index("idx_news_status", "extraction_status"),
        Index("idx_news_source_category", "source", "category"),  # 复合索引
    )


class EntityNews(Base):
    """
    实体-新闻关联表 - 记录实体出现在哪些新闻中
    """

    __tablename__ = "entity_news"

    # 主键ID
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    # 实体ID（外键）
    entity_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("entity.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 新闻ID（外键）
    news_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("news.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 实体在新闻中的上下文（用于实体消歧）
    context = sa.Column(sa.Text, nullable=True)

    # 实体在新闻中出现的次数
    occurrence_count = sa.Column(sa.Integer, default=1)

    # 创建时间
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    # 唯一约束，确保实体和新闻的关联不重复
    __table_args__ = (
        sa.UniqueConstraint("entity_id", "news_id", name="_entity_news_uc"),
        Index("idx_entity_news", "entity_id", "news_id"),
        Index("idx_news_entity", "news_id", "entity_id"),  # 反向查询索引
    )


class EntityGroup(Base):
    """
    实体分组表 - 管理相似实体的分组信息

    用于实体去重，将相似的实体（如：同义词、不同称谓等）归为一组
    """

    __tablename__ = "entity_group"

    # 主键ID
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    # 分组名称（通常使用规范名称）
    group_name = sa.Column(sa.String(500), nullable=False, unique=True, index=True)

    # 分组描述
    description = sa.Column(sa.Text, nullable=True)

    # 主要实体ID（作为该组的代表实体）
    primary_entity_id = sa.Column(
        sa.Integer, sa.ForeignKey("entity.id", ondelete="SET NULL"), nullable=True
    )

    # 实体数量
    entity_count = sa.Column(sa.Integer, default=1)

    # 创建时间
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    # 更新时间
    updated_at = sa.Column(
        sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class RelationGroup(Base):
    """
    关系分组表 - 管理相似关系的分组信息

    用于关系去重，将相似的关系（如：妻子、老婆等）归为一组
    """

    __tablename__ = "relation_group"

    # 主键ID
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    # 分组名称（通常使用规范关系名称）
    group_name = sa.Column(sa.String(200), nullable=False, unique=True, index=True)

    # 分组描述
    description = sa.Column(sa.Text, nullable=True)

    # 关系数量
    relation_count = sa.Column(sa.Integer, default=1)

    # 创建时间
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    # 更新时间
    updated_at = sa.Column(
        sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
