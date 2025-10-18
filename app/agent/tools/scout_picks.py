from langchain_tavily import TavilySearch
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.tools import tool
from app.core.config import settings
from app.core.logging import logger
import os
from datetime import datetime, timedelta

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY

@tool
def retrieve_scout_selection_advice(user_input: str) -> str:
    """
    Get real-time FPL scout selection content using Tavily search.
    Returns raw content for the agent to process.
    
    Examples:
    - "What are the best picks for gameweek 5?"
    - "Show me latest scout recommendations"
    - "Best differential picks this week"
    - "Scout captain picks"

    Args:
        user_input: Query about FPL scout recommendations

    Returns:
        str: Raw content from FPL sources for agent processing
    """
    
    try:
        logger.info(f"Tavily Scout Query: {user_input}")

        current_season = settings.CURRENT_FPL_SEASON
        current_gameweek = settings.CURRENT_GAMEWEEK
        
        search_tool = TavilySearch(
            topic="general",
            max_results=2,
            include_answers=True,
            include_domains=[
                "https://www.premierleague.com/en/news"
            ],
            start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        )
        
        # Enhanced query
        enhanced_query = f"FPL fantasy premier league scout picks recommendations {current_season} season gameweek {current_gameweek} {user_input}"
        
        # Perform search
        search_results = search_tool.invoke({"query": enhanced_query})
        
        if not search_results.get('results'):
            logger.warning("No search results found")
            return "No recent scout recommendations found. Please try a different query."
        
        # Extract URLs and load content
        urls = [result['url'] for result in search_results['results']]
        logger.info(f"Found {len(urls)} relevant sources")
        
        loader = WebBaseLoader(urls)
        docs = loader.load()
        
        # Process and combine content
        processed_content = f"=== LATEST FPL SCOUT RECOMMENDATIONS ({current_season} Season, Gameweek {current_gameweek}) ===\n\n"
        
        for i, doc in enumerate(docs, 1):
            # Clean content
            clean_content = doc.page_content.replace("\n", " ").strip()
            source_url = doc.metadata.get('source', f'Source {i}')
            
            processed_content += f"--- Source {i}: {source_url} ---\n"
            processed_content += f"{clean_content}\n\n"
        
        logger.info("Tavily scout content retrieved successfully")
        
        return processed_content
        
    except Exception as e:
        logger.error(f"Error in Tavily scout tool: {str(e)}")
        return f"Error retrieving scout recommendations: {str(e)}"