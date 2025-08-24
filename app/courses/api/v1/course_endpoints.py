"""课程管理API端点 - 实现课程全生命周期管理接口."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.courses.schemas.course_schemas import (
    CourseCreate,
    CourseListResponse,
    CourseResponse,
    CourseStatusUpdate,
    CourseTemplateCreate,
    CourseTemplateListResponse,
    CourseTemplateResponse,
    CourseTemplateUpdate,
    CourseUpdate,
    CourseVersionResponse,
)
from app.courses.services.course_service import CoursePermissionService, CourseService
from app.courses.services.template_service import CourseTemplateService
from app.courses.utils.version_utils import VersionUtils
from app.shared.models.enums import CourseStatus
from app.users.utils.auth_decorators import AuthRequired

router = APIRouter()


# 课程管理端点
@router.post("/courses/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    course_data: CourseCreate,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseResponse:
    """创建课程."""
    course_service = CourseService(db)

    try:
        course = await course_service.create_course(course_data, current_user["id"])
        return CourseResponse.model_validate(course)  # type: ignore[no-any-return]  # type: ignore[return-value]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建课程失败: {str(e)}",
        ) from e


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseResponse:
    """获取课程详情."""
    course_service = CourseService(db)
    permission_service = CoursePermissionService(db)

    # 检查权限
    has_access = await permission_service.check_course_access(course_id, current_user["id"], "read")
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此课程",
        )

    course = await course_service.get_course_by_id(course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在",
        )

    return CourseResponse.model_validate(course)  # type: ignore[no-any-return]


@router.get("/courses/", response_model=list[CourseListResponse])
async def get_courses(
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    status: CourseStatus | None = Query(None, description="课程状态筛选"),
    creator_id: int | None = Query(None, description="创建者ID筛选"),
) -> list[CourseListResponse]:
    """获取课程列表."""
    permission_service = CoursePermissionService(db)

    # 获取用户可访问的课程
    accessible_courses = await permission_service.get_accessible_courses(
        current_user["id"], current_user.get("role", "student")
    )

    # 应用筛选条件
    filtered_courses = []
    for course in accessible_courses[skip : skip + limit]:
        if status and course.status != status:
            continue
        if creator_id and course.created_by != creator_id:
            continue
        filtered_courses.append(course)

    return [CourseListResponse.model_validate(course) for course in filtered_courses]


@router.put("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseResponse:
    """更新课程."""
    course_service = CourseService(db)
    permission_service = CoursePermissionService(db)

    # 检查权限
    has_access = await permission_service.check_course_access(
        course_id, current_user["id"], "update"
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此课程",
        )

    course = await course_service.update_course(course_id, course_data, current_user["id"])
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在",
        )

    return CourseResponse.model_validate(course)  # type: ignore[no-any-return]


@router.patch("/courses/{course_id}/status", response_model=CourseResponse)
async def update_course_status(
    course_id: int,
    status_data: CourseStatusUpdate,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseResponse:
    """更新课程状态."""
    course_service = CourseService(db)
    permission_service = CoursePermissionService(db)

    # 检查权限
    has_access = await permission_service.check_course_access(
        course_id, current_user["id"], "update"
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此课程",
        )

    try:
        course = await course_service.update_course_status(
            course_id, status_data, current_user["id"]
        )
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="课程不存在",
            )

        return CourseResponse.model_validate(course)  # type: ignore[no-any-return]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """删除课程."""
    course_service = CourseService(db)
    permission_service = CoursePermissionService(db)

    # 检查权限
    has_access = await permission_service.check_course_access(
        course_id, current_user["id"], "delete"
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除此课程",
        )

    success = await course_service.delete_course(course_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程不存在",
        )


@router.post("/courses/{course_id}/duplicate", response_model=CourseResponse)
async def duplicate_course(
    course_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    new_name: str = Query(..., description="新课程名称"),
) -> CourseResponse:
    """复制课程."""
    course_service = CourseService(db)
    permission_service = CoursePermissionService(db)

    # 检查权限
    has_access = await permission_service.check_course_access(course_id, current_user["id"], "read")
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此课程",
        )

    course = await course_service.duplicate_course(course_id, new_name, current_user["id"])
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="源课程不存在",
        )

    return CourseResponse.model_validate(course)  # type: ignore[no-any-return]


# 版本管理端点
@router.get("/courses/{course_id}/versions", response_model=list[CourseVersionResponse])
async def get_course_versions(
    course_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CourseVersionResponse]:
    """获取课程版本历史."""
    course_service = CourseService(db)
    permission_service = CoursePermissionService(db)

    # 检查权限
    has_access = await permission_service.check_course_access(course_id, current_user["id"], "read")
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此课程",
        )

    versions = await course_service.get_course_versions(course_id)
    return [CourseVersionResponse.model_validate(version) for version in versions]


@router.post("/courses/{course_id}/versions/{version_id}/rollback", response_model=CourseResponse)
async def rollback_course_version(
    course_id: int,
    version_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseResponse:
    """回滚到指定版本."""
    course_service = CourseService(db)
    permission_service = CoursePermissionService(db)

    # 检查权限
    has_access = await permission_service.check_course_access(
        course_id, current_user["id"], "update"
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此课程",
        )

    course = await course_service.rollback_course_version(course_id, version_id, current_user["id"])
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="课程或版本不存在",
        )

    return CourseResponse.model_validate(course)  # type: ignore[no-any-return]


@router.get("/courses/{course_id}/versions/compare")
async def compare_course_versions(
    course_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    version1_id: int = Query(..., description="版本1 ID"),
    version2_id: int = Query(..., description="版本2 ID"),
) -> dict[str, Any]:
    """比较课程版本."""
    course_service = CourseService(db)
    permission_service = CoursePermissionService(db)

    # 检查权限
    has_access = await permission_service.check_course_access(course_id, current_user["id"], "read")
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此课程",
        )

    versions = await course_service.get_course_versions(course_id)
    version1_data = None
    version2_data = None

    for version in versions:
        if version.id == version1_id:
            version1_data = version.snapshot_data
        elif version.id == version2_id:
            version2_data = version.snapshot_data

    if not version1_data or not version2_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="指定的版本不存在",
        )

    diff_result = VersionUtils.compare_versions(version1_data, version2_data)
    change_summary = VersionUtils.generate_change_summary(diff_result)
    key_changes = VersionUtils.extract_key_changes(diff_result)

    return {
        "version1_id": version1_id,
        "version2_id": version2_id,
        "diff_result": diff_result,
        "change_summary": change_summary,
        "key_changes": key_changes,
    }


# 模板管理端点
@router.post(
    "/templates/",
    response_model=CourseTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course_template(
    template_data: CourseTemplateCreate,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseTemplateResponse:
    """创建课程模板."""
    template_service = CourseTemplateService(db)

    template = await template_service.create_template(template_data, current_user["id"])
    return CourseTemplateResponse.model_validate(template)  # type: ignore[no-any-return]


@router.get("/templates/", response_model=list[CourseTemplateListResponse])
async def get_course_templates(
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    category: str | None = Query(None, description="模板分类筛选"),
    is_public: bool | None = Query(None, description="是否公开筛选"),
    my_templates: bool = Query(False, description="只显示我的模板"),
) -> list[CourseTemplateListResponse]:
    """获取课程模板列表."""
    template_service = CourseTemplateService(db)

    creator_id = current_user["id"] if my_templates else None
    templates = await template_service.get_templates(
        skip=skip,
        limit=limit,
        category=category,
        is_public=is_public,
        creator_id=creator_id,
    )

    return [CourseTemplateListResponse.model_validate(template) for template in templates]


@router.get("/templates/public", response_model=list[CourseTemplateListResponse])
async def get_public_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    category: str | None = Query(None, description="模板分类筛选"),
) -> list[CourseTemplateListResponse]:
    """获取公开模板列表."""
    template_service = CourseTemplateService(db)

    templates = await template_service.get_public_templates(
        skip=skip, limit=limit, category=category
    )

    return [CourseTemplateListResponse.model_validate(template) for template in templates]


@router.get("/templates/popular", response_model=list[CourseTemplateListResponse])
async def get_popular_templates(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50, description="返回记录数"),
    category: str | None = Query(None, description="模板分类筛选"),
) -> list[CourseTemplateListResponse]:
    """获取热门模板列表."""
    template_service = CourseTemplateService(db)

    templates = await template_service.get_popular_templates(limit=limit, category=category)

    return [CourseTemplateListResponse.model_validate(template) for template in templates]


@router.get("/templates/{template_id}", response_model=CourseTemplateResponse)
async def get_course_template(
    template_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseTemplateResponse:
    """获取课程模板详情."""
    template_service = CourseTemplateService(db)

    template = await template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    # 检查访问权限：公开模板或自己创建的模板
    if not template.is_public and template.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限访问此模板",
        )

    return CourseTemplateResponse.model_validate(template)  # type: ignore[no-any-return]


@router.put("/templates/{template_id}", response_model=CourseTemplateResponse)
async def update_course_template(
    template_id: int,
    template_data: CourseTemplateUpdate,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CourseTemplateResponse:
    """更新课程模板."""
    template_service = CourseTemplateService(db)

    template = await template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    # 检查权限：只有创建者可以修改
    if template.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此模板",
        )

    updated_template = await template_service.update_template(template_id, template_data)
    return CourseTemplateResponse.model_validate(updated_template)  # type: ignore[no-any-return]


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course_template(
    template_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """删除课程模板."""
    template_service = CourseTemplateService(db)

    template = await template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    # 检查权限：只有创建者可以删除
    if template.created_by != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除此模板",
        )

    success = await template_service.delete_template(template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )


@router.post("/templates/{template_id}/use", response_model=CourseResponse)
async def use_course_template(
    template_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    course_name: str = Query(..., description="新课程名称"),
) -> CourseResponse:
    """使用模板创建课程."""
    template_service = CourseTemplateService(db)
    course_service = CourseService(db)

    # 使用模板生成课程数据
    course_data_dict = await template_service.use_template(
        template_id, course_name, current_user["id"]
    )
    if not course_data_dict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在",
        )

    # 创建CourseCreate对象
    course_create = CourseCreate(**course_data_dict)

    # 创建课程
    course = await course_service.create_course(course_create, current_user["id"])
    return CourseResponse.model_validate(course)  # type: ignore[no-any-return]


@router.post("/templates/{template_id}/clone", response_model=CourseTemplateResponse)
async def clone_course_template(
    template_id: int,
    current_user: Annotated[dict[str, Any], AuthRequired()],
    db: Annotated[AsyncSession, Depends(get_db)],
    new_name: str = Query(..., description="新模板名称"),
) -> CourseTemplateResponse:
    """克隆课程模板."""
    template_service = CourseTemplateService(db)

    cloned_template = await template_service.clone_template(
        template_id, new_name, current_user["id"]
    )
    if not cloned_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="源模板不存在",
        )

    return CourseTemplateResponse.model_validate(cloned_template)  # type: ignore[no-any-return]


@router.get("/templates/categories/", response_model=list[str])
async def get_template_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[str]:
    """获取模板分类列表."""
    template_service = CourseTemplateService(db)

    categories = await template_service.get_template_categories()
    return categories
