from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, List
import base64
import os
from app.core.config import settings
from app.core.logging import logger

# Player Schema
class Player(BaseModel):
    name: Optional[str] = Field(description="Player name", default=None)
    position: Optional[str] = Field(description="Position (GKP, DEF, MID, FWD) based on pitch location", default=None)
    value: Optional[str] = Field(description="Current price shown (e.g. £6.5m)", default=None)
    next_fixture: Optional[str] = Field(description="Next opponent shown below name (e.g. 'MUN (H)')", default=None)
    is_flagged: bool = Field(description="True if player has a yellow/red injury warning triangle", default=False)
    is_captain: bool = Field(description="True if player has the (C) armband", default=False)
    is_vice_captain: bool = Field(description="True if player has the (V) armband", default=False)

# Agent Response Schema
class FPLStats(BaseModel):
    screen_type: str = Field(description="Type of screen detected: 'Transfers', 'My Team', 'Points', or 'Other'", default="Other")
    starters: Optional[List[Player]] = Field(description="List of 11 starting players on the pitch", default=None)
    bench: Optional[List[Player]] = Field(description="List of 4 bench players at the bottom", default=None)
    free_transfers: Optional[int] = Field(description="Number of free transfers available (shown in header)", default=None)
    bank: Optional[str] = Field(description="Money in the bank (shown in header)", default=None)
    formation: Optional[str] = Field(description="Detected formation (e.g., '3-4-3')", default=None)
    chip_active: Optional[str] = Field(description="Active chip if visible (e.g., 'Wildcard', 'Free Hit')", default=None)

async def extract_squad_data(base64_image: str) -> dict:
    """
    Extracts FPL squad data using Google GenAI with structured output.
    """
    try:
        logger.info("Initializing Gemini Vision extraction with google-genai...")
        
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        # Decode base64 string to bytes
        image_bytes = base64.b64decode(base64_image)
        
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp", 
            contents=[
                types.Part.from_bytes(
                    data=image_bytes, 
                    mime_type="image/jpeg"
                ),
                "Analyze this FPL screenshot. First, identify the 'screen_type' (Transfers, My Team, Points). Then extract the 'starters' (11 players on pitch) and 'bench' (4 players at bottom). For each player, capture their name, position, price/value, next fixture, and any injury flags (yellow/red triangles). Also capture the bank, free transfers, and active chips if visible."
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=FPLStats,
            ),
        )
        
        # The response is already parsed into the Pydantic model
        result = response.parsed.model_dump()
        logger.info(f"Successfully extracted data: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in vision extraction: {str(e)}")
        return {
            "players": "",
            "error": str(e)
        }