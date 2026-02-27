"""
CrowdGuardian Sentinel - AI Crowd Analysis Model
Uses YOLOv8 for person detection and crowd density classification.
"""

import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import io
import base64

# Load YOLOv8 model (medium version for better accuracy)
model = YOLO("yolov8m.pt")

def analyze_image(image_bytes):
    """
    Analyze an image for crowd density.
    
    Args:
        image_bytes: Raw image bytes
    
    Returns:
        dict with analysis results
    """
    # Convert bytes to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"error": "Could not decode image"}
    
    h, w = img.shape[:2]
    
    # Run YOLOv8 detection with optimized thresholds for crowds
    # Lower confidence to detect partially visible people, stricter IOU to handle overlaps
    results = model(img, conf=0.15, iou=0.45, verbose=False)
    
    # Filter for "person" class (class 0 in COCO)
    persons = []
    for result in results:
        for box in result.boxes:
            if int(box.cls[0]) == 0:  # person class
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                persons.append({
                    "x1": x1, "y1": y1,
                    "x2": x2, "y2": y2,
                    "confidence": round(confidence, 2)
                })
    
    people_count = len(persons)
    
    # Calculate physical space occupancy (estimated percentage of screen filled by people)
    total_area = h * w
    person_area = sum([(p["x2"] - p["x1"]) * (p["y2"] - p["y1"]) for p in persons])
    occupancy = min(round((person_area / total_area) * 100, 1), 100)
    
    # Classify density dynamically: High risk requires BOTH high count (>50) AND high spatial constraint (small area)
    if people_count >= 50 and occupancy >= 45.0:
        density_level = "HIGH"
        density_color = "#ff3e3e"
        recommendation = "⚠️ Danger: Critical mass detected (50+ people) in a constrained space. Alert triggered."
    elif (people_count >= 25 and occupancy >= 30.0) or occupancy >= 40.0:
        density_level = "MODERATE"
        density_color = "#ff7b00"
        recommendation = "⚡ Monitor closely: Space is moderately filled or people count is rising in a compact zone."
    else:
        density_level = "LOW"
        density_color = "#37ff8b"
        recommendation = "✅ Area clear: Safe conditions. Substantial open space available for movement."
    
    # Generate annotated image with bounding boxes
    annotated_img = img.copy()
    for p in persons:
        x1, y1, x2, y2 = int(p["x1"]), int(p["y1"]), int(p["x2"]), int(p["y2"])
        # Draw bounding box
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), (0, 255, 213), 2)
        # Draw label background
        label = f"Person {p['confidence']}"
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        cv2.rectangle(annotated_img, (x1, y1 - lh - 6), (x1 + lw, y1), (0, 255, 213), -1)
        cv2.putText(annotated_img, label, (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    # Generate heatmap
    heatmap = generate_heatmap(img, persons)
    
    # Blend heatmap with original
    blended = cv2.addWeighted(annotated_img, 0.7, heatmap, 0.3, 0)
    
    # Encode result image to base64
    _, buffer = cv2.imencode('.jpg', blended, [cv2.IMWRITE_JPEG_QUALITY, 90])
    result_image_b64 = base64.b64encode(buffer).decode('utf-8')
    
    return {
        "people_count": people_count,
        "density_level": density_level,
        "density_color": density_color,
        "occupancy": occupancy,
        "recommendation": recommendation,
        "bounding_boxes": persons,
        "result_image": result_image_b64,
        "image_width": w,
        "image_height": h
    }


def generate_heatmap(img, persons):
    """Generate a crowd density heatmap overlay."""
    h, w = img.shape[:2]
    heatmap = np.zeros((h, w), dtype=np.float32)
    
    for p in persons:
        cx = int((p["x1"] + p["x2"]) / 2)
        cy = int((p["y1"] + p["y2"]) / 2)
        radius = int(max(p["x2"] - p["x1"], p["y2"] - p["y1"]) * 1.5)
        cv2.circle(heatmap, (cx, cy), radius, 1.0, -1)
    
    # Apply Gaussian blur for smooth heatmap
    heatmap = cv2.GaussianBlur(heatmap, (0, 0), sigmaX=40, sigmaY=40)
    
    # Normalize
    if heatmap.max() > 0:
        heatmap = heatmap / heatmap.max()
    
    # Apply colormap
    heatmap_colored = cv2.applyColorMap((heatmap * 255).astype(np.uint8), cv2.COLORMAP_JET)
    
    return heatmap_colored


def analyze_video_frame(video_bytes):
    """
    Analyze the first frame of a video for crowd density.
    
    Args:
        video_bytes: Raw video bytes
    
    Returns:
        dict with analysis results
    """
    import tempfile
    import os
    
    # Save video to temp file
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name
    
    try:
        cap = cv2.VideoCapture(tmp_path)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return {"error": "Could not read video frame"}
        
        # Encode frame as image bytes and analyze
        _, buffer = cv2.imencode('.jpg', frame)
        return analyze_image(buffer.tobytes())
    finally:
        os.unlink(tmp_path)
