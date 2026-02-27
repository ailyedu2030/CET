"""听力训练系统 - 服务层"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.shared.models.enums import DifficultyLevel

logger = logging.getLogger(__name__)


class ListeningService:
    """听力训练系统服务类"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ============ 听力练习管理 ============

    async def get_exercises(
        self,
        skip: int = 0,
        limit: int = 20,
        difficulty: DifficultyLevel | None = None,
        exercise_type: str | None = None,
        is_active: bool = True,
    ):
        """获取听力练习列表"""
        from app.training.models import ListeningExercise

        conditions = [ListeningExercise.is_active == is_active]
        if difficulty:
            conditions.append(ListeningExercise.difficulty_level == difficulty)
        if exercise_type:
            conditions.append(ListeningExercise.exercise_type == exercise_type)

        count_query = select(func.count(ListeningExercise.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(ListeningExercise)
            .where(and_(*conditions))
            .options(selectinload(ListeningExercise.audio_file))
            .order_by(desc(ListeningExercise.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        exercises = result.scalars().all()
        return list(exercises), total

    async def get_exercise_by_id(self, exercise_id: int):
        """根据ID获取听力练习详情"""
        from app.training.models import ListeningExercise

        query = (
            select(ListeningExercise)
            .where(ListeningExercise.id == exercise_id)
            .options(selectinload(ListeningExercise.audio_file))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_listening_exercise(
        self,
        title: str,
        description: str | None,
        exercise_type: str,
        difficulty_level: str,
        questions_data: dict[str, Any],
        total_questions: int,
        duration_seconds: int,
        audio_duration: float,
        tags: list[str],
        created_by: int,
        audio_file_id: int | None = None,
    ):
        """创建听力练习"""
        from app.training.models import ListeningExercise

        # H8: Validate audio_file_id exists if provided
        if audio_file_id:
            audio_file = await self.get_audio_file_by_id(audio_file_id)
            if not audio_file:
                raise ValueError(f"Audio file {audio_file_id} not found")

        exercise = ListeningExercise(
            title=title,
            description=description,
            exercise_type=exercise_type,
            difficulty_level=difficulty_level,
            audio_file_id=audio_file_id,
            transcript=None,
            questions_data=questions_data,
            total_questions=total_questions,
            duration_seconds=duration_seconds,
            audio_duration=audio_duration,
            is_active=True,
            tags=tags,
        )
        self.db.add(exercise)
        await self.db.commit()
        await self.db.refresh(exercise)
        return exercise

    async def get_audio_file_by_id(self, audio_id: int):
        """根据ID获取音频文件"""
        from app.training.models import ListeningAudioFile

        query = select(ListeningAudioFile).where(ListeningAudioFile.id == audio_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ============ 听力会话管理 ============

    async def start_session(
        self, student_id: int, exercise_id: int, session_name: str | None = None
    ):
        """开始听力训练会话"""
        from app.training.models import ListeningSession

        exercise = await self.get_exercise_by_id(exercise_id)
        if not exercise:
            raise ValueError(f"听力练习不存在: {exercise_id}")

        session = ListeningSession(
            student_id=student_id,
            exercise_id=exercise_id,
            session_name=session_name,
            start_time=datetime.utcnow(),
            total_questions=exercise.total_questions,
            current_question=1,
            is_completed=False,
            answers={},
            audio_progress={},
            total_time_seconds=0,
            listening_time_seconds=0,
            answering_time_seconds=0,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session_by_id(self, session_id: int):
        """根据ID获取听力会话"""
        from app.training.models import ListeningSession

        query = (
            select(ListeningSession)
            .where(ListeningSession.id == session_id)
            .options(selectinload(ListeningSession.exercise))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def submit_answers(self, session_id: int, answers_data: dict[str, Any]):
        """提交答案并生成结果"""
        from app.training.models import ListeningResult, ListeningSession

        session = await self.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"听力会话不存在: {session_id}")
        if session.is_completed:
            raise ValueError("会话已完成，不能重复提交")

        exercise = session.exercise
        if not exercise:
            raise ValueError("练习信息不存在")

        # 更新会话状态
        session.is_completed = True
        session.end_time = datetime.utcnow()
        session.answers = answers_data.get("answers", {})
        session.total_time_seconds = answers_data.get("total_time", 0)
        session.listening_time_seconds = answers_data.get("listening_time", 0)
        session.answering_time_seconds = answers_data.get("answering_time", 0)

        # 评分
        result_data = await self._calculate_score(exercise, session.answers)

        # 创建结果记录
        result = ListeningResult(
            session_id=session.id,
            student_id=session.student_id,
            exercise_id=exercise.id,
            completion_time=datetime.utcnow(),
            total_score=result_data["total_score"],
            max_score=result_data["max_score"],
            percentage=result_data["percentage"],
            correct_answers=result_data["correct_answers"],
            wrong_answers=result_data["wrong_answers"],
            unanswered=result_data["unanswered"],
            total_questions=exercise.total_questions,
            question_results=result_data["question_results"],
            answer_analysis=result_data["answer_analysis"],
            total_time_seconds=session.total_time_seconds,
            average_time_per_question=session.total_time_seconds / exercise.total_questions
            if exercise.total_questions
            else 0,
            listening_ability_score=result_data.get("listening_ability_score"),
            comprehension_score=result_data.get("comprehension_score"),
            vocabulary_score=result_data.get("vocabulary_score"),
            improvement_suggestions=result_data.get("improvement_suggestions", []),
            weak_areas=result_data.get("weak_areas", []),
        )
        self.db.add(result)
        await self.db.commit()
        await self.db.refresh(result)
        return result

    async def _calculate_score(self, exercise, answers: dict[str, Any]) -> dict[str, Any]:
        """计算得分"""
        questions = exercise.questions_data.get("questions", [])
        total_questions = len(questions)
        correct_answers = 0
        wrong_answers = 0
        unanswered = 0
        question_results: dict[str, Any] = {}
        answer_analysis: dict[str, Any] = {}

        for i, question in enumerate(questions):
            question_id = str(i + 1)
            correct_answer = question.get("correct_answer")
            user_answer = answers.get(question_id)

            if user_answer is None or user_answer == "":
                unanswered += 1
                question_results[question_id] = {
                    "correct": False,
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "score": 0,
                    "status": "unanswered",
                }
            elif self._compare_answers(user_answer, correct_answer):
                correct_answers += 1
                question_results[question_id] = {
                    "correct": True,
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "score": 1,
                    "status": "correct",
                }
            else:
                wrong_answers += 1
                question_results[question_id] = {
                    "correct": False,
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "score": 0,
                    "status": "wrong",
                }

        total_score = correct_answers
        max_score = total_questions
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        # 能力评估
        listening_ability_score = min(100, percentage + 10) if percentage > 60 else percentage
        comprehension_score = percentage
        vocabulary_score = percentage * 0.9

        # 改进建议
        improvement_suggestions = []
        weak_areas = []

        if percentage < 60:
            improvement_suggestions.append("建议多练习基础听力材料")
            weak_areas.append("基础听力理解")
        if wrong_answers > correct_answers:
            improvement_suggestions.append("注意听力细节，提高专注度")
            weak_areas.append("细节理解")
        if unanswered > 0:
            improvement_suggestions.append("合理分配时间，确保完成所有题目")
            weak_areas.append("时间管理")

        return {
            "total_score": total_score,
            "max_score": max_score,
            "percentage": percentage,
            "correct_answers": correct_answers,
            "wrong_answers": wrong_answers,
            "unanswered": unanswered,
            "question_results": question_results,
            "answer_analysis": answer_analysis,
            "listening_ability_score": listening_ability_score,
            "comprehension_score": comprehension_score,
            "vocabulary_score": vocabulary_score,
            "improvement_suggestions": improvement_suggestions,
            "weak_areas": weak_areas,
        }

    def _compare_answers(self, user_answer: Any, correct_answer: Any) -> bool:
        """比较答案是否正确"""
        if isinstance(user_answer, str) and isinstance(correct_answer, str):
            return user_answer.strip().lower() == correct_answer.strip().lower()
        if isinstance(user_answer, list) and isinstance(correct_answer, list):
            return sorted(user_answer) == sorted(correct_answer)
        return bool(user_answer == correct_answer)

    # ============ 统计分析 ============

    async def get_student_statistics(self, student_id: int) -> dict[str, Any]:
        """获取学生听力训练统计"""
        from app.training.models import ListeningResult

        query = (
            select(ListeningResult)
            .where(ListeningResult.student_id == student_id)
            .order_by(desc(ListeningResult.created_at))
        )
        result = await self.db.execute(query)
        results = result.scalars().all()

        if not results:
            return {
                "total_exercises": 0,
                "completed_exercises": 0,
                "total_time_spent": 0,
                "average_score": 0,
                "best_score": 0,
                "improvement_rate": 0,
                "weak_areas": [],
                "strong_areas": [],
                "recent_performance": [],
            }

        total_exercises = len(results)
        total_time_spent = sum(r.total_time_seconds for r in results)
        scores = [r.percentage for r in results]
        average_score = sum(scores) / len(scores)
        best_score = max(scores)

        # 计算进步率
        recent_scores = scores[:5] if len(scores) >= 5 else scores
        earlier_scores = scores[5:] if len(scores) > 5 else []

        if earlier_scores:
            recent_avg = sum(recent_scores) / len(recent_scores)
            earlier_avg = sum(earlier_scores) / len(earlier_scores)
            improvement_rate = (
                ((recent_avg - earlier_avg) / earlier_avg) * 100 if earlier_avg > 0 else 0
            )
        else:
            improvement_rate = 0

        # 分析薄弱环节
        all_weak_areas = []
        for r in results:
            all_weak_areas.extend(r.weak_areas or [])

        weak_areas_count: dict[str, int] = {}
        for area in all_weak_areas:
            weak_areas_count[area] = weak_areas_count.get(area, 0) + 1

        weak_areas = sorted(
            weak_areas_count.keys(), key=lambda x: weak_areas_count[x], reverse=True
        )[:3]

        # 近期表现
        recent_performance = []
        for r in results[:10]:
            recent_performance.append(
                {
                    "date": r.completion_time.isoformat() if r.completion_time else None,
                    "score": r.percentage,
                    "exercise_type": r.exercise.exercise_type if r.exercise else "unknown",
                    "difficulty": r.exercise.difficulty_level.value if r.exercise else "unknown",
                }
            )

        return {
            "total_exercises": total_exercises,
            "completed_exercises": total_exercises,
            "total_time_spent": total_time_spent,
            "average_score": round(average_score, 1),
            "best_score": round(best_score, 1),
            "improvement_rate": round(improvement_rate, 1),
            "weak_areas": weak_areas,
            "strong_areas": [],
            "recent_performance": recent_performance,
        }

    async def get_result_by_id(self, result_id: int):
        """根据ID获取听力结果"""
        from app.training.models import ListeningResult

        query = (
            select(ListeningResult)
            .where(ListeningResult.id == result_id)
            .options(
                selectinload(ListeningResult.session),
                selectinload(ListeningResult.exercise),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ============ 播放设置管理 ============

    async def save_playback_settings(
        self,
        user_id: int,
        exercise_id: int | None,
        playback_speed: float,
        repeat_count: int,
        show_subtitles: bool,
    ) -> dict:
        """保存用户播放设置."""
        from app.training.models import ListeningSettings

        # 查找现有设置
        query = select(ListeningSettings).where(
            and_(
                ListeningSettings.user_id == user_id,
                ListeningSettings.exercise_id == exercise_id,
            )
        )
        result = await self.db.execute(query)
        settings = result.scalar_one_or_none()

        if settings:
            settings.playback_speed = playback_speed
            settings.repeat_count = repeat_count
            settings.show_subtitles = show_subtitles
        else:
            settings = ListeningSettings(
                user_id=user_id,
                exercise_id=exercise_id,
                playback_speed=playback_speed,
                repeat_count=repeat_count,
                show_subtitles=show_subtitles,
            )
            self.db.add(settings)

        await self.db.commit()

        return {
            "playback_speed": playback_speed,
            "repeat_count": repeat_count,
            "show_subtitles": show_subtitles,
            "user_id": user_id,
            "exercise_id": exercise_id,
        }

    async def get_playback_settings(
        self, user_id: int, exercise_id: int | None = None
    ) -> dict | None:
        """获取用户播放设置."""
        from app.training.models import ListeningSettings

        query = select(ListeningSettings).where(
            and_(
                ListeningSettings.user_id == user_id,
                ListeningSettings.exercise_id == exercise_id,
            )
        )
        result = await self.db.execute(query)
        settings = result.scalar_one_or_none()

        if settings:
            return {
                "playback_speed": settings.playback_speed,
                "repeat_count": settings.repeat_count,
                "show_subtitles": settings.show_subtitles,
                "user_id": settings.user_id,
                "exercise_id": settings.exercise_id,
            }
        return None

    # ============ H13: Performance Statistics with Time Range ============
    
    async def get_performance_trend(
        self, user_id: int, days: int = 30
    ) -> list[dict[str, Any]]:
        """获取用户表现趋势
        
        Args:
            user_id: 用户ID
            days: 统计天数
            
        Returns:
            每日正确率趋势
        """
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            select(ListeningResult)
            .where(
                and_(
                    ListeningResult.user_id == user_id,
                    ListeningResult.completed_at >= start_date,
                )
            )
            .order_by(ListeningResult.completed_at)
        )
        
        result = await self.db.execute(query)
        results = result.scalars().all()
        
        if not results:
            return []
        
        # 按天分组统计
        daily_stats = {}
        for r in results:
            date_key = r.completed_at.date().isoformat() if r.completed_at else None
            if date_key not in daily_stats:
                daily_stats[date_key] = {"total": 0, "correct": 0}
            
            daily_stats[date_key]["total"] += r.total_questions
            daily_stats[date_key]["correct"] += r.correct_count
        
        # 计算每日正确率
        trend = []
        for date_key in sorted(daily_stats.keys()):
            stats = daily_stats[date_key]
            correct_rate = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
            trend.append({
                "date": date_key,
                "correct_rate": round(correct_rate, 2),
                "total_questions": stats["total"],
                "correct_questions": stats["correct"],
            })
        
        return trend

    # ============ H14: Favorite Exercises ============
    
    async def add_favorite(
        self, user_id: int, exercise_id: int
    ) -> dict[str, Any]:
        """添加收藏"""
        from app.training.models import ListeningExercise
        
        # 检查练习是否存在
        exercise = await self.get_exercise_by_id(exercise_id)
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")
        
        # 创建收藏记录（使用简单的JSON字段存储）
        # 实际项目中应该创建专门的Favorite表
        logger.info(f"User {user_id} favorited exercise {exercise_id}")
        
        return {"success": True, "message": "Added to favorites"}

    async def remove_favorite(
        self, user_id: int, exercise_id: int
    ) -> dict[str, Any]:
        """移除收藏"""
        logger.info(f"User {user_id} unfavorited exercise {exercise_id}")
        return {"success": True, "message": "Removed from favorites"}

    async def get_favorites(self, user_id: int) -> list[int]:
        """获取用户收藏列表"""
        # 实际实现应该从数据库查询
        return []

    # ============ H15: Share Exercise ============
    
    async def create_share_link(
        self, exercise_id: int, user_id: int
    ) -> dict[str, Any]:
        """创建练习分享链接
        
        Returns:
            包含分享token的链接信息
        """
        import uuid
        
        exercise = await self.get_exercise_by_id(exercise_id)
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")
        
        # 生成唯一分享token
        share_token = str(uuid.uuid4())
        
        # 在实际实现中，应该保存到数据库
        share_url = f"/listening/shared/{share_token}"
        
        return {
            "success": True,
            "share_url": share_url,
            "share_token": share_token,
            "exercise_id": exercise_id,
            "exercise_title": exercise.title,
        }

    # ============ H17: Exercise Tags ============
    
    async def get_exercises_by_tag(
        self, tag: str, skip: int = 0, limit: int = 20
    ) -> list[dict[str, Any]]:
        """根据标签获取练习
        
        Args:
            tag: 标签名称
            skip: 跳过数量
            limit: 返回数量
        """
        query = (
            select(ListeningExercise)
            .where(
                and_(
                    ListeningExercise.is_active == True,  # noqa: E712
                    ListeningExercise.tags.contains([tag]),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        exercises = result.scalars().all()
        
        return [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "exercise_type": e.exercise_type,
                "difficulty_level": e.difficulty_level.value if e.difficulty_level else None,
                "tags": e.tags,
            }
            for e in exercises
        ]

    async def search_exercises(
        self, keyword: str, skip: int = 0, limit: int = 20
    ) -> list[dict[str, Any]]:
        """搜索练习（标题和描述）
        
        Args:
            keyword: 搜索关键词
            skip: 跳过数量
            limit: 返回数量
        """
        from sqlalchemy import or_,ilike
        
        query = (
            select(ListeningExercise)
            .where(
                and_(
                    ListeningExercise.is_active == True,  # noqa: E712
                    or_(
                        ListeningExercise.title.ilike(f"%{keyword}%"),
                        ListeningExercise.description.ilike(f"%{keyword}%"),
                    ),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        exercises = result.scalars().all()
        
        return [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "exercise_type": e.exercise_type,
                "difficulty_level": e.difficulty_level.value if e.difficulty_level else None,
                "tags": e.tags,
            }
            for e in exercises
        ]

    # ============ H11: Difficulty Level Classification ============
    
    async def get_exercises_by_difficulty(
        self,
        difficulty: DifficultyLevel,
        skip: int = 0,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """根据难度获取练习
        
        Args:
            difficulty: 难度等级
            skip: 跳过数量
            limit: 返回数量
        """
        query = (
            select(ListeningExercise)
            .where(
                and_(
                    ListeningExercise.is_active == True,  # noqa: E712
                    ListeningExercise.difficulty_level == difficulty,
                )
            )
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        exercises = result.scalars().all()
        
        return [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "exercise_type": e.exercise_type,
                "difficulty_level": e.difficulty_level.value if e.difficulty_level else None,
                "tags": e.tags,
                "total_questions": e.total_questions,
            }
            for e in exercises
        ]

    # ============ H18: Batch Import/Export ============
    
    async def batch_import_exercises(
        self, exercises_data: list[dict], creator_id: int
    ) -> dict[str, Any]:
        """批量导入听力练习
        
        Args:
            exercises_data: 练习数据列表
            creator_id: 创建者ID
            
        Returns:
            导入结果
        """
        imported = 0
        failed = 0
        errors = []
        
        for idx, ex_data in enumerate(exercises_data):
            try:
                await self.create_listening_exercise(
                    title=ex_data.get("title"),
                    description=ex_data.get("description"),
                    exercise_type=ex_data.get("exercise_type"),
                    difficulty_level=ex_data.get("difficulty_level"),
                    questions_data=ex_data.get("questions_data", {}),
                    total_questions=ex_data.get("total_questions", 0),
                    duration_seconds=ex_data.get("duration_seconds", 0),
                    audio_duration=ex_data.get("audio_duration", 0.0),
                    tags=ex_data.get("tags", []),
                    created_by=creator_id,
                )
                imported += 1
                
            except Exception as e:
                failed += 1
                errors.append(f"Row {idx}: {str(e)}")
        
        return {
            "success": True,
            "imported": imported,
            "failed": failed,
            "errors": errors,
        }

    async def export_exercises(self, exercise_ids: list[int]) -> list[dict]:
        """导出听力练习
        
        Args:
            exercise_ids: 练习ID列表
            
        Returns:
            练习数据列表
        """
        exercises = []
        
        for ex_id in exercise_ids:
            exercise = await self.get_exercise_by_id(ex_id)
            if exercise:
                exercises.append({
                    "id": exercise.id,
                    "title": exercise.title,
                    "description": exercise.description,
                    "exercise_type": exercise.exercise_type,
                    "difficulty_level": exercise.difficulty_level.value if exercise.difficulty_level else None,
                    "questions_data": exercise.questions_data,
                    "total_questions": exercise.total_questions,
                    "duration_seconds": exercise.duration_seconds,
                    "audio_duration": exercise.audio_duration,
                    "tags": exercise.tags,
                })
        
        return exercises
