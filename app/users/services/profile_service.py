"""用户档案管理服务 - 处理用户基础信息和档案的CRUD操作."""

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.shared.models.enums import UserType
from app.users.models import StudentProfile, TeacherProfile, User
from app.users.utils.jwt_utils import jwt_manager


class ProfileUpdateHistory:
    """档案更新历史记录类."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化历史记录服务."""
        self.db = db_session

    async def record_update(
        self,
        user_id: int,
        field_name: str,
        old_value: Any,
        new_value: Any,
        updated_by: int,
        update_type: str = "profile_update",
    ) -> dict[str, Any]:
        """记录更新历史."""
        record = {
            "user_id": user_id,
            "field_name": field_name,
            "old_value": str(old_value) if old_value is not None else None,
            "new_value": str(new_value) if new_value is not None else None,
            "updated_by": updated_by,
            "updated_at": datetime.utcnow(),
            "update_type": update_type,
        }

        # 这里可以扩展为实际的历史记录表
        # 目前返回记录信息供日志使用
        return record


class ProfileService:
    """用户档案管理服务类."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化档案服务."""
        self.db = db_session
        self.history = ProfileUpdateHistory(db_session)

    # ===== 用户基础信息管理 =====

    async def get_user_profile(self, user_id: int) -> dict[str, Any] | None:
        """获取用户完整档案信息."""
        # 获取用户基础信息
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.student_profile),
                selectinload(User.teacher_profile),
                selectinload(User.roles),
            )
        )
        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()

        if not user:
            return None

        profile_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type.value,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "last_login": user.last_login,
            "login_count": user.login_count,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "roles": [{"code": role.code, "name": role.name} for role in user.roles],
        }

        # 根据用户类型添加对应档案信息
        if user.user_type == UserType.STUDENT and user.student_profile:
            profile_data["student_profile"] = await self._format_student_profile(
                user.student_profile
            )
        elif user.user_type == UserType.TEACHER and user.teacher_profile:
            profile_data["teacher_profile"] = await self._format_teacher_profile(
                user.teacher_profile
            )

        return profile_data

    async def update_user_basic_info(
        self,
        user_id: int,
        updates: dict[str, Any],
        updated_by: int,
    ) -> dict[str, Any]:
        """更新用户基础信息."""
        # 获取用户
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        # 允许更新的基础字段
        allowed_fields = {"username", "email", "is_active", "is_verified"}
        update_history = []

        for field, new_value in updates.items():
            if field not in allowed_fields:
                continue

            old_value = getattr(user, field)
            if old_value != new_value:
                # 特殊处理
                if field == "username":
                    # 检查用户名是否已存在
                    existing_user = await self._check_username_exists(
                        new_value, exclude_user_id=user_id
                    )
                    if existing_user:
                        raise ValueError("用户名已存在")
                elif field == "email":
                    # 检查邮箱是否已存在
                    existing_user = await self._check_email_exists(
                        new_value, exclude_user_id=user_id
                    )
                    if existing_user:
                        raise ValueError("邮箱已存在")

                # 更新字段值
                setattr(user, field, new_value)

                # 记录更新历史
                history_record = await self.history.record_update(
                    user_id=user_id,
                    field_name=field,
                    old_value=old_value,
                    new_value=new_value,
                    updated_by=updated_by,
                )
                update_history.append(history_record)

        user.updated_at = datetime.utcnow()
        await self.db.commit()

        return {
            "user_id": user_id,
            "updated_fields": list(updates.keys()),
            "update_history": update_history,
            "message": "用户基础信息更新成功",
        }

    async def change_user_password(
        self,
        user_id: int,
        new_password: str,
        updated_by: int,
        old_password: str | None = None,
    ) -> dict[str, Any]:
        """修改用户密码."""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")

        # 如果提供了旧密码，则验证
        if old_password and not jwt_manager.verify_password(old_password, user.password_hash):
            raise ValueError("原密码错误")

        # 更新密码
        user.password_hash = jwt_manager.hash_password(new_password)
        user.updated_at = datetime.utcnow()

        # 记录历史
        await self.history.record_update(
            user_id=user_id,
            field_name="password_hash",
            old_value="[HIDDEN]",
            new_value="[HIDDEN]",
            updated_by=updated_by,
            update_type="password_change",
        )

        await self.db.commit()

        return {
            "user_id": user_id,
            "message": "密码修改成功",
            "updated_at": user.updated_at,
        }

    # ===== 学生档案管理 =====

    async def get_student_profile(self, user_id: int) -> dict[str, Any] | None:
        """获取学生档案信息."""
        stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile: StudentProfile | None = result.scalar_one_or_none()

        if not profile:
            return None

        return await self._format_student_profile(profile)

    async def update_student_profile(
        self,
        user_id: int,
        updates: dict[str, Any],
        updated_by: int,
    ) -> dict[str, Any]:
        """更新学生档案信息."""
        # 获取学生档案
        stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile: StudentProfile | None = result.scalar_one_or_none()

        if not profile:
            raise ValueError("学生档案不存在")

        # 允许更新的字段
        allowed_fields = {
            "real_name",
            "age",
            "gender",
            "id_number",
            "phone",
            "emergency_contact_name",
            "emergency_contact_phone",
            "school",
            "department",
            "major",
            "grade",
            "class_name",
        }

        update_history = []

        for field, new_value in updates.items():
            if field not in allowed_fields:
                continue

            old_value = getattr(profile, field)
            if old_value != new_value:
                # 数据验证
                if field == "id_number" and new_value:
                    await self._validate_id_number(new_value, exclude_user_id=user_id)
                elif field == "phone" and new_value:
                    await self._validate_phone(new_value)

                # 更新字段值
                setattr(profile, field, new_value)

                # 记录更新历史
                history_record = await self.history.record_update(
                    user_id=user_id,
                    field_name=f"student_profile.{field}",
                    old_value=old_value,
                    new_value=new_value,
                    updated_by=updated_by,
                )
                update_history.append(history_record)

        profile.updated_at = datetime.utcnow()
        await self.db.commit()

        return {
            "user_id": user_id,
            "updated_fields": list(updates.keys()),
            "update_history": update_history,
            "message": "学生档案更新成功",
        }

    # ===== 教师档案管理 =====

    async def get_teacher_profile(self, user_id: int) -> dict[str, Any] | None:
        """获取教师档案信息."""
        stmt = select(TeacherProfile).where(TeacherProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile: TeacherProfile | None = result.scalar_one_or_none()

        if not profile:
            return None

        return await self._format_teacher_profile(profile)

    async def update_teacher_profile(
        self,
        user_id: int,
        updates: dict[str, Any],
        updated_by: int,
    ) -> dict[str, Any]:
        """更新教师档案信息."""
        # 获取教师档案
        stmt = select(TeacherProfile).where(TeacherProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        profile: TeacherProfile | None = result.scalar_one_or_none()

        if not profile:
            raise ValueError("教师档案不存在")

        # 允许更新的字段
        allowed_fields = {
            "real_name",
            "age",
            "gender",
            "title",
            "subject",
            "introduction",
            "phone",
            "teacher_certificate",
            "qualification_certificates",
            "honor_certificates",
        }

        update_history = []

        for field, new_value in updates.items():
            if field not in allowed_fields:
                continue

            old_value = getattr(profile, field)

            # 特殊处理JSON字段
            if field in ("qualification_certificates", "honor_certificates"):
                if old_value != new_value:
                    setattr(profile, field, new_value or {})
                    history_record = await self.history.record_update(
                        user_id=user_id,
                        field_name=f"teacher_profile.{field}",
                        old_value=old_value,
                        new_value=new_value,
                        updated_by=updated_by,
                    )
                    update_history.append(history_record)
            else:
                if old_value != new_value:
                    # 数据验证
                    if field == "phone" and new_value:
                        await self._validate_phone(new_value)

                    # 更新字段值
                    setattr(profile, field, new_value)

                    # 记录更新历史
                    history_record = await self.history.record_update(
                        user_id=user_id,
                        field_name=f"teacher_profile.{field}",
                        old_value=old_value,
                        new_value=new_value,
                        updated_by=updated_by,
                    )
                    update_history.append(history_record)

        profile.updated_at = datetime.utcnow()
        await self.db.commit()

        return {
            "user_id": user_id,
            "updated_fields": list(updates.keys()),
            "update_history": update_history,
            "message": "教师档案更新成功",
        }

    # ===== 档案统计信息 =====

    async def get_profile_statistics(self) -> dict[str, Any]:
        """获取档案统计信息."""
        # 用户类型统计
        user_stats = {}
        for user_type in UserType:
            stmt = select(User).where(User.user_type == user_type)
            result = await self.db.execute(stmt)
            users = result.scalars().all()

            active_count = sum(1 for user in users if user.is_active)
            verified_count = sum(1 for user in users if user.is_verified)

            user_stats[user_type.value] = {
                "total": len(users),
                "active": active_count,
                "verified": verified_count,
                "inactive": len(users) - active_count,
                "unverified": len(users) - verified_count,
            }

        # 档案完整度统计
        student_profiles_stmt = select(StudentProfile)
        student_result = await self.db.execute(student_profiles_stmt)
        student_profiles = student_result.scalars().all()

        teacher_profiles_stmt = select(TeacherProfile)
        teacher_result = await self.db.execute(teacher_profiles_stmt)
        teacher_profiles = teacher_result.scalars().all()

        return {
            "user_statistics": user_stats,
            "profile_statistics": {
                "student_profiles": {
                    "total": len(student_profiles),
                    "complete_profiles": sum(
                        1 for p in student_profiles if self._is_student_profile_complete(p)
                    ),
                },
                "teacher_profiles": {
                    "total": len(teacher_profiles),
                    "complete_profiles": sum(
                        1 for p in teacher_profiles if self._is_teacher_profile_complete(p)
                    ),
                },
            },
            "generated_at": datetime.utcnow(),
        }

    # ===== 私有辅助方法 =====

    async def _get_user_by_id(self, user_id: int) -> User | None:
        """根据ID获取用户."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()
        return user

    async def _check_username_exists(
        self, username: str, exclude_user_id: int | None = None
    ) -> User | None:
        """检查用户名是否已存在."""
        stmt = select(User).where(User.username == username)
        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)

        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()
        return user

    async def _check_email_exists(
        self, email: str, exclude_user_id: int | None = None
    ) -> User | None:
        """检查邮箱是否已存在."""
        stmt = select(User).where(User.email == email)
        if exclude_user_id:
            stmt = stmt.where(User.id != exclude_user_id)

        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()
        return user

    async def _validate_id_number(self, id_number: str, exclude_user_id: int | None = None) -> None:
        """验证身份证号."""
        # 格式验证
        if len(id_number) != 18:
            raise ValueError("身份证号必须为18位")

        if not id_number[:17].isdigit() or id_number[-1] not in "0123456789Xx":
            raise ValueError("身份证号格式不正确")

        # 唯一性验证
        stmt = select(StudentProfile).where(StudentProfile.id_number == id_number)
        if exclude_user_id:
            stmt = stmt.where(StudentProfile.user_id != exclude_user_id)

        result = await self.db.execute(stmt)
        existing_profile = result.scalar_one_or_none()
        if existing_profile:
            raise ValueError("身份证号已存在")

    async def _validate_phone(self, phone: str) -> None:
        """验证手机号格式."""
        import re

        if not re.match(r"^1[3-9]\d{9}$", phone):
            raise ValueError("手机号格式不正确")

    async def _format_student_profile(self, profile: StudentProfile) -> dict[str, Any]:
        """格式化学生档案信息."""
        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "real_name": profile.real_name,
            "age": profile.age,
            "gender": profile.gender,
            "id_number": profile.id_number,
            "phone": profile.phone,
            "emergency_contact_name": profile.emergency_contact_name,
            "emergency_contact_phone": profile.emergency_contact_phone,
            "school": profile.school,
            "department": profile.department,
            "major": profile.major,
            "grade": profile.grade,
            "class_name": profile.class_name,
            "current_level": profile.current_level,
            "total_study_time": profile.total_study_time,
            "total_score": profile.total_score,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }

    async def _format_teacher_profile(self, profile: TeacherProfile) -> dict[str, Any]:
        """格式化教师档案信息."""
        return {
            "id": profile.id,
            "user_id": profile.user_id,
            "real_name": profile.real_name,
            "age": profile.age,
            "gender": profile.gender,
            "title": profile.title,
            "subject": profile.subject,
            "introduction": profile.introduction,
            "phone": profile.phone,
            "teacher_certificate": profile.teacher_certificate,
            "qualification_certificates": profile.qualification_certificates,
            "honor_certificates": profile.honor_certificates,
            "total_teaching_hours": profile.total_teaching_hours,
            "student_count": profile.student_count,
            "average_rating": profile.average_rating,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }

    def _is_student_profile_complete(self, profile: StudentProfile) -> bool:
        """检查学生档案是否完整."""
        required_fields = ["real_name", "school", "department", "major", "grade"]
        return all(getattr(profile, field) for field in required_fields)

    def _is_teacher_profile_complete(self, profile: TeacherProfile) -> bool:
        """检查教师档案是否完整."""
        required_fields = ["real_name", "subject", "teacher_certificate"]
        return all(getattr(profile, field) for field in required_fields)
