from langchain_core.tools import tool
from app.core.config import settings
from app.core.logging import logger
from app.services.fpl.news_retriever import FPLNewsRetriever


@tool
async def retrieve_scout_selection_advice(user_input: str) -> str:
    """
    Get FPL scout selection content from cached database.
    Fast, reliable, and uses your own scraped data.
    
    Examples:
    - "What are the best picks for gameweek 11?"
    - "Show me latest scout recommendations"
    - "Best differential picks this week"
    - "Scout captain picks"

    Args:
        user_input: Query about FPL scout recommendations

    Returns:
        str: Formatted FPL news articles for the current gameweek
    """
    
    try:
        logger.info(f"Scout Picks Query: {user_input}")
        
        # Get formatted news from cache/database
        formatted_news = await FPLNewsRetriever.get_formatted_news(max_articles=15)
        
        if "No FPL news articles found" in formatted_news:
            logger.warning("No cached articles available")
            return (
                f"No scout news available for Gameweek {settings.CURRENT_GAMEWEEK}. "
                "Please run the scraper to fetch the latest articles."
            )
        
        logger.info("Successfully retrieved scout news from cache/database")
        return formatted_news
        
    except Exception as e:
        logger.error(f"Error in scout picks tool: {str(e)}")
        return f"Error retrieving scout recommendations: {str(e)}"