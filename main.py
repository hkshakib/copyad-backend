# main.py - FastAPI backend for CopyAd Admin Panel

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import jwt
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://copyad-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Supabase credentials and initialize client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
security = HTTPBearer()

# ----------------------------
# Helper: Decode JWT from Supabase and extract user info
# ----------------------------
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
        print("❌ JWT decode failed:", str(e))
        raise HTTPException(status_code=401, detail="Invalid token")

# ----------------------------
# Schema for Role Update
# ----------------------------
class RoleUpdateRequest(BaseModel):
    user_id: str
    new_role: str

# ----------------------------
# Route: Health check
# ----------------------------
@app.get("/")
def root():
    return {"message": "CopyAd API is running", "docs": "/docs"}

# ----------------------------
# Route: Get all users (admin only)
# ----------------------------
@app.get("/admin/users")
def get_users(current_user: dict = Depends(get_current_user)):
    print("🔐 Accessed by:", current_user)

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
        print("❌ Supabase error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch users")

# ----------------------------
# Route: Update user role (admin only)
# ----------------------------
@app.post("/admin/update-role")
def update_user_role(data: RoleUpdateRequest, current_user: dict = Depends(get_current_user)):
    print("🔧 Update role request by:", current_user)

    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        supabase.auth.admin.update_user_by_id(
            data.user_id,
            {"user_metadata": {"role": data.new_role}}
        )
        return {"status": "success"}
    except Exception as e:
        print("❌ Role update failed:", str(e))
        raise HTTPException(status_code=500, detail="Failed to update role")
