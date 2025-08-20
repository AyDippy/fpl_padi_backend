from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from app.core.config import settings
from app.core.logging import logger
import os


os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


@tool
def retrieve_scout_selection_advice(user_input: str) -> dict:
    """
    Get FPL scout selection advice from Premier League official website.
    Examples:
    - "What are the best picks for gameweek 1?"
    - "Show me scout recommendations"
    - "Best players to pick according to scouts"

    Args:
        user_input: Query about FPL scout recommendations

    Returns:
        dict with scout advice and recommendations
    """
    
    try:
        logger.info(f"Scout Query: {user_input}")
        
        # Load scout content from Premier League
        loader = WebBaseLoader("https://www.premierleague.com/en/news/4373986/scout-selection-the-best-fpl-squad-for-the-opening-gameweeks")
        docs = loader.load()
        
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
        
        # Create query with scout content
        query = f"{user_input}. Based on this scout content: {docs[0].page_content}"
        
        # Get response
        response = llm.invoke(query)
        
        logger.info("Scout advice retrieved successfully")
        
        return {
            'advice': response.content,
            'status': 'success',
            'source': 'Premier League Scout Selection'
        }
        
    except Exception as e:
        logger.error(f"Error in scout tool: {str(e)}")
        
        return {
            'advice': f"Error getting scout advice: {str(e)}",
            'status': 'error',
            'error': str(e)
        }