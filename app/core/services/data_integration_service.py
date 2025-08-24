"""
数据贯通服务 - 需求18验收标准5实现
知识点库贯通、热点数据流动、数据追踪、数据权属
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models.enums import CacheType
from app.shared.services.cache_service import CacheService
from app.shared.utils.exceptions import BusinessLogicError

logger = logging.getLogger(__name__)


class DataIntegrationService:
    """数据贯通服务 - 需求18验收标准5实现."""

    def __init__(
        self,
        db: AsyncSession,
        cache_service: CacheService,
    ) -> None:
        """初始化数据贯通服务."""
        self.db = db
        self.cache_service = cache_service
        self.logger = logger

    # ==================== 知识点库贯通：同时支撑教学设计和错题分析 ====================

    async def integrate_knowledge_points(
        self,
        teaching_design_data: dict[str, Any],
        error_analysis_data: dict[str, Any],
    ) -> dict[str, Any]:
        """知识点库贯通，同时支撑教学设计和错题分析."""
        try:
            # 提取教学设计中的知识点
            teaching_knowledge_points = self._extract_knowledge_points(
                teaching_design_data, "teaching_design"
            )

            # 提取错题分析中的知识点
            error_knowledge_points = self._extract_knowledge_points(
                error_analysis_data, "error_analysis"
            )

            # 知识点映射和关联
            knowledge_mapping = await self._map_knowledge_points(
                teaching_knowledge_points, error_knowledge_points
            )

            # 生成贯通的知识点库
            integrated_knowledge_base = await self._build_integrated_knowledge_base(
                knowledge_mapping
            )

            # 缓存贯通结果
            cache_key = f"integrated_knowledge:{hash(str(teaching_design_data))}:{hash(str(error_analysis_data))}"
            await self.cache_service.set(
                cache_key, integrated_knowledge_base, CacheType.KNOWLEDGE_DATA, ttl=3600
            )

            # 记录数据流转
            await self._track_data_flow(
                "knowledge_integration",
                {
                    "teaching_design": teaching_design_data,
                    "error_analysis": error_analysis_data,
                },
                integrated_knowledge_base,
            )

            return {
                "integrated_knowledge_base": integrated_knowledge_base,
                "knowledge_mapping": knowledge_mapping,
                "teaching_knowledge_points": teaching_knowledge_points,
                "error_knowledge_points": error_knowledge_points,
                "integration_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"知识点库贯通失败: {str(e)}")
            raise BusinessLogicError(f"知识点库贯通失败: {str(e)}") from e

    def _extract_knowledge_points(
        self, data: dict[str, Any], source_type: str
    ) -> list[dict[str, Any]]:
        """从数据中提取知识点."""
        knowledge_points = []

        if source_type == "teaching_design":
            # 从教学设计中提取知识点
            content = data.get("content", "")
            objectives = data.get("objectives", [])

            for objective in objectives:
                knowledge_points.append(
                    {
                        "id": str(uuid4()),
                        "name": objective,
                        "source": "teaching_design",
                        "context": content[:200],
                        "extracted_at": datetime.utcnow().isoformat(),
                    }
                )

        elif source_type == "error_analysis":
            # 从错题分析中提取知识点
            errors = data.get("errors", [])

            for error in errors:
                knowledge_points.append(
                    {
                        "id": str(uuid4()),
                        "name": error.get("knowledge_point", ""),
                        "source": "error_analysis",
                        "difficulty": error.get("difficulty", "medium"),
                        "error_rate": error.get("error_rate", 0),
                        "extracted_at": datetime.utcnow().isoformat(),
                    }
                )

        return knowledge_points

    async def _map_knowledge_points(
        self,
        teaching_points: list[dict[str, Any]],
        error_points: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """映射和关联知识点."""
        mapping = {
            "matched_points": [],
            "teaching_only": [],
            "error_only": [],
            "similarity_threshold": 0.8,
        }

        # 简化的知识点匹配逻辑
        for teaching_point in teaching_points:
            matched = False
            for error_point in error_points:
                # 简单的名称匹配（实际应该使用更复杂的语义匹配）
                if teaching_point["name"].lower() in error_point["name"].lower():
                    matched_points = mapping.get("matched_points", [])
                    if isinstance(matched_points, list):
                        matched_points.append(
                            {
                                "teaching_point": teaching_point,
                                "error_point": error_point,
                                "match_score": 0.9,  # 简化的匹配分数
                            }
                        )
                    matched = True
                    break

            if not matched:
                teaching_only = mapping.get("teaching_only", [])
                if isinstance(teaching_only, list):
                    teaching_only.append(teaching_point)

        # 找出只在错题分析中出现的知识点
        matched_points = mapping.get("matched_points", [])
        if isinstance(matched_points, list):
            matched_error_ids = {match["error_point"]["id"] for match in matched_points}
            mapping["error_only"] = [
                point for point in error_points if point["id"] not in matched_error_ids
            ]

        return mapping

    async def _build_integrated_knowledge_base(
        self, knowledge_mapping: dict[str, Any]
    ) -> dict[str, Any]:
        """构建贯通的知识点库."""
        integrated_base = {
            "knowledge_points": [],
            "relationships": [],
            "coverage_analysis": {},
            "built_at": datetime.utcnow().isoformat(),
        }

        # 处理匹配的知识点
        for match in knowledge_mapping["matched_points"]:
            teaching_point = match["teaching_point"]
            error_point = match["error_point"]

            integrated_point = {
                "id": str(uuid4()),
                "name": teaching_point["name"],
                "teaching_context": teaching_point.get("context", ""),
                "error_context": {
                    "difficulty": error_point.get("difficulty", "medium"),
                    "error_rate": error_point.get("error_rate", 0),
                },
                "integration_score": match["match_score"],
                "sources": ["teaching_design", "error_analysis"],
                "priority": self._calculate_priority(teaching_point, error_point),
            }

            knowledge_points = integrated_base.get("knowledge_points", [])
            if isinstance(knowledge_points, list):
                knowledge_points.append(integrated_point)

        # 添加只在教学设计中的知识点
        for teaching_point in knowledge_mapping["teaching_only"]:
            integrated_point = {
                "id": str(uuid4()),
                "name": teaching_point["name"],
                "teaching_context": teaching_point.get("context", ""),
                "sources": ["teaching_design"],
                "priority": "medium",
                "note": "仅在教学设计中出现，需要关注学生掌握情况",
            }
            knowledge_points = integrated_base.get("knowledge_points", [])
            if isinstance(knowledge_points, list):
                knowledge_points.append(integrated_point)

        # 添加只在错题分析中的知识点
        for error_point in knowledge_mapping["error_only"]:
            integrated_point = {
                "id": str(uuid4()),
                "name": error_point["name"],
                "error_context": {
                    "difficulty": error_point.get("difficulty", "medium"),
                    "error_rate": error_point.get("error_rate", 0),
                },
                "sources": ["error_analysis"],
                "priority": "high",
                "note": "学生错误频发，需要加强教学",
            }
            knowledge_points = integrated_base.get("knowledge_points", [])
            if isinstance(knowledge_points, list):
                knowledge_points.append(integrated_point)

        # 生成覆盖分析
        integrated_base["coverage_analysis"] = {
            "total_points": len(integrated_base["knowledge_points"]),
            "matched_points": len(knowledge_mapping["matched_points"]),
            "teaching_only": len(knowledge_mapping["teaching_only"]),
            "error_only": len(knowledge_mapping["error_only"]),
            "coverage_rate": len(knowledge_mapping["matched_points"])
            / max(1, len(integrated_base["knowledge_points"])),
        }

        return integrated_base

    def _calculate_priority(
        self, teaching_point: dict[str, Any], error_point: dict[str, Any]
    ) -> str:
        """计算知识点优先级."""
        error_rate = error_point.get("error_rate", 0)

        if error_rate > 0.7:
            return "high"
        elif error_rate > 0.4:
            return "medium"
        else:
            return "low"

    # ==================== 热点数据流动：双向流动 ====================

    async def manage_hotspot_data_flow(
        self,
        source_data: dict[str, Any],
        target_system: str,
        flow_direction: str,
    ) -> dict[str, Any]:
        """管理热点数据的双向流动."""
        try:
            flow_id = str(uuid4())

            # 数据预处理
            processed_data = await self._preprocess_hotspot_data(source_data, target_system)

            # 执行数据流动
            flow_result = await self._execute_data_flow(
                processed_data, target_system, flow_direction
            )

            # 记录数据流动
            flow_record = {
                "flow_id": flow_id,
                "source_data": source_data,
                "target_system": target_system,
                "flow_direction": flow_direction,
                "processed_data": processed_data,
                "flow_result": flow_result,
                "flow_time": datetime.utcnow().isoformat(),
                "status": "completed",
            }

            # 缓存流动记录
            cache_key = f"data_flow:{flow_id}"
            await self.cache_service.set(cache_key, flow_record, CacheType.SYSTEM_DATA, ttl=86400)

            # 追踪数据流转
            await self._track_data_flow("hotspot_data_flow", source_data, flow_result)

            return flow_record

        except Exception as e:
            self.logger.error(f"热点数据流动失败: {str(e)}")
            raise BusinessLogicError(f"热点数据流动失败: {str(e)}") from e

    async def _preprocess_hotspot_data(
        self, data: dict[str, Any], target_system: str
    ) -> dict[str, Any]:
        """预处理热点数据."""
        processed = data.copy()
        processed["preprocessed_at"] = datetime.utcnow().isoformat()
        processed["target_system"] = target_system

        # 根据目标系统进行数据格式转换
        if target_system == "teaching_system":
            processed["format"] = "teaching_format"
        elif target_system == "analysis_system":
            processed["format"] = "analysis_format"

        return processed

    async def _execute_data_flow(
        self, data: dict[str, Any], target_system: str, direction: str
    ) -> dict[str, Any]:
        """执行数据流动."""
        return {
            "transferred_records": len(data.get("records", [])),
            "target_system": target_system,
            "direction": direction,
            "executed_at": datetime.utcnow().isoformat(),
        }

    # ==================== 数据追踪：全链路数据流转追踪 ====================

    async def _track_data_flow(
        self,
        operation_type: str,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
    ) -> dict[str, Any]:
        """追踪数据流转."""
        try:
            tracking_record = {
                "tracking_id": str(uuid4()),
                "operation_type": operation_type,
                "input_data_hash": hash(str(input_data)),
                "output_data_hash": hash(str(output_data)),
                "input_size": len(str(input_data)),
                "output_size": len(str(output_data)),
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "input_keys": list(input_data.keys()),
                    "output_keys": list(output_data.keys()),
                },
            }

            # 缓存追踪记录
            cache_key = f"data_tracking:{tracking_record['tracking_id']}"
            await self.cache_service.set(
                cache_key,
                tracking_record,
                CacheType.SYSTEM_DATA,
                ttl=2592000,  # 30天
            )

            return tracking_record

        except Exception as e:
            self.logger.error(f"数据流转追踪失败: {str(e)}")
            return {}

    async def get_data_flow_history(
        self,
        operation_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取数据流转历史."""
        try:
            # 这里应该查询实际的追踪记录
            # 暂时返回示例数据
            return [
                {
                    "tracking_id": "example_tracking",
                    "operation_type": operation_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "completed",
                }
            ]

        except Exception as e:
            self.logger.error(f"获取数据流转历史失败: {str(e)}")
            return []

    # ==================== 数据权属：明确定义数据所有权和使用权 ====================

    async def define_data_ownership(
        self,
        data_id: str,
        data_type: str,
        owner_id: int,
        owner_type: str,
        usage_permissions: dict[str, Any],
    ) -> dict[str, Any]:
        """定义数据所有权和使用权."""
        try:
            ownership_record = {
                "data_id": data_id,
                "data_type": data_type,
                "owner_id": owner_id,
                "owner_type": owner_type,
                "usage_permissions": usage_permissions,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active",
            }

            # 缓存权属记录
            cache_key = f"data_ownership:{data_id}"
            await self.cache_service.set(
                cache_key, ownership_record, CacheType.PERMISSION, ttl=86400
            )

            return ownership_record

        except Exception as e:
            self.logger.error(f"定义数据权属失败: {str(e)}")
            raise BusinessLogicError(f"定义数据权属失败: {str(e)}") from e

    async def check_data_usage_permission(
        self,
        data_id: str,
        user_id: int,
        usage_type: str,
    ) -> bool:
        """检查数据使用权限."""
        try:
            # 获取数据权属信息
            cache_key = f"data_ownership:{data_id}"
            ownership_record = await self.cache_service.get(cache_key, CacheType.PERMISSION)

            if not ownership_record:
                self.logger.warning(f"数据 {data_id} 的权属信息不存在")
                return False

            # 检查所有权
            if ownership_record["owner_id"] == user_id:
                return True

            # 检查使用权限
            usage_permissions = ownership_record.get("usage_permissions", {})
            user_permissions = usage_permissions.get(str(user_id), [])

            return usage_type in user_permissions

        except Exception as e:
            self.logger.error(f"检查数据使用权限失败: {str(e)}")
            return False

    async def transfer_data_ownership(
        self,
        data_id: str,
        current_owner_id: int,
        new_owner_id: int,
        transfer_reason: str,
    ) -> dict[str, Any]:
        """转移数据所有权."""
        try:
            # 获取当前权属信息
            cache_key = f"data_ownership:{data_id}"
            ownership_record = await self.cache_service.get(cache_key, CacheType.PERMISSION)

            if not ownership_record:
                raise BusinessLogicError(f"数据 {data_id} 的权属信息不存在")

            if ownership_record["owner_id"] != current_owner_id:
                raise BusinessLogicError("只有数据所有者可以转移所有权")

            # 创建转移记录
            transfer_record = {
                "transfer_id": str(uuid4()),
                "data_id": data_id,
                "old_owner_id": current_owner_id,
                "new_owner_id": new_owner_id,
                "transfer_reason": transfer_reason,
                "transfer_time": datetime.utcnow().isoformat(),
            }

            # 更新权属信息
            ownership_record["owner_id"] = new_owner_id
            ownership_record["updated_at"] = datetime.utcnow().isoformat()
            ownership_record["transfer_history"] = ownership_record.get("transfer_history", [])
            ownership_record["transfer_history"].append(transfer_record)

            # 更新缓存
            await self.cache_service.set(
                cache_key, ownership_record, CacheType.PERMISSION, ttl=86400
            )

            return transfer_record

        except Exception as e:
            self.logger.error(f"转移数据所有权失败: {str(e)}")
            raise BusinessLogicError(f"转移数据所有权失败: {str(e)}") from e

    # ==================== 数据质量监控 ====================

    async def monitor_data_quality(
        self,
        data_source: str,
        quality_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """监控数据质量."""
        try:
            quality_report = {
                "data_source": data_source,
                "metrics": quality_metrics,
                "quality_score": self._calculate_quality_score(quality_metrics),
                "monitored_at": datetime.utcnow().isoformat(),
                "recommendations": self._generate_quality_recommendations(quality_metrics),
            }

            # 缓存质量报告
            cache_key = f"data_quality:{data_source}:{datetime.utcnow().date()}"
            await self.cache_service.set(
                cache_key, quality_report, CacheType.SYSTEM_DATA, ttl=86400
            )

            return quality_report

        except Exception as e:
            self.logger.error(f"数据质量监控失败: {str(e)}")
            raise BusinessLogicError(f"数据质量监控失败: {str(e)}") from e

    def _calculate_quality_score(self, metrics: dict[str, Any]) -> float:
        """计算数据质量分数."""
        # 简化的质量分数计算
        completeness = metrics.get("completeness", 0)
        accuracy = metrics.get("accuracy", 0)
        consistency = metrics.get("consistency", 0)

        return float((completeness + accuracy + consistency) / 3)

    def _generate_quality_recommendations(self, metrics: dict[str, Any]) -> list[str]:
        """生成数据质量改进建议."""
        recommendations = []

        if metrics.get("completeness", 1) < 0.8:
            recommendations.append("提高数据完整性，补充缺失字段")

        if metrics.get("accuracy", 1) < 0.9:
            recommendations.append("加强数据验证，提高数据准确性")

        if metrics.get("consistency", 1) < 0.85:
            recommendations.append("统一数据格式，保持数据一致性")

        return recommendations
