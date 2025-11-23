import base64
from fastapi import UploadFile, HTTPException
from app.core.logging import logger

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp", "image/jpg"]

async def validate_image(file: UploadFile) -> bool:
    """
    Validate uploaded image file
    """
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        logger.warning(f"Invalid file type: {file.content_type}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    return True

async def process_image_to_base64(file: UploadFile) -> str:
    """
    Read image file and convert to base64 string
    """
    try:
        # Read file content
        content = await file.read()
        
        # Check size
        if len(content) > MAX_FILE_SIZE:
            logger.warning(f"File too large: {len(content)} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size is {MAX_FILE_SIZE/1024/1024}MB"
            )
            
        # Convert to base64
        encoded_string = base64.b64encode(content).decode("utf-8")
        
        # Reset file cursor just in case
        await file.seek(0)
        
        return encoded_string
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process image")