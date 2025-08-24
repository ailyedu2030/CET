"""规则管理API端点 - 需求8：班级与课程规则管理."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.courses.schemas.rule_schemas import (
    RuleConfigurationCreate,
    RuleConfigurationResponse,
    RuleConfigurationUpdate,
    RuleTemplateResponse,
    RuleValidationRequest,
    RuleValidationResponse,
    RuleViolation,
)
from app.courses.services.rule_management_service import RuleManagementService
from app.users.models.user_models import User
from app.users.utils.auth_decorators import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rules", tags=["规则管理"])


# ===== 规则配置管理 - 需求8.1 =====


@router.post(
    "/",
    response_model=RuleConfigurationResponse,
    status_code=http_status.HTTP_201_CREATED,
)
async def create_rule_configuration(
    rule_data: RuleConfigurationCreate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RuleConfigurationResponse:
    """创建规则配置 - 需求8验收标准1."""
    try:
        service = RuleManagementService(db)
        rule_config = await service.create_rule_configuration(rule_data, current_user.id)

        logger.info(f"管理员 {current_user.id} 创建规则配置: {rule_data.rule_name}")

        return RuleConfigurationResponse.model_validate(rule_config)

    except ValueError as e:
        logger.warning(f"创建规则配置失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"创建规则配置异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建规则配置失败",
        ) from None


@router.get("/", response_model=list[RuleConfigurationResponse])
async def list_rule_configurations(
    rule_type: str | None = Query(None, description="规则类型筛选"),
    rule_category: str | None = Query(None, description="规则分类筛选"),
    is_enabled: bool | None = Query(None, description="启用状态筛选"),
    scope_type: str | None = Query(None, description="适用范围筛选"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[RuleConfigurationResponse]:
    """获取规则配置列表 - 需求8验收标准1."""
    try:
        service = RuleManagementService(db)
        rule_configs = await service.list_rule_configurations(
            rule_type=rule_type,
            rule_category=rule_category,
            is_enabled=is_enabled,
            scope_type=scope_type,
            offset=skip,
            limit=limit,
        )

        return [RuleConfigurationResponse.model_validate(config) for config in rule_configs]

    except Exception as e:
        logger.error(f"获取规则配置列表异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取规则配置列表失败",
        ) from None


@router.get("/{rule_id}", response_model=RuleConfigurationResponse)
async def get_rule_configuration(
    rule_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RuleConfigurationResponse:
    """获取规则配置详情 - 需求8验收标准1."""
    try:
        service = RuleManagementService(db)
        rule_config = await service.get_rule_configuration(rule_id)

        if not rule_config:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="规则配置不存在",
            )

        return RuleConfigurationResponse.model_validate(rule_config)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取规则配置详情异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取规则配置详情失败",
        ) from None


@router.put("/{rule_id}", response_model=RuleConfigurationResponse)
async def update_rule_configuration(
    rule_id: int,
    rule_data: RuleConfigurationUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RuleConfigurationResponse:
    """更新规则配置 - 需求8验收标准1."""
    try:
        service = RuleManagementService(db)
        rule_config = await service.update_rule_configuration(rule_id, rule_data, current_user.id)

        logger.info(f"管理员 {current_user.id} 更新规则配置: {rule_id}")

        return RuleConfigurationResponse.model_validate(rule_config)

    except ValueError as e:
        logger.warning(f"更新规则配置失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"更新规则配置异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新规则配置失败",
        ) from None


@router.delete("/{rule_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_rule_configuration(
    rule_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """删除规则配置 - 需求8验收标准1."""
    try:
        service = RuleManagementService(db)
        success = await service.delete_rule_configuration(rule_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="规则配置不存在",
            )

        logger.info(f"管理员 {current_user.id} 删除规则配置: {rule_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除规则配置异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除规则配置失败",
        ) from None


# ===== 规则验证与执行 - 需求8.2 =====


@router.post("/validate", response_model=RuleValidationResponse)
async def validate_rule_compliance(
    validation_request: RuleValidationRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> RuleValidationResponse:
    """验证规则合规性 - 需求8验收标准2."""
    try:
        service = RuleManagementService(db)
        result = await service.validate_rule_compliance(
            validation_request.rule_id,
            validation_request.target_type,
            validation_request.target_id,
            validation_request.context,
            current_user.id,
        )

        # 转换为响应模型
        violations = []
        if result.get("violations"):
            for violation in result["violations"]:
                violations.append(
                    RuleViolation(
                        rule=violation.get("rule", "unknown"),
                        message=violation.get("message", ""),
                        severity=violation.get("severity", "medium"),
                        details=violation,
                    )
                )

        return RuleValidationResponse(
            is_compliant=result.get("is_compliant", False),
            rule_name=result.get("rule_name"),
            violations=violations,
            rule_count=len(violations),
            severity=result.get("severity", "none"),
            message=result.get("message", ""),
            suggestions=result.get("suggestions", []),
        )

    except ValueError as e:
        logger.warning(f"规则验证失败: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except Exception as e:
        logger.error(f"规则验证异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="规则验证失败",
        ) from None


@router.get("/templates", response_model=list[RuleTemplateResponse])
async def get_rule_templates(
    template_type: str | None = Query(None, description="模板类型筛选"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> list[RuleTemplateResponse]:
    """获取规则模板列表 - 需求8验收标准4."""
    try:
        # 预定义的规则模板
        templates: list[dict[str, Any]] = [
            {
                "template_name": "班级教师绑定规则",
                "template_type": "class_binding",
                "description": "确保1班级↔1教师的强制绑定关系",
                "default_config": {
                    "one_class_one_teacher": True,
                    "allow_teacher_change": False,
                    "require_approval_for_change": True,
                },
                "required_fields": ["one_class_one_teacher"],
                "optional_fields": [
                    "allow_teacher_change",
                    "require_approval_for_change",
                ],
                "examples": [
                    {
                        "name": "严格绑定",
                        "config": {
                            "one_class_one_teacher": True,
                            "allow_teacher_change": False,
                        },
                    },
                    {
                        "name": "允许变更",
                        "config": {
                            "one_class_one_teacher": True,
                            "allow_teacher_change": True,
                        },
                    },
                ],
            },
            {
                "template_name": "班级课程绑定规则",
                "template_type": "class_binding",
                "description": "确保1班级↔1课程的强制绑定关系",
                "default_config": {
                    "one_class_one_course": True,
                    "allow_course_change": False,
                    "require_approval_for_change": True,
                },
                "required_fields": ["one_class_one_course"],
                "optional_fields": [
                    "allow_course_change",
                    "require_approval_for_change",
                ],
                "examples": [
                    {
                        "name": "严格绑定",
                        "config": {
                            "one_class_one_course": True,
                            "allow_course_change": False,
                        },
                    },
                ],
            },
            {
                "template_name": "教室排课规则",
                "template_type": "classroom_scheduling",
                "description": "单时段单教室仅允许1班级使用",
                "default_config": {
                    "single_classroom_single_timeslot": True,
                    "classroom_capacity_check": True,
                    "max_capacity_ratio": 1.0,
                    "allow_overtime": False,
                },
                "required_fields": ["single_classroom_single_timeslot"],
                "optional_fields": [
                    "classroom_capacity_check",
                    "max_capacity_ratio",
                    "allow_overtime",
                ],
                "examples": [
                    {
                        "name": "标准排课",
                        "config": {
                            "single_classroom_single_timeslot": True,
                            "classroom_capacity_check": True,
                            "max_capacity_ratio": 1.0,
                        },
                    },
                ],
            },
            {
                "template_name": "教师工作量规则",
                "template_type": "teacher_workload",
                "description": "限制教师最大班级数和学生数",
                "default_config": {
                    "max_classes_per_teacher": 5,
                    "max_students_per_teacher": 250,
                    "check_workload_balance": True,
                },
                "required_fields": [
                    "max_classes_per_teacher",
                    "max_students_per_teacher",
                ],
                "optional_fields": ["check_workload_balance"],
                "examples": [
                    {
                        "name": "标准工作量",
                        "config": {
                            "max_classes_per_teacher": 5,
                            "max_students_per_teacher": 250,
                        },
                    },
                    {
                        "name": "高工作量",
                        "config": {
                            "max_classes_per_teacher": 8,
                            "max_students_per_teacher": 400,
                        },
                    },
                ],
            },
        ]

        # 根据类型筛选
        if template_type:
            templates = [t for t in templates if t["template_type"] == template_type]

        return [
            RuleTemplateResponse(
                template_name=template["template_name"],
                template_type=template["template_type"],
                description=template["description"],
                default_config=template["default_config"],
                required_fields=template["required_fields"],
                optional_fields=template["optional_fields"],
                examples=template["examples"],
            )
            for template in templates
        ]

    except Exception as e:
        logger.error(f"获取规则模板列表异常: {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取规则模板列表失败",
        ) from None
