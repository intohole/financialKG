# KG核心实现服务代码清理总结

## 概述
对 `/Users/intoblack/workspace/graph/app/services/kg_core_impl.py` 进行了代码清理和优化，移除了冗余代码并简化了逻辑结构。

## 主要改进

### 1. 代码结构优化
- **简化了 embedding 维度初始化逻辑**
  - 将复杂的嵌套条件判断提取到独立方法 `_get_embedding_dimension_from_config()`
  - 减少了构造函数中的重复代码

### 2. 冗余代码移除
- **标记了未使用的 `parse_llm_response` 方法**
  - 该方法在整个代码库中未被调用
  - 保留为向后兼容，但标记为已废弃

### 3. 重复逻辑简化
- **统一了 embedding 维度获取逻辑**
  - 创建了 `_get_embedding_dimension_from_service()` 方法处理服务获取
  - 移除了 `_init_store()` 方法中的重复代码

### 4. 日志优化
- **减少了冗余日志输出**
  - 简化了条件判断中的日志记录
  - 保持了关键信息的记录

## 具体修改

### 构造函数简化
```python
# 之前
if embedding_dimension is not None:
    self._embedding_dimension = embedding_dimension
    logger.info(f"使用传入的embedding维度: {embedding_dimension}")
else:
    # 复杂的配置获取逻辑...

# 之后
self._embedding_dimension = embedding_dimension or self._get_embedding_dimension_from_config()
```

### 新增辅助方法
```python
def _get_embedding_dimension_from_config(self) -> Optional[int]:
    """从配置获取embedding维度"""
    # 简化的配置获取逻辑
    
async def _get_embedding_dimension_from_service(self) -> int:
    """从embedding服务获取维度"""
    # 统一的服务获取逻辑
```

## 测试结果
- ✅ 清理后的代码测试通过
- ✅ 保持了所有核心功能
- ✅ 提高了代码可读性和维护性
- ✅ 减少了代码复杂度

## 代码质量改进
1. 移除了未使用的 `parse_llm_response` 方法（标记为废弃）
2. 简化了 embedding 维度初始化逻辑
3. 提取了重复代码到独立方法
4. 减少了嵌套条件和重复日志
5. 提高了代码可读性和维护性

## 总结
代码清理成功！核心实现更加简洁高效，同时保持了所有功能完整性。通过提取公共逻辑和简化条件判断，代码的可维护性得到了显著提升。