## 单元测试
- 每个接口必写 `test_*.py`，单测覆盖率 ≥ 90%
- 用 `pytest` + `pytest-cov`，命令：`pytest --cov=src --cov-report=term-missing`
- 外部依赖全 Mock，数据库用 `pytest-mock` 或 `factory-boy`

## 测试规范
- 测试文件放 `tests/` 目录，与被测试代码对应
- 每个测试函数必写 `test_*`，用 `asyncio` 或 `pytest-asyncio` 测试异步代码

## 集成测试
- 起真实容器： `docker-compose -f docker-compose.test.yml up --abort-on-container-exit`
- 只测主流程，用 `httpx` 或 `requests`，断言状态码 + 核心字段

## 性能测试
- `locust` 脚本放 `tests/perf/`，单文件 ≤ 50 行
- 基准：P95 < 200 ms，RPS ≥ 目标值 * 1.2

## 代码质量
- 测试代码也要过 `ruff` 与 `mypy --strict`
- 禁止 `print`，用 `caplog` 捕获日志断言

## CI 门禁
- 测试失败即阻断合并；覆盖率下降 ≥ 1% 需 Review 特批
