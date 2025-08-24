---
inclusion: always
---

# 代码生成模板和最佳实践

## TypeScript/React 组件模板

### 标准React组件模板
```typescript
import React, { useState, useEffect, useCallback } from 'react';
import { Box, Button, Text, Alert } from '@mantine/core';
import { useQuery, useMutation } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';

interface ComponentProps {
  // 明确定义所有props的类型
  id: string;
  onSuccess?: (data: ResultType) => void;
  onError?: (error: Error) => void;
}

interface ComponentState {
  // 定义组件内部状态类型
  loading: boolean;
  error: string | null;
  data: DataType | null;
}

export const ComponentName: React.FC<ComponentProps> = ({
  id,
  onSuccess,
  onError
}) => {
  // 状态管理
  const [state, setState] = useState<ComponentState>({
    loading: false,
    error: null,
    data: null
  });

  // API查询
  const { data, isLoading, error } = useQuery({
    queryKey: ['componentData', id],
    queryFn: () => fetchData(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5分钟
  });

  // API变更
  const mutation = useMutation({
    mutationFn: updateData,
    onSuccess: (data) => {
      notifications.show({
        title: 'Success',
        message: 'Operation completed successfully',
        color: 'green',
      });
      onSuccess?.(data);
    },
    onError: (error) => {
      notifications.show({
        title: 'Error',
        message: error.message,
        color: 'red',
      });
      onError?.(error);
    },
  });

  // 事件处理
  const handleSubmit = useCallback(async () => {
    try {
      await mutation.mutateAsync({ id });
    } catch (error) {
      console.error('Submit failed:', error);
    }
  }, [id, mutation]);

  // 错误处理
  if (error) {
    return (
      <Alert color="red" title="Error">
        {error.message}
      </Alert>
    );
  }

  return (
    <Box>
      <Text>Component content</Text>
      <Button 
        onClick={handleSubmit}
        loading={mutation.isPending}
        disabled={!id}
      >
        Submit
      </Button>
    </Box>
  );
};
```##
# API服务模板
```typescript
// API服务标准模板
import { z } from 'zod';

// 请求/响应类型定义
const RequestSchema = z.object({
  id: z.string(),
  data: z.object({
    // 定义具体字段
  }),
});

const ResponseSchema = z.object({
  success: z.boolean(),
  data: z.object({
    // 定义响应数据结构
  }),
  message: z.string().optional(),
});

type RequestType = z.infer<typeof RequestSchema>;
type ResponseType = z.infer<typeof ResponseSchema>;

// API服务类
export class APIService {
  private baseURL: string;
  private timeout: number;

  constructor(baseURL: string, timeout = 30000) {
    this.baseURL = baseURL;
    this.timeout = timeout;
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new APIError(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data as T;
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new TimeoutError('Request timeout');
      }
      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'GET',
    });
  }
}

// 错误类定义
export class APIError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'APIError';
  }
}

export class TimeoutError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'TimeoutError';
  }
}
```

## Python FastAPI 服务模板

### 标准API端点模板
```python
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, validator
import logging

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.service_name import ServiceName

# 路由器
router = APIRouter(prefix="/api/v1/endpoint", tags=["endpoint"])
logger = logging.getLogger(__name__)

# 请求/响应模型
class RequestModel(BaseModel):
    """请求模型 - 严格类型定义"""
    field1: str
    field2: int
    field3: Optional[str] = None
    
    @validator('field1')
    def validate_field1(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Field1 cannot be empty')
        return v.strip()
    
    @validator('field2')
    def validate_field2(cls, v):
        if v <= 0:
            raise ValueError('Field2 must be positive')
        return v

class ResponseModel(BaseModel):
    """响应模型 - 严格类型定义"""
    id: int
    data: dict
    message: str
    success: bool = True
    
    class Config:
        from_attributes = True

# API端点实现
@router.post("/", response_model=ResponseModel)
async def create_resource(
    request: RequestModel,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel:
    """创建资源 - 完整的错误处理和日志"""
    try:
        # 1. 权限验证
        if not current_user.has_permission("create_resource"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        
        # 2. 业务逻辑验证
        service = ServiceName(db)
        await service.validate_creation_rules(request, current_user.id)
        
        # 3. 执行业务逻辑
        result = await service.create_resource(request, current_user.id)
        
        # 4. 记录操作日志
        logger.info(
            "Resource created successfully",
            extra={
                "user_id": current_user.id,
                "resource_id": result.id,
                "request_data": request.dict()
            }
        )
        
        # 5. 返回结果
        return ResponseModel(
            id=result.id,
            data=result.to_dict(),
            message="Resource created successfully"
        )
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}", extra={"user_id": current_user.id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except PermissionError as e:
        logger.warning(f"Permission denied: {e}", extra={"user_id": current_user.id})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error: {e}",
            extra={"user_id": current_user.id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{resource_id}", response_model=ResponseModel)
async def get_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ResponseModel:
    """获取资源 - 标准查询实现"""
    try:
        service = ServiceName(db)
        
        # 权限检查
        await service.check_read_permission(resource_id, current_user.id)
        
        # 获取资源
        resource = await service.get_resource(resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        return ResponseModel(
            id=resource.id,
            data=resource.to_dict(),
            message="Resource retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### 服务层模板
```python
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
import logging

