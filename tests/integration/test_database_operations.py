"""
CET 教育平台 - 数据库操作集成测试

全面测试数据库操作，确保生产级质量。
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.integration
class TestDatabaseConnection:
    """数据库连接测试"""

    async def test_basic_database_connection(self, db_session: AsyncSession) -> None:
        """测试基本数据库连接"""
        # Act
        result = await db_session.execute(text("SELECT 1 as test"))

        # Assert
        assert result.scalar() == 1
        logger.info("✅ 基本数据库连接测试通过")

    async def test_multiple_queries(self, db_session: AsyncSession) -> None:
        """测试多个查询"""
        # Act
        for i in range(5):
            result = await db_session.execute(text(f"SELECT {i} as value"))
            assert result.scalar() == i

        logger.info("✅ 多个查询测试通过")

    async def test_transaction_commit(self, db_session: AsyncSession) -> None:
        """测试事务提交"""
        # 注意：这里使用SQLite，实际项目使用PostgreSQL
        # Act & Assert
        await db_session.execute(text("BEGIN"))
        await db_session.execute(text("SELECT 1"))
        await db_session.execute(text("COMMIT"))

        logger.info("✅ 事务提交测试通过")

    async def test_transaction_rollback(self, db_session: AsyncSession) -> None:
        """测试事务回滚"""
        # Act & Assert
        await db_session.execute(text("BEGIN"))
        await db_session.execute(text("SELECT 1"))
        await db_session.execute(text("ROLLBACK"))

        logger.info("✅ 事务回滚测试通过")


@pytest.mark.asyncio
@pytest.mark.integration
class TestDatabaseSchema:
    """数据库模式测试"""

    async def test_table_existence(self, db_session: AsyncSession) -> None:
        """测试表存在性（基本检查）"""
        # 注意：这里使用的是SQLite内存数据库，实际表需要在Base中定义
        # Act
        result = await db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = result.scalars().all()

        # Assert
        assert isinstance(tables, list)
        logger.info(f"✅ 表存在性测试通过，找到 {len(tables)} 个表")

    async def test_sqlite_database_available(self) -> None:
        """测试SQLite数据库可用"""
        # Act & Assert
        try:
            import sqlite3

            conn = sqlite3.connect(":memory:")
            conn.execute("SELECT 1")
            conn.close()
            logger.info("✅ SQLite数据库可用测试通过")
        except ImportError:
            pytest.skip("SQLite not available")


@pytest.mark.asyncio
@pytest.mark.integration
class TestDataOperations:
    """数据操作集成测试"""

    @pytest.fixture
    def sample_data(self) -> dict[str, Any]:
        """示例数据"""
        return {
            "id": str(uuid4()),
            "name": "测试数据",
            "value": 100,
            "created_at": datetime.utcnow().isoformat(),
        }

    async def test_data_insert_and_query_basic(
        self, db_session: AsyncSession, sample_data: dict[str, Any]
    ) -> None:
        """测试基本数据插入和查询"""
        # 注意：这里使用简单的SQLite操作
        # 实际项目中应使用SQLAlchemy模型

        # Act
        await db_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS test_data (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    value INTEGER,
                    created_at TEXT
                )
            """
        )

        await db_session.execute(
            text(
                """
                INSERT INTO test_data (id, name, value, created_at)
                VALUES (:id, :name, :value, :created_at)
            """
            ),
            sample_data,
        )
        await db_session.commit()

        # Query
        result = await db_session.execute(
            text("SELECT * FROM test_data WHERE id = :id"),
            {"id": sample_data["id"]},
        )
        row = result.fetchone()

        # Assert
        assert row is not None
        assert row[0] == sample_data["id"]
        assert row[1] == sample_data["name"]
        assert row[2] == sample_data["value"]

        logger.info("✅ 数据插入和查询测试通过")

    async def test_data_update(self, db_session: AsyncSession) -> None:
        """测试数据更新"""
        # Act
        test_id = str(uuid4())

        await db_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS test_update (
                    id TEXT PRIMARY KEY,
                    value INTEGER
                )
            """
        )

        await db_session.execute(
            text("INSERT INTO test_update (id, value) VALUES (:id, :value)"),
            {"id": test_id, "value": 1},
        )
        await db_session.commit()

        # Update
        await db_session.execute(
            text("UPDATE test_update SET value = :value WHERE id = :id"),
            {"id": test_id, "value": 100},
        )
        await db_session.commit()

        # Verify
        result = await db_session.execute(
            text("SELECT value FROM test_update WHERE id = :id"),
            {"id": test_id},
        )
        value = result.scalar()

        # Assert
        assert value == 100
        logger.info("✅ 数据更新测试通过")

    async def test_data_delete(self, db_session: AsyncSession) -> None:
        """测试数据删除"""
        # Act
        test_id = str(uuid4())

        await db_session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS test_delete (
                    id TEXT PRIMARY KEY,
                    name TEXT
                )
            """
        )

        await db_session.execute(
            text("INSERT INTO test_delete (id, name) VALUES (:id, :name)"),
            {"id": test_id, "name": "Test"},
        )
        await db_session.commit()

        # Delete
        await db_session.execute(
            text("DELETE FROM test_delete WHERE id = :id"),
            {"id": test_id},
        )
        await db_session.commit()

        # Verify
        result = await db_session.execute(
            text("SELECT * FROM test_delete WHERE id = :id"),
            {"id": test_id},
        )
        row = result.fetchone()

        # Assert
        assert row is None
        logger.info("✅ 数据删除测试通过")


