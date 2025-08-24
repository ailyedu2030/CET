"""用户认证相关的API端点."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.users.models import User
from app.users.schemas.auth_schemas import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    UserProfile,
)
from app.users.services.auth_service import AuthService
from app.users.utils.auth_decorators import get_current_active_user

router = APIRouter(prefix="/auth", tags=["用户认证"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录",
    description="用户登录认证，支持学生、教师、管理员三种角色",
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """用户登录端点."""
    try:
        service = AuthService(db)
        result = await service.authenticate_user(
            username=request.username,
            password=request.password,
            user_type=request.user_type,
        )
        return LoginResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试",
        ) from e


@router.post(
    "/logout",
    summary="用户登出",
    description="用户登出，清除会话信息",
    dependencies=[Depends(get_current_active_user)],
)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """用户登出端点."""
    try:
        service = AuthService(db)
        await service.logout_user_by_id(current_user.id)
        return {"message": "登出成功"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="登出失败"
        ) from e


@router.get(
    "/profile",
    response_model=UserProfile,
    summary="获取用户档案",
    description="获取当前用户的详细档案信息",
    dependencies=[Depends(get_current_active_user)],
)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """获取用户档案端点."""
    try:
        service = AuthService(db)
        profile = await service.get_user_profile(current_user.id)
        return UserProfile(**profile)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取用户档案失败"
        ) from e


@router.put(
    "/profile",
    response_model=UserProfile,
    summary="更新用户档案",
    description="更新当前用户的档案信息",
    dependencies=[Depends(get_current_active_user)],
)
async def update_user_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """更新用户档案端点."""
    try:
        service = AuthService(db)
        profile = await service.update_user_profile(
            current_user.id, request.model_dump(exclude_unset=True)
        )
        return UserProfile(**profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新用户档案失败"
        ) from e


@router.post(
    "/change-password",
    summary="修改密码",
    description="用户修改登录密码",
    dependencies=[Depends(get_current_active_user)],
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """修改密码端点."""
    try:
        service = AuthService(db)
        await service.change_password(
            user_id=current_user.id,
            old_password=request.old_password,
            new_password=request.new_password,
        )
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="密码修改失败"
        ) from e


@router.get(
    "/verify-token",
    summary="验证Token",
    description="验证当前访问令牌的有效性",
    dependencies=[Depends(get_current_active_user)],
)
async def verify_token(
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """验证Token端点."""
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "user_type": current_user.user_type.value,
        "is_verified": current_user.is_verified,
        "last_login": (current_user.last_login.isoformat() if current_user.last_login else None),
    }


@router.get(
    "/session-info",
    summary="获取会话信息",
    description="获取当前用户的会话统计信息",
    dependencies=[Depends(get_current_active_user)],
)
async def get_session_info(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """获取会话信息端点."""
    try:
        service = AuthService(db)
        session_info = await service.get_session_info(current_user.id)
        return session_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取会话信息失败"
        ) from e
