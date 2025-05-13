from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
from app.core.supabase_client import supabase, get_current_user
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter()


# ===================== MODELS =====================

class AdCreate(BaseModel):
    platform: str
    tone: str
    product: str
    description: str
    template_id: Optional[str] = None
    language: Optional[str] = "en"

class AdUpdate(BaseModel):
    platform: Optional[str]
    tone: Optional[str]
    product: Optional[str]
    description: Optional[str]
    template_id: Optional[str]
    language: Optional[str]

class AdOut(AdCreate):
    id: str
    user_id: str
    created_at: str

class GenerateRequest(BaseModel):
    template_id: str
    product: str
    feature_description: str

class CustomGenerateRequest(BaseModel):
    platform: str
    tone: str
    product: str
    description: str  # this is treated as "feature"
    language: Optional[str] = "en"

class GenerateResponse(BaseModel):
    prompt: str
    description: str


# ===================== ROUTES =====================

@router.post("/", response_model=AdOut)
def create_ad(ad: AdCreate, user=Depends(get_current_user)):
    try:
        ad_id = str(uuid4())
        response = supabase.table("generated_ads").insert({
            "id": ad_id,
            "user_id": user.id,
            "platform": ad.platform,
            "tone": ad.tone,
            "product": ad.product,
            "description": ad.description,
            "template_id": ad.template_id,
            "language": ad.language,
        }).execute()
        data = response.data
        if not data:
            raise HTTPException(status_code=500, detail="No data returned after insert")
        return data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))


@router.get("/", response_model=List[AdOut])
def get_ads(user=Depends(get_current_user)):
    try:
        response = supabase.from_("generated_ads").select("*").eq("user_id", user.id).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))


@router.get("/{ad_id}", response_model=AdOut)
def get_ad(ad_id: str, user=Depends(get_current_user)):
    try:
        response = supabase.from_("generated_ads").select("*").eq("id", ad_id).eq("user_id", user.id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Ad not found")
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching ad: " + str(e))


@router.put("/{ad_id}", response_model=AdOut)
def update_ad(ad_id: str, ad: AdUpdate, user=Depends(get_current_user)):
    try:
        update_data = {k: v for k, v in ad.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        response = supabase.table("generated_ads").update(update_data).eq("id", ad_id).eq("user_id", user.id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Ad not found or not updated")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating ad: " + str(e))


@router.delete("/{ad_id}")
def delete_ad(ad_id: str, user=Depends(get_current_user)):
    try:
        response = supabase.from_("generated_ads").delete().eq("id", ad_id).eq("user_id", user.id).execute()
        return {"message": "Ad deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting ad: " + str(e))


@router.post("/generate", response_model=GenerateResponse)
def generate_ad(data: GenerateRequest = Body(...), user=Depends(get_current_user)):
    try:
        template_resp = supabase.from_("templates").select("*").eq("id", data.template_id).single().execute()
        template = template_resp.data
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        filled_prompt = template["prompt"].format(
            product=data.product,
            feature_description=data.feature_description
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": filled_prompt}],
            max_tokens=120
        )
        generated_ad = response.choices[0].message.content.strip()

        ad_id = str(uuid4())
        insert_result = supabase.table("generated_ads").insert({
            "id": ad_id,
            "user_id": user.id,
            "platform": template["platform"],
            "tone": template["tone"],
            "product": data.product,
            "description": generated_ad,
            "template_id": data.template_id,
            "language": "en"
        }).execute()

        if not insert_result.data:
            raise HTTPException(status_code=500, detail="Failed to save ad")

        return {
            "prompt": filled_prompt,
            "description": generated_ad
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generating ad: " + str(e))


@router.post("/custom-generate", response_model=GenerateResponse)
def custom_generate_ad(data: AdCreate, user=Depends(get_current_user)):
    try:
        print("Received data:", data)
        print("User:", user)

        prompt = f"Write a {data.tone} {data.platform} ad about {data.product} that highlights {data.description}."
        print("Generated prompt:", prompt)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        generated = response.choices[0].message.content.strip()

        ad_id = str(uuid4())
        supabase.table("generated_ads").insert({
            "id": ad_id,
            "user_id": user.id,
            "platform": data.platform,
            "tone": data.tone,
            "product": data.product,
            "description": generated,
            "language": data.language or "en"
        }).execute()

        return {"prompt": prompt, "description": generated}

    except Exception as e:
        print("❌ Error in /custom-generate:", e)
        raise HTTPException(status_code=500, detail="Error generating ad: " + str(e))