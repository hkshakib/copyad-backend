from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.core.supabase_client import supabase

router = APIRouter()

class Template(BaseModel):
    id: str
    name: str
    platform: str
    tone: str
    prompt: str
    example: str
    created_at: str

@router.get("/", response_model=List[Template])
def get_templates():
    try:
        response = supabase.from_("templates").select("*").order("created_at", desc=True).execute()
        if not response.data:
            return []
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load templates: " + str(e))

@router.get("/{template_id}", response_model=Template)
def get_template(template_id: str):
    try:
        response = supabase.from_("templates").select("*").eq("id", template_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Template not found")
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch template: " + str(e))
