"""班级管理API端点 - 需求4：班级管理与资源配置."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.courses.schemas.class_schemas import (
    ClassBatchCreate,
    ClassCreate,
    ClassResponse,
    ClassUpdate,
)
from app.courses.services.class_management_service import ClassManagementService
from app.shared.models.enums import UserType
from app.users.models import User
from app.users.utils.auth_decorators import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/class-management", tags=["班级管理"])


@router.post("/classes")
async def create_class(
    class_data: ClassCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClassResponse:
    """创建班级 - 需求4验收标准1."""
    # 权限检查：只有管理员可以创建班级
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建班级",
        )

    try:
        service = ClassManagementService(db)
        class_obj = await service.create_class(class_data, current_user.id)

        logger.info(f"管理员 {current_user.id} 创建班级: {class_obj.name}")

        return ClassResponse.model_validate(class_obj)

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"创建班级失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建班级失败",
        ) from e


@router.put("/classes/{class_id}")
async def update_class(
    class_id: int,
    class_data: ClassUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClassResponse:
    """更新班级 - 需求4验收标准1."""
    # 权限检查：只有管理员可以更新班级
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以更新班级",
        )

    try:
        service = ClassManagementService(db)
        class_obj = await service.update_class(class_id, class_data, current_user.id)

        if not class_obj:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="班级不存在",
            )

        logger.info(f"管理员 {current_user.id} 更新班级: {class_obj.name}")

        return ClassResponse.model_validate(class_obj)

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"更新班级失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新班级失败",
        ) from e


@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """删除班级 - 需求4验收标准1."""
    # 权限检查：只有管理员可以删除班级
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除班级",
        )

    try:
        service = ClassManagementService(db)
        success = await service.delete_class(class_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="班级不存在",
            )

        logger.info(f"管理员 {current_user.id} 删除班级: ID {class_id}")

        return {
            "message": "班级删除成功",
            "class_id": class_id,
        }

    except Exception as e:
        logger.error(f"删除班级失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除班级失败",
        ) from e


@router.post("/classes/from-template")
async def create_class_from_template(
    course_id: int = Query(..., description="课程模板ID"),
    class_name: str = Query(..., description="班级名称"),
    teacher_id: int | None = Query(None, description="教师ID"),
    max_students: int = Query(50, description="最大学生数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ClassResponse:
    """基于课程模板创建班级 - 需求4验收标准2."""
    # 权限检查：只有管理员可以创建班级
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建班级",
        )

    try:
        service = ClassManagementService(db)
        class_obj = await service.create_class_from_course_template(
            course_id=course_id,
            class_name=class_name,
            creator_id=current_user.id,
            teacher_id=teacher_id,
            max_students=max_students,
        )

        logger.info(f"管理员 {current_user.id} 基于课程模板创建班级: {class_name}")

        return ClassResponse.model_validate(class_obj)

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"基于课程模板创建班级失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="基于课程模板创建班级失败",
        ) from e


@router.post("/classes/batch")
async def batch_create_classes(
    batch_data: ClassBatchCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """批量创建班级 - 需求4验收标准2."""
    # 权限检查：只有管理员可以批量创建班级
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以批量创建班级",
        )

    try:
        service = ClassManagementService(db)
        created_classes = await service.batch_create_classes_from_template(
            batch_data, current_user.id
        )

        logger.info(f"管理员 {current_user.id} 批量创建班级: {len(created_classes)} 个")

        return {
            "message": "批量创建班级成功",
            "created_count": len(created_classes),
            "classes": [
                {
                    "id": class_obj.id,
                    "name": class_obj.name,
                    "code": class_obj.code,
                }
                for class_obj in created_classes
            ],
        }

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"批量创建班级失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量创建班级失败",
        ) from e


@router.post("/classes/{class_id}/resources")
async def allocate_class_resources(
    class_id: int,
    resource_allocation: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """分配班级资源 - 需求4验收标准3."""
    # 权限检查：只有管理员可以分配资源
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以分配资源",
        )

    try:
        service = ClassManagementService(db)
        result = await service.allocate_class_resources(
            class_id, resource_allocation, current_user.id
        )

        logger.info(f"管理员 {current_user.id} 分配班级资源: 班级ID {class_id}")

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"分配班级资源失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分配班级资源失败",
        ) from e


@router.put("/classes/{class_id}/resources")
async def update_class_resources(
    class_id: int,
    resource_updates: dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """更新班级资源配置 - 需求4验收标准3."""
    # 权限检查：管理员和教师可以更新资源配置
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以更新资源配置",
        )

    try:
        service = ClassManagementService(db)
        result = await service.update_class_resources(class_id, resource_updates, current_user.id)

        logger.info(f"用户 {current_user.id} 更新班级资源: 班级ID {class_id}")

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"更新班级资源失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新班级资源失败",
        ) from e


@router.get("/classes/{class_id}/resource-history")
async def get_resource_change_history(
    class_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取班级资源变更历史 - 需求4验收标准4."""
    # 权限检查：管理员和教师可以查看资源变更历史
    if current_user.user_type not in [UserType.ADMIN, UserType.TEACHER]:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员和教师可以查看资源变更历史",
        )

    try:
        service = ClassManagementService(db)
        history = await service.get_resource_change_history(class_id)

        logger.info(f"用户 {current_user.id} 查看班级资源变更历史: 班级ID {class_id}")

        return {
            "class_id": class_id,
            "history": history,
            "total_changes": len(history),
        }

    except Exception as e:
        logger.error(f"获取资源变更历史失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取资源变更历史失败",
        ) from e


@router.get("/classes/{class_id}/binding-validation")
async def validate_class_binding_rules(
    class_id: int,
    teacher_id: int | None = Query(None, description="教师ID"),
    course_id: int | None = Query(None, description="课程ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """验证班级绑定规则 - 需求4验收标准5."""
    # 权限检查：只有管理员可以验证绑定规则
    if current_user.user_type != UserType.ADMIN:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以验证绑定规则",
        )

    try:
        service = ClassManagementService(db)
        validation_result = await service.validate_class_binding_rules(
            class_id, teacher_id, course_id
        )

        logger.info(f"管理员 {current_user.id} 验证班级绑定规则: 班级ID {class_id}")

        return validation_result

    except Exception as e:
        logger.error(f"验证绑定规则失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证绑定规则失败",
        ) from e
