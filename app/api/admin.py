from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.auth import get_current_user
from supabase import create_client
from app.core.config import settings

router = APIRouter()

supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)

class RoleUpdateRequest(BaseModel):
    user_id: str
    new_role: str

@router.get("/users")
def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        users = supabase.auth.admin.list_users(per_page=100)
        return [
            {
                "id": user.id,
                "email": user.email,
                "role": (user.user_metadata or {}).get("role", "user")
            }
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch users")

@router.post("/update-role")
def update_user_role(data: RoleUpdateRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        supabase.auth.admin.update_user_by_id(
            data.user_id,
            {"user_metadata": {"role": data.new_role}}
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update role")

@router.get("/summary")
def admin_summary(user=Depends(get_current_user)):
    if user.user_metadata.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    user_stats = supabase.from_("user_profile").select("plan").execute()

    if not user_stats.data:
        return {"total_users": 0, "plan_distribution": {}}

    plan_counts = {}
    for user in user_stats.data:
        plan = user.get("plan", "free")
        plan_counts[plan] = plan_counts.get(plan, 0) + 1

    return {
        "total_users": len(user_stats.data),
        "plan_distribution": plan_counts,
        "monthly_revenue": (
            plan_counts.get("pro", 0) * 15 +
            plan_counts.get("enterprise", 0) * 25
        ),
        "active_subscriptions": (
            plan_counts.get("pro", 0) + plan_counts.get("enterprise", 0)
        )
    }
