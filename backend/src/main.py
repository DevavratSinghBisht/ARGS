# The FastAPI app will be hosted wherever you run it.
# By default, if you run this file with: uvicorn src.main:app --reload
# It will be available at: http://127.0.0.1:8000
# The endpoint /get-prediction will be at: http://127.0.0.1:8000/get-prediction

import os
import shutil
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse

from predict import getPrediction
from reportGenerator import ReportGenerator
from cheXpert import CheXpert
from summarizer import ClinicalTextSummarizer
from utils import get_medical_studies

app = FastAPI()

report_generator = ReportGenerator()
chexpert = CheXpert()
summarizer = ClinicalTextSummarizer()

@app.post("/get-prediction")
async def process_image_text(
    uid: str = Form(...),
    lateralImage: UploadFile = File(...),
    frontalImage: UploadFile = File(...),
    indications: str = Form(...),
    maxStudies: int = Form(5, description="Maximum number of medical studies to return")
):
    
    # Create a directory to save uploaded images if it doesn't exist
    upload_dir = "assets/uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # Save lateral image
    lateral_path = os.path.join(upload_dir, f"{uid}_lateral_{lateralImage.filename}")
    with open(lateral_path, "wb") as buffer:
        shutil.copyfileobj(lateralImage.file, buffer)

    # Save frontal image
    frontal_path = os.path.join(upload_dir, f"{uid}_frontal_{frontalImage.filename}")
    with open(frontal_path, "wb") as buffer:
        shutil.copyfileobj(frontalImage.file, buffer)

    data = [
      {"uid": uid,
        "lateral_images": [lateral_path],
        "frontal_images": [frontal_path],
        "indications": indications}
      ]

    # Call getPrediction with the saved image paths, indications, and uid
    result = getPrediction(
        data=data,
        report_generator=report_generator,
        chexpert=chexpert,
        summarizer=summarizer
    )

    print("Final Result:", result)


    result[0]['medical_studies'] = get_medical_studies(indications + result[0]['findings'] + result[0]['impression'], max_results=maxStudies)

    print("Final Result:", result)

    
    # Clean up uploaded files after processing
    os.remove(lateral_path)
    os.remove(frontal_path)
    
    return JSONResponse(content=result)
