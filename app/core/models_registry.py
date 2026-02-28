"""模型注册模块 - 解决循环导入问题."""

# 在模块级别导入所有模型
# 课程相关模型
from app.courses.models import *  # noqa: F403
from app.shared.models.base_model import Base  # noqa: F401
# 训练相关模型
from app.training.models import *  # noqa: F403
# 用户相关模型
from app.users.models import *  # noqa: F403

# AI相关模型
try:
    from app.ai.models import *  # noqa: F403
except ImportError:
    # AI模块可能还未完全实现，忽略导入错误
    pass

# 资源相关模型
try:
    from app.resources.models import *  # noqa: F403
except ImportError:
    # 资源模块可能还未完全实现，忽略导入错误
    pass


def register_all_models() -> None:
    """注册所有模型以确保关系映射正确."""
    # 所有模型已在模块级别导入
    # 配置SQLAlchemy注册表以确保关系映射正确
    from sqlalchemy.orm import configure_mappers

    try:
        configure_mappers()
    except Exception as e:
        print(f"Warning: Failed to configure mappers: {e}")
