from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
from app.core.supabase_client import supabase, get_current_user

router = APIRouter()

class AdCreate(BaseModel):
    platform: str
    tone: str
    product: str
    ad_text: str
    template_id: Optional[str] = None
    language: Optional[str] = "en"

class AdUpdate(BaseModel):
    platform: Optional[str]
    tone: Optional[str]
    product: Optional[str]
    ad_text: Optional[str]
    template_id: Optional[str]
    language: Optional[str]

class AdOut(AdCreate):
    id: str
    user_id: str
    created_at: str

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
            "ad_text": ad.ad_text,
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