from app.models.model_name import ModelName
from app.core.exceptions import BusinessLogicError, ValidationError

class ServiceName:
    """服务类 - 标准业务逻辑实现"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def create_resource(
        self,
        data: Dict[str, Any],
        user_id: int
    ) -> ModelName:
        """创建资源 - 完整的事务处理"""
        async with self.db.begin():
            try:
                # 1. 数据验证
                validated_data = await self._validate_creation_data(data)
                
                # 2. 业务规则检查
                await self._check_business_rules(validated_data, user_id)
                
                # 3. 创建实体
                resource = ModelName(**validated_data, created_by=user_id)
                self.db.add(resource)
                await self.db.flush()  # 获取ID但不提交
                
                # 4. 关联数据处理
                await self._handle_related_data(resource, validated_data)
                
                # 5. 提交事务
                await self.db.commit()
                
                # 6. 记录日志
                self.logger.info(
                    f"Resource created: {resource.id}",
                    extra={"user_id": user_id, "resource_id": resource.id}
                )
                
                return resource
                
            except Exception as e:
                await self.db.rollback()
                self.logger.error(f"Failed to create resource: {e}")
                raise
    
    async def get_resource(
        self,
        resource_id: int,
        include_related: bool = False
    ) -> Optional[ModelName]:
        """获取资源 - 优化的查询实现"""
        try:
            query = select(ModelName).where(ModelName.id == resource_id)
            
            if include_related:
                query = query.options(
                    selectinload(ModelName.related_field)
                )
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error(f"Failed to get resource {resource_id}: {e}")
            raise
    
    async def update_resource(
        self,
        resource_id: int,
        data: Dict[str, Any],
        user_id: int
    ) -> ModelName:
        """更新资源 - 乐观锁和版本控制"""
        async with self.db.begin():
            try:
                # 1. 获取现有资源
                resource = await self.get_resource(resource_id)
                if not resource:
                    raise ValidationError("Resource not found")
                
                # 2. 权限检查
                await self._check_update_permission(resource, user_id)
                
                # 3. 数据验证
                validated_data = await self._validate_update_data(data, resource)
                
                # 4. 更新资源
                for key, value in validated_data.items():
                    setattr(resource, key, value)
                
                resource.updated_by = user_id
                resource.version += 1  # 版本控制
                
                await self.db.commit()
                
                self.logger.info(
                    f"Resource updated: {resource.id}",
                    extra={"user_id": user_id, "resource_id": resource.id}
                )
                
                return resource
                
            except Exception as e:
                await self.db.rollback()
                self.logger.error(f"Failed to update resource {resource_id}: {e}")
                raise
    
    async def delete_resource(
        self,
        resource_id: int,
        user_id: int
    ) -> bool:
        """删除资源 - 软删除实现"""
        async with self.db.begin():
            try:
                resource = await self.get_resource(resource_id)
                if not resource:
                    return False
                
                # 权限检查
                await self._check_delete_permission(resource, user_id)
                
                # 软删除
                resource.is_deleted = True
                resource.deleted_by = user_id
                resource.deleted_at = datetime.utcnow()
                
                await self.db.commit()
                
                self.logger.info(
                    f"Resource deleted: {resource.id}",
                    extra={"user_id": user_id, "resource_id": resource.id}
                )
                
                return True
                
            except Exception as e:
                await self.db.rollback()
                self.logger.error(f"Failed to delete resource {resource_id}: {e}")
                raise
    
    # 私有辅助方法
    async def _validate_creation_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证创建数据"""
        # 实现数据验证逻辑
        return data
    
    async def _check_business_rules(self, data: Dict[str, Any], user_id: int) -> None:
        """检查业务规则"""
        # 实现业务规则检查
        pass
    
    async def _handle_related_data(self, resource: ModelName, data: Dict[str, Any]) -> None:
        """处理关联数据"""
        # 实现关联数据处理
        pass
    
    async def _check_update_permission(self, resource: ModelName, user_id: int) -> None:
        """检查更新权限"""
        # 实现权限检查逻辑
        pass
    
    async def _validate_update_data(
        self, 
        data: Dict[str, Any], 
        resource: ModelName
    ) -> Dict[str, Any]:
        """验证更新数据"""
        # 实现更新数据验证
        return data
    
    async def _check_delete_permission(self, resource: ModelName, user_id: int) -> None:
        """检查删除权限"""
        # 实现删除权限检查
        pass
