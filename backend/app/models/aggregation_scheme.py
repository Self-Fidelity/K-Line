from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AggregationSchemeCreate(BaseModel):
    name: str
    description: str = ""
    stock_code: Optional[str] = None
    strategies: List[Dict[str, Any]]  # List of {name, weight, params}
    buy_threshold: float
    sell_threshold: float
    required_strategies: List[str]

class AggregationScheme(AggregationSchemeCreate):
    id: int
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
