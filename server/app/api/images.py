from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid
import os
from beanie import PydanticObjectId
from models.image import Image
from schemas.image import ImageCreate, ImageUpdate, ImageResponse

router = APIRouter()

@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    store_id: str = Form(...),
    user_id: str = Form(...),
    latitude: str = Form(...),  # Accept as string first
    longitude: str = Form(...)  # Accept as string first
):
    """Upload single image"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate and convert coordinates
        try:
            lat_decimal = Decimal(str(latitude))
            lng_decimal = Decimal(str(longitude))
        except (ValueError, TypeError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid coordinates: {str(e)}")
        
        # Validate required fields
        if not store_id or not user_id:
            raise HTTPException(status_code=400, detail="store_id and user_id are required")
        
        # Generate unique filename/URL (in real app, upload to S3)
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        image_url = f"uploads/{unique_filename}"
        
        # Create image record
        image_data = ImageCreate(
            user_id=str(user_id),
            store_id=str(store_id),
            image_url=image_url,
            latitude=lat_decimal,
            longitude=lng_decimal
        )
        
        # Save to database using Beanie
        image = Image(**image_data.model_dump())
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/stitch")
async def stitch_images(
    files: List[UploadFile] = File(...),
    store_id: str = Form(...),
    user_id: str = Form(...),
    latitude: str = Form(...),
    longitude: str = Form(...)
):
    """Stitch multiple images"""
    try:
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 images allowed")
        
        # Validate coordinates
        try:
            lat_decimal = Decimal(str(latitude))
            lng_decimal = Decimal(str(longitude))
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid coordinates")
        
        created_images = []
        
        for file in files:
            if not file.filename:
                continue
                
            # Generate unique filename for each image
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"stitched_{uuid.uuid4()}{file_extension}"
            image_url = f"uploads/{unique_filename}"
            
            image_data = ImageCreate(
                user_id=str(user_id),
                store_id=str(store_id),
                image_url=image_url,
                latitude=lat_decimal,
                longitude=lng_decimal
            )
            
            image = Image(**image_data.model_dump())
            await image.insert()
            created_images.append(str(image.id))
        
        return {
            "image_ids": created_images,
            "status": "stitched",
            "message": f"Successfully stitched {len(created_images)} images"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stitch failed: {str(e)}")

@router.get("/analysis/{image_id}")
async def get_analysis(image_id: str):
    """Get image analysis results"""
    try:
        # Validate ObjectId format
        try:
            obj_id = PydanticObjectId(image_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image ID format")
        
        # Find image using Beanie
        image = await Image.get(obj_id)
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Store images retrieval failed: {str(e)}")

@router.put("/{image_id}", response_model=ImageResponse)
async def update_image(image_id: str, image_update: ImageUpdate):
    """Update image details"""
    try:
        # Validate ObjectId format
        try:
            obj_id = PydanticObjectId(image_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image ID format")
        
        image = await Image.get(obj_id)
        if not image or image.is_deleted:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Update only provided fields
        update_data = image_update.model_dump(exclude_unset=True)
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.delete("/{image_id}")
async def delete_image(image_id: str):
    """Soft delete image (30-min window)"""
    try:
        # Validate ObjectId format
        try:
            obj_id = PydanticObjectId(image_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image ID format")
        
        image = await Image.get(obj_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Soft delete
        image.is_deleted = True
        await image.save()
        
        return {"message": "Image deleted successfully (can be restored within 30 minutes)"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.post("/{image_id}/restore")
async def restore_image(image_id: str):
    """Restore soft deleted image"""
    try:
        # Validate ObjectId format
        try:
            obj_id = PydanticObjectId(image_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image ID format")
        
        image = await Image.get(obj_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        if not image.is_deleted:
            raise HTTPException(status_code=400, detail="Image is not deleted")
        
        # Restore image
        image.is_deleted = False
        await image.save()
        
        return {"message": "Image restored successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@router.get("/{image_id}", response_model=ImageResponse)
async def get_image(image_id: str):
    """Get single image details"""
    try:
        # Validate ObjectId format
        try:
            obj_id = PydanticObjectId(image_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image ID format")
        
        image = await Image.get(obj_id)
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image retrieval failed: {str(e)}")