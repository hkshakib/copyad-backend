from fastapi import APIRouter, Header, HTTPException
from app.auth.supabase_auth import verify_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/me")
async def get_logged_in_user(authorization: str = Header(...)):
    # Remove "Bearer " prefix
    token = authorization.replace("Bearer ", "")

    # Verify token
    user = await verify_token(token)

    return {
        "email": user.get("email"),
        "user_id": user.get("id")
    }
