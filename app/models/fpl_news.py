from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from app.db.session import Base


class FPLNews(Base):
    """
    FPL Scout News Articles
    Stores scraped articles from premierleague.com/en/fantasy-news
    """
    __tablename__ = "fpl_news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)  
    tags = Column(PG_ARRAY(String), nullable=True)
    gameweek = Column(Integer, nullable=False, index=True)
    season = Column(String(20), nullable=False, index=True)
    published_at = Column(TIMESTAMP(timezone=True), nullable=True) 
    scraped_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<FPLNews(id={self.id}, title='{self.title[:50]}...', gw={self.gameweek})>"