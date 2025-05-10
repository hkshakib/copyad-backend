from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user
from app.core.config import settings
from app.schemas.templates import TemplateCreate, TemplateOut
from supabase import create_client
from typing import List

router = APIRouter()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
print("Running")

@router.get("/", response_model=List[TemplateOut])
def list_templates():
    try:
        response = supabase.table("templates").select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch templates")

@router.post("/", response_model=TemplateOut)
def create_template(template: TemplateCreate, user=Depends(get_current_user)):
    try:
        response = supabase.table("templates").insert({
            "name": template.name,
            "content": template.content
        }).execute()
        if response.data:
            return response.data[0]
        raise HTTPException(status_code=400, detail="Insert failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create template")
