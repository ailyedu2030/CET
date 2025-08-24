"""用户注册相关的API端点 - 教师资质管理重点功能."""

import os
import tempfile
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.models.enums import UserType
from app.users.models import User
from app.users.schemas.registration_schemas import (
    ApplicationListFilter,
    ApplicationListResponse,
    ApplicationReviewRequest,
    BatchReviewRequest,
    RegistrationApplicationDetail,
    RegistrationStatusResponse,
    RegistrationSuccessResponse,
    StudentRegistrationRequest,
    TeacherRegistrationRequest,
)
from app.users.services.registration_service import RegistrationService
from app.users.utils.auth_decorators import get_current_active_user

router = APIRouter(prefix="/registration", tags=["用户注册"])


# ===== 学生注册相关端点 =====


@router.post(
    "/student",
    response_model=RegistrationSuccessResponse,
    summary="学生注册申请",
    description="提交学生注册申请，包含11项必要信息",
)
async def register_student(
    request: StudentRegistrationRequest,
    db: AsyncSession = Depends(get_db),
) -> RegistrationSuccessResponse:
    """学生注册申请端点."""
    try:
        service = RegistrationService(db)
        result = await service.register_student(request)
        return RegistrationSuccessResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册申请提交失败，请稍后重试",
        ) from e


# ===== 教师注册相关端点（重点功能）=====


@router.post(
    "/teacher",
    response_model=RegistrationSuccessResponse,
    summary="教师注册申请",
    description="提交教师注册申请，包含7项基础信息和3类资质材料",
)
async def register_teacher(
    request: TeacherRegistrationRequest,
    db: AsyncSession = Depends(get_db),
) -> RegistrationSuccessResponse:
    """教师注册申请端点."""
    try:
        service = RegistrationService(db)
        result = await service.register_teacher(request)
        return RegistrationSuccessResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="教师注册申请提交失败，请稍后重试",
        ) from e


@router.post(
    "/teacher/upload-certificate",
    summary="教师资质材料上传",
    description="上传教师证、职业资格证书、荣誉证书等资质材料",
)
async def upload_teacher_certificate(
    file: UploadFile = File(..., description="资质文件"),
    certificate_type: str = Form(..., description="证书类型: teacher_cert/qualification/honor"),
    description: str = Form(None, description="证书描述"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """教师资质材料上传端点."""

    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="文件类型不支持，请上传JPG、PNG或PDF格式文件",
        )

    # 验证文件大小（最大5MB）
    max_size = 5 * 1024 * 1024  # 5MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="文件大小不能超过5MB"
        )

    # 验证证书类型（需求1：3类资质材料）
    valid_types = [
        "teacher_certificate",
        "qualification_certificates",
        "honor_certificates",
    ]
    if certificate_type not in valid_types:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"证书类型无效，支持的类型：{', '.join(valid_types)}",
        )

    try:
        # 使用文件存储服务上传文件
        from app.shared.services.file_storage_service import FileStorageService

        file_storage = FileStorageService(db)

        # 重置文件指针
        await file.seek(0)

        # 上传文件到对应的证书类型存储桶
        upload_result = await file_storage.upload_file(
            file=file,
            bucket_type="certificates",
            access_level="private",
            metadata={
                "certificate_type": certificate_type,
                "description": description,
                "original_filename": file.filename,
            },
        )

        return {
            "message": "资质材料上传成功",
            "file_id": upload_result.file_id,
            "file_url": upload_result.download_url,
            "file_name": file.filename,
            "file_size": upload_result.file_size,
            "certificate_type": certificate_type,
            "description": description,
            "upload_time": upload_result.upload_time.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="文件上传失败，请稍后重试",
        ) from e


# ===== 申请状态查询 =====


@router.get(
    "/status/{application_id}",
    response_model=RegistrationStatusResponse,
    summary="查询申请状态",
    description="根据申请ID查询注册申请的审核状态",
)
async def get_application_status(
    application_id: int,
    db: AsyncSession = Depends(get_db),
) -> RegistrationStatusResponse:
    """查询申请状态端点."""
    try:
        service = RegistrationService(db)
        result = await service.get_application_status(application_id)
        return RegistrationStatusResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="状态查询失败，请稍后重试",
        ) from e


# ===== 管理员审核相关端点 =====


