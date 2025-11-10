from playwright.async_api import async_playwright, Page, Browser
from typing import List, Dict, Optional
from app.core.logging import logger
from app.core.config import settings
import asyncio


class FPLNewsScraper:
    """
    Scrapes FPL Scout news from premierleague.com/en/fantasy-news
    Uses Playwright for reliable scraping
    """
    
    BASE_URL = "https://www.premierleague.com/en/fantasy-news"
    
    def __init__(self, headless: bool = True, timeout: int = 60000):
        """
        Initialize scraper
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds (default 60s)
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Start Playwright browser"""
        logger.info("Starting Playwright browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        logger.info("Browser started successfully")
    
    async def close(self):
        """Close browser and Playwright"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        logger.info("Browser closed")
    
    async def get_article_list(self, max_articles: int = 20) -> List[Dict[str, str]]:
        """
        Scrape the main news listing page for article metadata
        
        Args:
            max_articles: Maximum number of articles to fetch (default 20 = first page)
        
        Returns:
            List of dictionaries with article metadata
        """
        logger.info(f"Fetching article list from {self.BASE_URL}")
        
        try:
            # Navigate to the main news page with networkidle (wait for network to be quiet)
            logger.info("Loading page...")
            await self.page.goto(
                self.BASE_URL, 
                timeout=self.timeout,
                wait_until="domcontentloaded"  # Don't wait for everything, just DOM
            )
            
            # Wait for article cards to load
            logger.info("Waiting for article cards...")
            await self.page.wait_for_selector("a.content-card__button", timeout=self.timeout)
            
            # Give it an extra second for JS to finish
            await asyncio.sleep(2)
            
            # Extract article links
            article_links = await self.page.query_selector_all("a.content-card__button.js-button")
            
            logger.info(f"Found {len(article_links)} article links on page")
            
            articles = []
            
            for link in article_links[:max_articles]:
                try:
                    # Extract title from aria-label
                    aria_label = await link.get_attribute("aria-label")
                    if not aria_label:
                        continue
                    
                    # Remove " Content Card" suffix
                    title = aria_label.replace(" Content Card", "").strip()
                    
                    # Extract URL from href
                    relative_url = await link.get_attribute("href")
                    if not relative_url:
                        continue
                    
                    # Build full URL
                    full_url = relative_url if relative_url.startswith("http") else f"https:{relative_url}"
                    
                    # filtering url articles with videos
                    if '/video/' in full_url:
                        logger.debug(f"Skipping video URL: {title[:50]}...")
                        continue
                    
                    # Extract tags from parent (optional)
                    tags = ["Fantasy Premier League"]  # Default tag
                    
                    articles.append({
                        "title": title,
                        "url": full_url,
                        "tags": tags
                    })
                    
                    logger.debug(f"Extracted: {title[:60]}...")
                    
                except Exception as e:
                    logger.warning(f"Error extracting article link: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(articles)} article metadata (videos excluded)")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching article list: {str(e)}")
            return []
    
    async def get_article_content(self, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape full content from an individual article page
        
        Args:
            url: Full URL of the article
        
        Returns:
            Dictionary with article data
        """
        logger.info(f"Fetching article content from: {url}")
        
        try:
            # Navigate to article page
            await self.page.goto(
                url, 
                timeout=self.timeout,
                wait_until="domcontentloaded"
            )
            
            # Wait for article content
            await self.page.wait_for_selector("article", timeout=self.timeout)
            await asyncio.sleep(1)  # Let JS finish
            
            # Get all paragraphs
            paragraphs = await self.page.query_selector_all("article p")
            
            # Extract text from each paragraph
            content_parts = []
            for p in paragraphs:
                text = await p.inner_text()
                if text and len(text) > 20:  # Skip short lines
                    content_parts.append(text.strip())
            
            # Join all paragraphs
            content = "\n\n".join(content_parts)
            
            if not content:
                logger.warning(f"No content extracted from {url}")
                return None
            
            logger.info(f"Extracted {len(content)} characters")
            
            return {
                "content": content.strip(),
                "published_at": None,
                "tags": ["Fantasy Premier League"]
            }
            
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {str(e)}")
            return None


# Convenience function for one-off scraping
async def scrape_fpl_news(max_articles: int = 20) -> List[Dict]:
    """
    Convenience function to scrape FPL news
    
    Args:
        max_articles: Maximum number of articles to scrape
    
    Returns:
        List of article dictionaries with full content
    """
    async with FPLNewsScraper() as scraper:
        # Get article list
        articles = await scraper.get_article_list(max_articles)
        
        if not articles:
            return []
        
        # Fetch full content for each article
        full_articles = []
        for article in articles:
            content_data = await scraper.get_article_content(article["url"])
            if content_data:
                # Merge metadata with content
                full_article = {**article, **content_data}
                full_articles.append(full_article)
                
                # Be nice to the server
                await asyncio.sleep(2)
        
        return full_articles