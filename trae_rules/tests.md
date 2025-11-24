## 单元测试
- 每个接口必写 `test_*.py`，单测覆盖率 ≥ 90%
- 用 `pytest` + `pytest-cov`，命令：`pytest --cov=src --cov-report=term-missing`
- 外部依赖全 Mock，数据库用 `pytest-mock` 或 `factory-boy`

## 测试规范
- 测试文件放 `tests/` 目录，与被测试代码对应
- 每个测试函数必写 `test_*`，用 `asyncio` 或 `pytest-asyncio` 测试异步代码

## 集成测试
- 只测主流程，用 `httpx` 或 `requests`，断言状态码 + 核心字段

## 代码质量
- 测试代码也要过 `ruff` 与 `mypy --strict`
- 禁止 `print`，用 `caplog` 捕获日志断言

## 测试文件结构
- 测试文件与源代码文件结构保持一致
- 测试文件命名采用 `test_*.py` 格式
- 使用 `pytest` 框架进行测试


## 测试路径
- 测试路径与源代码路径保持一致
- 测试路径下的文件命名采用 `test_*.py` 格式