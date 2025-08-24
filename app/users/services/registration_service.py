"""用户注册服务 - 处理学生和教师注册、审核等业务逻辑."""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.email import EmailService
from app.shared.models.enums import UserType
from app.shared.services.cache_service import CacheService
from app.users.models import (
    RegistrationApplication,
    StudentProfile,
    TeacherProfile,
    User,
)
from app.users.schemas.registration_schemas import (
    ApplicationListFilter,
    StudentRegistrationRequest,
    TeacherRegistrationRequest,
)
from app.users.utils.excel_import_utils import StudentExcelImportUtils
from app.users.utils.jwt_utils import jwt_manager


class RegistrationService:
    """用户注册服务类."""

    def __init__(
        self,
        db_session: AsyncSession,
        cache_service: CacheService | None = None,
        email_service: EmailService | None = None,
    ) -> None:
        """初始化注册服务."""
        self.db = db_session
        self.cache_service = cache_service
        self.email_service = email_service

    # ===== 学生注册 =====

    async def register_student(self, request: StudentRegistrationRequest) -> dict[str, Any]:
        """学生注册流程."""
        # 检查用户名和邮箱是否已存在
        existing_user = await self._check_username_email_exists(request.username, request.email)
        if existing_user:
            raise ValueError(f"用户名或邮箱已存在: {existing_user}")

        # 创建用户基础信息
        user = User(
            username=request.username,
            email=request.email,
            password_hash=jwt_manager.hash_password(request.password),
            user_type=UserType.STUDENT,
            is_active=False,  # 待审核状态
            is_verified=False,
        )

        self.db.add(user)
        await self.db.flush()  # 获取用户ID

        # 准备申请数据
        application_data = {
            "real_name": request.real_name,
            "age": request.age,
            "gender": request.gender,
            "id_number": request.id_number,
            "phone": request.phone,
            "emergency_contact_name": request.emergency_contact_name,
            "emergency_contact_phone": request.emergency_contact_phone,
            "school": request.school,
            "department": request.department,
            "major": request.major,
            "grade": request.grade,
            "class_name": request.class_name,
        }

        # 创建注册申请
        application = RegistrationApplication(
            user_id=user.id,
            application_type=UserType.STUDENT,
            application_data=application_data,
            submitted_documents={},  # 学生注册暂无文件要求
            status="pending",
        )

        self.db.add(application)
        await self.db.commit()

        return {
            "application_id": application.id,
            "user_id": user.id,
            "message": "学生注册申请已提交，请等待管理员审核",
            "estimated_review_time": "1-3个工作日",
            "status_check_url": f"/api/v1/registration/status/{application.id}",
        }

    # ===== 教师注册 =====

    async def register_teacher(self, request: TeacherRegistrationRequest) -> dict[str, Any]:
        """教师注册流程."""
        # 检查用户名和邮箱是否已存在
        existing_user = await self._check_username_email_exists(request.username, request.email)
        if existing_user:
            raise ValueError(f"用户名或邮箱已存在: {existing_user}")

        # 创建用户基础信息
        user = User(
            username=request.username,
            email=request.email,
            password_hash=jwt_manager.hash_password(request.password),
            user_type=UserType.TEACHER,
            is_active=False,  # 待审核状态
            is_verified=False,
        )

        self.db.add(user)
        await self.db.flush()  # 获取用户ID

        # 准备申请数据
        application_data = {
            "real_name": request.real_name,
            "age": request.age,
            "gender": request.gender,
            "title": request.title,
            "subject": request.subject,
            "introduction": request.introduction,
            "phone": request.phone,
        }

        # 准备提交文件信息
        submitted_documents = {
            "teacher_certificate": request.teacher_certificate,
            "qualification_certificates": request.qualification_certificates,
            "honor_certificates": request.honor_certificates,
        }

        # 创建注册申请
        application = RegistrationApplication(
            user_id=user.id,
            application_type=UserType.TEACHER,
            application_data=application_data,
            submitted_documents=submitted_documents,
            status="pending",
        )

        self.db.add(application)
        await self.db.commit()

        return {
            "application_id": application.id,
            "user_id": user.id,
            "message": "教师注册申请已提交，请等待管理员审核",
            "estimated_review_time": "3-5个工作日",
            "status_check_url": f"/api/v1/registration/status/{application.id}",
        }

    # ===== 申请审核 =====

    async def review_application(
        self,
        application_id: int,
        reviewer_id: int,
        action: str,
        review_notes: str | None = None,
    ) -> dict[str, Any]:
        """审核申请."""
        # 获取申请
        application = await self._get_application_by_id(application_id)
        if not application:
            raise ValueError("申请不存在")

        if application.status != "pending":
            raise ValueError("申请已被审核，无法重复审核")

        # 更新申请状态
        application.reviewer_id = reviewer_id
        application.status = "approved" if action == "approve" else "rejected"
        application.review_notes = review_notes
        application.reviewed_at = datetime.utcnow()

        # 如果审核通过，发送激活邮件并创建档案 - 🔥需求20验收标准5
        if action == "approve":
            user = await self._get_user_by_id(application.user_id)
            if user:
                # 发送激活邮件而不是直接激活用户
                if self.cache_service and self.email_service:
                    # 动态导入避免循环依赖
                    from app.users.services.activation_service import ActivationService

                    activation_service = ActivationService(
                        self.db, self.cache_service, self.email_service
                    )
                    await activation_service.send_activation_email(
                        user.id, user.email, user.username
                    )

                # 根据用户类型创建对应档案
                if application.application_type == UserType.STUDENT:
                    await self._create_student_profile(user.id, application.application_data)
                elif application.application_type == UserType.TEACHER:
                    await self._create_teacher_profile(
                        user.id,
                        application.application_data,
                        application.submitted_documents,
                    )

        await self.db.commit()

        return {
            "application_id": application.id,
            "action": action,
            "status": application.status,
            "reviewed_at": application.reviewed_at.isoformat(),
            "message": f"申请已{('通过' if action == 'approve' else '驳回')}",
        }

    async def batch_review_applications(
        self,
        application_ids: list[int],
        reviewer_id: int,
        action: str,
        review_notes: str | None = None,
    ) -> dict[str, Any]:
        """批量审核申请."""
        if len(application_ids) > 20:
            raise ValueError("批量审核最多支持20条申请")

        results = []
        success_count = 0
        failed_count = 0

        for app_id in application_ids:
            try:
                result = await self.review_application(app_id, reviewer_id, action, review_notes)
                results.append({"application_id": app_id, "status": "success", "result": result})
                success_count += 1
            except Exception as e:
                results.append({"application_id": app_id, "status": "failed", "error": str(e)})
                failed_count += 1

        return {
            "total": len(application_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "message": f"批量审核完成：成功{success_count}条，失败{failed_count}条",
        }

    # ===== 状态查询 =====

    async def get_application_status(self, application_id: int) -> dict[str, Any]:
        """获取申请状态."""
        application = await self._get_application_by_id(application_id)
        if not application:
            raise ValueError("申请不存在")

        status_descriptions = {
            "pending": "待审核",
            "approved": "已通过",
            "rejected": "已驳回",
        }

        estimated_review_time = None
        if application.status == "pending":
            # 根据申请类型计算预计审核时间
            days = 3 if application.application_type == UserType.STUDENT else 5
            estimated_time = application.created_at + timedelta(days=days)
            estimated_review_time = f"{estimated_time.strftime('%Y-%m-%d')}"

        return {
            "application_id": application.id,
            "status": application.status,
            "status_description": status_descriptions.get(application.status, "未知状态"),
            "submitted_at": application.created_at,
            "reviewed_at": application.reviewed_at,
            "estimated_review_time": estimated_review_time,
            "review_notes": application.review_notes,
        }

    async def list_applications(self, filters: ApplicationListFilter) -> dict[str, Any]:
        """获取申请列表."""
        stmt = select(RegistrationApplication).options(selectinload(RegistrationApplication.user))

        # 应用过滤条件
        if filters.application_type:
            stmt = stmt.where(RegistrationApplication.application_type == filters.application_type)

        if filters.status:
            stmt = stmt.where(RegistrationApplication.status == filters.status)

        if filters.start_date:
            stmt = stmt.where(RegistrationApplication.created_at >= filters.start_date)

        if filters.end_date:
            stmt = stmt.where(RegistrationApplication.created_at <= filters.end_date)

        # 分页
        offset = (filters.page - 1) * filters.size
        stmt = stmt.offset(offset).limit(filters.size)

        # 按创建时间倒序
        stmt = stmt.order_by(RegistrationApplication.created_at.desc())

        result = await self.db.execute(stmt)
        applications = result.scalars().all()

        # 获取总数
        count_stmt = select(RegistrationApplication)
        if filters.application_type:
            count_stmt = count_stmt.where(
                RegistrationApplication.application_type == filters.application_type
            )
        if filters.status:
            count_stmt = count_stmt.where(RegistrationApplication.status == filters.status)
        if filters.start_date:
            count_stmt = count_stmt.where(RegistrationApplication.created_at >= filters.start_date)
        if filters.end_date:
            count_stmt = count_stmt.where(RegistrationApplication.created_at <= filters.end_date)

        count_result = await self.db.execute(count_stmt)
        total = len(count_result.scalars().all())

        return {
            "total": total,
            "page": filters.page,
            "size": filters.size,
            "items": applications,
        }

    # ===== 私有辅助方法 =====

    async def _check_username_email_exists(self, username: str, email: str) -> str | None:
        """检查用户名和邮箱是否已存在."""
        stmt = select(User).where((User.username == username) | (User.email == email))
        result = await self.db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.username == username:
                return "用户名"
            if existing_user.email == email:
                return "邮箱"

        return None

    async def _get_application_by_id(self, application_id: int) -> RegistrationApplication | None:
        """根据ID获取申请."""
        stmt = select(RegistrationApplication).where(RegistrationApplication.id == application_id)
        result = await self.db.execute(stmt)
        application: RegistrationApplication | None = result.scalar_one_or_none()
        return application

    async def _get_user_by_id(self, user_id: int) -> User | None:
        """根据ID获取用户."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user: User | None = result.scalar_one_or_none()
        return user

    async def _create_student_profile(
        self, user_id: int, application_data: dict[str, Any]
    ) -> StudentProfile:
        """创建学生档案."""
        profile = StudentProfile(
            user_id=user_id,
            real_name=application_data["real_name"],
            age=application_data.get("age"),
            gender=application_data.get("gender"),
            id_number=application_data.get("id_number"),
            phone=application_data.get("phone"),
            emergency_contact_name=application_data.get("emergency_contact_name"),
            emergency_contact_phone=application_data.get("emergency_contact_phone"),
            school=application_data.get("school"),
            department=application_data.get("department"),
            major=application_data.get("major"),
            grade=application_data.get("grade"),
            class_name=application_data.get("class_name"),
        )

        self.db.add(profile)
        return profile

    async def _create_teacher_profile(
        self,
        user_id: int,
        application_data: dict[str, Any],
        submitted_documents: dict[str, Any],
    ) -> TeacherProfile:
        """创建教师档案."""
        profile = TeacherProfile(
            user_id=user_id,
            real_name=application_data["real_name"],
            age=application_data.get("age"),
            gender=application_data.get("gender"),
            title=application_data.get("title"),
            subject=application_data.get("subject"),
            introduction=application_data.get("introduction"),
            phone=application_data.get("phone"),
            teacher_certificate=submitted_documents.get("teacher_certificate"),
            qualification_certificates=submitted_documents.get("qualification_certificates", {}),
            honor_certificates=submitted_documents.get("honor_certificates", {}),
        )

        self.db.add(profile)
        return profile

    # ===== Excel批量导入功能 =====

    async def import_students_from_excel(self, file_path: str, created_by: int) -> dict[str, Any]:
        """Excel批量导入学生信息."""
        # 1. 解析Excel文件
        import_result = await StudentExcelImportUtils.parse_excel_file(file_path)

        if import_result.validation_errors:
            return {
                "success": False,
                "total_records": import_result.total_records,
                "successful_imports": 0,
                "failed_imports": import_result.total_records,
                "validation_errors": import_result.validation_errors,
                "message": "Excel文件解析失败，请检查数据格式",
            }

        # 2. 批量创建学生申请
        created_applications = []
        failed_records = []

        for student_record in import_result.created_students:
            try:
                # 创建StudentRegistrationRequest对象
                student_data = student_record["data"]
                request = StudentRegistrationRequest(**student_data)

                # 调用单个学生注册方法
                result = await self.register_student(request)
                created_applications.append(
                    {
                        "row_number": student_record["row_number"],
                        "application_id": result["application_id"],
                        "user_id": result["user_id"],
                        "username": student_data["username"],
                        "real_name": student_data["real_name"],
                    }
                )

            except Exception as e:
                failed_records.append(
                    {
                        "row_number": student_record["row_number"],
                        "username": student_data.get("username", "未知"),
                        "real_name": student_data.get("real_name", "未知"),
                        "error": str(e),
                    }
                )

        # 3. 返回导入结果
        successful_count = len(created_applications)
        failed_count = len(failed_records) + len(import_result.failed_records)

        return {
            "success": True,
            "total_records": import_result.total_records,
            "successful_imports": successful_count,
            "failed_imports": failed_count,
            "created_applications": created_applications,
            "failed_records": failed_records + import_result.failed_records,
            "validation_errors": import_result.validation_errors,
            "message": f"批量导入完成：成功{successful_count}条，失败{failed_count}条",
            "created_by": created_by,
        }

    @staticmethod
    def get_excel_import_template() -> dict[str, Any]:
        """获取Excel导入模板."""
        return StudentExcelImportUtils.generate_excel_template()

    @staticmethod
    def validate_excel_file(file_path: str) -> dict[str, Any]:
        """验证Excel文件格式."""
        return StudentExcelImportUtils.validate_excel_format(file_path)
