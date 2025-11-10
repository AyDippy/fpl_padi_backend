from app.services.fpl.news_scraper import scrape_fpl_news
from app.services.fpl.news_cache import FPLNewsCache
from app.crud.fpl_news import create_article, article_exists, get_articles_by_gameweek
from app.schemas.fpl_news import FPLNewsCreate
from app.db.session import get_db
from app.core.logging import logger
from app.core.config import settings


async def save_fpl_news_to_db(gameweek: int, season: str, max_articles: int = 20):
    """
    Scrape FPL news, save to database, and cache in Redis
    
    Args:
        gameweek: Current gameweek number
        season: Current season (e.g., "2025/2026")
        max_articles: How many articles to scrape (default 20)
    
    Returns:
        Dictionary with stats: {'saved': 10, 'skipped': 5, 'failed': 0}
    """
    logger.info(f"Starting scrape for GW{gameweek} {season}")
    
    stats = {'saved': 0, 'skipped': 0, 'failed': 0}
    
    # Step 1: Scrape articles from website
    articles = await scrape_fpl_news(max_articles)
    
    if not articles:
        logger.warning("No articles scraped")
        return stats
    
    # Step 2: Save each article to database
    async for db in get_db():
        for article in articles:
            try:
                url = article['url']
                title = article['title']
                content = article['content']
                
                # Check if article already exists
                if await article_exists(db, url):
                    logger.info(f"Article already exists: {title[:50]}...")
                    stats['skipped'] += 1
                    continue
                
                # Create summary (first 300 characters)
                summary = content[:300] + "..." if len(content) > 300 else content
                
                # Get tags from article (already scraped)
                tags = article.get('tags', ["Fantasy Premier League"])
                
                # Get published date if available
                published_at = article.get('published_at')
                
                # Create article object
                new_article = FPLNewsCreate(
                    title=title,
                    url=url,
                    content=content,
                    summary=summary,
                    tags=tags,
                    gameweek=gameweek,
                    season=season,
                    published_at=published_at
                )
                
                # Save to database
                saved_article = await create_article(db, new_article)
                
                if saved_article:
                    logger.info(f"Saved: {title[:50]}...")
                    stats['saved'] += 1
                else:
                    logger.error(f"Failed to save: {title}")
                    stats['failed'] += 1
                    
            except Exception as e:
                logger.error(f"Error saving article: {str(e)}")
                stats['failed'] += 1
        
        # Step 3: Update Redis cache
        if stats['saved'] > 0:
            logger.info("Updating Redis cache...")
            try:
                # Clear old cache first
                await FPLNewsCache.clear_gameweek_cache(gameweek, season)
                
                # Get all articles for this gameweek from DB
                cached_articles = await get_articles_by_gameweek(db, gameweek, season)
                
                # Cache them
                cache_success = await FPLNewsCache.cache_articles(
                    gameweek=gameweek,
                    season=season,
                    articles=cached_articles
                )
                
                if cache_success:
                    logger.info(f"Successfully cached {len(cached_articles)} articles to Redis")
                else:
                    logger.warning("Failed to cache articles (Redis might be unavailable)")
                    
            except Exception as e:
                logger.error(f"Error caching articles: {str(e)}")
        
        break  # Exit after first db session
    
    logger.info(f"Scraping complete: {stats}")
    return stats


async def scrape_current_gameweek():
    """
    Scrape news for current gameweek (uses .env variables)
    """
    gameweek = settings.CURRENT_GAMEWEEK
    season = settings.CURRENT_FPL_SEASON
    
    logger.info(f"Scraping current gameweek: GW{gameweek} {season}")
    
    return await save_fpl_news_to_db(
        gameweek=gameweek,
        season=season,
        max_articles=20
    )


# Test the scraper
if __name__ == "__main__":
    import asyncio
    import sys
    from app.services.redis_cache import Cache
    
    async def test():
        try:
            stats = await scrape_current_gameweek()
            print(f"Results: {stats}")
            return stats
        finally:
            # Close Redis connection properly
            await Cache.close()
    
    # Fix event loop error on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")