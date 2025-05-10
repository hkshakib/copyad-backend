from pydantic import BaseModel

class TemplateCreate(BaseModel):
    name: str
    content: str

class TemplateOut(BaseModel):
    id: str
    name: str
    content: str
    created_at: str
