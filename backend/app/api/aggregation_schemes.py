from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from backend.app.models.aggregation_scheme import AggregationScheme, AggregationSchemeCreate
from backend.app.services.aggregation_scheme_service import AggregationSchemeService

router = APIRouter(
    responses={404: {"description": "Not found"}},
)

service = AggregationSchemeService()

@router.post("/", response_model=dict)
async def create_scheme(scheme: AggregationSchemeCreate):
    """创建策略聚合方案"""
    scheme_id = service.create_scheme(scheme)
    if not scheme_id:
        raise HTTPException(status_code=500, detail="保存聚合方案失败")
    return {"id": scheme_id, "message": "保存成功"}

@router.get("/", response_model=List[AggregationScheme])
async def get_schemes(stock_code: Optional[str] = Query(None)):
    """获取策略聚合方案列表"""
    return service.get_schemes(stock_code)

@router.delete("/{scheme_id}")
async def delete_scheme(scheme_id: int):
    """删除策略聚合方案"""
    success = service.delete_scheme(scheme_id)
    if not success:
        raise HTTPException(status_code=500, detail="删除失败")
    return {"message": "删除成功"}
