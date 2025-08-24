"""智能批改相关Schema定义."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.training.schemas.training_schemas import GradingResult


class StreamingGradingRequest(BaseModel):
    """流式批改请求."""

    question_id: int = Field(..., description="题目ID")
    user_answer: str = Field(..., min_length=1, description="用户答案")
    context: dict[str, Any] | None = Field(None, description="批改上下文")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": 123,
                "user_answer": "My favorite hobby is reading books...",
                "context": {"time_spent": 300, "attempt_count": 1},
            }
        }


class GradingRequest(BaseModel):
    """传统批改请求."""

    question_id: int = Field(..., description="题目ID")
    user_answer: dict[str, Any] = Field(..., description="用户答案")
    context: dict[str, Any] | None = Field(None, description="批改上下文")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": 123,
                "user_answer": {
                    "text": "My favorite hobby is reading books...",
                    "word_count": 150,
                },
                "context": {"time_spent": 300, "attempt_count": 1},
            }
        }


class GradingResponse(BaseModel):
    """批改响应."""

    question_id: int = Field(..., description="题目ID")
    user_id: int = Field(..., description="用户ID")
    grading_result: GradingResult = Field(..., description="批改结果")
    grading_time: datetime = Field(..., description="批改时间")
    cet4_standard_applied: bool = Field(True, description="是否应用四级标准")

    class Config:
        json_schema_extra = {
            "example": {
                "question_id": 123,
                "user_id": 456,
                "grading_result": {
                    "is_correct": True,
                    "score": 12.5,
                    "max_score": 15.0,
                    "detailed_feedback": "写作内容切题，表达清楚...",
                    "improvement_suggestions": ["注意语法准确性", "增加词汇多样性"],
                },
                "grading_time": "2024-01-15T10:30:00Z",
                "cet4_standard_applied": True,
            }
        }


class WritingAssistanceRequest(BaseModel):
    """写作辅助请求."""

    text: str = Field(..., min_length=1, description="待检查文本")
    assistance_type: str = Field(
        "grammar", description="辅助类型", pattern="^(grammar|vocabulary|style)$"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "I am very interesting in learning English.",
                "assistance_type": "grammar",
            }
        }


class StreamingChunk(BaseModel):
    """流式输出块."""

    type: str = Field(..., description="块类型")
    content: str | None = Field(None, description="内容")
    progress: int = Field(0, ge=0, le=100, description="进度百分比")
    timestamp: float = Field(..., description="时间戳")
    message: str | None = Field(None, description="状态消息")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "grading",
                "content": "您的作文内容切题，表达思想清楚...",
                "progress": 45,
                "timestamp": 1642234567.123,
                "message": "正在分析语法结构...",
            }
        }


class StreamingGradingResult(BaseModel):
    """流式批改最终结果."""

    score: float = Field(..., ge=0, description="得分")
    max_score: float = Field(..., gt=0, description="满分")
    accuracy_rate: float = Field(..., ge=0, le=1, description="准确率")
    detailed_feedback: str = Field(..., description="详细反馈")
    error_analysis: list[str] = Field(default_factory=list, description="错误分析")
    improvement_suggestions: list[str] = Field(default_factory=list, description="改进建议")
    grammar_issues: list[str] = Field(default_factory=list, description="语法问题")
    vocabulary_suggestions: list[str] = Field(default_factory=list, description="词汇建议")
    confidence: float = Field(..., ge=0, le=1, description="批改置信度")
    grading_criteria: dict[str, float] = Field(default_factory=dict, description="评分细则")

    class Config:
        json_schema_extra = {
            "example": {
                "score": 12.5,
                "max_score": 15.0,
                "accuracy_rate": 0.83,
                "detailed_feedback": "您的作文内容切题，表达思想清楚...",
                "error_analysis": ["第二段第三句语法错误", "词汇使用不够准确"],
                "improvement_suggestions": ["注意时态一致性", "增加高级词汇使用"],
                "grammar_issues": ["时态不一致", "主谓不一致"],
                "vocabulary_suggestions": ["使用更精确的动词", "增加形容词多样性"],
                "confidence": 0.92,
                "grading_criteria": {
                    "content": 4.0,
                    "language": 3.5,
                    "structure": 3.0,
                    "mechanics": 2.0,
                },
            }
        }


class WritingAssistanceResult(BaseModel):
    """写作辅助结果."""

    suggestions: list[dict[str, Any]] = Field(default_factory=list, description="建议列表")
    overall_score: int = Field(0, ge=0, le=100, description="整体评分")
    improvement_tips: list[str] = Field(default_factory=list, description="改进提示")

    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "error": "interesting",
                        "position": "第1句第4个词",
                        "suggestion": "interested",
                        "explanation": "应使用过去分词形式表示'感兴趣的'",
                    }
                ],
                "overall_score": 75,
                "improvement_tips": ["注意形容词的正确形式", "加强语法基础练习"],
            }
        }


class QualityMetrics(BaseModel):
    """批改质量指标."""

    response_time: float = Field(..., description="响应时间(秒)")
    chunk_count: int = Field(..., description="流式块数量")
    avg_chunk_interval: float = Field(..., description="平均块间隔(秒)")
    confidence_score: float = Field(..., ge=0, le=1, description="置信度")
    accuracy_estimate: float = Field(..., ge=0, le=1, description="准确性估计")

    class Config:
        json_schema_extra = {
            "example": {
                "response_time": 2.35,
                "chunk_count": 15,
                "avg_chunk_interval": 0.156,
                "confidence_score": 0.92,
                "accuracy_estimate": 0.95,
            }
        }


class BatchGradingRequest(BaseModel):
    """批量批改请求."""

    grading_requests: list[GradingRequest] = Field(..., description="批改请求列表")
    priority: str = Field("normal", description="优先级", pattern="^(low|normal|high|urgent)$")

    class Config:
        json_schema_extra = {
            "example": {
                "grading_requests": [
                    {
                        "question_id": 123,
                        "user_answer": {"text": "My hobby is reading..."},
                        "context": {"time_spent": 300},
                    },
                    {
                        "question_id": 124,
                        "user_answer": {"text": "I like sports..."},
                        "context": {"time_spent": 250},
                    },
                ],
                "priority": "normal",
            }
        }


class BatchGradingResponse(BaseModel):
    """批量批改响应."""

    results: list[GradingResponse] = Field(..., description="批改结果列表")
    total_count: int = Field(..., description="总数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    processing_time: float = Field(..., description="处理时间(秒)")

    class Config:
        json_schema_extra = {
            "example": {
                "results": [],
                "total_count": 10,
                "success_count": 9,
                "failed_count": 1,
                "processing_time": 15.6,
            }
        }


class GradingStatistics(BaseModel):
    """批改统计信息."""

    total_graded: int = Field(..., description="总批改数量")
    avg_response_time: float = Field(..., description="平均响应时间")
    avg_accuracy: float = Field(..., description="平均准确率")
    success_rate: float = Field(..., description="成功率")
    quality_score: float = Field(..., description="质量评分")

    class Config:
        json_schema_extra = {
            "example": {
                "total_graded": 1250,
                "avg_response_time": 2.1,
                "avg_accuracy": 0.94,
                "success_rate": 0.98,
                "quality_score": 0.92,
            }
        }
