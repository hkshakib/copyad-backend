from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import admin, templates

app = FastAPI()

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route group
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])

@app.get("/")
def root():
    print('hello')
    return {"message": "CopyAd API is running"}
