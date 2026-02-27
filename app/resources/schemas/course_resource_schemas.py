"""
课程资源库管理Schema定义 - 需求11数据模型
符合设计文档技术要求：严格类型检查、完整数据验证
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator

# =================== 枚举定义 ===================


class PermissionLevel(str, Enum):
    """权限级别枚举 - 需求11三级权限"""

    PRIVATE = "private"
    CLASS = "class"
    PUBLIC = "public"


class ResourceType(str, Enum):
    """资源类型枚举"""

    VOCABULARY = "vocabulary"
    KNOWLEDGE = "knowledge"
    MATERIAL = "material"
    SYLLABUS = "syllabus"


class CognitiveLevel(str, Enum):
    """布鲁姆分类法认知层次"""

    REMEMBER = "remember"  # 记忆
    UNDERSTAND = "understand"  # 理解
    APPLY = "apply"  # 应用
    ANALYZE = "analyze"  # 分析
    EVALUATE = "evaluate"  # 评价
    CREATE = "create"  # 创造


# =================== 词汇库相关Schema ===================


class VocabularyLibraryCreate(BaseModel):
    """创建词汇库请求"""

    name: str = Field(..., min_length=1, max_length=200, description="词汇库名称")
    description: str = Field("", max_length=1000, description="词汇库描述")
    permission: PermissionLevel = Field(PermissionLevel.PRIVATE, description="权限级别")

    @validator("name")
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("词汇库名称不能为空")
        return v.strip()


class VocabularyLibraryResponse(BaseModel):
    """词汇库响应"""

    id: int
    course_id: int
    name: str
    description: str | None
    item_count: int = Field(description="词汇数量")
    permission: str
    version: str
    created_at: str
    updated_at: str
    last_import_at: str | None = None


class VocabularyItemCreate(BaseModel):
    """创建词汇项请求"""

    word: str = Field(..., min_length=1, max_length=100)
    pronunciation: str | None = Field(None, max_length=200)
    part_of_speech: str | None = Field(None, max_length=20)
    definitions: list[str] = Field(default_factory=list)
    chinese_meaning: str = Field(..., min_length=1)
    example_sentences: list[str] = Field(default_factory=list)
    difficulty_level: int = Field(1, ge=1, le=6, description="CEFR标准分级1-6")
    topic_category: str | None = Field(None, max_length=100)
    frequency_rank: int | None = Field(None, ge=1)
    synonyms: list[str] = Field(default_factory=list)
    antonyms: list[str] = Field(default_factory=list)
    collocations: list[str] = Field(default_factory=list)


class VocabularyItemResponse(VocabularyItemCreate):
    """词汇项响应"""

    id: int
    library_id: int
    total_attempts: int = 0
    correct_attempts: int = 0
    mastery_rate: float = 0.0
    created_at: str
    updated_at: str


# =================== 知识点库相关Schema ===================


class KnowledgeLibraryCreate(BaseModel):
    """创建知识点库请求"""

    name: str = Field(..., min_length=1, max_length=200, description="知识点库名称")
    description: str = Field("", max_length=1000, description="知识点库描述")
    permission: PermissionLevel = Field(PermissionLevel.PRIVATE, description="权限级别")


class KnowledgeLibraryResponse(BaseModel):
    """知识点库响应"""

    id: int
    course_id: int
    name: str
    description: str | None
    item_count: int = Field(description="知识点数量")
    permission: str
    version: str
    created_at: str
    updated_at: str


class KnowledgePointCreate(BaseModel):
    """创建知识点请求"""

    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    category: str = Field(..., max_length=100)
    difficulty_level: int = Field(1, ge=1, le=5)
    cognitive_level: CognitiveLevel = Field(CognitiveLevel.REMEMBER)
    prerequisites: list[int] = Field(default_factory=list, description="前置知识点ID")
    related_points: list[int] = Field(default_factory=list, description="相关知识点ID")
    examples: list[str] = Field(default_factory=list)
    exercises: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KnowledgePointResponse(KnowledgePointCreate):
    """知识点响应"""

    id: int
    library_id: int
    created_at: str
    updated_at: str


# =================== 教材库相关Schema ===================


class MaterialCreate(BaseModel):
    """创建教材请求"""

    title: str = Field(..., min_length=1, max_length=300)
    isbn: str | None = Field(None, max_length=20)
    publisher: str = Field(..., min_length=1, max_length=200)
    edition: str = Field(..., min_length=1, max_length=50)
    authors: list[str] = Field(..., min_length=1)
    publication_year: int = Field(..., ge=1900, le=2030)
    description: str = Field("", max_length=1000)
    is_custom: bool = Field(False, description="是否为自编教材")

    @validator("isbn")
    def validate_isbn(cls, v: str | None) -> str | None:
        if v and not v.replace("-", "").isdigit():
            raise ValueError("ISBN格式不正确")
        return v


class MaterialChapterCreate(BaseModel):
    """创建章节请求"""

    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field("", description="章节内容")
    page_start: int = Field(1, ge=1)
    page_end: int = Field(1, ge=1)

    @validator("page_end")
    def validate_page_range(cls, v: int, values: dict[str, Any]) -> int:
        if "page_start" in values and v < values["page_start"]:
            raise ValueError("结束页码不能小于起始页码")
        return v


class MaterialChapterResponse(MaterialChapterCreate):
    """章节响应"""

    id: int
    material_id: int
    sections: list[dict[str, Any]] = Field(default_factory=list)


class MaterialResponse(BaseModel):
    """教材响应"""

    id: int
    title: str
    course_id: int
    isbn: str | None
    publisher: str
    edition: str
    authors: list[str]
    publication_year: int
    description: str
    file_url: str | None
    file_size: int | None
    file_format: str | None
    chapters: list[MaterialChapterResponse]
    is_custom: bool
    created_at: str
    updated_at: str


class MaterialLibraryResponse(BaseModel):
    """教材库响应"""

    id: int
    course_id: int
    materials: list[MaterialResponse]
    total_count: int
    permission: str = "private"
    created_at: str = ""
    updated_at: str = ""


# =================== 考纲相关Schema ===================


class SyllabusKnowledgePointCreate(BaseModel):
    """考纲知识点创建请求"""

    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(..., min_length=1)
    cognitive_level: CognitiveLevel = Field(CognitiveLevel.REMEMBER)
    weight: float = Field(..., ge=0.0, le=1.0, description="权重0-1")
    required_hours: int = Field(1, ge=1, description="要求学时")
    assessment_methods: list[str] = Field(default_factory=list)


class SyllabusKnowledgePointResponse(SyllabusKnowledgePointCreate):
    """考纲知识点响应"""

    id: int


class AssessmentCriterionCreate(BaseModel):
    """评估标准创建请求"""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    weight: float = Field(..., ge=0.0, le=1.0)
    rubric: list[str] = Field(default_factory=list, description="评分标准")


class AssessmentCriterionResponse(AssessmentCriterionCreate):
    """评估标准响应"""

    id: int


class TimeAllocationCreate(BaseModel):
    """时间分配创建请求"""

    topic: str = Field(..., min_length=1, max_length=200)
    hours: int = Field(..., ge=1)
    weeks: list[int] = Field(..., min_length=1)


class TimeAllocationResponse(TimeAllocationCreate):
    """时间分配响应"""

    id: int


class SyllabusCreate(BaseModel):
    """创建考纲请求"""

    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(..., min_length=1)
    objectives: list[str] = Field(..., min_length=1)
    knowledge_points: list[SyllabusKnowledgePointCreate] = Field(..., min_length=1)
    assessment_criteria: list[AssessmentCriterionCreate] = Field(default_factory=list)
    time_allocation: list[TimeAllocationCreate] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


class SyllabusResponse(BaseModel):
    """考纲响应"""

    id: int
    course_id: int
    title: str
    version: str
    description: str
    objectives: list[str]
    knowledge_points: list[SyllabusKnowledgePointResponse]
    assessment_criteria: list[AssessmentCriterionResponse]
    time_allocation: list[TimeAllocationResponse]
    references: list[str]
    is_active: bool
    parent_syllabus_id: int | None
    created_at: str
    updated_at: str


# =================== 导入相关Schema ===================


class ImportError(BaseModel):
    """导入错误"""

    row: int
    field: str
    value: str
    message: str


class ImportWarning(BaseModel):
    """导入警告"""

    row: int
    message: str


class ImportResultResponse(BaseModel):
    """导入结果响应"""

    success: int = Field(description="成功导入数量")
    failed: int = Field(description="失败数量")
    total: int = Field(description="总数量")
    errors: list[ImportError] = Field(default_factory=list)
    warnings: list[ImportWarning] = Field(default_factory=list)


# =================== 权限相关Schema ===================


class SharedWithConfig(BaseModel):
    """共享配置"""

    class_ids: list[int] | None = Field(None, description="共享班级ID列表")
    teacher_ids: list[int] | None = Field(None, description="共享教师ID列表")


class PermissionSettingRequest(BaseModel):
    """权限设置请求"""

    resource_type: ResourceType
    resource_id: int
    permission: PermissionLevel
    shared_with: SharedWithConfig | None = None


class PermissionSettingResponse(BaseModel):
    """权限设置响应"""

    success: bool
    message: str = "权限设置成功"
    resource_type: str
    resource_id: int
    permission: str
    shared_with: dict[str, Any] | None = None
