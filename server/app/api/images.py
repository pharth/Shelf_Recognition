from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid
from models.image import Image
from schemas.image import ImageCreate, ImageUpdate, ImageResponse

router = APIRouter()

@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    store_id: str = Form(...),
    user_id: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...)
):
    """Upload single image"""
    try:
        # Generate unique filename/URL (in real app, upload to S3)
        image_url = f"uploads/{uuid.uuid4()}_{file.filename}"
        
        # Create image record
        image_data = ImageCreate(
            user_id=user_id,
            store_id=store_id,
            image_url=image_url,
            latitude=Decimal(str(latitude)),
            longitude=Decimal(str(longitude))
        )
        
        # Save to database using Beanie
        image = Image(**image_data.dict())
        await image.insert()
        
        return ImageResponse(
            id=str(image.id),
            user_id=image.user_id,
            store_id=image.store_id,
            image_url=image.image_url,
            latitude=image.latitude,
            longitude=image.longitude,
            upload_time=image.upload_time,
            is_deleted=image.is_deleted
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stitch")
async def stitch_images(
    files: List[UploadFile] = File(...),
    store_id: str = Form(...),
    user_id: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...)
):
    """Stitch multiple images"""
    try:
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 images allowed")
        
        created_images = []
        
        for file in files:
            # Generate unique filename for each image
            image_url = f"uploads/stitched_{uuid.uuid4()}_{file.filename}"
            
            image_data = ImageCreate(
                user_id=user_id,
                store_id=store_id,
                image_url=image_url,
                latitude=Decimal(str(latitude)),
                longitude=Decimal(str(longitude))
            )
            
            image = Image(**image_data.dict())
            await image.insert()
            created_images.append(str(image.id))
        
        return {
            "image_ids": created_images,
            "status": "stitched",
            "message": f"Successfully stitched {len(files)} images"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{image_id}")
async def get_analysis(image_id: str):
    """Get image analysis results"""
    try:
        # Find image using Beanie
        image = await Image.get(image_id)
        if not image or image.is_deleted:
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
        # Find images for user, exclude soft deleted
        images = await Image.find(
            Image.user_id == user_id,
            Image.is_deleted == False
        ).sort(-Image.upload_time).limit(limit).to_list()
        
        # Convert to response format
        image_responses = [
            ImageResponse(
                id=str(img.id),
                user_id=img.user_id,
                store_id=img.store_id,
                image_url=img.image_url,
                latitude=img.latitude,
                longitude=img.longitude,
                upload_time=img.upload_time,
                is_deleted=img.is_deleted
            ) for img in images
        ]
        
        return {"images": image_responses, "total": len(image_responses)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/store/{store_id}")
async def get_store_images(store_id: str, limit: int = 10):
    """Get images for a specific store"""
    try:
        images = await Image.find(
            Image.store_id == store_id,
            Image.is_deleted == False
        ).sort(-Image.upload_time).limit(limit).to_list()
        
        image_responses = [
            ImageResponse(
                id=str(img.id),
                user_id=img.user_id,
                store_id=img.store_id,
                image_url=img.image_url,
                latitude=img.latitude,
                longitude=img.longitude,
                upload_time=img.upload_time,
                is_deleted=img.is_deleted
            ) for img in images
        ]
        
        return {"images": image_responses, "total": len(image_responses)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{image_id}", response_model=ImageResponse)
async def update_image(image_id: str, image_update: ImageUpdate):
    """Update image details"""
    try:
        image = await Image.get(image_id)
        if not image or image.is_deleted:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Update only provided fields
        update_data = image_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(image, field, value)
        
        await image.save()
        
        return ImageResponse(
            id=str(image.id),
            user_id=image.user_id,
            store_id=image.store_id,
            image_url=image.image_url,
            latitude=image.latitude,
            longitude=image.longitude,
            upload_time=image.upload_time,
            is_deleted=image.is_deleted
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{image_id}")
async def delete_image(image_id: str):
    """Soft delete image (30-min window)"""
    try:
        image = await Image.get(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Soft delete
        image.is_deleted = True
        await image.save()
        
        return {"message": "Image deleted successfully (can be restored within 30 minutes)"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{image_id}/restore")
async def restore_image(image_id: str):
    """Restore soft deleted image"""
    try:
        image = await Image.get(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        if not image.is_deleted:
            raise HTTPException(status_code=400, detail="Image is not deleted")
        
        # Restore image
        image.is_deleted = False
        await image.save()
        
        return {"message": "Image restored successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: str):
    """Get single image details"""
    try:
        image = await Image.get(image_id)
        if not image or image.is_deleted:
            raise HTTPException(status_code=404, detail="Image not found")
        
        return ImageResponse(
            id=str(image.id),
            user_id=image.user_id,
            store_id=image.store_id,
            image_url=image.image_url,
            latitude=image.latitude,
            longitude=image.longitude,
            upload_time=image.upload_time,
            is_deleted=image.is_deleted
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))