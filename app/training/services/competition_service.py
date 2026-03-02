"""学习竞赛服务 - 公平公正的学习竞赛系统."""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.training.models.competition_models import (
    CompetitionModel,
    CompetitionRegistrationModel,
    CompetitionSessionModel,
    LeaderboardEntryModel,
)

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
                "difficulty_level": validated_data.get(
                    "difficulty_level", "intermediate"
                ),
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

            logger.info("用户 %d 创建竞赛: %s", organizer_id, competition["title"])
            return competition

        except Exception as e:
            logger.error("创建竞赛失败: %s", str(e))
            raise

    async def register_for_competition(
        self, user_id: int, competition_id: str
    ) -> dict[str, Any]:
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

            logger.info("用户 %d 报名竞赛: %s", user_id, competition_id)
            return {
                "registration": registration,
                "competition": competition,
                "message": "报名成功！",
            }

        except Exception as e:
            logger.error("竞赛报名失败: %s", str(e))
            raise

    async def start_competition_session(
        self, user_id: int, competition_id: str
    ) -> dict[str, Any]:
        """开始竞赛答题会话."""
        try:
            # 验证参赛资格
            if not await self._verify_participation_eligibility(
                user_id, competition_id
            ):
                raise ValueError("您没有参加此竞赛的资格")

            # 获取竞赛信息
            competition = await self._get_competition(competition_id)

            # 检查竞赛状态
            if competition and competition["status"] != "active":
                raise ValueError("竞赛尚未开始或已结束")

            # 检查是否已有进行中的会话
            existing_session = await self._get_active_competition_session(
                user_id, competition_id
            )
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
                + timedelta(
                    minutes=competition["duration_minutes"] if competition else 60
                ),
                "current_question_index": 0,
                "answers": [],
                "score": 0.0,
                "status": "active",
            }

            # 保存竞赛会话
            await self._save_competition_session(session)

            logger.info("用户 %d 开始竞赛会话: %s", user_id, competition_id)
            return {
                "session": session,
                "first_question": questions[0] if questions else None,
                "time_limit": competition["duration_minutes"] if competition else 60,
            }

        except Exception as e:
            logger.error("开始竞赛会话失败: %s", str(e))
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
            score_result = await self._score_competition_answer(
                current_question, validated_answer
            )

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
            updated_session = await self._update_competition_session(
                session_id, answer_record
            )

            # 检查是否完成所有题目
            if updated_session["current_question_index"] >= len(session["questions"]):
                final_result = await self._complete_competition_session(session_id)
                return {
                    "answer_result": score_result,
                    "session_completed": True,
                    "final_result": final_result,
                }

            # 返回下一题
            next_question = session["questions"][
                updated_session["current_question_index"]
            ]
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
            logger.error("提交竞赛答案失败: %s", str(e))
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
            logger.error("获取竞赛排行榜失败: %s", str(e))
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
            logger.error("获取用户竞赛历史失败: %s", str(e))
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
        db_competition = CompetitionModel(
            competition_id=competition["competition_id"],
            organizer_id=competition["organizer_id"],
            title=competition["title"],
            description=competition.get("description", ""),
            competition_type=competition["competition_type"],
            difficulty_level=competition.get("difficulty_level", "intermediate"),
            start_time=competition["start_time"],
            end_time=competition["end_time"],
            registration_deadline=competition["registration_deadline"],
            max_participants=competition.get("max_participants", 100),
            participant_count=competition.get("participant_count", 0),
            entry_requirements=competition.get("entry_requirements", {}),
            question_pool=competition.get("question_pool", []),
            rules=competition.get("rules", []),
            prizes=competition.get("prizes", {}),
            status=competition.get("status", "upcoming"),
        )
        # Set duration_minutes based on competition type if available
        if competition["competition_type"] in self.competition_types:
            db_competition.duration_minutes = self.competition_types[
                competition["competition_type"]
            ]["duration_minutes"]
            db_competition.scoring_method = self.competition_types[
                competition["competition_type"]
            ]["scoring_method"]
        self.db.add(db_competition)
        await self.db.commit()
        await self.db.refresh(db_competition)
        logger.info("保存竞赛: %s", competition["competition_id"])

    async def _prepare_competition_questions(
        self, competition_id: str, competition_data: dict[str, Any]
    ) -> None:
        """准备竞赛题库."""
        try:
            # 获取竞赛类型和难度
            competition_type = competition_data.get("competition_type")
            difficulty = competition_data.get("difficulty_level", "intermediate")

            # 基础题库配置
            question_pool_config = {
                "competition_type": competition_type,
                "difficulty_level": difficulty,
                "total_questions": 0,
                "questions": [],
                "prepared_at": datetime.now().isoformat(),
            }

            # 根据竞赛类型确定题目数量和类型
            if competition_type == "speed_challenge":
                question_count = 50
                question_types = ["multiple_choice", "true_false"]
            elif competition_type == "accuracy_contest":
                question_count = 30
                question_types = ["multiple_choice", "short_answer"]
            elif competition_type == "endurance_marathon":
                question_count = 100
                question_types = [
                    "multiple_choice",
                    "true_false",
                    "short_answer",
                    "essay",
                ]
            elif competition_type == "team_battle":
                question_count = 40
                question_types = ["multiple_choice", "team_challenge"]
            else:  # daily_challenge
                question_count = 15
                question_types = ["multiple_choice"]

            # 生成示例题目（实际项目中应从题库服务获取）
            questions = []
            for i in range(question_count):
                question = {
                    "id": f"q_{i+1}",
                    "type": question_types[i % len(question_types)],
                    "difficulty": difficulty,
                    "question": f"这是第 {i+1} 道题目，类型：{question_types[i % len(question_types)]}",
                    "options": ["选项A", "选项B", "选项C", "选项D"]
                    if question_types[i % len(question_types)] == "multiple_choice"
                    else [],
                    "correct_answer": "选项A"
                    if question_types[i % len(question_types)] == "multiple_choice"
                    else "正确答案",
                    "points": 10
                    if difficulty == "easy"
                    else 20
                    if difficulty == "intermediate"
                    else 30,
                    "time_limit": 30
                    if question_types[i % len(question_types)] == "multiple_choice"
                    else 60,
                }
                questions.append(question)

            # 随机打乱题目顺序（确保公平性）
            import random

            random.shuffle(questions)

            question_pool_config["total_questions"] = len(questions)
            question_pool_config["questions"] = questions

            # 更新竞赛的题库配置
            result = await self.db.execute(
                select(CompetitionModel).where(
                    CompetitionModel.competition_id == competition_id
                )
            )
            db_competition = result.scalar_one_or_none()
            if db_competition:
                db_competition.question_pool = question_pool_config
                await self.db.commit()
                await self.db.refresh(db_competition)

            logger.info("准备竞赛题库: %s, 题目数量: %d", competition_id, len(questions))

        except Exception as e:
            logger.error("准备竞赛题库失败: %s", str(e))
            raise

    async def _publish_competition_announcement(
        self, competition: dict[str, Any]
    ) -> None:
        """发布竞赛公告."""
        try:
            # 创建活动日志条目
            announcement = {
                "competition_id": competition["competition_id"],
                "title": f"新竞赛发布: {competition['title']}",
                "content": f"""
                🎉 新竞赛上线啦！
                竞赛名称：{competition['title']}
                竞赛类型：{self.competition_types.get(competition['competition_type'], {}).get('name', '未知')}
                开始时间：{competition['start_time'].strftime('%Y-%m-%d %H:%M')}
                结束时间：{competition['end_time'].strftime('%Y-%m-%d %H:%M')}
                报名截止：{competition['registration_deadline'].strftime('%Y-%m-%d %H:%M')}
                最大参与人数：{competition['max_participants']}

                {competition.get('description', '')}

                快来报名参加吧！
                """,
                "published_at": datetime.now().isoformat(),
                "target_audience": "all_students",  # 可以根据entry_requirements调整
            }

            # TODO: 这里可以集成通知系统，发送给相关用户
            # 例如：
            # - 发送系统通知给所有学生
            # - 发送邮件给关注竞赛的用户
            # - 创建活动动态

            # 记录公告发布日志
            logger.info(
                "发布竞赛公告: %s, 目标受众: %s",
                competition["title"],
                announcement["target_audience"],
            )

            # TODO: 如果有班级或小组限制，可以针对性通知
            # entry_requirements = competition.get('entry_requirements', {})
            # if 'target_classes' in entry_requirements:
            #     await self._notify_classes(entry_requirements['target_classes'], announcement)

        except Exception as e:
            logger.error("发布竞赛公告失败: %s", str(e))
            # 公告发布失败不应阻止竞赛创建，只记录日志

    async def _get_competition(self, competition_id: str) -> dict[str, Any] | None:
        """获取竞赛信息."""
        result = await self.db.execute(
            select(CompetitionModel).where(
                CompetitionModel.competition_id == competition_id
            )
        )
        db_competition = result.scalar_one_or_none()
        if not db_competition:
            return None

        return {
            "competition_id": db_competition.competition_id,
            "organizer_id": db_competition.organizer_id,
            "title": db_competition.title,
            "description": db_competition.description,
            "competition_type": db_competition.competition_type,
            "difficulty_level": db_competition.difficulty_level,
            "start_time": db_competition.start_time,
            "end_time": db_competition.end_time,
            "registration_deadline": db_competition.registration_deadline,
            "duration_minutes": db_competition.duration_minutes,
            "max_participants": db_competition.max_participants,
            "participant_count": db_competition.participant_count,
            "entry_requirements": db_competition.entry_requirements,
            "question_pool": db_competition.question_pool,
            "rules": db_competition.rules,
            "prizes": db_competition.prizes,
            "status": db_competition.status,
            "scoring_method": db_competition.scoring_method,
        }

    async def _check_registration_eligibility(
        self, user_id: int, competition: dict[str, Any]
    ) -> None:
        """检查报名资格."""
        try:
            # 1. 检查用户是否被禁止参加该竞赛
            # TODO: 实现封禁检查逻辑
            # if await self._is_user_banned(user_id, competition['competition_id']):
            #     raise ValueError("您已被禁止参加此竞赛")

            # 2. 检查参赛要求
            entry_requirements = competition.get("entry_requirements", {})

            # 检查最低积分要求
            if "min_points" in entry_requirements:
                min_points = entry_requirements["min_points"]
                # TODO: 从用户服务获取用户积分
                # user_points = await self._get_user_points(user_id)
                # if user_points < min_points:
                #     raise ValueError(f"您的积分不足，需要至少 {min_points} 积分")
                logger.debug("检查积分要求: %d", min_points)

            # 检查历史竞赛参与次数限制
            if "max_previous_competitions" in entry_requirements:
                max_prev = entry_requirements["max_previous_competitions"]
                # 获取用户历史竞赛记录
                user_competitions = await self._get_user_competitions(user_id)
                if len(user_competitions) > max_prev:
                    raise ValueError(f"您已参加过 {len(user_competitions)} 次竞赛，超出限制")

            # 3. 检查用户在同类竞赛中的历史表现（可选）
            if "min_accuracy_rate" in entry_requirements:
                min_accuracy = entry_requirements["min_accuracy_rate"]
                # TODO: 计算用户在同类竞赛中的平均准确率
                # avg_accuracy = await self._get_user_average_accuracy(user_id, competition['competition_type'])
                # if avg_accuracy < min_accuracy:
                #     raise ValueError(f"您的历史准确率不足，需要至少 {min_accuracy*100}%")
                logger.debug("检查准确率要求: %.2f", min_accuracy)

            # 4. 检查用户是否已经完成过该竞赛（如果不允许重复参加）
            if entry_requirements.get("no_repeat", False):
                user_result = await self._get_user_competition_result(
                    user_id, competition["competition_id"]
                )
                if user_result.get("score", 0) > 0:
                    raise ValueError("您已经参加过此竞赛，不能重复报名")

            # 5. 检查用户状态是否正常
            # TODO: 实现用户状态检查
            # if not await self._is_user_active(user_id):
            #     raise ValueError("您的账户状态异常，无法报名")

            logger.info("用户 %d 报名资格检查通过: %s", user_id, competition["competition_id"])

        except ValueError:
            # 直接重新抛出 ValueError（我们自己抛出的资格不符合错误）
            raise
        except Exception as e:
            logger.error("检查报名资格失败: %s", str(e))
            raise ValueError("报名资格检查失败，请稍后再试") from e

    async def _is_already_registered(self, user_id: int, competition_id: str) -> bool:
        """检查是否已报名."""
        result = await self.db.execute(
            select(CompetitionRegistrationModel).where(
                and_(
                    CompetitionRegistrationModel.user_id == user_id,
                    CompetitionRegistrationModel.competition_id == competition_id,
                    CompetitionRegistrationModel.status == "registered",
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def _generate_registration_id(self) -> str:
        """生成报名ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"reg_{timestamp}_{hash(timestamp) % 10000:04d}"

    async def _save_registration(self, registration: dict[str, Any]) -> None:
        """保存报名记录."""
        db_registration = CompetitionRegistrationModel(
            registration_id=registration["registration_id"],
            competition_id=registration["competition_id"],
            user_id=registration["user_id"],
            team_id=registration.get("team_id"),
            registered_at=registration["registered_at"],
            status=registration["status"],
        )
        self.db.add(db_registration)
        await self.db.commit()
        await self.db.refresh(db_registration)
        logger.info("保存报名记录: %s", registration["registration_id"])

    async def _update_participant_count(
        self, competition_id: str, increment: int
    ) -> None:
        """更新参与人数."""
        result = await self.db.execute(
            select(CompetitionModel).where(
                CompetitionModel.competition_id == competition_id
            )
        )
        db_competition = result.scalar_one_or_none()
        if db_competition:
            db_competition.participant_count += increment
            await self.db.commit()
            await self.db.refresh(db_competition)
        logger.info("更新竞赛参与人数: %s", competition_id)

    async def _send_registration_confirmation(
        self, user_id: int, competition: dict[str, Any]
    ) -> None:
        """发送报名确认通知."""
        # TODO: 实现通知发送逻辑
        logger.info("发送报名确认: 用户%d, 竞赛%s", user_id, competition["competition_id"])

    async def _verify_participation_eligibility(
        self, user_id: int, competition_id: str
    ) -> bool:
        """验证参赛资格."""
        # TODO: 实现参赛资格验证逻辑
        return True

    async def _get_active_competition_session(
        self, user_id: int, competition_id: str
    ) -> dict[str, Any] | None:
        """获取活跃的竞赛会话."""
        result = await self.db.execute(
            select(CompetitionSessionModel).where(
                and_(
                    CompetitionSessionModel.user_id == user_id,
                    CompetitionSessionModel.competition_id == competition_id,
                    CompetitionSessionModel.status == "active",
                )
            )
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None

        return {
            "session_id": db_session.session_id,
            "competition_id": db_session.competition_id,
            "user_id": db_session.user_id,
            "questions": db_session.questions or [],
            "start_time": db_session.start_time,
            "end_time": db_session.end_time,
            "current_question_index": db_session.current_question_index,
            "answers": db_session.answers or [],
            "score": db_session.score,
            "status": db_session.status,
        }

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
        db_session = CompetitionSessionModel(
            session_id=session["session_id"],
            competition_id=session["competition_id"],
            user_id=session["user_id"],
            questions=session["questions"],
            start_time=session["start_time"],
            end_time=session["end_time"],
            current_question_index=session["current_question_index"],
            answers=session["answers"],
            score=session["score"],
            status=session["status"],
        )
        self.db.add(db_session)
        await self.db.commit()
        await self.db.refresh(db_session)
        logger.info("保存竞赛会话: %s", session["session_id"])

    async def _get_competition_session(self, session_id: str) -> dict[str, Any] | None:
        """获取竞赛会话."""
        result = await self.db.execute(
            select(CompetitionSessionModel).where(
                CompetitionSessionModel.session_id == session_id
            )
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            return None

        return {
            "session_id": db_session.session_id,
            "competition_id": db_session.competition_id,
            "user_id": db_session.user_id,
            "questions": db_session.questions or [],
            "start_time": db_session.start_time,
            "end_time": db_session.end_time,
            "current_question_index": db_session.current_question_index,
            "answers": db_session.answers or [],
            "score": db_session.score,
            "status": db_session.status,
        }

    async def _end_competition_session(self, session_id: str) -> None:
        """结束竞赛会话."""
        result = await self.db.execute(
            select(CompetitionSessionModel).where(
                CompetitionSessionModel.session_id == session_id
            )
        )
        db_session = result.scalar_one_or_none()
        if db_session:
            db_session.status = "completed"
            await self.db.commit()
            await self.db.refresh(db_session)
        logger.info("结束竞赛会话: %s", session_id)

    async def _validate_answer_data(
        self, answer_data: dict[str, Any]
    ) -> dict[str, Any]:
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
        result = await self.db.execute(
            select(CompetitionSessionModel).where(
                CompetitionSessionModel.session_id == session_id
            )
        )
        db_session = result.scalar_one_or_none()
        if not db_session:
            raise ValueError("Session not found")

        # Update answers list
        current_answers = db_session.answers or []
        current_answers.append(answer_record)
        db_session.answers = current_answers

        # Update score
        db_session.score += answer_record["score"]

        # Update current question index
        db_session.current_question_index += 1

        await self.db.commit()
        await self.db.refresh(db_session)

        return {
            "current_question_index": db_session.current_question_index,
            "score": db_session.score,
        }

    async def _complete_competition_session(self, session_id: str) -> dict[str, Any]:
        """完成竞赛会话."""
        # First, end the session
        await self._end_competition_session(session_id)

        # Get the session
        session = await self._get_competition_session(session_id)
        if not session:
            raise ValueError("Session not found")

        # Calculate completion time
        completion_time = int(
            (session["end_time"] - session["start_time"]).total_seconds()
        )

        # Calculate accuracy
        total_questions = len(session["questions"]) if session["questions"] else 0
        correct_answers = sum(1 for a in session["answers"] if a.get("is_correct"))
        accuracy_rate = (
            correct_answers / total_questions if total_questions > 0 else 0.0
        )

        # Get total participants
        competition_result = await self._get_competition(session["competition_id"])
        total_participants = (
            competition_result.get("participant_count", 0) if competition_result else 0
        )

        # Create leaderboard entry
        leaderboard_entry = LeaderboardEntryModel(
            competition_id=session["competition_id"],
            user_id=session["user_id"],
            final_score=session["score"],
            completion_time=completion_time,
            accuracy_rate=accuracy_rate,
            total_participants=total_participants,
            rank=None,  # Will be calculated later
        )
        self.db.add(leaderboard_entry)
        await self.db.commit()
        await self.db.refresh(leaderboard_entry)

        return {
            "final_score": session["score"],
            "accuracy_rate": accuracy_rate,
            "completion_time": completion_time,
            "total_participants": total_participants,
        }

    async def _get_leaderboard_data(
        self, competition_id: str, limit: int
    ) -> list[dict[str, Any]]:
        """获取排行榜数据."""
        result = await self.db.execute(
            select(LeaderboardEntryModel)
            .where(LeaderboardEntryModel.competition_id == competition_id)
            .order_by(desc(LeaderboardEntryModel.final_score))
            .limit(limit)
        )
        entries = result.scalars().all()

        return [
            {
                "user_id": entry.user_id,
                "final_score": entry.final_score,
                "accuracy_rate": entry.accuracy_rate,
                "completion_time": entry.completion_time,
                "rank": None,  # Will be set by caller
            }
            for entry in entries
        ]

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
        # Total participants
        participants_result = await self.db.execute(
            select(func.count(CompetitionRegistrationModel.id)).where(
                CompetitionRegistrationModel.competition_id == competition_id
            )
        )
        total_participants = participants_result.scalar() or 0

        # Completed sessions
        sessions_result = await self.db.execute(
            select(func.count(CompetitionSessionModel.id)).where(
                and_(
                    CompetitionSessionModel.competition_id == competition_id,
                    CompetitionSessionModel.status == "completed",
                )
            )
        )
        completed_sessions = sessions_result.scalar() or 0

        # Average score
        avg_score_result = await self.db.execute(
            select(func.avg(LeaderboardEntryModel.final_score)).where(
                LeaderboardEntryModel.competition_id == competition_id
            )
        )
        average_score = avg_score_result.scalar() or 0.0

        # Average time
        avg_time_result = await self.db.execute(
            select(func.avg(LeaderboardEntryModel.completion_time)).where(
                LeaderboardEntryModel.competition_id == competition_id
            )
        )
        average_time_seconds = avg_time_result.scalar() or 0
        average_time = int(average_time_seconds / 60) if average_time_seconds > 0 else 0

        completion_rate = (
            completed_sessions / total_participants if total_participants > 0 else 0.0
        )

        return {
            "total_participants": total_participants,
            "completion_rate": completion_rate,
            "average_score": average_score,
            "average_time": average_time,
        }

    async def _get_user_competitions(self, user_id: int) -> list[dict[str, Any]]:
        """获取用户参与的竞赛."""
        # Get registrations for this user
        registrations_result = await self.db.execute(
            select(CompetitionRegistrationModel).where(
                CompetitionRegistrationModel.user_id == user_id
            )
        )
        registrations = registrations_result.scalars().all()

        competitions = []
        for reg in registrations:
            # Get competition details
            comp = await self._get_competition(reg.competition_id)
            if comp:
                competitions.append(comp)

        return competitions

    async def _get_user_competition_result(
        self, user_id: int, competition_id: str
    ) -> dict[str, Any]:
        """获取用户竞赛结果."""
        result = await self.db.execute(
            select(LeaderboardEntryModel).where(
                and_(
                    LeaderboardEntryModel.user_id == user_id,
                    LeaderboardEntryModel.competition_id == competition_id,
                )
            )
        )
        entry = result.scalar_one_or_none()

        if not entry:
            return {"score": 0.0, "rank": None, "completion_time": None}

        # Calculate rank
        rank_result = await self.db.execute(
            select(func.count(LeaderboardEntryModel.id)).where(
                and_(
                    LeaderboardEntryModel.competition_id == competition_id,
                    LeaderboardEntryModel.final_score > entry.final_score,
                )
            )
        )
        rank = (rank_result.scalar() or 0) + 1

        return {
            "score": entry.final_score,
            "rank": rank,
            "completion_time": entry.completion_time,
        }

    async def _calculate_user_competition_stats(
        self, competitions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """计算用户竞赛统计."""
        if not competitions:
            return {"total": 0, "wins": 0, "avg_rank": 0, "best_score": 0}

        return {
            "total": len(competitions),
            "wins": len(
                [c for c in competitions if c.get("result", {}).get("rank", 999) == 1]
            ),
            "avg_rank": sum(c.get("result", {}).get("rank", 999) for c in competitions)
            / len(competitions),
            "best_score": max(
                c.get("result", {}).get("score", 0) for c in competitions
            ),
        }