```

## 数据模型模板

### SQLAlchemy模型模板
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any

from app.core.database import Base

class ModelName(Base):
    """模型类 - 标准字段和方法"""
    __tablename__ = "table_name"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 业务字段
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    status = Column(String(20), default="active", index=True)
    
    # 外键关系
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 审计字段
    created_by = Column(Integer, ForeignKey("users.id"))
    updated_by = Column(Integer, ForeignKey("users.id"))
    deleted_by = Column(Integer, ForeignKey("users.id"))
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    
    # 软删除
    is_deleted = Column(Boolean, default=False, index=True)
    
    # 版本控制
    version = Column(Integer, default=1)
    
    # 关系定义
    user = relationship("User", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 - 标准序列化方法"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, name='{self.name}')>"
```

## 测试模板

### 前端测试模板
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MantineProvider } from '@mantine/core';
import { ComponentName } from './ComponentName';

// 测试工具函数
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MantineProvider>
        {children}
      </MantineProvider>
    </QueryClientProvider>
  );
};

// Mock数据
const mockData = {
  id: '1',
  name: 'Test Item',
  status: 'active',
};

// Mock API
jest.mock('../api/service', () => ({
  fetchData: jest.fn(),
  updateData: jest.fn(),
}));

describe('ComponentName', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly with valid props', async () => {
    const mockFetchData = require('../api/service').fetchData;
    mockFetchData.mockResolvedValue(mockData);

    render(
      <ComponentName id="1" />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Test Item')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    const mockFetchData = require('../api/service').fetchData;
    mockFetchData.mockImplementation(() => new Promise(() => {}));

    render(
      <ComponentName id="1" />,
      { wrapper: createWrapper() }
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    const mockFetchData = require('../api/service').fetchData;
    mockFetchData.mockRejectedValue(new Error('API Error'));

    render(
      <ComponentName id="1" />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('handles user interactions', async () => {
    const mockUpdateData = require('../api/service').updateData;
    mockUpdateData.mockResolvedValue({ success: true });

    const onSuccess = jest.fn();

    render(
      <ComponentName id="1" onSuccess={onSuccess} />,
      { wrapper: createWrapper() }
    );

    const button = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockUpdateData).toHaveBeenCalledWith({ id: '1' });
      expect(onSuccess).toHaveBeenCalled();
    });
  });
});
```

### 后端测试模板
```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, AsyncMock

from app.main import app
from app.models.model_name import ModelName
from app.core.deps import get_db, get_current_user

# 测试夹具
@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session():
    # 创建测试数据库会话
    pass

@pytest.fixture
def mock_user():
    user = Mock()
    user.id = 1
    user.has_permission = Mock(return_value=True)
    return user

