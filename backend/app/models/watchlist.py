from pydantic import BaseModel
from typing import Optional

class WatchlistBase(BaseModel):
    stock_code: str

class WatchlistCreate(WatchlistBase):
    pass

class WatchlistResponse(WatchlistBase):
    id: int
    user_id: int
    stock_name: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True

class WatchlistStatus(BaseModel):
    is_favorite: bool
