from app.services.fpl.news_cache import FPLNewsCache
from app.crud.fpl_news import get_articles_by_gameweek
from app.db.session import get_db
from app.core.logging import logger
from app.core.config import settings
from typing import List, Dict, Optional


class FPLNewsRetriever:
    """
    Retrieves FPL news articles with cache-first strategy
    1. Check Redis cache (fast)
    2. Fall back to PostgreSQL (slower but reliable)
    """
    
    @staticmethod
    async def get_current_gameweek_news() -> Optional[List[Dict]]:
        """
        Get news for current gameweek
        Tries cache first, then database
        
        Returns:
            List of article dictionaries or None
        """
        gameweek = settings.CURRENT_GAMEWEEK
        season = settings.CURRENT_FPL_SEASON
        
        logger.info(f"Retrieving news for GW{gameweek} {season}")
        
        # Try cache first
        cached_articles = await FPLNewsCache.get_cached_articles(gameweek, season)
        
        if cached_articles:
            logger.info(f"Cache HIT: Found {len(cached_articles)} articles in Redis")
            return cached_articles
        
        # Cache miss - fetch from database
        logger.info("Cache MISS: Fetching from PostgreSQL")
        
        async for db in get_db():
            db_articles = await get_articles_by_gameweek(db, gameweek, season)
            
            if db_articles:
                # Convert to dict format
                articles = [
                    {
                        "id": article.id,
                        "title": article.title,
                        "url": article.url,
                        "content": article.content,
                        "summary": article.summary,
                        "tags": article.tags,
                        "gameweek": article.gameweek,
                        "season": article.season,
                        "published_at": article.published_at.isoformat() if article.published_at else None,
                        "scraped_at": article.scraped_at.isoformat() if article.scraped_at else None
                    }
                    for article in db_articles
                ]
                
                # Re-cache for next time
                await FPLNewsCache.cache_articles(gameweek, season, db_articles)
                logger.info(f"Database: Found {len(articles)} articles and re-cached")
                
                return articles
            
            break
        
        logger.warning(f"No articles found for GW{gameweek} {season}")
        return None
    
    @staticmethod
    def format_for_agent(articles: List[Dict], max_articles: int = 10) -> str:
        """
        Format articles into a readable string for the AI agent
        
        Args:
            articles: List of article dictionaries
            max_articles: Maximum number to include (default 10)
        
        Returns:
            Formatted string with article content
        """
        if not articles:
            return "No FPL news articles found for the current gameweek."
        
        gameweek = settings.CURRENT_GAMEWEEK
        season = settings.CURRENT_FPL_SEASON
        
        # Sort by scraped_at (most recent first)
        sorted_articles = sorted(
            articles, 
            key=lambda x: x.get('scraped_at', ''), 
            reverse=True
        )[:max_articles]
        
        formatted = f"=== FPL SCOUT NEWS ({season} Season, Gameweek {gameweek}) ===\n\n"
        formatted += f"Found {len(sorted_articles)} recent articles:\n\n"
        
        for i, article in enumerate(sorted_articles, 1):
            formatted += f"--- Article {i}: {article['title']} ---\n"
            formatted += f"URL: {article['url']}\n"
            formatted += f"Tags: {', '.join(article.get('tags', []))}\n\n"
            
            # Use summary for brevity, full content if summary unavailable
            content = article.get('content', '')
            formatted += f"{content}\n\n"
            formatted += "-" * 80 + "\n\n"
        
        return formatted
    
    @classmethod
    async def get_formatted_news(cls, max_articles: int = 10) -> str:
        """
        Convenience method: Get current gameweek news formatted for agent
        
        Args:
            max_articles: Maximum number of articles to return
        
        Returns:
            Formatted string ready for AI agent
        """
        articles = await cls.get_current_gameweek_news()
        return cls.format_for_agent(articles, max_articles)