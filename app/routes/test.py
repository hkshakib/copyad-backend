from fastapi import APIRouter, Header, HTTPException
from app.auth.supabase_auth import verify_token

router = APIRouter(prefix="/test", tags=["Test"])

@router.get("/me")
async def get_me(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user = await verify_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"email": user.get("email"), "id": user.get("id")}
