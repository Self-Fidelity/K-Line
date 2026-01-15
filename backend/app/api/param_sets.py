"""参数集管理API"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.auth import get_current_user_id
from backend.app.models.param_sets import (
    ParamSetCreate,
    ParamSetResponse,
    ParamSetListResponse,
    SetDefaultRequest
)
from backend.app.services.param_sets_service import ParamSetsService

router = APIRouter()
param_sets_service = ParamSetsService()


@router.post("/param-sets", response_model=ParamSetResponse)
async def create_param_set(
    param_set: ParamSetCreate,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """创建参数集"""
    try:
        param_set_id = param_sets_service.create_param_set(param_set)
        if not param_set_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="保存参数集失败"
            )
        
        # 获取创建的参数集并返回
        result = param_sets_service.get_param_set_by_id(param_set_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取参数集失败"
            )
        
        return ParamSetResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建参数集失败: {str(e)}"
        )


@router.get("/param-sets/{stock_code}/{strategy_name}", response_model=ParamSetListResponse)
async def get_param_sets(
    stock_code: str,
    strategy_name: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取参数集列表"""
    try:
        param_sets = param_sets_service.get_param_sets(stock_code, strategy_name)
        return ParamSetListResponse(
            param_sets=[ParamSetResponse(**ps) for ps in param_sets],
            total=len(param_sets)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取参数集列表失败: {str(e)}"
        )


@router.get("/param-sets/id/{param_set_id}", response_model=ParamSetResponse)
async def get_param_set(
    param_set_id: int,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """根据ID获取参数集"""
    try:
        param_set = param_sets_service.get_param_set_by_id(param_set_id)
        if not param_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"参数集 {param_set_id} 不存在"
            )
        return ParamSetResponse(**param_set)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取参数集失败: {str(e)}"
        )


@router.delete("/param-sets/{param_set_id}")
async def delete_param_set(
    param_set_id: int,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """删除参数集"""
    try:
        success = param_sets_service.delete_param_set(param_set_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除参数集失败"
            )
        return {"status": "success", "message": "参数集已删除"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除参数集失败: {str(e)}"
        )


@router.put("/param-sets/{param_set_id}/set-default")
async def set_default_param_set(
    param_set_id: int,
    request: SetDefaultRequest,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """设置默认参数集"""
    try:
        success = param_sets_service.set_default_param_set(
            param_set_id,
            request.stock_code,
            request.strategy_name
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="设置默认参数集失败"
            )
        return {"status": "success", "message": "已设置为默认参数集"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置默认参数集失败: {str(e)}"
        )


@router.get("/param-sets/{stock_code}/{strategy_name}/default", response_model=ParamSetResponse)
async def get_default_param_set(
    stock_code: str,
    strategy_name: str,
    current_user_id: Annotated[int, Depends(get_current_user_id)] = None,
):
    """获取默认参数集"""
    try:
        param_set = param_sets_service.get_default_param_set(stock_code, strategy_name)
        if not param_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到默认参数集"
            )
        return ParamSetResponse(**param_set)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取默认参数集失败: {str(e)}"
        )