# API测试
class TestResourceAPI:
    """资源API测试 - 完整场景覆盖"""
    
    async def test_create_resource_success(self, client: AsyncClient, mock_user):
        """测试成功创建资源"""
        # 覆盖依赖
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        # 测试数据
        request_data = {
            "name": "Test Resource",
            "description": "Test Description"
        }
        
        # 执行请求
        response = await client.post("/api/v1/endpoint/", json=request_data)
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test Resource"
    
    async def test_create_resource_validation_error(self, client: AsyncClient, mock_user):
        """测试创建资源验证错误"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        # 无效数据
        request_data = {
            "name": "",  # 空名称
            "description": "Test Description"
        }
        
        response = await client.post("/api/v1/endpoint/", json=request_data)
        
        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"]
    
    async def test_create_resource_permission_denied(self, client: AsyncClient):
        """测试权限拒绝"""
        mock_user = Mock()
        mock_user.has_permission = Mock(return_value=False)
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        request_data = {"name": "Test Resource"}
        response = await client.post("/api/v1/endpoint/", json=request_data)
        
        assert response.status_code == 403
        assert "Permission denied" in response.json()["detail"]
    
    async def test_get_resource_success(self, client: AsyncClient, mock_user):
        """测试成功获取资源"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        response = await client.get("/api/v1/endpoint/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
    
    async def test_get_resource_not_found(self, client: AsyncClient, mock_user):
        """测试资源不存在"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        response = await client.get("/api/v1/endpoint/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

# 服务测试
class TestResourceService:
    """资源服务测试 - 业务逻辑测试"""
    
    @pytest.fixture
    def service(self, db_session):
        return ResourceService(db_session)
    
    async def test_create_resource_success(self, service, db_session):
        """测试成功创建资源"""
        data = {
            "name": "Test Resource",
            "description": "Test Description"
        }
        
        result = await service.create_resource(data, user_id=1)
        
        assert result.name == "Test Resource"
        assert result.created_by == 1
    
    async def test_create_resource_business_rule_violation(self, service):
        """测试业务规则违反"""
        data = {
            "name": "Duplicate Name",  # 假设名称重复
            "description": "Test Description"
        }
        
        with pytest.raises(BusinessLogicError):
            await service.create_resource(data, user_id=1)
    
    async def test_get_resource_with_relations(self, service):
        """测试获取资源及关联数据"""
        result = await service.get_resource(1, include_related=True)
        
        assert result is not None
        assert hasattr(result, 'related_field')
    
    async def test_update_resource_optimistic_locking(self, service):
        """测试乐观锁更新"""
        # 模拟并发更新场景
        resource1 = await service.get_resource(1)
        resource2 = await service.get_resource(1)
        
        # 第一个更新成功
        await service.update_resource(1, {"name": "Updated 1"}, user_id=1)
        
        # 第二个更新应该失败（版本冲突）
        with pytest.raises(ConcurrencyError):
            await service.update_resource(1, {"name": "Updated 2"}, user_id=2)
```

这些模板提供了完整的代码生成标准，确保生成的代码具有：
1. 严格的类型安全
2. 完整的错误处理
3. 全面的测试覆盖
4. 标准的日志记录
5. 合理的性能优化
6. 清晰的代码结构
## API
网关代码模板

### API网关路由转发模板
```python
# backend/app/core/gateway.py
from typing import Dict, Any
import httpx
from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)

# 微服务路由映射
MICROSERVICE_ROUTES = {
    "/api/v1/auth": "http://user-service:8001",
    "/api/v1/users": "http://user-service:8001",
    "/api/v1/permissions": "http://user-service:8001",
    "/api/v1/courses": "http://course-service:8002",
    "/api/v1/classes": "http://course-service:8002",
    "/api/v1/resources": "http://course-service:8002",
    "/api/v1/training": "http://training-service:8003",
    "/api/v1/questions": "http://training-service:8003",
    "/api/v1/analytics": "http://training-service:8003",
    "/api/v1/ai": "http://ai-service:8004",
    "/api/v1/generate": "http://ai-service:8004",
    "/api/v1/notifications": "http://notification-service:8005",
    "/api/v1/messages": "http://notification-service:8005"
}

class APIGateway:
    """API网关核心类"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.service_health = {}
    
    async def route_request(self, request: Request) -> Response:
        """路由请求到对应的微服务"""
        try:
            # 1. 解析请求路径
            path = request.url.path
            target_service = self._find_target_service(path)
            
            if not target_service:
                raise HTTPException(status_code=404, detail="Service not found")
            
            # 2. 检查服务健康状态
            if not await self._check_service_health(target_service):
                raise HTTPException(status_code=503, detail="Service unavailable")
            
            # 3. 转发请求
            response = await self._forward_request(request, target_service)
            
            # 4. 记录请求日志
            await self._log_request(request, response, target_service)
            
            return response
            
        except Exception as e:
            logger.error(f"Gateway routing failed: {e}")
            raise HTTPException(status_code=500, detail="Gateway error")
    
    def _find_target_service(self, path: str) -> str:
        """根据路径找到目标服务"""
        for route_prefix, service_url in MICROSERVICE_ROUTES.items():
            if path.startswith(route_prefix):
                return service_url
        return None
    
    async def _check_service_health(self, service_url: str) -> bool:
        """检查服务健康状态"""
        try:
            health_url = f"{service_url}/health"
            response = await self.client.get(health_url, timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False
    
    async def _forward_request(self, request: Request, target_service: str) -> Response:
        """转发请求到目标服务"""
        # 构建目标URL
        target_url = f"{target_service}{request.url.path}"
        if request.url.query:
            target_url += f"?{request.url.query}"
        
        # 准备请求头（移除Host头）
        headers = dict(request.headers)
        headers.pop('host', None)
        
        # 读取请求体
        body = await request.body()
        
        # 发送请求
        response = await self.client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body
        )
        
        # 返回响应
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    
    async def _log_request(self, request: Request, response: Response, service: str):
        """记录请求日志"""
        logger.info(
            f"Gateway: {request.method} {request.url.path} -> {service} "
            f"[{response.status_code}] {len(response.body) if response.body else 0}bytes"
        )

