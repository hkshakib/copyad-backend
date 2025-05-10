from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from app.core.config import settings

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        user_id = payload.get("sub")
        role = (payload.get("user_metadata") or {}).get("role", "user")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {"id": user_id, "role": role}
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
