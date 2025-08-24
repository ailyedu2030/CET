"""用户认证服务 - 处理登录、注册、权限验证等核心业务逻辑."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.users.models import LoginAttempt, LoginSession, Permission, Role, User
from app.users.utils.jwt_utils import jwt_manager


class AuthenticationError(Exception):
    """认证异常."""

    def __init__(self, message: str, error_code: str = "AUTH_ERROR") -> None:
        """初始化认证异常."""
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthService:
    """用户认证服务类."""

    def __init__(self, db_session: AsyncSession) -> None:
        """初始化认证服务."""
        self.db = db_session

    async def authenticate_user(
        self,
        username: str,
        password: str,
        user_type: str | None = None,
        ip_address: str = "127.0.0.1",
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """用户认证."""
        # 记录登录尝试
        await self._record_login_attempt(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,  # 先假设失败，成功后更新
        )

        # 检查是否被锁定
        if await self._is_account_locked(username, ip_address):
            raise AuthenticationError("账户已被锁定，请稍后再试", "ACCOUNT_LOCKED")

        # 查找用户
        user = await self._get_user_by_username(username)
        if not user:
            raise AuthenticationError("用户名或密码错误", "INVALID_CREDENTIALS")

        # 验证密码
        if not jwt_manager.verify_password(password, user.password_hash):
            raise AuthenticationError("用户名或密码错误", "INVALID_CREDENTIALS")

        # 检查用户状态
        if not user.is_active:
            raise AuthenticationError("账户已被禁用", "ACCOUNT_DISABLED")

        if not user.is_verified:
            raise AuthenticationError("账户未验证，请联系管理员", "ACCOUNT_UNVERIFIED")

        # 验证用户类型（如果指定）
        if user_type and user.user_type.value != user_type:
            raise AuthenticationError("用户类型不匹配", "INVALID_USER_TYPE")

        # 获取用户角色和权限
        user_roles = await self._get_user_roles(user.id)
        user_permissions = await self._get_user_permissions(user.id)

        # 创建JWT令牌对
        token_pair = jwt_manager.create_token_pair(
            user_id=user.id,
            username=user.username,
            user_type=user.user_type,
            roles=[role.code for role in user_roles],
        )

        # 创建登录会话
        session_token = jwt_manager.generate_session_token()
        await self._create_login_session(
            user_id=user.id,
            session_token=session_token,
            refresh_token=token_pair["refresh_token"],
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # 更新用户登录统计
        await self._update_login_stats(user.id)

        # 更新登录尝试记录为成功
        await self._record_login_attempt(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
        )

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type.value,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            },
            "tokens": token_pair,
            "session_token": session_token,
            "roles": [{"id": role.id, "code": role.code, "name": role.name} for role in user_roles],
            "permissions": [perm.code for perm in user_permissions],
        }

    async def refresh_token(self, refresh_token: str, session_token: str) -> dict[str, str] | None:
        """刷新访问令牌."""
        # 验证会话
        session = await self._get_active_session(session_token)
        if not session or session.refresh_token != refresh_token:
            return None

        # 使用JWT管理器刷新令牌
        new_access_token = jwt_manager.refresh_access_token(refresh_token)
        if not new_access_token:
            return None

        # 更新会话活动时间
        session.last_activity = datetime.utcnow()
        await self.db.commit()

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
        }

    async def logout_user(self, session_token: str) -> bool:
        """用户登出."""
        session = await self._get_active_session(session_token)
        if not session:
            return False

        # 标记会话为非活动状态
        session.is_active = False
        await self.db.commit()

        return True

    async def verify_user_permission(
        self,
        user_id: int,
        required_permission: str,
    ) -> bool:
        """验证用户权限."""
        user_permissions = await self._get_user_permissions(user_id)
        return any(perm.code == required_permission for perm in user_permissions)

    async def verify_user_role(
        self,
        user_id: int,
        required_role: str,
    ) -> bool:
        """验证用户角色."""
        user_roles = await self._get_user_roles(user_id)
        return any(role.code == required_role for role in user_roles)

    async def get_user_by_token(self, token: str) -> User | None:
        """根据令牌获取用户信息."""
        payload = jwt_manager.verify_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        try:
            user_id_int = int(user_id)
        except ValueError:
            return None

        return await self._get_user_by_id(user_id_int)

    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> bool:
        """修改密码."""
        user = await self._get_user_by_id(user_id)
        if not user:
            return False

        # 验证旧密码
        if not jwt_manager.verify_password(old_password, user.password_hash):
            return False

        # 验证新密码强度
        if len(new_password) < settings.PASSWORD_MIN_LENGTH:
            return False

        # 更新密码
        user.password_hash = jwt_manager.hash_password(new_password)
        await self.db.commit()

        # 使所有会话失效（强制重新登录）
        await self._invalidate_all_user_sessions(user_id)

        return True

    async def _get_user_by_username(self, username: str) -> User | None:
        """根据用户名获取用户."""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()
        return user

    async def _get_user_by_id(self, user_id: int) -> User | None:
        """根据用户ID获取用户."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()
        return user

    async def _get_user_roles(self, user_id: int) -> list[Role]:
        """获取用户角色."""
        stmt = select(User).where(User.id == user_id).options(selectinload(User.roles))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        return user.roles if user else []

    async def _get_user_permissions(self, user_id: int) -> list[Permission]:
        """获取用户权限."""
        user_roles = await self._get_user_roles(user_id)
        permissions: list[Permission] = []

        for role in user_roles:
            # 获取角色的权限
            stmt = select(Role).where(Role.id == role.id).options(selectinload(Role.permissions))
            result = await self.db.execute(stmt)
            role_with_perms = result.scalar_one_or_none()
            if role_with_perms:
                permissions.extend(role_with_perms.permissions)

        # 去重并返回
        unique_permissions = []
        seen_codes = set()
        for perm in permissions:
            if perm.code not in seen_codes:
                unique_permissions.append(perm)
                seen_codes.add(perm.code)

        return unique_permissions

    async def _record_login_attempt(
        self,
        username: str,
        ip_address: str,
        success: bool,
        user_agent: str | None = None,
        failure_reason: str | None = None,
    ) -> None:
        """记录登录尝试."""
        attempt = LoginAttempt(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
            attempted_at=datetime.utcnow(),
        )
        self.db.add(attempt)
        await self.db.commit()

    async def _is_account_locked(self, username: str, ip_address: str) -> bool:
        """检查账户是否被锁定."""
        # 检查最近的失败尝试次数
        lockout_start = datetime.utcnow() - timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)

        stmt = select(LoginAttempt).where(
            LoginAttempt.username == username,
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.attempted_at >= lockout_start,
            LoginAttempt.success.is_(False),
        )

        result = await self.db.execute(stmt)
        failed_attempts = result.scalars().all()

        return len(failed_attempts) >= settings.MAX_LOGIN_ATTEMPTS

    async def _create_login_session(
        self,
        user_id: int,
        session_token: str,
        refresh_token: str,
        ip_address: str,
        user_agent: str | None = None,
    ) -> LoginSession:
        """创建登录会话."""
        expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        session = LoginSession(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            login_ip=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            last_activity=datetime.utcnow(),
        )

        self.db.add(session)
        await self.db.commit()
        return session

    async def _get_active_session(self, session_token: str) -> LoginSession | None:
        """获取活跃会话."""
        stmt = select(LoginSession).where(
            LoginSession.session_token == session_token,
            LoginSession.is_active.is_(True),
            LoginSession.expires_at > datetime.utcnow(),
        )
        result = await self.db.execute(stmt)
        session: LoginSession | None = result.scalar_one_or_none()
        return session

    async def _update_login_stats(self, user_id: int) -> None:
        """更新用户登录统计."""
        user = await self._get_user_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            user.login_count += 1
            await self.db.commit()

    async def _invalidate_all_user_sessions(self, user_id: int) -> None:
        """使用户所有会话失效."""
        stmt = select(LoginSession).where(
            LoginSession.user_id == user_id,
            LoginSession.is_active.is_(True),
        )
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()

        for session in sessions:
            session.is_active = False

        await self.db.commit()

    async def get_user_profile(self, user_id: int) -> dict[str, Any]:
        """获取用户档案信息."""
        stmt = (
            select(User)
            .options(selectinload(User.student_profile), selectinload(User.teacher_profile))
            .where(User.id == user_id)
        )

        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        profile_data = None
        if user.user_type.value == "student" and user.student_profile:
            profile_data = {
                "real_name": user.student_profile.real_name,
                "age": user.student_profile.age,
                "gender": user.student_profile.gender,
                "phone": user.student_profile.phone,
                "school": user.student_profile.school,
                "department": user.student_profile.department,
                "major": user.student_profile.major,
                "grade": user.student_profile.grade,
                "class_name": user.student_profile.class_name,
                "current_level": user.student_profile.current_level,
                "total_study_time": user.student_profile.total_study_time,
                "total_score": user.student_profile.total_score,
            }
        elif user.user_type.value == "teacher" and user.teacher_profile:
            profile_data = {
                "real_name": user.teacher_profile.real_name,
                "age": user.teacher_profile.age,
                "gender": user.teacher_profile.gender,
                "title": user.teacher_profile.title,
                "subject": user.teacher_profile.subject,
                "introduction": user.teacher_profile.introduction,
                "phone": user.teacher_profile.phone,
                "total_teaching_hours": user.teacher_profile.total_teaching_hours,
                "student_count": user.teacher_profile.student_count,
                "average_rating": user.teacher_profile.average_rating,
                "qualification_status": self._get_qualification_status(user.teacher_profile),
            }

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "last_login": user.last_login,
            "login_count": user.login_count,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "profile_data": profile_data,
        }

    async def update_user_profile(
        self, user_id: int, update_data: dict[str, Any]
    ) -> dict[str, Any]:
        """更新用户档案信息."""
        stmt = (
            select(User)
            .options(selectinload(User.student_profile), selectinload(User.teacher_profile))
            .where(User.id == user_id)
        )

        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        # 更新基本信息
        if "email" in update_data:
            user.email = update_data["email"]

        # 更新档案数据
        profile_data = update_data.get("profile_data", {})
        if profile_data and user.user_type.value == "teacher" and user.teacher_profile:
            teacher_profile = user.teacher_profile
            for field, value in profile_data.items():
                if hasattr(teacher_profile, field):
                    setattr(teacher_profile, field, value)
        elif profile_data and user.user_type.value == "student" and user.student_profile:
            student_profile = user.student_profile
            for field, value in profile_data.items():
                if hasattr(student_profile, field):
                    setattr(student_profile, field, value)

        await self.db.commit()

        # 返回更新后的档案
        return await self.get_user_profile(user_id)

    async def logout_user_by_id(self, user_id: int) -> None:
        """根据用户ID登出用户."""
        await self._invalidate_all_user_sessions(user_id)

    async def get_session_info(self, user_id: int) -> dict[str, Any]:
        """获取用户会话信息."""
        stmt = (
            select(LoginSession)
            .where(LoginSession.user_id == user_id, LoginSession.is_active.is_(True))
            .order_by(LoginSession.created_at.desc())
        )

        result = await self.db.execute(stmt)
        active_sessions: list[LoginSession] = result.scalars().all()

        # 获取最近的登录尝试
        stmt = (
            select(LoginAttempt)
            .where(LoginAttempt.username == (select(User.username).where(User.id == user_id)))
            .order_by(LoginAttempt.attempted_at.desc())
            .limit(10)
        )

        result = await self.db.execute(stmt)
        recent_attempts: list[LoginAttempt] = result.scalars().all()

        return {
            "user_id": user_id,
            "active_sessions_count": len(active_sessions),
            "active_sessions": [
                {
                    "session_token": session.session_token,
                    "ip_address": session.login_ip,
                    "user_agent": session.user_agent,
                    "created_at": session.created_at,
                    "expires_at": session.expires_at,
                }
                for session in active_sessions[:5]  # 只返回最近5个活跃会话
            ],
            "recent_login_attempts": [
                {
                    "ip_address": attempt.ip_address,
                    "success": attempt.success,
                    "attempted_at": attempt.attempted_at,
                    "user_agent": attempt.user_agent,
                }
                for attempt in recent_attempts
            ],
        }

    def _get_qualification_status(self, teacher_profile: Any) -> str:
        """获取教师资质认证状态."""
        if not teacher_profile:
            return "incomplete"

        required_count = 0
        completed_count = 0

        # 检查基础信息
        basic_fields = ["real_name", "subject"]
        for field in basic_fields:
            required_count += 1
            if getattr(teacher_profile, field, None):
                completed_count += 1

        # 检查资质材料
        cert_fields = [
            "teacher_certificate",
            "qualification_certificates",
            "honor_certificates",
        ]
        for field in cert_fields:
            required_count += 1
            value = getattr(teacher_profile, field, None)
            if value:  # 对于JSON字段，检查是否非空
                completed_count += 1

        completion_rate = completed_count / required_count

        if completion_rate >= 1.0:
            return "complete"
        elif completion_rate >= 0.7:
            return "partial"
        else:
            return "incomplete"
