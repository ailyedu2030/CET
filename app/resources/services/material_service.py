"""教材库管理服务."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.resources.models.resource_models import ResourceLibrary, TeachingMaterial
from app.resources.schemas.resource_schemas import (
    TeachingMaterialCreate,
    TeachingMaterialSearchRequest,
    TeachingMaterialUpdate,
)
from app.shared.models.enums import ContentType, DifficultyLevel


class MaterialService:
    """教材库管理服务."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_teaching_material(
        self, material_data: TeachingMaterialCreate, user_id: int
    ) -> TeachingMaterial:
        """创建教材."""
        # 检查资源库是否存在
        library = await self._get_library_by_id(material_data.library_id)
        if not library:
            raise ValueError(f"Resource library {material_data.library_id} not found")

        # 处理文件上传
        file_info = {}
        if material_data.file_path:
            file_info = await self._process_file_upload(material_data.file_path)

        # 创建教材记录
        material_dict = material_data.model_dump()
        material_dict.update(file_info)

        teaching_material = TeachingMaterial(**material_dict)
        self.db.add(teaching_material)
        await self.db.commit()
        await self.db.refresh(teaching_material)

        # 更新资源库统计
        await self._update_library_stats(material_data.library_id)

        return teaching_material

    async def get_teaching_material(self, material_id: int) -> TeachingMaterial | None:
        """获取教材."""
        stmt = select(TeachingMaterial).where(TeachingMaterial.id == material_id)
        result = await self.db.execute(stmt)
        material: TeachingMaterial | None = result.scalar_one_or_none()
        return material

    async def update_teaching_material(
        self,
        material_id: int,
        material_data: TeachingMaterialUpdate,
        user_id: int,
    ) -> TeachingMaterial | None:
        """更新教材."""
        teaching_material = await self.get_teaching_material(material_id)
        if not teaching_material:
            return None

        # 更新字段
        for field, value in material_data.model_dump(exclude_unset=True).items():
            setattr(teaching_material, field, value)

        await self.db.commit()
        await self.db.refresh(teaching_material)
        return teaching_material

    async def delete_teaching_material(self, material_id: int, user_id: int) -> bool:
        """删除教材."""
        teaching_material = await self.get_teaching_material(material_id)
        if not teaching_material:
            return False

        # 删除关联文件
        if teaching_material.file_path:
            await self._delete_file(teaching_material.file_path)

        library_id = teaching_material.library_id
        await self.db.delete(teaching_material)
        await self.db.commit()

        # 更新资源库统计
        await self._update_library_stats(library_id)
        return True

    async def search_teaching_materials(
        self, search_request: TeachingMaterialSearchRequest
    ) -> tuple[list[TeachingMaterial], int]:
        """搜索教材."""
        # 构建查询
        stmt = select(TeachingMaterial)

        # 添加筛选条件
        if search_request.library_id:
            stmt = stmt.where(TeachingMaterial.library_id == search_request.library_id)

        if search_request.keyword:
            keyword = f"%{search_request.keyword}%"
            stmt = stmt.where(
                or_(
                    TeachingMaterial.title.ilike(keyword),
                    TeachingMaterial.isbn.ilike(keyword),
                    TeachingMaterial.publisher.ilike(keyword),
                )
            )

        if search_request.authors:
            # 使用PostgreSQL的JSON操作符检查作者
            for author in search_request.authors:
                stmt = stmt.where(TeachingMaterial.authors.op("@>")([author]))

        if search_request.publisher:
            stmt = stmt.where(TeachingMaterial.publisher == search_request.publisher)

        if search_request.difficulty_level:
            stmt = stmt.where(TeachingMaterial.difficulty_level == search_request.difficulty_level)

        if search_request.content_type:
            stmt = stmt.where(TeachingMaterial.content_type == search_request.content_type)

        if search_request.is_primary is not None:
            stmt = stmt.where(TeachingMaterial.is_primary == search_request.is_primary)

        if search_request.tags:
            # 使用PostgreSQL的JSON操作符
            for tag in search_request.tags:
                stmt = stmt.where(TeachingMaterial.tags.op("@>")([tag]))

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total: int = total_result.scalar() or 0

        # 添加排序
        if search_request.sort_by == "title":
            order_col = TeachingMaterial.title
        elif search_request.sort_by == "publication_date":
            order_col = TeachingMaterial.publication_date
        elif search_request.sort_by == "usage_count":
            order_col = TeachingMaterial.usage_count
        elif search_request.sort_by == "rating":
            order_col = TeachingMaterial.rating
        else:
            order_col = TeachingMaterial.rating

        if search_request.sort_order == "desc":
            stmt = stmt.order_by(desc(order_col))
        else:
            stmt = stmt.order_by(order_col)

        # 分页
        offset = (search_request.page - 1) * search_request.page_size
        stmt = stmt.offset(offset).limit(search_request.page_size)

        # 执行查询
        result = await self.db.execute(stmt)
        materials = list(result.scalars().all())

        return materials, total

    async def update_material_rating(self, material_id: int, rating: float, user_id: int) -> bool:
        """更新教材评分."""
        teaching_material = await self.get_teaching_material(material_id)
        if not teaching_material:
            return False

        # 计算新的平均评分
        current_total = teaching_material.rating * teaching_material.review_count
        new_total = current_total + rating
        new_count = teaching_material.review_count + 1
        new_rating = new_total / new_count

        teaching_material.rating = new_rating
        teaching_material.review_count = new_count
        await self.db.commit()
        return True

    async def increment_usage_count(self, material_id: int) -> bool:
        """增加教材使用次数."""
        teaching_material = await self.get_teaching_material(material_id)
        if not teaching_material:
            return False

        teaching_material.usage_count += 1
        await self.db.commit()
        return True

    async def get_popular_materials(
        self, library_id: int | None = None, limit: int = 10
    ) -> list[TeachingMaterial]:
        """获取热门教材."""
        stmt = select(TeachingMaterial)

        if library_id:
            stmt = stmt.where(TeachingMaterial.library_id == library_id)

        stmt = stmt.order_by(
            desc(TeachingMaterial.rating),
            desc(TeachingMaterial.usage_count),
        ).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_primary_materials(self, library_id: int) -> list[TeachingMaterial]:
        """获取主教材."""
        stmt = (
            select(TeachingMaterial)
            .where(
                TeachingMaterial.library_id == library_id,
                TeachingMaterial.is_primary,
            )
            .order_by(desc(TeachingMaterial.rating))
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_supplementary_materials(self, library_id: int) -> list[TeachingMaterial]:
        """获取辅助教材."""
        stmt = (
            select(TeachingMaterial)
            .where(
                TeachingMaterial.library_id == library_id,
                TeachingMaterial.is_supplementary,
            )
            .order_by(desc(TeachingMaterial.rating))
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_materials_by_difficulty(
        self, library_id: int, difficulty_level: DifficultyLevel
    ) -> list[TeachingMaterial]:
        """按难度级别获取教材."""
        stmt = (
            select(TeachingMaterial)
            .where(
                TeachingMaterial.library_id == library_id,
                TeachingMaterial.difficulty_level == difficulty_level,
            )
            .order_by(desc(TeachingMaterial.rating))
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_material_statistics(self, library_id: int | None = None) -> dict[str, Any]:
        """获取教材统计信息."""
        stmt = select(TeachingMaterial)
        if library_id:
            stmt = stmt.where(TeachingMaterial.library_id == library_id)

        result = await self.db.execute(stmt)
        materials = list(result.scalars().all())

        # 统计不同类型的教材数量
        content_type_stats = {}
        for content_type in ContentType:
            content_type_stats[content_type.value] = sum(
                1 for m in materials if m.content_type == content_type
            )

        # 统计不同难度级别的教材数量
        difficulty_stats = {}
        for level in DifficultyLevel:
            difficulty_stats[level.value] = sum(1 for m in materials if m.difficulty_level == level)

        # 统计主教材和辅助教材
        primary_count = sum(1 for m in materials if m.is_primary)
        supplementary_count = sum(1 for m in materials if m.is_supplementary)

        # 评分统计
        ratings = [m.rating for m in materials if m.rating > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        # 使用统计
        total_usage = sum(m.usage_count for m in materials)
        avg_usage = total_usage / len(materials) if materials else 0

        # 文件大小统计
        total_size = sum(m.file_size for m in materials)
        avg_size = total_size / len(materials) if materials else 0

        return {
            "total_count": len(materials),
            "content_type_distribution": content_type_stats,
            "difficulty_distribution": difficulty_stats,
            "primary_materials_count": primary_count,
            "supplementary_materials_count": supplementary_count,
            "average_rating": float(avg_rating),
            "total_usage": total_usage,
            "average_usage": float(avg_usage),
            "total_file_size": total_size,
            "average_file_size": float(avg_size),
            "materials_with_files": sum(1 for m in materials if m.file_path),
        }

    async def _process_file_upload(self, file_path: str) -> dict[str, Any]:
        """处理文件上传信息."""
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        file_info = {
            "file_size": os.path.getsize(file_path),
            "file_format": Path(file_path).suffix.lower(),
        }

        # 生成预览URL和下载URL（这里只是示例，实际需要根据文件存储服务实现）
        filename = Path(file_path).name
        file_info["preview_url"] = f"/api/v1/materials/preview/{filename}"
        file_info["download_url"] = f"/api/v1/materials/download/{filename}"

        return file_info

    async def _delete_file(self, file_path: str) -> None:
        """删除文件."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            # 静默忽略文件删除错误
            pass

    async def _get_library_by_id(self, library_id: int) -> ResourceLibrary | None:
        """获取资源库."""
        stmt = select(ResourceLibrary).where(ResourceLibrary.id == library_id)
        result = await self.db.execute(stmt)
        library: ResourceLibrary | None = result.scalar_one_or_none()
        return library

    async def _update_library_stats(self, library_id: int) -> None:
        """更新资源库统计信息."""
        # 更新资源库统计信息（如果需要可以添加统计字段到模型）
        # 暂时跳过，因为ResourceLibrary模型没有total_items字段
        pass
