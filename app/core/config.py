from dotenv import load_dotenv
from pydantic_settings import BaseSettings

import os

load_dotenv()

class Settings(BaseSettings):
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    JWT_SECRET: str = os.getenv("JWT_SECRET")
    ALLOWED_ORIGINS: list = ["http://localhost:5173", "https://copyad-frontend.vercel.app"]
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str


settings = Settings()
