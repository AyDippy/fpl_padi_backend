from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FPLNewsBase(BaseModel):
    """Base schema with common fields"""
    title: str = Field(..., max_length=500)
    url: str = Field(..., max_length=1000)
    content: str
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    gameweek: int = Field(..., ge=1, le=38)
    season: str = Field(..., max_length=20) 
    published_at: Optional[datetime] = None


class FPLNewsCreate(FPLNewsBase):
    """Schema for creating new articles"""
    pass


class FPLNewsUpdate(BaseModel):
    """Schema for updating articles (all fields optional)"""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    gameweek: Optional[int] = Field(None, ge=1, le=38)
    season: Optional[str] = Field(None, max_length=20)
    published_at: Optional[datetime] = None


class FPLNewsInDB(FPLNewsBase):
    """Schema for articles in database (includes ID and scraped_at)"""
    id: int
    scraped_at: datetime

    class Config:
        from_attributes = True  


class FPLNewsResponse(FPLNewsInDB):
    """Schema for API responses"""
    pass


class FPLNewsListResponse(BaseModel):
    """Schema for listing multiple articles"""
    articles: List[FPLNewsResponse]
    total: int
    gameweek: Optional[int] = None
    season: Optional[str] = None