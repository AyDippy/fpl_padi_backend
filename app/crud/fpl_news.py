from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional
from app.models.fpl_news import FPLNews
from app.schemas.fpl_news import FPLNewsCreate, FPLNewsUpdate
from app.core.logging import logger
from app.core.config import settings


# Create a new article
async def create_article(db: AsyncSession, article: FPLNewsCreate) -> FPLNews:
    """
    Create a new FPL news article
    """
    db_article = FPLNews(
        title=article.title,
        url=article.url,
        content=article.content,
        summary=article.summary,
        tags=article.tags,
        gameweek=article.gameweek,
        season=article.season,
        published_at=article.published_at
    )
    
    db.add(db_article)
    await db.commit()
    await db.refresh(db_article)
    
    logger.info(f"Article created: {db_article.title[:50]}... (GW{db_article.gameweek})")
    return db_article


# Get article by ID
async def get_article_by_id(db: AsyncSession, article_id: int) -> Optional[FPLNews]:
    """
    Get article by ID
    """
    stmt = select(FPLNews).where(FPLNews.id == article_id)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    
    if article:
        logger.info(f"Article found: {article.title[:50]}...")
        return article
    else:
        logger.info(f"No article with ID {article_id} found")
        return None


# Get article by URL
async def get_article_by_url(db: AsyncSession, url: str) -> Optional[FPLNews]:
    """
    Get article by URL (useful for checking duplicates before scraping)
    """
    stmt = select(FPLNews).where(FPLNews.url == url)
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    
    if article:
        logger.info(f"Article already exists: {url}")
        return article
    else:
        return None


# Check if article exists by URL
async def article_exists(db: AsyncSession, url: str) -> bool:
    """
    Check if article already exists (by URL)
    Useful before scraping to avoid duplicates
    """
    article = await get_article_by_url(db, url)
    return article is not None


# Get articles by gameweek
async def get_articles_by_gameweek(
    db: AsyncSession, 
    gameweek: int, 
    season: str,
    limit: int = 50
) -> List[FPLNews]:
    """
    Get all articles for a specific gameweek and season
    Ordered by published_at (newest first)
    """
    stmt = (
        select(FPLNews)
        .where(
            and_(
                FPLNews.gameweek == gameweek,
                FPLNews.season == season
            )
        )
        .order_by(desc(FPLNews.published_at))
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    articles = result.scalars().all()
    
    logger.info(f"Found {len(articles)} articles for GW{gameweek} {season}")
    return list(articles)


# Get current gameweek articles 
async def get_current_gameweek_articles(db: AsyncSession) -> List[FPLNews]:
    """
    Get articles for the current gameweek using environment variables
    This is what we'll cache in Redis
    """
    current_gameweek = settings.CURRENT_GAMEWEEK
    current_season = settings.CURRENT_FPL_SEASON
    
    return await get_articles_by_gameweek(
        db, 
        gameweek=current_gameweek, 
        season=current_season
    )


# Get all articles for a season
async def get_articles_by_season(
    db: AsyncSession, 
    season: str,
    skip: int = 0,
    limit: int = 100
) -> List[FPLNews]:
    """
    Get all articles for a season with pagination
    """
    stmt = (
        select(FPLNews)
        .where(FPLNews.season == season)
        .order_by(desc(FPLNews.gameweek), desc(FPLNews.published_at))
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    articles = result.scalars().all()
    
    logger.info(f"Found {len(articles)} articles for season {season}")
    return list(articles)


# Get latest articles across all gameweeks
async def get_latest_articles(db: AsyncSession, limit: int = 10) -> List[FPLNews]:
    """
    Get the most recent articles across all gameweeks
    """
    stmt = (
        select(FPLNews)
        .order_by(desc(FPLNews.scraped_at))
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    articles = result.scalars().all()
    
    logger.info(f"Retrieved {len(articles)} latest articles")
    return list(articles)


# Search articles by tags
async def search_articles_by_tags(
    db: AsyncSession,
    tags: List[str],
    gameweek: Optional[int] = None,
    season: Optional[str] = None,
    limit: int = 50
) -> List[FPLNews]:
    """
    Search articles by tags (e.g., ["Scout Picks", "Captaincy"])
    Optionally filter by gameweek and season
    Uses PostgreSQL array overlap operator
    """
    stmt = select(FPLNews).where(FPLNews.tags.overlap(tags))
    
    if gameweek:
        stmt = stmt.where(FPLNews.gameweek == gameweek)
    
    if season:
        stmt = stmt.where(FPLNews.season == season)
    
    stmt = stmt.order_by(desc(FPLNews.published_at)).limit(limit)
    
    result = await db.execute(stmt)
    articles = result.scalars().all()
    
    logger.info(f"Found {len(articles)} articles with tags: {tags}")
    return list(articles)


# Update an article
async def update_article(
    db: AsyncSession, 
    article_id: int, 
    article_update: FPLNewsUpdate
) -> Optional[FPLNews]:
    """
    Update an existing article
    """
    db_article = await get_article_by_id(db, article_id)
    if not db_article:
        logger.warning(f"Cannot update: Article {article_id} not found")
        return None
    
    update_data = article_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_article, field, value)
    
    await db.commit()
    await db.refresh(db_article)
    
    logger.info(f"Article updated: {db_article.title[:50]}...")
    return db_article


# Delete an article
async def delete_article(db: AsyncSession, article_id: int) -> bool:
    """
    Delete an article by ID
    """
    db_article = await get_article_by_id(db, article_id)
    if not db_article:
        logger.warning(f"Cannot delete: Article {article_id} not found")
        return False
    
    await db.delete(db_article)
    await db.commit()
    
    logger.info(f"Article deleted: {article_id}")
    return True