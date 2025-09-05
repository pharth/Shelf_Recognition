from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ultralytics import YOLO
import boto3
from PIL import Image
import numpy as np
import io
import os
from fuzzywuzzy import fuzz
import re
import base64

# ---------------------------
# Router instead of app
# ---------------------------
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# Get the current file's directory and construct the model path
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "..", "ml", "models", "best.pt")

# Init models - LAZY LOADING
yolo_model = None

# AWS Textract client - will be initialized lazily
textract_client = None

def get_yolo_model():
    global yolo_model
    if yolo_model is None:
        yolo_model = YOLO(model_path)
    return yolo_model

def get_textract_client():
    global textract_client
    if textract_client is None:
        # Initialize AWS Textract client
        # AWS credentials should be set via environment variables:
        # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
        textract_client = boto3.client(
            'textract',
            region_name='us-east-1',  # Change this to your preferred region
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
    return textract_client

def clean_text(text):
    """Clean and preprocess text for better matching"""
    # Remove special characters, extra spaces, and normalize
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().upper()

def fuzzy_match_text(search_text, detected_text, threshold=60):
    """
    Advanced fuzzy matching with multiple methods
    Returns (is_match, best_score, method_used)
    """
    search_clean = clean_text(search_text)
    detected_clean = clean_text(detected_text)

    # Method 1: Basic ratio
    ratio_score = fuzz.ratio(search_clean, detected_clean)

    # Method 2: Partial ratio (good for substrings)
    partial_score = fuzz.partial_ratio(search_clean, detected_clean)

    # Method 3: Token sort ratio (ignores word order)
    token_sort_score = fuzz.token_sort_ratio(search_clean, detected_clean)

    # Method 4: Token set ratio (ignores duplicates and order)
    token_set_score = fuzz.token_set_ratio(search_clean, detected_clean)

    # Get the best score
    scores = {
        'ratio': ratio_score,
        'partial': partial_score,
        'token_sort': token_sort_score,
        'token_set': token_set_score
    }

    best_method = max(scores, key=scores.get)
    best_score = scores[best_method]

    return best_score >= threshold, best_score, best_method

def extract_text_with_textract(image_bytes):
    """
    Extract text from image using AWS Textract
    Returns list of detected text strings
    """
    try:
        client = get_textract_client()
        
        # Call Textract
        response = client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        
        # Extract text from response
        detected_texts = []
        
        for item in response['Blocks']:
            if item['BlockType'] == 'WORD':
                text = item['Text']
                confidence = item['Confidence']
                
                # Only include text with reasonable confidence
                if confidence > 50:  # Adjust threshold as needed
                    detected_texts.append(text)
                    
        print(f"Textract detected {len(detected_texts)} text elements")
        return detected_texts
        
    except Exception as e:
        print(f"Error with AWS Textract: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Textract error: {str(e)}")

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

    # Stage 1: YOLO - Load model lazily
    model = get_yolo_model()
    results = model.predict(np.array(image), conf=0.2, iou=0.3)
    res_img = results[0].plot()  # numpy array with bounding boxes drawn

    # Save it with OpenCV - fix the output path as well
    output_path = "output.jpg"
    Image.fromarray(res_img).save(output_path)

    boxes = results[0].boxes
    num_boxes = len(boxes)

    # Stage 2: AWS Textract OCR - PROCESS ENTIRE IMAGE ONCE (NOT individual boxes)
    print("Starting AWS Textract OCR on WHOLE IMAGE...")
    detected_texts = extract_text_with_textract(contents)
    
    print("Textract Results:", detected_texts)

    # Enhanced fuzzy matching with lower threshold
    count = 0
    threshold = 60  # Lowered from 80 to 60

    print(f"\n=== FUZZY MATCHING DEBUG ===")
    print(f"Search term: '{search_text}'")
    print(f"Threshold: {threshold}%")
    print("=" * 40)

    for text in detected_texts:
        # Try fuzzy matching with multiple methods
        is_match, best_score, method = fuzzy_match_text(search_text, text, threshold)

        print(f"Textract Text: '{text}' | Score: {best_score}% | Method: {method} | Match: {is_match}")

        if is_match:
            count += 1
            print(f"✅ MATCH FOUND: '{text}' (Score: {best_score}%, Method: {method})")

        # Fallback: Try simple substring matching as backup
        if not is_match and search_text.upper() in text.upper():
            count += 1
            print(f"✅ SUBSTRING MATCH: '{text}' contains '{search_text}'")

    print(f"=" * 40)
    print(f"Total matches found: {count}")
    print(f"=== END DEBUG ===\n")

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