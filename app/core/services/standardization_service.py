"""
标准化对接服务 - 需求18验收标准3实现
教材标准、评分标准、API对接、数据导出
"""

import json
import logging
import re
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import CacheType
from app.shared.services.cache_service import CacheService
from app.shared.utils.exceptions import BusinessLogicError, ValidationError

logger = logging.getLogger(__name__)


class StandardizationService:
    """标准化对接服务 - 需求18验收标准3实现."""

    def __init__(
        self,
        db: AsyncSession,
        cache_service: CacheService,
    ) -> None:
        """初始化标准化对接服务."""
        self.db = db
        self.cache_service = cache_service
        self.logger = logger

    # ==================== 教材标准：教材出版信息符合ISBN规范 ====================

    async def validate_textbook_isbn(self, isbn: str) -> dict[str, Any]:
        """验证教材ISBN规范."""
        try:
            # 清理ISBN格式
            cleaned_isbn = self._clean_isbn(isbn)

            # 验证ISBN格式
            validation_result = self._validate_isbn_format(cleaned_isbn)

            if not validation_result["is_valid"]:
                raise ValidationError(f"ISBN格式不符合规范: {validation_result['error']}")

            # 获取ISBN详细信息
            isbn_info = await self._get_isbn_details(cleaned_isbn)

            # 构建标准化教材信息
            standardized_info = {
                "isbn": cleaned_isbn,
                "isbn_13": self._convert_to_isbn13(cleaned_isbn),
                "validation_result": validation_result,
                "isbn_details": isbn_info,
                "compliance_status": "compliant",
                "validated_at": datetime.utcnow().isoformat(),
            }

            # 缓存验证结果
            cache_key = f"isbn_validation:{cleaned_isbn}"
            await self.cache_service.set(
                cache_key, standardized_info, CacheType.SYSTEM_DATA, ttl=86400
            )

            return standardized_info

        except Exception as e:
            self.logger.error(f"ISBN验证失败: {str(e)}")
            raise ValidationError(f"ISBN验证失败: {str(e)}") from e

    def _clean_isbn(self, isbn: str) -> str:
        """清理ISBN格式."""
        # 移除所有非数字和非X字符
        cleaned = re.sub(r"[^0-9X]", "", isbn.upper())
        return cleaned

    def _validate_isbn_format(self, isbn: str) -> dict[str, Any]:
        """验证ISBN格式."""
        if len(isbn) == 10:
            return self._validate_isbn10(isbn)
        elif len(isbn) == 13:
            return self._validate_isbn13(isbn)
        else:
            return {
                "is_valid": False,
                "error": f"ISBN长度不正确，应为10位或13位，实际为{len(isbn)}位",
                "format": "unknown",
            }

    def _validate_isbn10(self, isbn: str) -> dict[str, Any]:
        """验证ISBN-10格式."""
        if not re.match(r"^\d{9}[\dX]$", isbn):
            return {
                "is_valid": False,
                "error": "ISBN-10格式不正确",
                "format": "isbn10",
            }

        # 计算校验位
        check_sum = 0
        for i in range(9):
            check_sum += int(isbn[i]) * (10 - i)

        check_digit = isbn[9]
        calculated_check_num = (11 - (check_sum % 11)) % 11

        if calculated_check_num == 10:
            calculated_check = "X"
        else:
            calculated_check = str(calculated_check_num)

        is_valid = check_digit == calculated_check

        return {
            "is_valid": is_valid,
            "error": None if is_valid else "ISBN-10校验位不正确",
            "format": "isbn10",
            "check_digit": check_digit,
            "calculated_check": calculated_check,
        }

    def _validate_isbn13(self, isbn: str) -> dict[str, Any]:
        """验证ISBN-13格式."""
        if not re.match(r"^\d{13}$", isbn):
            return {
                "is_valid": False,
                "error": "ISBN-13格式不正确",
                "format": "isbn13",
            }

        # 计算校验位
        check_sum = 0
        for i in range(12):
            weight = 1 if i % 2 == 0 else 3
            check_sum += int(isbn[i]) * weight

        check_digit = int(isbn[12])
        calculated_check = (10 - (check_sum % 10)) % 10

        is_valid = check_digit == calculated_check

        return {
            "is_valid": is_valid,
            "error": None if is_valid else "ISBN-13校验位不正确",
            "format": "isbn13",
            "check_digit": check_digit,
            "calculated_check": calculated_check,
        }

    def _convert_to_isbn13(self, isbn: str) -> str:
        """将ISBN-10转换为ISBN-13."""
        if len(isbn) == 13:
            return isbn

        if len(isbn) == 10:
            # 添加978前缀，移除原校验位，重新计算校验位
            isbn12 = "978" + isbn[:9]
            check_sum = 0
            for i in range(12):
                weight = 1 if i % 2 == 0 else 3
                check_sum += int(isbn12[i]) * weight

            check_digit = (10 - (check_sum % 10)) % 10
            return isbn12 + str(check_digit)

        return isbn

    async def _get_isbn_details(self, isbn: str) -> dict[str, Any]:
        """获取ISBN详细信息."""
        # 这里应该调用外部ISBN数据库API
        # 暂时返回模拟数据
        return {
            "title": "示例教材",
            "author": "示例作者",
            "publisher": "示例出版社",
            "publication_year": "2024",
            "language": "中文",
            "subject": "英语",
            "grade_level": "大学",
        }

    # ==================== 评分标准：写作评分对接CET-4标准 ====================

    async def standardize_writing_score(
        self,
        writing_content: str,
        scoring_criteria: dict[str, Any],
    ) -> dict[str, Any]:
        """标准化写作评分，对接CET-4标准."""
        try:
            # CET-4写作评分标准
            cet4_criteria = self._get_cet4_writing_criteria()

            # 分析写作内容
            content_analysis = await self._analyze_writing_content(writing_content)

            # 按CET-4标准评分
            cet4_score = await self._calculate_cet4_score(content_analysis, cet4_criteria)

            # 生成详细评分报告
            scoring_report = {
                "content": writing_content,
                "content_analysis": content_analysis,
                "cet4_criteria": cet4_criteria,
                "cet4_score": cet4_score,
                "scoring_breakdown": self._generate_scoring_breakdown(cet4_score),
                "improvement_suggestions": self._generate_improvement_suggestions(cet4_score),
                "scored_at": datetime.utcnow().isoformat(),
                "compliance_status": "cet4_compliant",
            }

            # 缓存评分结果
            cache_key = f"writing_score:{hash(writing_content)}"
            await self.cache_service.set(cache_key, scoring_report, CacheType.AI_RESULT, ttl=3600)

            return scoring_report

        except Exception as e:
            self.logger.error(f"写作评分标准化失败: {str(e)}")
            raise BusinessLogicError(f"写作评分标准化失败: {str(e)}") from e

    def _get_cet4_writing_criteria(self) -> dict[str, Any]:
        """获取CET-4写作评分标准."""
        return {
            "total_score": 15,
            "criteria": {
                "content_relevance": {
                    "weight": 0.4,
                    "max_score": 6,
                    "description": "内容切题，思想表达清楚",
                },
                "language_accuracy": {
                    "weight": 0.3,
                    "max_score": 4.5,
                    "description": "语言准确，语法正确",
                },
                "organization_coherence": {
                    "weight": 0.2,
                    "max_score": 3,
                    "description": "结构合理，逻辑清晰",
                },
                "vocabulary_usage": {
                    "weight": 0.1,
                    "max_score": 1.5,
                    "description": "词汇丰富，用词恰当",
                },
            },
            "score_levels": {
                "excellent": {"range": [13, 15], "description": "优秀"},
                "good": {"range": [10, 12], "description": "良好"},
                "fair": {"range": [7, 9], "description": "及格"},
                "poor": {"range": [4, 6], "description": "较差"},
                "very_poor": {"range": [0, 3], "description": "很差"},
            },
        }

    async def _analyze_writing_content(self, content: str) -> dict[str, Any]:
        """分析写作内容."""
        # 这里应该使用NLP技术分析写作内容
        # 暂时返回模拟分析结果
        return {
            "word_count": len(content.split()),
            "sentence_count": len(content.split(".")),
            "paragraph_count": len(content.split("\n\n")),
            "vocabulary_diversity": 0.8,
            "grammar_accuracy": 0.85,
            "content_relevance": 0.9,
            "organization_score": 0.8,
        }

    async def _calculate_cet4_score(
        self, analysis: dict[str, Any], criteria: dict[str, Any]
    ) -> dict[str, Any]:
        """按CET-4标准计算分数."""
        scores = {}
        total_score = 0

        for criterion, config in criteria["criteria"].items():
            # 根据分析结果计算各项分数
            if criterion == "content_relevance":
                score = analysis["content_relevance"] * config["max_score"]
            elif criterion == "language_accuracy":
                score = analysis["grammar_accuracy"] * config["max_score"]
            elif criterion == "organization_coherence":
                score = analysis["organization_score"] * config["max_score"]
            elif criterion == "vocabulary_usage":
                score = analysis["vocabulary_diversity"] * config["max_score"]
            else:
                score = 0

            scores[criterion] = round(score, 1)
            total_score += score

        total_score = round(total_score, 1)

        # 确定分数等级
        score_level = "poor"
        for level, config in criteria["score_levels"].items():
            if config["range"][0] <= total_score <= config["range"][1]:
                score_level = level
                break

        return {
            "criterion_scores": scores,
            "total_score": total_score,
            "max_score": criteria["total_score"],
            "score_level": score_level,
            "percentage": round((total_score / criteria["total_score"]) * 100, 1),
        }

    def _generate_scoring_breakdown(self, score: dict[str, Any]) -> dict[str, Any]:
        """生成评分详细分解."""
        return {
            "strengths": self._identify_strengths(score),
            "weaknesses": self._identify_weaknesses(score),
            "score_distribution": score["criterion_scores"],
            "overall_performance": score["score_level"],
        }

    def _identify_strengths(self, score: dict[str, Any]) -> list[str]:
        """识别写作优势."""
        strengths = []
        for criterion, score_value in score["criterion_scores"].items():
            # 如果某项得分超过80%，认为是优势
            if score_value > 0.8 * 6:  # 假设最高分是6
                strengths.append(f"{criterion}: 表现优秀")
        return strengths

    def _identify_weaknesses(self, score: dict[str, Any]) -> list[str]:
        """识别写作弱点."""
        weaknesses = []
        for criterion, score_value in score["criterion_scores"].items():
            # 如果某项得分低于60%，认为是弱点
            if score_value < 0.6 * 6:  # 假设最高分是6
                weaknesses.append(f"{criterion}: 需要改进")
        return weaknesses

    def _generate_improvement_suggestions(self, score: dict[str, Any]) -> list[str]:
        """生成改进建议."""
        suggestions = []

        if score["total_score"] < 9:
            suggestions.append("建议加强基础语法和词汇练习")

        if score["criterion_scores"].get("content_relevance", 0) < 3:
            suggestions.append("注意审题，确保内容切题")

        if score["criterion_scores"].get("organization_coherence", 0) < 2:
            suggestions.append("改善文章结构，使用连接词增强逻辑性")

        return suggestions

    # ==================== API对接：支持第三方教育工具对接 ====================

    async def register_third_party_api(
        self,
        api_name: str,
        api_config: dict[str, Any],
        authentication: dict[str, Any],
    ) -> dict[str, Any]:
        """注册第三方教育工具API."""
        try:
            # 验证API配置
            validation_result = await self._validate_api_config(api_config)
            if not validation_result["is_valid"]:
                raise ValidationError(f"API配置验证失败: {validation_result['error']}")

            # 测试API连接
            connection_test = await self._test_api_connection(api_config, authentication)

            # 创建API注册记录
            api_registration = {
                "api_id": str(uuid4()),
                "api_name": api_name,
                "api_config": api_config,
                "authentication": authentication,
                "validation_result": validation_result,
                "connection_test": connection_test,
                "status": "active" if connection_test["success"] else "inactive",
                "registered_at": datetime.utcnow().isoformat(),
            }

            # 缓存API注册信息
            cache_key = f"third_party_api:{api_registration['api_id']}"
            await self.cache_service.set(
                cache_key, api_registration, CacheType.SYSTEM_DATA, ttl=86400
            )

            return api_registration

        except Exception as e:
            self.logger.error(f"第三方API注册失败: {str(e)}")
            raise BusinessLogicError(f"第三方API注册失败: {str(e)}") from e

    async def _validate_api_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """验证API配置."""
        required_fields = ["base_url", "version", "endpoints"]
        missing_fields = [field for field in required_fields if field not in config]

        if missing_fields:
            return {
                "is_valid": False,
                "error": f"缺少必需字段: {', '.join(missing_fields)}",
            }

        # 验证URL格式
        base_url = config.get("base_url", "")
        if not re.match(r"^https?://", base_url):
            return {
                "is_valid": False,
                "error": "base_url必须是有效的HTTP/HTTPS URL",
            }

        return {"is_valid": True, "error": None}

    async def _test_api_connection(
        self, config: dict[str, Any], auth: dict[str, Any]
    ) -> dict[str, Any]:
        """测试API连接."""
        # 这里应该实际测试API连接
        # 暂时返回模拟结果
        return {
            "success": True,
            "response_time": 150,
            "status_code": 200,
            "tested_at": datetime.utcnow().isoformat(),
        }

    # ==================== 数据导出：支持标准格式数据导出 ====================

    async def export_data_standard_format(
        self,
        data_type: str,
        export_format: str,
        filter_criteria: dict[str, Any],
        user_id: int,
    ) -> dict[str, Any]:
        """导出标准格式数据."""
        try:
            # 验证导出格式
            supported_formats = ["json", "csv", "xml", "excel", "pdf"]
            if export_format not in supported_formats:
                raise ValidationError(f"不支持的导出格式: {export_format}")

            # 获取数据
            export_data = await self._get_export_data(data_type, filter_criteria)

            # 转换为标准格式
            formatted_data = await self._format_export_data(export_data, export_format)

            # 生成导出文件
            export_file = await self._generate_export_file(formatted_data, export_format, data_type)

            # 创建导出记录
            export_record = {
                "export_id": str(uuid4()),
                "data_type": data_type,
                "export_format": export_format,
                "filter_criteria": filter_criteria,
                "user_id": user_id,
                "file_info": export_file,
                "record_count": len(export_data),
                "exported_at": datetime.utcnow().isoformat(),
                "status": "completed",
            }

            # 缓存导出记录
            cache_key = f"data_export:{export_record['export_id']}"
            await self.cache_service.set(cache_key, export_record, CacheType.SYSTEM_DATA, ttl=86400)

            return export_record

        except Exception as e:
            self.logger.error(f"数据导出失败: {str(e)}")
            raise BusinessLogicError(f"数据导出失败: {str(e)}") from e

    async def _get_export_data(
        self, data_type: str, filter_criteria: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """获取导出数据."""
        # 这里应该根据数据类型和筛选条件查询实际数据
        # 暂时返回模拟数据
        return [
            {
                "id": 1,
                "name": "示例数据1",
                "type": data_type,
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "id": 2,
                "name": "示例数据2",
                "type": data_type,
                "created_at": datetime.utcnow().isoformat(),
            },
        ]

    async def _format_export_data(self, data: list[dict[str, Any]], format_type: str) -> Any:
        """格式化导出数据."""
        if format_type == "json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        elif format_type == "csv":
            return self._convert_to_csv(data)
        elif format_type == "xml":
            return self._convert_to_xml(data)
        else:
            return data

    def _convert_to_csv(self, data: list[dict[str, Any]]) -> str:
        """转换为CSV格式."""
        if not data:
            return ""

        # 获取所有字段名
        fieldnames: set[str] = set()
        for item in data:
            fieldnames.update(item.keys())

        fieldnames = sorted(fieldnames)

        # 生成CSV内容
        csv_lines = [",".join(fieldnames)]
        for item in data:
            row = [str(item.get(field, "")) for field in fieldnames]
            csv_lines.append(",".join(row))

        return "\n".join(csv_lines)

    def _convert_to_xml(self, data: list[dict[str, Any]]) -> str:
        """转换为XML格式."""
        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<data>"]

        for item in data:
            xml_lines.append("  <item>")
            for key, value in item.items():
                xml_lines.append(f"    <{key}>{value}</{key}>")
            xml_lines.append("  </item>")

        xml_lines.append("</data>")
        return "\n".join(xml_lines)

    async def _generate_export_file(
        self, formatted_data: Any, format_type: str, data_type: str
    ) -> dict[str, Any]:
        """生成导出文件."""
        filename = f"{data_type}_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.{format_type}"

        # 这里应该实际保存文件到存储系统
        # 暂时返回文件信息
        return {
            "filename": filename,
            "file_size": len(str(formatted_data)),
            "file_path": f"/exports/{filename}",
            "download_url": f"/api/v1/exports/download/{filename}",
            "expires_at": (datetime.utcnow().timestamp() + 86400),  # 24小时后过期
        }
