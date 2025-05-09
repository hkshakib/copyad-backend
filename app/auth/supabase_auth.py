import httpx
from fastapi import HTTPException
from app.config import settings

async def verify_token(token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.SUPABASE_URL}/auth/v1/user", headers=headers
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return response.json()  # This is the user info
