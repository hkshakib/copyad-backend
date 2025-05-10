from pydantic import BaseModel
from typing import List
from datetime import datetime

class AdRequest(BaseModel):
    product_name: str
    audience: str
    goal: str

class AdResponse(BaseModel):
    id: str
    product_name: str
    audience: str
    goal: str
    generated_ad: str
    created_at: datetime

class AdListResponse(BaseModel):
    ads: List[AdResponse]
