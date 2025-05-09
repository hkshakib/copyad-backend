from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import jwt

app = FastAPI()

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Allow frontend access
origins = [
    "http://localhost:5173",
    "https://copyad-frontend.vercel.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
# print("Loaded SUPABASE_URL:", os.getenv("SUPABASE_URL"))

# JWT secret to decode tokens
JWT_SECRET = os.getenv("JWT_SECRET")

security = HTTPBearer()

# Validate JWT token from frontend
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        user_role = payload.get("user_metadata", {}).get("role", "user")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user_id, "role": user_role}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class RoleUpdateRequest(BaseModel):
    user_id: str
    new_role: str

@app.get("/")
def root():
    return {"message": "API is running"}

@app.get("/secure/admin/users")
def secure_get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    result = supabase.auth.admin.list_users(per_page=100)
    users = result["users"]
    return [
        {
            "id": u["id"],
            "email": u["email"],
            "role": u.get("user_metadata", {}).get("role", "user")
        }
        for u in users
    ]

@app.post("/secure/admin/update-role")
def secure_update_role(data: RoleUpdateRequest, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    updated = supabase.auth.admin.update_user_by_id(
        data.user_id,
        {"user_metadata": {"role": data.new_role}}
    )
    return {"status": "success", "user": updated}
