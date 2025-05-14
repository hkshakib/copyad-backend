from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.core.supabase_client import get_current_user
from app.core.supabase_client import supabase
from openai import OpenAI
from uuid import uuid4
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter()

class Template(BaseModel):
    id: str
    name: str
    platform: str
    tone: str
    prompt: str
    example: str
    created_at: str

class TemplateCreate(BaseModel):
    name: str
    platform: str
    tone: str
    prompt: str
    example: str

class GenerateRequest(BaseModel):
    template_id: str
    product: str
    feature_description: str

class GenerateResponse(BaseModel):
    prompt: str
    ad_text: str

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


@router.post("/generate", response_model=GenerateResponse)
def generate_ad(data: GenerateRequest, user=Depends(get_current_user)):
    try:
        # 1. Fetch template
        template_resp = supabase.from_("templates").select("prompt").eq("id", data.template_id).single().execute()
        template = template_resp.data
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # 2. Fill in template
        filled_prompt = template["prompt"].format(
            product=data.product,
            feature_description=data.feature_description
        )

        # 3. OpenAI generate
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": filled_prompt } ],
            max_tokens=120
        )
        generated = response.choices[0].message.content.strip()

        return {
            "prompt": filled_prompt,
            "ad_text": generated
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generating ad: " + str(e))

@router.post("/")
def create_template(template: TemplateCreate, user=Depends(get_current_user)):
    try:
        new_id = str(uuid4())
        response = supabase.table("templates").insert({
            "id": new_id,
            "name": template.name,
            "platform": template.platform,
            "tone": template.tone,
            "prompt": template.prompt,
            "example": template.example
        }).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create template")

        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error creating template: " + str(e))
