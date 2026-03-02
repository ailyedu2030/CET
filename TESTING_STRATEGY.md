# CET 教育平台 - 测试策略

## 概述

本文档描述了CET教育平台的全面测试策略，确保系统能够进入生产环节，没有任何妥协。

## 测试金字塔

```
        /\
       /E2E\      端到端测试（少量，关键流程）
      /------\
     /集成测试\    集成测试（中等数量，关键交互）
    /---------\
   /  单元测试  \   单元测试（大量，每个函数）
  /-------------\
 /   基础测试     \  数据库连接、配置验证等
/-----------------\
```

## 测试类型

### 1. 单元测试
- **覆盖范围**: 所有服务类、工具函数、业务逻辑
- **目标**: 80%+ 代码覆盖率
- **框架**: pytest + pytest-asyncio
- **位置**: `tests/unit/`

### 2. 集成测试
- **覆盖范围**: 数据库操作、API端点、服务间交互
- **目标**: 验证组件间正确协作
- **框架**: pytest + AsyncSQLAlchemy
- **位置**: `tests/integration/`

### 3. 端到端测试
- **覆盖范围**: 关键用户流程（学生学习、教师管理、管理员操作）
- **目标**: 验证完整业务流程
- **框架**: pytest + httpx
- **位置**: `tests/e2e/`

## 测试环境

### 本地开发环境
- **数据库**: SQLite in-memory（快速）
- **缓存**: Mock Redis
- **AI服务**: Mock 响应

### CI/CD环境
- **数据库**: PostgreSQL 容器
- **缓存**: Redis 容器
- **AI服务**: Mock 或测试端点

### 预发布/生产环境
- **数据库**: 真实PostgreSQL实例
- **缓存**: 真实Redis实例
- **AI服务**: 真实AI API（限流）

## 测试执行

### 本地执行
```bash
# 安装测试依赖
pip install -r requirements-test.txt

# 运行所有测试
pytest tests/ -v

# 运行单元测试
pytest tests/unit/ -v -m unit

# 运行集成测试
pytest tests/integration/ -v -m integration

# 运行端到端测试
pytest tests/e2e/ -v -m e2e

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html --cov-report=term

# 特定文件测试
pytest tests/unit/test_achievement_service.py -v
```

### CI/CD执行
通过GitHub Actions自动执行，包含：
1. 代码质量检查
2. 单元测试（带覆盖率）
3. 集成测试
4. 端到端测试
5. 安全扫描
6. 报告生成

## 测试覆盖率要求

### 最低覆盖率
- **总体**: 80%
- **核心服务**: 90%
- **关键业务逻辑**: 95%

### 覆盖率豁免
- `__repr__` 方法
- 调试代码
- 第三方库包装
- 明确标记 `# pragma: no cover`

## 测试夹具（Fixtures）

### 共享夹具（conftest.py）
- `db_session`: 数据库会话
- `test_user_data`: 测试用户数据
- `test_teacher_data`: 测试教师数据
- `test_admin_data`: 测试管理员数据
- `test_competition_data`: 测试竞赛数据
- `test_achievement_data`: 测试成就数据
- `test_goal_data`: 测试学习目标数据
- `test_learning_plan_data`: 测试学习计划数据
- `mock_file_metadata`: 模拟文件元数据
- `sample_questions`: 示例题目数据

## 测试文件组织

```
tests/
├── conftest.py              # 共享夹具
├── unit/                    # 单元测试
│   ├── test_achievement_service.py
│   ├── test_competition_service.py
│   ├── test_goal_setting_service.py
│   ├── test_learning_plan_service.py
│   ├── test_progress_monitoring_service.py
│   ├── test_social_learning_service.py
│   └── test_error_analysis_service.py
├── integration/             # 集成测试
│   ├── test_database_operations.py
│   ├── test_api_endpoints.py
│   ├── test_service_integration.py
│   └── test_transaction_management.py
├── e2e/                    # 端到端测试
│   ├── test_student_workflow.py
│   ├── test_teacher_workflow.py
│   └── test_admin_workflow.py
└── fixtures/               # 测试数据生成器
    ├── test_data.py
    └── mock_services.py
```

## 测试最佳实践

### 1. 测试独立性
- 每个测试独立运行
- 测试间不共享状态
- 使用夹具进行隔离

### 2. 测试命名
- 格式: `test_<功能>_<场景>_<期望结果>`
- 示例: `test_create_competition_with_valid_data_succeeds`

### 3. AAA模式
```python
async def test_example():
    # Arrange - 准备
    data = prepare_test_data()
    
    # Act - 执行
    result = await service.do_something(data)
    
    # Assert - 验证
    assert result.is_success
    assert result.value == expected
```

### 4. 异步测试
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    result = await async_service.method()
    assert result is not None
```

## 性能测试

### 基准测试
- 使用 `pytest-benchmark`
- 关键操作性能指标
- 响应时间SLA验证

### 负载测试
- 并发用户模拟
- 数据库连接池测试
- API限流验证

## 安全测试

### 认证测试
- JWT令牌验证
- 权限边界测试
- 会话管理测试

### 授权测试
- 角色权限验证
- 资源访问控制
- 越权访问防护

### 数据安全
- SQL注入防护
- XSS防护
- 敏感数据加密

## 测试报告

### 覆盖率报告
- HTML格式（详细）
- XML格式（CI集成）
- 终端输出（快速查看）

### 测试结果报告
- 测试总数
- 通过/失败/跳过
- 执行时间
- 失败详情

## 持续改进

### 测试回顾
- 每次失败的根本原因分析
- 测试缺口识别
- 测试套件优化

### 测试指标监控
- 测试通过率趋势
- 覆盖率趋势
- 测试执行时间
- 缺陷逃逸率

## 生产就绪检查清单

- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 核心服务覆盖率 ≥ 90%
- [ ] 所有集成测试通过
- [ ] 关键E2E流程测试通过
- [ ] 安全测试通过
- [ ] 性能测试满足SLA
- [ ] CI/CD流水线完整
- [ ] 测试文档完整
- [ ] 团队测试培训完成

---

**最后更新**: 2026-03-02
**版本**: 1.0