@router.get(
    "/applications",
    response_model=ApplicationListResponse,
    summary="获取申请列表",
    description="管理员查看所有待审核和已审核的注册申请",
    dependencies=[Depends(get_current_active_user)],
)
async def list_applications(
    application_type: str | None = Query(None, description="申请类型: student/teacher"),
    status: str | None = Query(None, description="申请状态: pending/approved/rejected"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
) -> ApplicationListResponse:
    """获取申请列表端点."""
    try:
        # 转换application_type从字符串到UserType枚举
        app_type_enum = None
        if application_type:
            try:
                app_type_enum = UserType(application_type)
            except ValueError as e:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的申请类型: {application_type}",
                ) from e

        filters = ApplicationListFilter(
            application_type=app_type_enum,
            status=status,
            start_date=None,  # 可以后续添加为参数
            end_date=None,  # 可以后续添加为参数
            page=page,
            size=size,
        )

        service = RegistrationService(db)
        result = await service.list_applications(filters)
        return ApplicationListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取申请列表失败",
        ) from e


@router.get(
    "/applications/{application_id}",
    response_model=RegistrationApplicationDetail,
    summary="获取申请详情",
    description="管理员查看特定注册申请的详细信息",
    dependencies=[Depends(get_current_active_user)],
)
async def get_application_detail(
    application_id: int,
    db: AsyncSession = Depends(get_db),
) -> RegistrationApplicationDetail:
    """获取申请详情端点."""
    try:
        service = RegistrationService(db)
        application = await service._get_application_by_id(application_id)

        if not application:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="申请不存在")

        # 获取申请人信息
        user = await service._get_user_by_id(application.user_id)

        return RegistrationApplicationDetail(
            id=application.id,
            user_id=application.user_id,
            application_type=application.application_type,
            application_data=application.application_data,
            submitted_documents=application.submitted_documents,
            status=application.status,
            submitted_at=application.created_at,
            reviewed_at=application.reviewed_at,
            reviewer_id=application.reviewer_id,
            review_notes=application.review_notes,
            username=user.username if user else "未知用户",
            email=user.email if user else "未知邮箱",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取申请详情失败",
        ) from e


