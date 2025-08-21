from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime
import uuid
import motor.motor_asyncio
from config import settings

router = APIRouter()

# Database connection
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
db = client[settings.DATABASE_NAME]

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    store_id: str = Form(...),
    user_id: str = Form(...)
):
    """Upload single image"""
    try:
        # Generate ID
        image_id = str(uuid.uuid4())
        
        # Read image data
        image_data = await file.read()
        
        # Save to database
        image_record = {
            "id": image_id,
            "user_id": user_id,
            "store_id": store_id,
            "filename": file.filename,
            "upload_time": datetime.utcnow(),
            "status": "uploaded"
        }
        
        await db.images.insert_one(image_record)
        
        return {
            "image_id": image_id,
            "status": "uploaded",
            "message": "Image uploaded successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stitch")
async def stitch_images(
    files: List[UploadFile] = File(...),
    store_id: str = Form(...),
    user_id: str = Form(...)
):
    """Stitch multiple images"""
    try:
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 images allowed")
        
        image_id = str(uuid.uuid4())
        
        # Read all images
        image_data_list = []
        for file in files:
            data = await file.read()
            image_data_list.append(data)
        
        # Save record
        image_record = {
            "id": image_id,
            "user_id": user_id,
            "store_id": store_id,
            "image_count": len(files),
            "upload_time": datetime.utcnow(),
            "status": "stitched"
        }
        
        await db.images.insert_one(image_record)
        
        return {
            "image_id": image_id,
            "status": "stitched",
            "message": f"Successfully stitched {len(files)} images"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{image_id}")
async def get_analysis(image_id: str):
    """Get image analysis results"""
    try:
        # Find image
        image = await db.images.find_one({"id": image_id})
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Mock analysis results for now
        analysis = {
            "image_id": image_id,
            "osa_percent": 85.5,
            "sos_percent": 42.3,
            "planogram_compliance": True,
            "analysis_time": datetime.utcnow(),
            "status": "completed"
        }
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{user_id}")
async def get_history(user_id: str, limit: int = 10):
    """Get user's image history"""
    try:
        cursor = db.images.find({"user_id": user_id}).sort("upload_time", -1).limit(limit)
        images = await cursor.to_list(length=limit)
        
        return {"images": images, "total": len(images)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{image_id}")
async def delete_image(image_id: str):
    """Delete image"""
    try:
        result = await db.images.delete_one({"id": image_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return {"message": "Image deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))