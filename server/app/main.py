from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import motor.motor_asyncio
from beanie import init_beanie
from datetime import datetime
from api import images
from config import settings

# Import all Beanie models
from models.user import User
from models.store import Store
from models.image import Image
from models.shelf_analysis import ShelfAnalysis
from models.sku_reference import SKUReference
from models.panogram import Planogram
    
app = FastAPI(title="MAssist Shelf SDK", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
database = client[settings.DATABASE_NAME]

@app.on_event("startup")
async def init_db():
    """Initialize Beanie with document models"""
    await init_beanie(
        database=database,
        document_models=[
            User,
            Store,
            Image,
            ShelfAnalysis,
            SKUReference,
            Planogram
        ]
    )

# Routes
app.include_router(images.router, prefix="/api/images")

@app.get("/")
async def root():
    return {"message": "MAssist API", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint to verify API and database connectivity"""
    try:
        # Check database connectivity
        await database.command("ping")
        
        # Check if collections exist (optional)
        collections = await database.list_collection_names()
        
        return {
            "status": "healthy",
            "message": "API is running and database is connected",
            "database": {
                "connected": True,
                "name": settings.DATABASE_NAME,
                "collections_count": len(collections)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Database connection failed",
            "error": str(e),
            "database": {
                "connected": False,
                "name": settings.DATABASE_NAME
            },
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)