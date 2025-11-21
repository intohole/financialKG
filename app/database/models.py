from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# 实体表：增加"canonical_id"用于合并重复实体
class Entity(Base):
    __tablename__ = 'entities'
    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment='实体名称')
    type = Column(String(64),  nullable=False, comment='实体类型，如人名、地名、组织等')
    description = Column(Text, comment='实体描述')
    # 指向官方/合并后的实体，NULL 表示自己就是官方实体
    canonical_id = Column(Integer, ForeignKey('entities.id'), nullable=True, comment='合并后的官方实体ID')
    vector_id = Column(String(255), nullable=True, comment='向量存储中的ID')
    meta_data = Column(JSON, nullable=True, comment='实体的元数据信息')
    created_at  = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 自引用关系：官方实体可拥有多个别名实体
    canonical = relationship('Entity', remote_side=[id], backref='aliases')
    # 作为主体或客体的关系
    as_subject  = relationship('Relation', foreign_keys='Relation.subject_id', back_populates='subject')
    as_object   = relationship('Relation', foreign_keys='Relation.object_id',  back_populates='object')


# 关系表：增加唯一约束防止重复三元组
class Relation(Base):
    __tablename__ = 'relations'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    subject_id  = Column(Integer, ForeignKey('entities.id'), nullable=False, comment='主体实体ID')
    predicate   = Column(String(128), nullable=False, comment='谓词/关系类型')
    object_id   = Column(Integer, ForeignKey('entities.id'), nullable=False, comment='客体实体ID')
    description = Column(Text, comment='关系描述')
    vector_id = Column(String(255), nullable=True, comment='向量存储中的ID')
    meta_data = Column(JSON, nullable=True, comment='关系的元数据信息')
    created_at  = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 联合唯一：同一主体+谓词+客体只能出现一次
    __table_args__ = (
        UniqueConstraint('subject_id', 'predicate', 'object_id', name='uq_relation_spo'),
        Index('idx_relation_subject', 'subject_id'),
        Index('idx_relation_object', 'object_id'),
    )

    subject = relationship('Entity', foreign_keys=[subject_id], back_populates='as_subject')
    object  = relationship('Entity', foreign_keys=[object_id],  back_populates='as_object')


# 属性表（可选：给实体挂任意键值属性）
class Attribute(Base):
    __tablename__ = 'attributes'
    id        = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=False, comment='所属实体ID')
    key       = Column(String(128), nullable=False, comment='属性键')
    value     = Column(Text, comment='属性值')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    # 同一实体下属性键唯一
    __table_args__ = (
        UniqueConstraint('entity_id', 'key', name='uq_attribute_entity_key'),
    )

    entity = relationship('Entity')


# 新闻事件表：将新闻事件挂载到实体上
class NewsEvent(Base):
    __tablename__ = 'news_events'
    id          = Column(Integer, primary_key=True, autoincrement=True)
    title       = Column(String(512), nullable=False, comment='新闻标题')
    content     = Column(Text, comment='新闻正文')
    source      = Column(String(255), comment='新闻来源')
    publish_time = Column(DateTime, comment='发布时间')
    created_at  = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 与实体的多对多关联
    entities = relationship('Entity', secondary='news_event_entity', back_populates='news_events')


# 新闻事件与实体的关联表
news_event_entity = Table(
    'news_event_entity',
    Base.metadata,
    Column('news_event_id', Integer, ForeignKey('news_events.id'), primary_key=True),
    Column('entity_id', Integer, ForeignKey('entities.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow, comment='关联创建时间')
)


# 在Entity类中补充与新闻事件的反向关系
Entity.news_events = relationship('NewsEvent', secondary='news_event_entity', back_populates='entities')