# 网关中间件
async def gateway_middleware(request: Request) -> Response:
    """网关中间件入口"""
    gateway = APIGateway()
    return await gateway.route_request(request)
```

### 微服务健康检查模板
```python
# services/{service-name}/app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
import asyncio
import time

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """应用健康检查端点"""
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION,
        "timestamp": int(time.time()),
        "checks": {}
    }
    
    try:
        # 数据库连接检查
        await db.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time": f"{(time.time() - start_time) * 1000:.2f}ms"
        }
        
        # Redis连接检查（如果使用）
        if hasattr(settings, 'REDIS_URL'):
            redis_start = time.time()
            # Redis连接检查逻辑
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "response_time": f"{(time.time() - redis_start) * 1000:.2f}ms"
            }
        
        # 外部服务检查（如AI服务）
        if hasattr(settings, 'EXTERNAL_SERVICES'):
            for service_name, service_url in settings.EXTERNAL_SERVICES.items():
                service_start = time.time()
                try:
                    # 外部服务健康检查
                    health_status["checks"][service_name] = {
                        "status": "healthy",
                        "response_time": f"{(time.time() - service_start) * 1000:.2f}ms"
                    }
                except Exception:
                    health_status["checks"][service_name] = {
                        "status": "unhealthy",
                        "error": "Connection failed"
                    }
        
        # 计算总响应时间
        health_status["response_time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        
        return health_status
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        
        return health_status
```

### 微服务间通信模板
```python
# services/shared/http_client.py
import httpx
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class MicroserviceClient:
    """微服务间HTTP通信客户端"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.base_url = settings.MICROSERVICES.get(service_name)
        if not self.base_url:
            raise ValueError(f"Service {service_name} not configured")
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={"X-Service-Client": settings.SERVICE_NAME}
        )
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET请求"""
        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {self.service_name}{endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling {self.service_name}{endpoint}: {e}")
            raise
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST请求"""
        try:
            response = await self.client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {self.service_name}{endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling {self.service_name}{endpoint}: {e}")
            raise
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT请求"""
        try:
            response = await self.client.put(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {self.service_name}{endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling {self.service_name}{endpoint}: {e}")
            raise
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE请求"""
        try:
            response = await self.client.delete(endpoint)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling {self.service_name}{endpoint}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling {self.service_name}{endpoint}: {e}")
            raise
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()

# 使用示例
class UserServiceClient(MicroserviceClient):
    """用户服务客户端"""
    
    def __init__(self):
        super().__init__("user-service")
    
    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """获取用户信息"""
        return await self.get(f"/api/v1/users/{user_id}")
    
    async def verify_permissions(self, user_id: int, permission: str) -> bool:
        """验证用户权限"""
        try:
            result = await self.post("/api/v1/permissions/verify", {
                "user_id": user_id,
                "permission": permission
            })
            return result.get("has_permission", False)
        except Exception:
            return False

class AIServiceClient(MicroserviceClient):
    """AI服务客户端"""
    
    def __init__(self):
        super().__init__("ai-service")
    
    async def generate_questions(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成题目"""
        return await self.post("/api/v1/generate/questions", request_data)
    
    async def grade_writing(self, writing_data: Dict[str, Any]) -> Dict[str, Any]:
        """批改作文"""
        return await self.post("/api/v1/ai/grade-writing", writing_data)
```

### 微服务配置模板
```python
# services/{service-name}/app/core/config.py
import os
from typing import Dict, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """微服务配置"""
    
    # 服务基本信息
    SERVICE_NAME: str = "user-service"  # 根据实际服务修改
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务端口
    PORT: int = 8001  # 根据实际服务修改
    
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@postgres:5432/cet4_learning"
    )
    
    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # 其他微服务地址
    MICROSERVICES: Dict[str, str] = {
        "user-service": "http://user-service:8001",
        "course-service": "http://course-service:8002",
        "training-service": "http://training-service:8003",
        "ai-service": "http://ai-service:8004",
        "notification-service": "http://notification-service:8005",
    }
    
    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 外部服务配置（如AI服务）
    EXTERNAL_SERVICES: Dict[str, str] = {}
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

这些模板确保了API网关+微服务架构的正确实现，包括：

1. **API网关路由转发**：统一入口和智能路由
2. **微服务健康检查**：标准化的健康检查端点
3. **服务间通信**：类型安全的HTTP客户端
4. **配置管理**：标准化的微服务配置

使用这些模板可以确保所有微服务都遵循统一的架构标准和最佳实践。