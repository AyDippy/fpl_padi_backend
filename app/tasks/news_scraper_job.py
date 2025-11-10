from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.fpl.news_processor import scrape_current_gameweek
from app.services.fpl.scraper import FPLScraper
from app.core.logging import logger
import asyncio


class FPLScheduler:
    """
    Schedules automatic FPL data scraping
    - News scraping: Daily at 6 PM Nigerian time (5 PM UTC)
    - Complete FPL pipeline: Every Friday at 5 PM Nigerian time (4 PM UTC)
      (Includes: fixtures, players, processing, and database upload)
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.fpl_scraper = FPLScraper()
    
    async def _run_complete_fpl_pipeline(self):
        """
        Wrapper for COMPLETE FPL pipeline (sync to async)
        Runs: scrape_fixtures + scrape_players + process_all + upload_to_postgres
        """
        try:
            logger.info("Starting scheduled COMPLETE FPL pipeline...")
            logger.info("This includes: fixtures scraping, players scraping, data processing, and PostgreSQL upload")
            
            success = await asyncio.to_thread(
                self.fpl_scraper.scrape_process_and_upload
            )
            
            if success:
                logger.info("✅ Scheduled COMPLETE FPL pipeline completed successfully")
            else:
                logger.error("❌ Scheduled COMPLETE FPL pipeline failed")
        except Exception as e:
            logger.error(f"Error in scheduled COMPLETE FPL pipeline: {str(e)}")
    
    async def _scrape_news(self):
        """Wrapper for FPL news scraping"""
        try:
            logger.info("Starting scheduled FPL news scrape...")
            stats = await scrape_current_gameweek()
            logger.info(f"Scheduled news scrape completed: {stats}")
        except Exception as e:
            logger.error(f"Error in scheduled news scrape: {str(e)}")
    
    def start(self):
        """Start the scheduler with configured jobs"""
        
        # Nigerian time is UTC+1
        # 6 PM Nigerian time = 5 PM UTC (17:00)
        # 5 PM Nigerian time = 4 PM UTC (16:00)
        
        # ===== FPL NEWS SCRAPING =====
        # Daily at 6 PM Nigerian time (5 PM UTC)
        self.scheduler.add_job(
            self._scrape_news,
            CronTrigger(hour=17, minute=0),  # 5 PM UTC = 6 PM Nigerian
            id="daily_fpl_news_scrape",
            name="Daily FPL News Scrape (6 PM Nigerian Time)",
            replace_existing=True
        )
        
        # ===== COMPLETE FPL PIPELINE =====
        # Every Friday at 5 PM Nigerian time (4 PM UTC)
        # Includes: fixtures + players + processing + PostgreSQL upload
        self.scheduler.add_job(
            self._run_complete_fpl_pipeline,
            CronTrigger(day_of_week='fri', hour=16, minute=0),  # 4 PM UTC = 5 PM Nigerian
            id="weekly_complete_fpl_pipeline",
            name="Weekly Complete FPL Pipeline (Friday 5 PM Nigerian Time)",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("FPL Scheduler started successfully")
        logger.info("Scheduled jobs:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name}: {job.next_run_time}")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("FPL Scheduler stopped")


# Global scheduler instance
fpl_scheduler = FPLScheduler()