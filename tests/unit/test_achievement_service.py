"""
CET 教育平台 - 成就服务单元测试

全面测试成就服务的所有功能，确保生产级质量。
"""

import logging
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.training.services.achievement_service import AchievementService

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.unit
class TestAchievementService:
    """成就服务单元测试"""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """模拟数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def achievement_service(self, mock_db_session: AsyncMock) -> AchievementService:
        """成就服务实例"""
        return AchievementService(db=mock_db_session)

    @pytest.fixture
    def sample_achievement_data(self) -> dict[str, Any]:
        """示例成就数据"""
        return {
            "achievement_id": "ach_test_001",
            "title": "学习新星",
            "description": "完成第一个学习会话",
            "achievement_type": "completion",
            "criteria": {"type": "completion", "target": 1},
            "points": 100,
            "badge": "new_star",
            "is_active": True,
            "created_at": datetime.utcnow(),
        }

    @pytest.fixture
    def sample_user_data(self) -> dict[str, Any]:
        """示例用户数据"""
        return {
            "user_id": 1,
            "username": "test_user",
            "email": "test@example.com",
            "full_name": "测试用户",
            "role": "student",
            "is_active": True,
        }

    @pytest.fixture
    def sample_training_session(self) -> dict[str, Any]:
        """示例训练会话数据"""
        now = datetime.utcnow()
        return {
            "session_id": "session_test_001",
            "user_id": 1,
            "training_type": "vocabulary",
            "start_time": now - timedelta(minutes=30),
            "end_time": now,
            "status": "completed",
            "score": 85,
            "accuracy": 0.85,
        }

    async def test_service_initialization(
        self,
        achievement_service: AchievementService,
        mock_db_session: AsyncMock,
    ) -> None:
        """测试服务初始化"""
        # Assert
        assert achievement_service is not None
        assert achievement_service.db == mock_db_session
        logger.info("✅ 服务初始化测试通过")

    async def test_create_achievement_success(
        self,
        achievement_service: AchievementService,
        sample_achievement_data: dict[str, Any],
        mock_db_session: AsyncMock,
    ) -> None:
        """测试成功创建成就"""
        # Arrange
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_execute_result

        # Act
        result = await achievement_service.create_achievement(sample_achievement_data)

        # Assert
        assert result is not None
        assert result["achievement_id"] == sample_achievement_data["achievement_id"]
        assert result["title"] == sample_achievement_data["title"]
        assert result["is_active"] is True

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
        logger.info("✅ 创建成就成功测试通过")

    async def test_create_achievement_duplicate_id(
        self,
        achievement_service: AchievementService,
        sample_achievement_data: dict[str, Any],
        mock_db_session: AsyncMock,
    ) -> None:
        """测试创建重复ID的成就"""
        # Arrange
        mock_existing_achievement = MagicMock()
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = mock_existing_achievement
        mock_db_session.execute.return_value = mock_execute_result

        # Act & Assert
        with pytest.raises(ValueError, match="Achievement already exists"):
            await achievement_service.create_achievement(sample_achievement_data)

        logger.info("✅ 重复ID测试通过")

    async def test_get_achievement_success(
        self,
        achievement_service: AchievementService,
        sample_achievement_data: dict[str, Any],
        mock_db_session: AsyncMock,
    ) -> None:
        """测试成功获取成就"""
        # Arrange
        mock_achievement = MagicMock()
        mock_achievement.achievement_id = sample_achievement_data["achievement_id"]
        mock_achievement.title = sample_achievement_data["title"]
        mock_achievement.description = sample_achievement_data["description"]
        mock_achievement.achievement_type = sample_achievement_data["achievement_type"]
        mock_achievement.points = sample_achievement_data["points"]
        mock_achievement.badge = sample_achievement_data["badge"]
        mock_achievement.is_active = sample_achievement_data["is_active"]
        mock_achievement.created_at = sample_achievement_data["created_at"]

        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = mock_achievement
        mock_db_session.execute.return_value = mock_execute_result

        # Act
        result = await achievement_service.get_achievement(
            sample_achievement_data["achievement_id"]
        )

        # Assert
        assert result is not None
        assert result["achievement_id"] == sample_achievement_data["achievement_id"]
        assert result["title"] == sample_achievement_data["title"]
        logger.info("✅ 获取成就成功测试通过")

    async def test_get_achievement_not_found(
        self,
        achievement_service: AchievementService,
        mock_db_session: AsyncMock,
    ) -> None:
        """测试获取不存在的成就"""
        # Arrange
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_execute_result

        # Act
        result = await achievement_service.get_achievement("non_existent_id")

        # Assert
        assert result is None
        logger.info("✅ 成就不存在测试通过")

    async def test_award_achievement_success(
        self,
        achievement_service: AchievementService,
        sample_achievement_data: dict[str, Any],
        sample_user_data: dict[str, Any],
        mock_db_session: AsyncMock,
    ) -> None:
        """测试成功授予成就"""
        # Arrange
        # Mock achievement query
        mock_achievement = MagicMock()
        mock_achievement.achievement_id = sample_achievement_data["achievement_id"]
        mock_achievement.points = sample_achievement_data["points"]
        mock_achievement.is_active = True

        mock_achievement_result = MagicMock()
        mock_achievement_result.scalar_one_or_none.return_value = mock_achievement

        # Mock existing user achievement query (returns None)
        mock_user_achievement_result = MagicMock()
        mock_user_achievement_result.scalar_one_or_none.return_value = None

        def side_effect(*args, **kwargs):
            if "user_achievements" in str(args):
                return mock_user_achievement_result
            return mock_achievement_result

        mock_db_session.execute.side_effect = side_effect

        # Act
        result = await achievement_service.award_achievement(
            user_id=sample_user_data["user_id"],
            achievement_id=sample_achievement_data["achievement_id"],
        )

        # Assert
        assert result is not None
        assert result["user_id"] == sample_user_data["user_id"]
        assert result["achievement_id"] == sample_achievement_data["achievement_id"]
        assert result["awarded_at"] is not None

        logger.info("✅ 授予成就成功测试通过")

    async def test_award_achievement_already_awarded(
        self,
        achievement_service: AchievementService,
        sample_achievement_data: dict[str, Any],
        sample_user_data: dict[str, Any],
        mock_db_session: AsyncMock,
    ) -> None:
        """测试授予已获得的成就"""
        # Arrange
        # Mock achievement query
        mock_achievement = MagicMock()
        mock_achievement.achievement_id = sample_achievement_data["achievement_id"]
        mock_achievement.is_active = True

        mock_achievement_result = MagicMock()
        mock_achievement_result.scalar_one_or_none.return_value = mock_achievement

        # Mock existing user achievement query (returns existing)
        mock_user_achievement = MagicMock()
        mock_user_achievement_result = MagicMock()
        mock_user_achievement_result.scalar_one_or_none.return_value = (
            mock_user_achievement
        )

        def side_effect(*args, **kwargs):
            if "user_achievements" in str(args):
                return mock_user_achievement_result
            return mock_achievement_result

        mock_db_session.execute.side_effect = side_effect

        # Act & Assert
        with pytest.raises(ValueError, match="Achievement already awarded"):
            await achievement_service.award_achievement(
                user_id=sample_user_data["user_id"],
                achievement_id=sample_achievement_data["achievement_id"],
            )

        logger.info("✅ 成就已授予测试通过")

    async def test_get_user_achievements(
        self,
        achievement_service: AchievementService,
        sample_user_data: dict[str, Any],
        mock_db_session: AsyncMock,
    ) -> None:
        """测试获取用户成就列表"""
        # Arrange
        mock_achievement_1 = MagicMock()
        mock_achievement_1.achievement_id = "ach_001"
        mock_achievement_1.title = "成就1"
        mock_achievement_1.points = 100
        mock_achievement_1.awarded_at = datetime.utcnow()

        mock_achievement_2 = MagicMock()
        mock_achievement_2.achievement_id = "ach_002"
        mock_achievement_2.title = "成就2"
        mock_achievement_2.points = 200
        mock_achievement_2.awarded_at = datetime.utcnow()

        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value.all.return_value = [
            mock_achievement_1,
            mock_achievement_2,
        ]
        mock_db_session.execute.return_value = mock_execute_result

        # Act
        result = await achievement_service.get_user_achievements(
            sample_user_data["user_id"]
        )

        # Assert
        assert result is not None
        assert len(result) == 2
        assert result[0]["achievement_id"] == "ach_001"
        assert result[1]["achievement_id"] == "ach_002"
        logger.info("✅ 获取用户成就列表测试通过")

    async def test_check_achievement_criteria_completion(
        self,
        achievement_service: AchievementService,
        sample_training_session: dict[str, Any],
    ) -> None:
        """测试检查成就标准-完成类型"""
        # Arrange
        criteria = {"type": "completion", "target": 1}
        session_count = 1

        # Act
        result = achievement_service._check_achievement_criteria(
            criteria=criteria,
            session_count=session_count,
            total_score=100,
            accuracy=0.85,
            streak=5,
        )

        # Assert
        assert result is True
        logger.info("✅ 成就标准-完成类型测试通过")

    async def test_check_achievement_criteria_score(
        self,
        achievement_service: AchievementService,
    ) -> None:
        """测试检查成就标准-分数类型"""
        # Arrange
        criteria = {"type": "score", "target": 80}
        total_score = 85

        # Act
        result = achievement_service._check_achievement_criteria(
            criteria=criteria,
            session_count=1,
            total_score=total_score,
            accuracy=0.85,
            streak=5,
        )

        # Assert
        assert result is True
        logger.info("✅ 成就标准-分数类型测试通过")

    async def test_check_achievement_criteria_not_met(
        self,
        achievement_service: AchievementService,
    ) -> None:
        """测试检查成就标准-未达到"""
        # Arrange
        criteria = {"type": "completion", "target": 10}
        session_count = 5

        # Act
        result = achievement_service._check_achievement_criteria(
            criteria=criteria,
            session_count=session_count,
            total_score=100,
            accuracy=0.85,
            streak=5,
        )

        # Assert
        assert result is False
        logger.info("✅ 成就标准-未达到测试通过")

    async def test_error_handling_database_error(
        self,
        achievement_service: AchievementService,
        sample_achievement_data: dict[str, Any],
        mock_db_session: AsyncMock,
    ) -> None:
        """测试数据库错误处理"""
        # Arrange
        mock_db_session.execute.side_effect = Exception("Database connection failed")

        # Act & Assert
        with pytest.raises(Exception):  # noqa: B017
            await achievement_service.get_achievement(
                sample_achievement_data["achievement_id"]
            )

        logger.info("✅ 数据库错误处理测试通过")


@pytest.mark.asyncio
@pytest.mark.unit
class TestAchievementServiceEdgeCases:
    """成就服务边界条件测试"""

    @pytest.fixture
    def mock_db_session(self) -> AsyncMock:
        """模拟数据库会话"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def achievement_service(self, mock_db_session: AsyncMock) -> AchievementService:
        """成就服务实例"""
        return AchievementService(db=mock_db_session)

    async def test_empty_achievement_list(
        self,
        achievement_service: AchievementService,
        mock_db_session: AsyncMock,
    ) -> None:
        """测试空成就列表"""
        # Arrange
        mock_execute_result = MagicMock()
        mock_execute_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_execute_result

        # Act
        result = await achievement_service.get_user_achievements(999)

        # Assert
        assert result == []
        logger.info("✅ 空成就列表测试通过")

    async def test_inactive_achievement_not_awarded(
        self,
        achievement_service: AchievementService,
        mock_db_session: AsyncMock,
    ) -> None:
        """测试非活动成就不能授予"""
        # Arrange
        mock_achievement = MagicMock()
        mock_achievement.is_active = False

        mock_achievement_result = MagicMock()
        mock_achievement_result.scalar_one_or_none.return_value = mock_achievement
        mock_db_session.execute.return_value = mock_achievement_result

        # Act & Assert
        with pytest.raises(ValueError, match="Achievement is not active"):
            await achievement_service.award_achievement(
                user_id=1, achievement_id="ach_001"
            )

        logger.info("✅ 非活动成就测试通过")

    async def test_achievement_with_empty_title(
        self,
        achievement_service: AchievementService,
        mock_db_session: AsyncMock,
    ) -> None:
        """测试空标题的成就"""
        # Arrange
        invalid_data = {
            "achievement_id": "ach_test_empty",
            "title": "",
            "description": "测试",
            "achievement_type": "completion",
            "criteria": {"type": "completion", "target": 1},
            "points": 100,
            "badge": "test",
            "is_active": True,
        }

        # Act & Assert
        with pytest.raises(ValueError):
            await achievement_service.create_achievement(invalid_data)

        logger.info("✅ 空标题测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
