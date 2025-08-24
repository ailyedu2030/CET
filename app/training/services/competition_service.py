"""学习竞赛服务 - 公平公正的学习竞赛系统."""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CompetitionService:
    """学习竞赛服务 - 组织和管理各类学习竞赛活动."""

    def __init__(self, db: AsyncSession) -> None:
        """初始化竞赛服务."""
        self.db = db

        # 竞赛类型配置
        self.competition_types = {
            "speed_challenge": {
                "name": "速度挑战",
                "description": "在限定时间内完成最多题目",
                "duration_minutes": 30,
                "scoring_method": "speed_accuracy",
                "max_participants": 100,
            },
            "accuracy_contest": {
                "name": "准确率竞赛",
                "description": "追求最高的答题准确率",
                "duration_minutes": 60,
                "scoring_method": "accuracy_first",
                "max_participants": 50,
            },
            "endurance_marathon": {
                "name": "学习马拉松",
                "description": "长时间持续学习挑战",
                "duration_minutes": 180,
                "scoring_method": "endurance_points",
                "max_participants": 200,
            },
            "team_battle": {
                "name": "团队对战",
                "description": "班级或小组间的团队竞赛",
                "duration_minutes": 45,
                "scoring_method": "team_average",
                "max_participants": 8,  # 每队最多8人
            },
            "daily_challenge": {
                "name": "每日挑战",
                "description": "每日限时挑战题目",
                "duration_minutes": 15,
                "scoring_method": "daily_points",
                "max_participants": 1000,
            },
        }

        # 奖励配置
        self.reward_config = {
            "champion": {"points": 500, "badge": "🏆", "title": "冠军"},
            "runner_up": {"points": 300, "badge": "🥈", "title": "亚军"},
            "third_place": {"points": 200, "badge": "🥉", "title": "季军"},
            "top_10": {"points": 100, "badge": "🏅", "title": "前十强"},
            "participant": {"points": 20, "badge": "🎖️", "title": "参与者"},
        }

    async def create_competition(
        self, organizer_id: int, competition_data: dict[str, Any]
    ) -> dict[str, Any]:
        """创建学习竞赛."""
        try:
            # 验证组织者权限
            if not await self._verify_organizer_permission(organizer_id):
                raise ValueError("没有权限创建竞赛")

            # 验证竞赛数据
            validated_data = await self._validate_competition_data(competition_data)

            # 生成竞赛ID
            competition_id = await self._generate_competition_id()

            # 创建竞赛
            competition = {
                "competition_id": competition_id,
                "organizer_id": organizer_id,
                "title": validated_data["title"],
                "description": validated_data.get("description", ""),
                "competition_type": validated_data["competition_type"],
                "difficulty_level": validated_data.get("difficulty_level", "intermediate"),
                "start_time": datetime.fromisoformat(validated_data["start_time"]),
                "end_time": datetime.fromisoformat(validated_data["end_time"]),
                "registration_deadline": datetime.fromisoformat(
                    validated_data["registration_deadline"]
                ),
                "max_participants": validated_data.get("max_participants", 100),
                "entry_requirements": validated_data.get("entry_requirements", {}),
                "question_pool": validated_data.get("question_pool", []),
                "rules": validated_data.get("rules", []),
                "prizes": validated_data.get("prizes", {}),
                "status": "upcoming",
                "participant_count": 0,
                "created_at": datetime.now(),
            }

            # 保存竞赛
            await self._save_competition(competition)

            # 创建竞赛题库
            await self._prepare_competition_questions(competition_id, validated_data)

            # 发布竞赛公告
            await self._publish_competition_announcement(competition)

            logger.info(f"用户 {organizer_id} 创建竞赛: {competition['title']}")
            return competition

        except Exception as e:
            logger.error(f"创建竞赛失败: {str(e)}")
            raise

    async def register_for_competition(self, user_id: int, competition_id: str) -> dict[str, Any]:
        """报名参加竞赛."""
        try:
            # 获取竞赛信息
            competition = await self._get_competition(competition_id)
            if not competition:
                raise ValueError(f"竞赛不存在: {competition_id}")

            # 检查报名条件
            await self._check_registration_eligibility(user_id, competition)

            # 检查是否已报名
            if await self._is_already_registered(user_id, competition_id):
                raise ValueError("您已经报名了这个竞赛")

            # 检查报名截止时间
            if datetime.now() > competition["registration_deadline"]:
                raise ValueError("报名时间已截止")

            # 检查参与人数限制
            if competition["participant_count"] >= competition["max_participants"]:
                raise ValueError("竞赛报名已满")

            # 创建报名记录
            registration = {
                "registration_id": await self._generate_registration_id(),
                "competition_id": competition_id,
                "user_id": user_id,
                "registered_at": datetime.now(),
                "status": "registered",
                "team_id": None,  # 个人赛为None，团队赛需要分配
            }

            # 保存报名记录
            await self._save_registration(registration)

            # 更新竞赛参与人数
            await self._update_participant_count(competition_id, 1)

            # 发送确认通知
            await self._send_registration_confirmation(user_id, competition)

            logger.info(f"用户 {user_id} 报名竞赛: {competition_id}")
            return {
                "registration": registration,
                "competition": competition,
                "message": "报名成功！",
            }

        except Exception as e:
            logger.error(f"竞赛报名失败: {str(e)}")
            raise

    async def start_competition_session(self, user_id: int, competition_id: str) -> dict[str, Any]:
        """开始竞赛答题会话."""
        try:
            # 验证参赛资格
            if not await self._verify_participation_eligibility(user_id, competition_id):
                raise ValueError("您没有参加此竞赛的资格")

            # 获取竞赛信息
            competition = await self._get_competition(competition_id)

            # 检查竞赛状态
            if competition and competition["status"] != "active":
                raise ValueError("竞赛尚未开始或已结束")

            # 检查是否已有进行中的会话
            existing_session = await self._get_active_competition_session(user_id, competition_id)
            if existing_session:
                return existing_session

            # 获取竞赛题目
            questions = await self._get_competition_questions(competition_id, user_id)

            # 创建竞赛会话
            session = {
                "session_id": await self._generate_session_id(),
                "competition_id": competition_id,
                "user_id": user_id,
                "questions": questions,
                "start_time": datetime.now(),
                "end_time": datetime.now()
                + timedelta(minutes=competition["duration_minutes"] if competition else 60),
                "current_question_index": 0,
                "answers": [],
                "score": 0.0,
                "status": "active",
            }

            # 保存竞赛会话
            await self._save_competition_session(session)

            logger.info(f"用户 {user_id} 开始竞赛会话: {competition_id}")
            return {
                "session": session,
                "first_question": questions[0] if questions else None,
                "time_limit": competition["duration_minutes"] if competition else 60,
            }

        except Exception as e:
            logger.error(f"开始竞赛会话失败: {str(e)}")
            raise

    async def submit_competition_answer(
        self, user_id: int, session_id: str, answer_data: dict[str, Any]
    ) -> dict[str, Any]:
        """提交竞赛答案."""
        try:
            # 获取竞赛会话
            session = await self._get_competition_session(session_id)
            if not session or session["user_id"] != user_id:
                raise ValueError("无效的竞赛会话")

            # 检查会话状态
            if session["status"] != "active":
                raise ValueError("竞赛会话已结束")

            # 检查时间限制
            if datetime.now() > session["end_time"]:
                await self._end_competition_session(session_id)
                raise ValueError("竞赛时间已结束")

            # 验证答案数据
            validated_answer = await self._validate_answer_data(answer_data)

            # 获取当前题目
            current_question = session["questions"][session["current_question_index"]]

            # 评分
            score_result = await self._score_competition_answer(current_question, validated_answer)

            # 记录答案
            answer_record = {
                "question_id": current_question["id"],
                "user_answer": validated_answer["answer"],
                "correct_answer": current_question["correct_answer"],
                "is_correct": score_result["is_correct"],
                "score": score_result["score"],
                "time_spent": validated_answer.get("time_spent", 0),
                "answered_at": datetime.now(),
            }

            # 更新会话
            updated_session = await self._update_competition_session(session_id, answer_record)

            # 检查是否完成所有题目
            if updated_session["current_question_index"] >= len(session["questions"]):
                final_result = await self._complete_competition_session(session_id)
                return {
                    "answer_result": score_result,
                    "session_completed": True,
                    "final_result": final_result,
                }

            # 返回下一题
            next_question = session["questions"][updated_session["current_question_index"]]
            return {
                "answer_result": score_result,
                "next_question": next_question,
                "session_completed": False,
                "progress": {
                    "current": updated_session["current_question_index"],
                    "total": len(session["questions"]),
                    "score": updated_session["score"],
                },
            }

        except Exception as e:
            logger.error(f"提交竞赛答案失败: {str(e)}")
            raise

    async def get_competition_leaderboard(
        self, competition_id: str, limit: int = 50
    ) -> dict[str, Any]:
        """获取竞赛排行榜."""
        try:
            # 获取竞赛信息
            competition = await self._get_competition(competition_id)
            if not competition:
                raise ValueError(f"竞赛不存在: {competition_id}")

            # 获取排行榜数据
            leaderboard_data = await self._get_leaderboard_data(competition_id, limit)

            # 计算排名
            for i, entry in enumerate(leaderboard_data):
                entry["rank"] = i + 1
                entry["reward"] = self._calculate_reward(i + 1, len(leaderboard_data))

            # 获取竞赛统计
            competition_stats = await self._get_competition_statistics(competition_id)

            return {
                "competition": competition,
                "leaderboard": leaderboard_data,
                "statistics": competition_stats,
                "updated_at": datetime.now(),
            }

        except Exception as e:
            logger.error(f"获取竞赛排行榜失败: {str(e)}")
            raise

    async def get_user_competition_history(self, user_id: int) -> dict[str, Any]:
        """获取用户竞赛历史."""
        try:
            # 获取用户参与的竞赛
            competitions = await self._get_user_competitions(user_id)

            # 获取详细结果
            for competition in competitions:
                competition["result"] = await self._get_user_competition_result(
                    user_id, competition["competition_id"]
                )

            # 计算统计数据
            stats = await self._calculate_user_competition_stats(competitions)

            return {
                "competitions": competitions,
                "statistics": stats,
                "total_competitions": len(competitions),
            }

        except Exception as e:
            logger.error(f"获取用户竞赛历史失败: {str(e)}")
            raise

    # ==================== 私有方法 ====================

    async def _verify_organizer_permission(self, user_id: int) -> bool:
        """验证组织者权限."""
        # TODO: 实现权限验证逻辑
        return True

    async def _validate_competition_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """验证竞赛数据."""
        required_fields = [
            "title",
            "competition_type",
            "start_time",
            "end_time",
            "registration_deadline",
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必需字段: {field}")

        # 验证竞赛类型
        if data["competition_type"] not in self.competition_types:
            raise ValueError(f"无效的竞赛类型: {data['competition_type']}")

        return data

    async def _generate_competition_id(self) -> str:
        """生成竞赛ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"comp_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def _save_competition(self, competition: dict[str, Any]) -> None:
        """保存竞赛到数据库."""
        # TODO: 实现数据库保存逻辑
        logger.info(f"保存竞赛: {competition['competition_id']}")

    async def _prepare_competition_questions(
        self, competition_id: str, competition_data: dict[str, Any]
    ) -> None:
        """准备竞赛题库."""
        # TODO: 实现题库准备逻辑
        logger.info(f"准备竞赛题库: {competition_id}")

    async def _publish_competition_announcement(self, competition: dict[str, Any]) -> None:
        """发布竞赛公告."""
        # TODO: 实现公告发布逻辑
        logger.info(f"发布竞赛公告: {competition['title']}")

    async def _get_competition(self, competition_id: str) -> dict[str, Any] | None:
        """获取竞赛信息."""
        # TODO: 实现从数据库获取竞赛信息的逻辑
        return {
            "competition_id": competition_id,
            "status": "active",
            "registration_deadline": datetime.now() + timedelta(days=1),
            "max_participants": 100,
            "participant_count": 50,
            "duration_minutes": 30,
        }

    async def _check_registration_eligibility(
        self, user_id: int, competition: dict[str, Any]
    ) -> None:
        """检查报名资格."""
        # TODO: 实现报名资格检查逻辑
        pass

    async def _is_already_registered(self, user_id: int, competition_id: str) -> bool:
        """检查是否已报名."""
        # TODO: 实现报名状态检查逻辑
        return False

    async def _generate_registration_id(self) -> str:
        """生成报名ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"reg_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def _save_registration(self, registration: dict[str, Any]) -> None:
        """保存报名记录."""
        # TODO: 实现数据库保存逻辑
        logger.info(f"保存报名记录: {registration['registration_id']}")

    async def _update_participant_count(self, competition_id: str, increment: int) -> None:
        """更新参与人数."""
        # TODO: 实现参与人数更新逻辑
        logger.info(f"更新竞赛参与人数: {competition_id}")

    async def _send_registration_confirmation(
        self, user_id: int, competition: dict[str, Any]
    ) -> None:
        """发送报名确认通知."""
        # TODO: 实现通知发送逻辑
        logger.info(f"发送报名确认: 用户{user_id}, 竞赛{competition['competition_id']}")

    async def _verify_participation_eligibility(self, user_id: int, competition_id: str) -> bool:
        """验证参赛资格."""
        # TODO: 实现参赛资格验证逻辑
        return True

    async def _get_active_competition_session(
        self, user_id: int, competition_id: str
    ) -> dict[str, Any] | None:
        """获取活跃的竞赛会话."""
        # TODO: 实现活跃会话获取逻辑
        return None

    async def _get_competition_questions(
        self, competition_id: str, user_id: int
    ) -> list[dict[str, Any]]:
        """获取竞赛题目."""
        # TODO: 实现题目获取逻辑
        return [
            {
                "id": 1,
                "question": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "correct_answer": "Paris",
            }
        ]

    async def _generate_session_id(self) -> str:
        """生成会话ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"session_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def _save_competition_session(self, session: dict[str, Any]) -> None:
        """保存竞赛会话."""
        # TODO: 实现数据库保存逻辑
        logger.info(f"保存竞赛会话: {session['session_id']}")

    async def _get_competition_session(self, session_id: str) -> dict[str, Any] | None:
        """获取竞赛会话."""
        # TODO: 实现从数据库获取会话的逻辑
        return {
            "session_id": session_id,
            "user_id": 1,
            "status": "active",
            "end_time": datetime.now() + timedelta(minutes=30),
            "questions": [],
            "current_question_index": 0,
        }

    async def _end_competition_session(self, session_id: str) -> None:
        """结束竞赛会话."""
        # TODO: 实现会话结束逻辑
        logger.info(f"结束竞赛会话: {session_id}")

    async def _validate_answer_data(self, answer_data: dict[str, Any]) -> dict[str, Any]:
        """验证答案数据."""
        if "answer" not in answer_data:
            raise ValueError("缺少答案数据")
        return answer_data

    async def _score_competition_answer(
        self, question: dict[str, Any], answer: dict[str, Any]
    ) -> dict[str, Any]:
        """评分竞赛答案."""
        is_correct = answer["answer"] == question["correct_answer"]
        score = 1.0 if is_correct else 0.0

        return {
            "is_correct": is_correct,
            "score": score,
            "explanation": (
                "答案正确" if is_correct else f"正确答案是: {question['correct_answer']}"
            ),
        }

    async def _update_competition_session(
        self, session_id: str, answer_record: dict[str, Any]
    ) -> dict[str, Any]:
        """更新竞赛会话."""
        # TODO: 实现会话更新逻辑
        return {"current_question_index": 1, "score": 1.0}

    async def _complete_competition_session(self, session_id: str) -> dict[str, Any]:
        """完成竞赛会话."""
        # TODO: 实现会话完成逻辑
        return {"final_score": 0.8, "rank": 15, "total_participants": 50}

    async def _get_leaderboard_data(self, competition_id: str, limit: int) -> list[dict[str, Any]]:
        """获取排行榜数据."""
        # TODO: 实现排行榜数据获取逻辑
        return []

    def _calculate_reward(self, rank: int, total_participants: int) -> dict[str, Any]:
        """计算奖励."""
        if rank == 1:
            return self.reward_config["champion"]
        elif rank == 2:
            return self.reward_config["runner_up"]
        elif rank == 3:
            return self.reward_config["third_place"]
        elif rank <= 10:
            return self.reward_config["top_10"]
        else:
            return self.reward_config["participant"]

    async def _get_competition_statistics(self, competition_id: str) -> dict[str, Any]:
        """获取竞赛统计."""
        # TODO: 实现统计数据获取逻辑
        return {
            "total_participants": 50,
            "completion_rate": 0.9,
            "average_score": 0.75,
            "average_time": 25,
        }

    async def _get_user_competitions(self, user_id: int) -> list[dict[str, Any]]:
        """获取用户参与的竞赛."""
        # TODO: 实现用户竞赛获取逻辑
        return []

    async def _get_user_competition_result(
        self, user_id: int, competition_id: str
    ) -> dict[str, Any]:
        """获取用户竞赛结果."""
        # TODO: 实现用户结果获取逻辑
        return {"score": 0.8, "rank": 15, "completion_time": 25}

    async def _calculate_user_competition_stats(
        self, competitions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """计算用户竞赛统计."""
        if not competitions:
            return {"total": 0, "wins": 0, "avg_rank": 0, "best_score": 0}

        return {
            "total": len(competitions),
            "wins": len([c for c in competitions if c.get("result", {}).get("rank", 999) == 1]),
            "avg_rank": sum(c.get("result", {}).get("rank", 999) for c in competitions)
            / len(competitions),
            "best_score": max(c.get("result", {}).get("score", 0) for c in competitions),
        }
