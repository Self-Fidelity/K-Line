"""自定义策略API路由"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.auth import get_current_user_id, get_current_user
from backend.app.models.custom_strategy import (
    CustomStrategyCreate,
    CustomStrategyUpdate,
    CustomStrategyInfo,
    CustomStrategyDetail,
    CustomStrategyListResponse,
    CustomStrategyValidateRequest,
    CustomStrategyValidateResponse,
)

from backend.app.services.custom_strategy_service import CustomStrategyService
from backend.app.services.audit_log_service import AuditLogService
from backend.app.models.audit_log import AuditLogCreate
from fastapi import Request

router = APIRouter()
service = CustomStrategyService()
log_service = AuditLogService()


@router.post("", response_model=CustomStrategyInfo, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    request: Request,
    strategy_data: CustomStrategyCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """创建自定义策略"""
    try:
        user_id = current_user['id']
        username = current_user['username']
        new_strategy = service.create_strategy(user_id, strategy_data)
        
        # 记录日志
        try:
            log_service.log_event(AuditLogCreate(
                user_id=user_id,
                username=username,
                action="创建策略",
                details=f"创建了策略: {new_strategy.name}",
                ip_address=request.client.host if request.client else None
            ))
        except Exception as e:
            print(f"Failed to log strategy creation: {e}")
            
        return new_strategy
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建策略失败: {str(e)}",
        )


@router.get("", response_model=CustomStrategyListResponse)
async def list_strategies(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """获取用户的所有自定义策略"""
    try:
        strategies = service.list_strategies(current_user_id)
        return CustomStrategyListResponse(
            strategies=strategies,
            total=len(strategies),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略列表失败: {str(e)}",
        )


@router.get("/{strategy_id}", response_model=CustomStrategyDetail)
async def get_strategy(
    strategy_id: int,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """获取策略详情（包含代码）"""
    try:
        return service.get_strategy_detail(strategy_id, current_user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取策略详情失败: {str(e)}",
        )


@router.put("/{strategy_id}", response_model=CustomStrategyInfo)
async def update_strategy(
    strategy_id: int,
    strategy_data: CustomStrategyUpdate,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
):
    """更新自定义策略"""
    try:
        return service.update_strategy(strategy_id, current_user_id, strategy_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新策略失败: {str(e)}",
        )


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)

async def delete_strategy(
    strategy_id: int,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """删除自定义策略"""
    try:
        user_id = current_user['id']
        is_admin = current_user['role'] == 'admin'
        service.delete_strategy(strategy_id, user_id, is_admin=is_admin)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除策略失败: {str(e)}",
        )


@router.post("/validate", response_model=CustomStrategyValidateResponse)
async def validate_strategy_code(
    request: CustomStrategyValidateRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """验证策略代码"""
    try:
        return service.validate_strategy_code(
            request.code,
            test_data=request.test_data,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证策略代码失败: {str(e)}",
        )
