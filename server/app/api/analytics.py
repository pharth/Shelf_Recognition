from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ultralytics import YOLO
import easyocr
from PIL import Image
import numpy as np
import io
import os

# ---------------------------
# Router instead of app
# ---------------------------
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Get the current file's directory and construct the model path
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "..", "ml", "models", "best.pt")

# Init models
yolo_model = YOLO(model_path)   # your trained YOLO model
reader = easyocr.Reader(['en'])         # OCR model

class SKUResponse(BaseModel):
    OSA: float
    SOS: float
    found: int
    expected: int
    total_boxes: int

@router.post("/analyze", response_model=SKUResponse)
async def analyze_sku(
    file: UploadFile = File(...),
    expected: int = Form(...),
    search_text: str = Form(default="VI-JOHN")
):
    # Load image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    # Stage 1: YOLO
    results = yolo_model.predict(np.array(image))
    res_img = results[0].plot()   # numpy array with bounding boxes drawn

    # Save it with OpenCV - fix the output path as well
    output_path = "output.jpg"  # Since client is mounted to /app/client
    Image.fromarray(res_img).save(output_path)
    
    boxes = results[0].boxes
    num_boxes = len(boxes)

    # Stage 2: OCR
    ocr_results = reader.readtext(np.array(image))
    print("OCR Results:", ocr_results)

    count = sum(1 for (_, text, prob) in ocr_results if search_text.upper() in text.upper())

    # Metrics
    osa = count / expected if expected > 0 else 0.0
    sos = count / num_boxes if num_boxes > 0 else 0.0

    return SKUResponse(
        OSA=round(osa, 3),
        SOS=round(sos, 3),
        found=count,
        expected=expected,
        total_boxes=num_boxes
    )

@router.get("/output-image")
async def get_output_image():
    """
    Simple endpoint to serve the output.jpg file
    """
    output_path = "output.jpg"
    
    # Check if file exists
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output image not found")
    
    return FileResponse(
        path=output_path,
        media_type="image/jpeg",
        filename="output.jpg"
    )