"""
课程资源库管理API端点 - 需求11专门实现
符合设计文档技术要求：零缺陷交付、统一异常处理、完整日志记录
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import PermissionDeniedError, ResourceNotFoundError, ValidationError
from app.resources.schemas.course_resource_schemas import (
    ImportResultResponse,
    KnowledgeLibraryCreate,
    KnowledgeLibraryResponse,
    MaterialCreate,
    MaterialLibraryResponse,
    MaterialResponse,
    SyllabusCreate,
    SyllabusResponse,
    VocabularyLibraryCreate,
    VocabularyLibraryResponse,
)
from app.resources.services.course_resource_service import CourseResourceService
from app.users.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/api/v1/course-resources", tags=["课程资源库管理"])

# =================== 词汇库管理 ===================


@router.get(
    "/courses/{course_id}/vocabulary-libraries",
    response_model=list[VocabularyLibraryResponse],
)
async def get_vocabulary_libraries(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[VocabularyLibraryResponse]:
    """
    获取课程词汇库列表 - 需求11验收标准1
    1课程1库管理规则，支持CEFR标准分级
    """
    try:
        logger.info(
            f"获取课程{course_id}的词汇库列表",
            extra={
                "user_id": current_user.id,
                "course_id": course_id,
                "action": "get_vocabulary_libraries",
            },
        )

        service = CourseResourceService(db)
        libraries = await service.get_vocabulary_libraries(course_id, current_user.id)

        logger.info(
            f"成功获取{len(libraries)}个词汇库",
            extra={"course_id": course_id, "library_count": len(libraries)},
        )

        return libraries

    except PermissionDeniedError as e:
        logger.warning(
            f"权限不足: {e.message}",
            extra={"user_id": current_user.id, "course_id": course_id},
        )
        raise HTTPException(status_code=403, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"获取词汇库列表失败: {str(e)}",
            extra={"user_id": current_user.id, "course_id": course_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="获取词汇库列表失败") from e


@router.post(
    "/courses/{course_id}/vocabulary-libraries",
    response_model=VocabularyLibraryResponse,
)
async def create_vocabulary_library(
    course_id: int,
    library_data: VocabularyLibraryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VocabularyLibraryResponse:
    """
    创建词汇库 - 需求11验收标准1
    支持三级权限设置：私有/班级/公开
    """
    try:
        logger.info(
            f"创建词汇库: {library_data.name}",
            extra={
                "user_id": current_user.id,
                "course_id": course_id,
                "library_name": library_data.name,
                "permission": library_data.permission,
            },
        )

        service = CourseResourceService(db)
        library = await service.create_vocabulary_library(
            course_id, library_data, current_user.id
        )

        logger.info(
            f"词汇库创建成功: {library.name}",
            extra={"library_id": library.id, "course_id": course_id},
        )

        return library

    except ValidationError as e:
        logger.warning(
            f"数据验证失败: {e.message}",
            extra={"user_id": current_user.id, "validation_errors": e.details},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"创建词汇库失败: {str(e)}",
            extra={"user_id": current_user.id, "course_id": course_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="创建词汇库失败") from e


@router.post(
    "/vocabulary-libraries/{library_id}/import", response_model=ImportResultResponse
)
async def import_vocabulary(
    library_id: int,
    file: UploadFile = File(...),
    import_mode: str = Form(default="append"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImportResultResponse:
    """
    批量导入词汇 - 需求11验收标准6
    支持PDF/Excel导入，完整的错误处理和结果反馈
    """
    try:
        # 验证文件类型
        allowed_types = [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "application/pdf",
            "text/csv",
        ]
        if file.content_type not in allowed_types:
            raise ValidationError(
                message="不支持的文件类型",
                error_code="INVALID_FILE_TYPE",
                details={"supported_types": ["Excel", "PDF", "CSV"]},
            )

        logger.info(
            f"开始导入词汇文件: {file.filename}",
            extra={
                "user_id": current_user.id,
                "library_id": library_id,
                "file_name": file.filename,
                "file_type": file.content_type,
                "import_mode": import_mode,
            },
        )

        service = CourseResourceService(db)
        result = await service.import_vocabulary(
            library_id, file, import_mode, current_user.id
        )

        logger.info(
            f"词汇导入完成: 成功{result.success}条，失败{result.failed}条",
            extra={
                "library_id": library_id,
                "success_count": result.success,
                "failed_count": result.failed,
                "total_count": result.total,
            },
        )

        return result

    except ValidationError as e:
        logger.warning(
            f"导入验证失败: {e.message}",
            extra={
                "user_id": current_user.id,
                "library_id": library_id,
                "file_name": file.filename,
            },
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"词汇导入失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "library_id": library_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="词汇导入失败") from e


# =================== 知识点库管理 ===================


@router.get(
    "/courses/{course_id}/knowledge-libraries",
    response_model=list[KnowledgeLibraryResponse],
)
async def get_knowledge_libraries(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeLibraryResponse]:
    """
    获取课程知识点库列表 - 需求11验收标准2
    1课程1库管理规则，支持布鲁姆分类法标注
    """
    try:
        logger.info(
            f"获取课程{course_id}的知识点库列表",
            extra={
                "user_id": current_user.id,
                "course_id": course_id,
                "action": "get_knowledge_libraries",
            },
        )

        service = CourseResourceService(db)
        libraries = await service.get_knowledge_libraries(course_id, current_user.id)

        logger.info(
            f"成功获取{len(libraries)}个知识点库",
            extra={"course_id": course_id, "library_count": len(libraries)},
        )

        return libraries

    except PermissionDeniedError as e:
        logger.warning(
            f"权限不足: {e.message}",
            extra={"user_id": current_user.id, "course_id": course_id},
        )
        raise HTTPException(status_code=403, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"获取知识点库列表失败: {str(e)}",
            extra={"user_id": current_user.id, "course_id": course_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="获取知识点库列表失败") from e


@router.post(
    "/courses/{course_id}/knowledge-libraries", response_model=KnowledgeLibraryResponse
)
async def create_knowledge_library(
    course_id: int,
    library_data: KnowledgeLibraryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeLibraryResponse:
    """
    创建知识点库 - 需求11验收标准2
    支持跨课程共享、认知层次标注
    """
    try:
        logger.info(
            f"创建知识点库: {library_data.name}",
            extra={
                "user_id": current_user.id,
                "course_id": course_id,
                "library_name": library_data.name,
                "permission": library_data.permission,
            },
        )

        service = CourseResourceService(db)
        library = await service.create_knowledge_library(
            course_id, library_data, current_user.id
        )

        logger.info(
            f"知识点库创建成功: {library.name}",
            extra={"library_id": library.id, "course_id": course_id},
        )

        return library

    except ValidationError as e:
        logger.warning(
            f"数据验证失败: {e.message}",
            extra={"user_id": current_user.id, "validation_errors": e.details},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"创建知识点库失败: {str(e)}",
            extra={"user_id": current_user.id, "course_id": course_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="创建知识点库失败") from e


@router.post(
    "/knowledge-libraries/{library_id}/import", response_model=ImportResultResponse
)
async def import_knowledge_points(
    library_id: int,
    file: UploadFile = File(...),
    import_mode: str = Form(default="append"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ImportResultResponse:
    """
    批量导入知识点 - 需求11验收标准6
    支持Excel导入，布鲁姆分类法自动标注
    """
    try:
        logger.info(
            f"开始导入知识点文件: {file.filename}",
            extra={
                "user_id": current_user.id,
                "library_id": library_id,
                "file_name": file.filename,
                "import_mode": import_mode,
            },
        )

        service = CourseResourceService(db)
        result = await service.import_knowledge_points(
            library_id, file, import_mode, current_user.id
        )

        logger.info(
            f"知识点导入完成: 成功{result.success}条，失败{result.failed}条",
            extra={
                "library_id": library_id,
                "success_count": result.success,
                "failed_count": result.failed,
            },
        )

        return result

    except ValidationError as e:
        logger.warning(
            f"导入验证失败: {e.message}",
            extra={"user_id": current_user.id, "library_id": library_id},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"知识点导入失败: {str(e)}",
            extra={
                "user_id": current_user.id,
                "library_id": library_id,
                "error": str(e),
            },
        )
        raise HTTPException(status_code=500, detail="知识点导入失败") from e


# =================== 教材库管理 ===================


@router.get(
    "/courses/{course_id}/material-library", response_model=MaterialLibraryResponse
)
async def get_material_library(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialLibraryResponse:
    """
    获取课程教材库 - 需求11验收标准3
    1课程多教材，支持出版信息登记+自编教材上传
    """
    try:
        logger.info(
            f"获取课程{course_id}的教材库",
            extra={
                "user_id": current_user.id,
                "course_id": course_id,
                "action": "get_material_library",
            },
        )

        service = CourseResourceService(db)
        library = await service.get_material_library(course_id, current_user.id)

        # 转换为响应格式
        materials = library.get("materials", [])
        logger.info(
            f"成功获取教材库，包含{len(materials)}个教材",
            extra={"course_id": course_id, "material_count": len(materials)},
        )

        return MaterialLibraryResponse(
            id=library.get("id", 1),
            course_id=course_id,
            materials=materials,
            total_count=len(materials),
        )

    except ResourceNotFoundError as e:
        logger.warning(
            f"教材库不存在: {e.message}",
            extra={"user_id": current_user.id, "course_id": course_id},
        )
        raise HTTPException(status_code=404, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"获取教材库失败: {str(e)}",
            extra={"user_id": current_user.id, "course_id": course_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="获取教材库失败") from e


@router.post("/courses/{course_id}/materials", response_model=MaterialResponse)
async def add_material(
    course_id: int,
    material_data: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialResponse:
    """
    添加教材 - 需求11验收标准3
    支持ISBN标准管理、章节树状结构
    """
    try:
        logger.info(
            f"添加教材: {material_data.title}",
            extra={
                "user_id": current_user.id,
                "course_id": course_id,
                "material_title": material_data.title,
                "is_custom": material_data.is_custom,
            },
        )

        service = CourseResourceService(db)
        material = await service.add_material(
            course_id, material_data.dict(), current_user.id
        )

        logger.info(
            f"教材添加成功: {material.get('title', '')}",
            extra={"material_id": material.get("id", 0), "course_id": course_id},
        )

        return MaterialResponse(
            id=material.get("id", 1),
            title=material.get("title", ""),
            course_id=course_id,
            isbn=material.get("isbn"),
            publisher=material.get("publisher", ""),
            edition=material.get("edition", ""),
            authors=material.get("authors", []),
            publication_year=material.get("publication_year", 2024),
            description=material.get("description", ""),
            file_url=material.get("file_url"),
            file_size=material.get("file_size"),
            file_format=material.get("file_format"),
            chapters=material.get("chapters", []),
            is_custom=material.get("is_custom", False),
            created_at=material.get("created_at", ""),
            updated_at=material.get("updated_at", ""),
        )

    except ValidationError as e:
        logger.warning(
            f"教材数据验证失败: {e.message}",
            extra={"user_id": current_user.id, "validation_errors": e.details},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"添加教材失败: {str(e)}",
            extra={"user_id": current_user.id, "course_id": course_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="添加教材失败") from e


@router.post("/courses/{course_id}/materials/upload", response_model=MaterialResponse)
async def upload_custom_material(
    course_id: int,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...),
    authors: str = Form(...),  # JSON字符串
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialResponse:
    """
    上传自编教材 - 需求11验收标准3
    支持PDF文件上传、OCR识别、章节自动提取
    """
    try:
        # 验证文件类型
        if file.content_type != "application/pdf":
            raise ValidationError(
                message="仅支持PDF格式的自编教材",
                error_code="INVALID_FILE_TYPE",
                details={"supported_types": ["PDF"]},
            )

        logger.info(
            f"上传自编教材: {title}",
            extra={
                "user_id": current_user.id,
                "course_id": course_id,
                "file_name": file.filename,
                "file_size": file.size,
            },
        )

        service = CourseResourceService(db)
        material = await service.upload_custom_material(
            course_id, file, current_user.id
        )

        logger.info(
            f"自编教材上传成功: {material.get('title', '')}",
            extra={
                "material_id": material.get("id", 0),
                "course_id": course_id,
                "file_size": material.get("file_size", 0),
            },
        )

        return MaterialResponse(
            id=material.get("id", 1),
            title=material.get("title", ""),
            course_id=course_id,
            isbn=material.get("isbn"),
            publisher=material.get("publisher", ""),
            edition=material.get("edition", ""),
            authors=material.get("authors", []),
            publication_year=material.get("publication_year", 2024),
            description=material.get("description", ""),
            file_url=material.get("file_url"),
            file_size=material.get("file_size"),
            file_format=material.get("file_format"),
            chapters=material.get("chapters", []),
            is_custom=material.get("is_custom", True),
            created_at=material.get("created_at", ""),
            updated_at=material.get("updated_at", ""),
        )

    except ValidationError as e:
        logger.warning(
            f"文件验证失败: {e.message}",
            extra={"user_id": current_user.id, "file_name": file.filename},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"上传自编教材失败: {str(e)}",
            extra={"user_id": current_user.id, "course_id": course_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="上传自编教材失败") from e


# =================== 考纲管理 ===================


@router.get("/courses/{course_id}/syllabus", response_model=SyllabusResponse | None)
async def get_syllabus(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyllabusResponse | None:
    """
    获取课程考纲 - 需求11验收标准4
    1课程1考纲的版本化管理，支持Git-like版本控制
    """
    try:
        logger.info(
            f"获取课程{course_id}的考纲",
            extra={
                "user_id": current_user.id,
                "course_id": course_id,
                "action": "get_syllabus",
            },
        )

        service = CourseResourceService(db)
        syllabus = await service.get_syllabus(course_id, current_user.id)

        if syllabus:
            logger.info(
                f"成功获取考纲: {syllabus.get('title', '')}",
                extra={
                    "syllabus_id": syllabus.get("id", 0),
                    "version": syllabus.get("version", ""),
                },
            )
            return SyllabusResponse(
                id=syllabus.get("id", 1),
                title=syllabus.get("title", ""),
                course_id=course_id,
                version=syllabus.get("version", "1.0"),
                description=syllabus.get("description", ""),
                objectives=syllabus.get("objectives", []),
                knowledge_points=syllabus.get("knowledge_points", []),
                assessment_criteria=syllabus.get("assessment_criteria", []),
                time_allocation=syllabus.get("time_allocation", []),
                references=syllabus.get("references", []),
                is_active=syllabus.get("is_active", True),
                parent_syllabus_id=syllabus.get("parent_syllabus_id"),
                created_at=syllabus.get("created_at", ""),
                updated_at=syllabus.get("updated_at", ""),
            )
        else:
            logger.info("课程暂无考纲", extra={"course_id": course_id})

        return None

    except PermissionDeniedError as e:
        logger.warning(
            f"权限不足: {e.message}",
            extra={"user_id": current_user.id, "course_id": course_id},
        )
        raise HTTPException(status_code=403, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"获取考纲失败: {str(e)}",
            extra={"user_id": current_user.id, "course_id": course_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="获取考纲失败") from e


@router.post("/courses/{course_id}/syllabus", response_model=SyllabusResponse)
async def create_syllabus(
    course_id: int,
    syllabus_data: SyllabusCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyllabusResponse:
    """
    创建考纲 - 需求11验收标准4
    支持版本控制、权重计算、标准符合性检查
    """
    try:
        logger.info(
            f"创建考纲: {syllabus_data.title}",
            extra={
                "user_id": current_user.id,
                "course_id": course_id,
                "syllabus_title": syllabus_data.title,
                "knowledge_points_count": len(syllabus_data.knowledge_points),
            },
        )

        service = CourseResourceService(db)
        syllabus = await service.create_syllabus(
            course_id, syllabus_data.dict(), current_user.id
        )

        logger.info(
            f"考纲创建成功: {syllabus.get('title', '')}",
            extra={
                "syllabus_id": syllabus.get("id", 0),
                "version": syllabus.get("version", ""),
            },
        )

        return SyllabusResponse(
            id=syllabus.get("id", 1),
            title=syllabus.get("title", ""),
            course_id=course_id,
            version=syllabus.get("version", "1.0"),
            description=syllabus.get("description", ""),
            objectives=syllabus.get("objectives", []),
            knowledge_points=syllabus.get("knowledge_points", []),
            assessment_criteria=syllabus.get("assessment_criteria", []),
            time_allocation=syllabus.get("time_allocation", []),
            references=syllabus.get("references", []),
            is_active=syllabus.get("is_active", True),
            parent_syllabus_id=syllabus.get("parent_syllabus_id"),
            created_at=syllabus.get("created_at", ""),
            updated_at=syllabus.get("updated_at", ""),
        )

    except ValidationError as e:
        logger.warning(
            f"考纲数据验证失败: {e.message}",
            extra={"user_id": current_user.id, "validation_errors": e.details},
        )
        raise HTTPException(status_code=422, detail=e.message) from e
    except Exception as e:
        logger.error(
            f"创建考纲失败: {str(e)}",
            extra={"user_id": current_user.id, "course_id": course_id, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="创建考纲失败") from e
