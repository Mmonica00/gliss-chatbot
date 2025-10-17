from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form
from app.services.analysis import analyze_user_input

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.post("/analyze")
async def analyze_hair(
    message: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    if isinstance(image, str) or image is None:
        image = None
    result = await analyze_user_input(message, image)
    return result