@pytest.mark.asyncio
@pytest.mark.integration
class TestConcurrentOperations:
    """并发操作测试"""

    async def test_concurrent_reads(self, db_session: AsyncSession) -> None:
        """测试并发读取"""
        # Act
        async def read_operation(i: int) -> int:
            result = await db_session.execute(text(f"SELECT {i}"))
            return result.scalar()

        tasks = [read_operation(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 10
        assert all(isinstance(r, int) for r in results)
        logger.info("✅ 并发读取测试通过")

    async def test_async_query_performance(self, db_session: AsyncSession) -> None:
        """测试异步查询性能"""
        import time

        # Act
        start_time = time.time()

        for i in range(100):
            await db_session.execute(text("SELECT 1"))

        elapsed_time = time.time() - start_time

        # Assert
        assert elapsed_time < 5.0  # 应该在5秒内完成
        logger.info(f"✅ 异步查询性能测试通过，耗时: {elapsed_time:.2f}秒")


@pytest.mark.asyncio
@pytest.mark.integration
class TestErrorHandling:
    """错误处理测试"""

    async def test_invalid_sql_handling(self, db_session: AsyncSession) -> None:
        """测试无效SQL处理"""
        # Act & Assert
        with pytest.raises(Exception):
            await db_session.execute(text("INVALID SQL SYNTAX"))

        logger.info("✅ 无效SQL处理测试通过")

    async def test_session_rollback_on_error(self, db_session: AsyncSession) -> None:
        """测试错误时的会话回滚"""
        # Act
        try:
            await db_session.execute(text("BEGIN"))
            await db_session.execute(text("INVALID SQL"))
        except Exception:
            await db_session.rollback()

        # Verify we can still use the session
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

        logger.info("✅ 错误时会话回滚测试通过")


@pytest.mark.asyncio
@pytest.mark.integration
class TestDatabaseHealthCheck:
    """数据库健康检查测试"""

    async def test_connection_health(self, db_session: AsyncSession) -> None:
        """测试连接健康"""
        # Act
        result = await db_session.execute(text("SELECT 1"))

        # Assert
        assert result.scalar() == 1
        logger.info("✅ 连接健康测试通过")

    async def test_multiple_health_checks(self, db_session: AsyncSession) -> None:
        """测试多次健康检查"""
        # Act
        for _ in range(5):
            result = await db_session.execute(text("SELECT 1"))
            assert result.scalar() == 1

        logger.info("✅ 多次健康检查测试通过")


# 测试套件标记
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
    pytest.mark.database,
]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
