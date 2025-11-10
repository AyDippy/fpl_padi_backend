from app.services.redis_cache import Cache
from app.core.logging import logger
from app.core.config import settings
from typing import List, Optional, Dict
import json


class FPLNewsCache:
    """
    Redis cache manager for FPL news articles
    Caches current gameweek articles for fast retrieval
    """
    
    @staticmethod
    def _get_cache_key(gameweek: int, season: str) -> str:
        """Generate Redis key for gameweek articles"""
        return f"fpl:news:gw:{gameweek}:season:{season}"
    
    @staticmethod
    def _get_current_gw_key() -> str:
        """Key to track current gameweek"""
        return "fpl:news:current_gw"
    
    @classmethod
    async def cache_articles(
        cls, 
        gameweek: int, 
        season: str, 
        articles: List[Dict]
    ) -> bool:
        """
        Cache articles for a specific gameweek
        
        Args:
            gameweek: Gameweek number
            season: Season string (e.g., "2025/2026")
            articles: List of article dictionaries from database
        
        Returns:
            True if cached successfully
        """
        try:
            cache_key = cls._get_cache_key(gameweek, season)
            
            # Convert articles to JSON-serializable format
            articles_data = [
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
                for article in articles
            ]
            
            # Store as JSON
            json_data = json.dumps(articles_data)
            success = await Cache.set(cache_key, json_data)
            
            if success:
                # Also store current gameweek reference
                await Cache.set(
                    cls._get_current_gw_key(), 
                    f"{gameweek}:{season}"
                )
                logger.info(f"Cached {len(articles)} articles for GW{gameweek} {season}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error caching articles: {str(e)}")
            return False
    
    @classmethod
    async def get_cached_articles(
        cls, 
        gameweek: int, 
        season: str
    ) -> Optional[List[Dict]]:
        """
        Retrieve cached articles for a gameweek
        
        Args:
            gameweek: Gameweek number
            season: Season string
        
        Returns:
            List of article dictionaries or None if not cached
        """
        try:
            cache_key = cls._get_cache_key(gameweek, season)
            cached_data = await Cache.get(cache_key)
            
            if cached_data:
                articles = json.loads(cached_data)
                logger.info(f"Retrieved {len(articles)} articles from cache (GW{gameweek})")
                return articles
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached articles: {str(e)}")
            return None
    
    @classmethod
    async def get_current_gameweek_articles(cls) -> Optional[List[Dict]]:
        """
        Get articles for current gameweek from cache
        Uses environment variables for current GW and season
        
        Returns:
            List of article dictionaries or None
        """
        gameweek = settings.CURRENT_GAMEWEEK
        season = settings.CURRENT_FPL_SEASON
        
        return await cls.get_cached_articles(gameweek, season)
    
    @classmethod
    async def clear_gameweek_cache(cls, gameweek: int, season: str) -> bool:
        """
        Clear cache for a specific gameweek
        Useful when new articles are scraped
        
        Args:
            gameweek: Gameweek number
            season: Season string
        
        Returns:
            True if cleared successfully
        """
        try:
            cache_key = cls._get_cache_key(gameweek, season)
            
            # Delete the cache key
            success = await Cache.delete(cache_key)
            
            if success:
                logger.info(f"Cleared cache for GW{gameweek} {season}")
            else:
                logger.warning(f"No cache found for GW{gameweek} {season}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    @classmethod
    async def clear_current_gameweek_cache(cls) -> bool:
        """
        Clear cache for the current gameweek
        Convenience method that uses env variables
        
        Returns:
            True if cleared successfully
        """
        gameweek = settings.CURRENT_GAMEWEEK
        season = settings.CURRENT_FPL_SEASON
        
        return await cls.clear_gameweek_cache(gameweek, season)