@router.post(
    "/applications/{application_id}/review",
    summary="审核申请",
    description="管理员审核注册申请（通过或驳回）",
    dependencies=[Depends(get_current_active_user)],
)
async def review_application(
    application_id: int,
    request: ApplicationReviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """审核申请端点."""
    try:
        service = RegistrationService(db)
        result = await service.review_application(
            application_id=application_id,
            reviewer_id=current_user.id,
            action=request.action,
            review_notes=request.review_notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="申请审核失败",
        ) from e


@router.post(
    "/applications/batch-review",
    summary="批量审核申请",
    description="管理员批量审核多个注册申请",
    dependencies=[Depends(get_current_active_user)],
)
async def batch_review_applications(
    request: BatchReviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """批量审核申请端点."""
    try:
        service = RegistrationService(db)
        result = await service.batch_review_applications(
            application_ids=request.application_ids,
            reviewer_id=current_user.id,
            action=request.action,
            review_notes=request.review_notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量审核失败",
        ) from e


# ===== 资质认证状态查询 =====


@router.get(
    "/teacher/qualification-status/{user_id}",
    summary="查询教师资质认证状态",
    description="查询教师的资质认证状态和材料完整性",
    dependencies=[Depends(get_current_active_user)],
)
async def get_teacher_qualification_status(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """查询教师资质认证状态."""

    # 权限检查：教师只能查询自己的状态，管理员可以查询任何人的状态
    if current_user.user_type.value != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="无权限查询其他教师的资质状态",
        )

    try:
        service = RegistrationService(db)
        user = await service._get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="用户不存在")

        if user.user_type.value != "teacher":
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST, detail="该用户不是教师"
            )

        # 获取教师档案
        teacher_profile = user.teacher_profile

        if not teacher_profile:
            return {
                "user_id": user_id,
                "qualification_status": "incomplete",
                "message": "教师档案未创建",
                "missing_items": ["基础信息", "资质材料"],
                "completion_rate": 0,
            }

        # 检查资质完整性
        missing_items = []
        completed_items = []

        # 基础信息检查
        required_fields = ["real_name", "subject"]
        for field in required_fields:
            if getattr(teacher_profile, field, None):
                completed_items.append(field)
            else:
                missing_items.append(field)

        # 资质材料检查
        cert_status = {
            "teacher_certificate": bool(teacher_profile.teacher_certificate),
            "qualification_certificates": bool(teacher_profile.qualification_certificates),
            "honor_certificates": bool(teacher_profile.honor_certificates),
        }

        for cert_type, has_cert in cert_status.items():
            if has_cert:
                completed_items.append(cert_type)
            else:
                missing_items.append(cert_type)

        # 计算完成率
        total_items = len(required_fields) + len(cert_status)
        completion_rate = len(completed_items) / total_items * 100

        # 确定资质状态
        if completion_rate >= 100:
            qualification_status = "complete"
            message = "资质认证完整"
        elif completion_rate >= 70:
            qualification_status = "partial"
            message = "资质认证基本完整，建议补充缺失材料"
        else:
            qualification_status = "incomplete"
            message = "资质认证不完整，请补充必要材料"

        return {
            "user_id": user_id,
            "qualification_status": qualification_status,
            "message": message,
            "missing_items": missing_items,
            "completed_items": completed_items,
            "completion_rate": round(completion_rate, 1),
            "certificate_status": cert_status,
            "is_verified": user.is_verified,
            "profile_created_at": (
                teacher_profile.created_at.isoformat() if teacher_profile.created_at else None
            ),
            "last_updated": (
                teacher_profile.updated_at.isoformat() if teacher_profile.updated_at else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查询资质状态失败",
        ) from e


# ===== Excel批量导入相关端点 =====


@router.post(
    "/students/import-excel",
    summary="Excel批量导入学生信息",
    description="管理员通过Excel文件批量导入学生注册信息",
    dependencies=[Depends(get_current_active_user)],
)
async def import_students_from_excel(
    file: UploadFile = File(..., description="Excel文件"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Excel批量导入学生信息端点."""
    # 权限检查：只有管理员可以批量导入
    if current_user.user_type.value != "admin":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以执行批量导入操作",
        )

    # 验证文件类型
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="文件格式不正确，请上传Excel文件(.xlsx或.xls)",
        )

    # 验证文件大小（最大10MB）
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail="文件大小不能超过10MB"
        )

    try:
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # 先验证文件格式
            service = RegistrationService(db)
            validation_result = service.validate_excel_file(temp_file_path)

            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": "Excel文件格式验证失败",
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"],
                    "file_info": validation_result.get("file_info", {}),
                }

            # 执行导入
            result = await service.import_students_from_excel(temp_file_path, current_user.id)

            return result

        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量导入失败: {str(e)}",
        ) from e


@router.get(
    "/students/import-template",
    summary="获取Excel导入模板",
    description="下载学生信息批量导入的Excel模板",
    dependencies=[Depends(get_current_active_user)],
)
async def get_excel_import_template(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """获取Excel导入模板端点."""
    # 权限检查：只有管理员可以获取模板
    if current_user.user_type.value != "admin":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以获取导入模板",
        )

    try:
        template_data = RegistrationService.get_excel_import_template()
        return {
            "success": True,
            "template": template_data,
            "message": "Excel导入模板获取成功",
        }
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取导入模板失败",
        ) from e


@router.post(
    "/students/validate-excel",
    summary="验证Excel文件格式",
    description="上传前验证Excel文件格式是否正确",
    dependencies=[Depends(get_current_active_user)],
)
async def validate_excel_file(
    file: UploadFile = File(..., description="Excel文件"),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """验证Excel文件格式端点."""
    # 权限检查：只有管理员可以验证文件
    if current_user.user_type.value != "admin":
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以验证Excel文件",
        )

    # 验证文件类型
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="文件格式不正确，请上传Excel文件(.xlsx或.xls)",
        )

    try:
        # 读取文件内容
        content = await file.read()

        # 使用上下文管理器确保临时文件安全清理
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=True) as temp_file:
            temp_file.write(content)
            temp_file.flush()  # 确保内容写入磁盘

            # 验证文件格式
            validation_result = RegistrationService.validate_excel_file(temp_file.name)
            return {
                "success": True,
                "validation_result": validation_result,
                "message": "文件格式验证完成",
            }
            # 临时文件会在with块结束时自动删除

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件验证失败: {str(e)}",
        ) from e
