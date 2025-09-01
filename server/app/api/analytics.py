from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from ultralytics import YOLO
import easyocr
from PIL import Image
import numpy as np
import io

# ---------------------------
# Router instead of app
# ---------------------------
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Init models
yolo_model = YOLO("ml/models/best.pt")   # your trained YOLO model
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
    expected: int = Form(...)
):
    # Load image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    # Stage 1: YOLO
    results = yolo_model.predict(np.array(image))
    res_img = results[0].plot()   # numpy array with bounding boxes drawn

# Save it with OpenCV
    Image.fromarray(res_img).save("../../client/output.jpg")
    boxes = results[0].boxes
    num_boxes = len(boxes)

    # Stage 2: OCR
    ocr_results = reader.readtext(np.array(image))
    print("OCR Results:", ocr_results)

    vjohn_count = sum(1 for (_, text, prob) in ocr_results if "VI-JOHN" in text.upper())

    # Metrics
    osa = vjohn_count / expected if expected > 0 else 0.0
    sos = vjohn_count / num_boxes if num_boxes > 0 else 0.0

    return SKUResponse(
        OSA=round(osa, 3),
        SOS=round(sos, 3),
        found=vjohn_count,
        expected=expected,
        total_boxes=num_boxes
    )