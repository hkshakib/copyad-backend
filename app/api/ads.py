from fastapi import APIRouter, Depends, HTTPException
from app.schemas.ads import AdRequest, AdResponse, AdListResponse
from app.core.auth import get_current_user
from app.core.config import settings
from supabase import create_client

router = APIRouter()
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

@router.post("/", response_model=AdResponse)
def generate_ad(data: AdRequest, user=Depends(get_current_user)):
    # 🧠 Mock ad generation
    ad_text = f"Introducing {data.product_name}! Perfect for {data.audience}. {data.goal.capitalize()} today!"

    try:
        response = supabase.table("generated_ads").insert({
            "user_id": user["id"],
            "product_name": data.product_name,
            "audience": data.audience,
            "goal": data.goal,
            "generated_ad": ad_text
        }).execute()

        if response.data:
            return response.data[0]

        raise HTTPException(status_code=500, detail="Failed to save ad")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error generating ad")

@router.get("/", response_model=AdListResponse)
def get_user_ads(user=Depends(get_current_user)):
    try:
        response = supabase.table("generated_ads").select("*").eq("user_id", user["id"]).order("created_at", desc=True).execute()
        return {"ads": response.data}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch ads")
