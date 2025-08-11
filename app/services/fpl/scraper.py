# app/services/fpl/scraper.py
from app.core.logging import logger
from app.services.fpl.fixtures_data import get_fixture_data
from app.services.fpl.players_data import get_bootstrap_data
from app.services.fpl.data_processor import FPLDataProcessor
from app.services.fpl.store_data_postgres import upload_fpl_data_to_postgres

class FPLScraper:
    def __init__(self):
        self.data_path = "app/data/raw"
        self.processor = FPLDataProcessor()
    
    def scrape_fixtures(self):
        """Scrape and save fixtures data"""
        logger.info("Starting fixtures data scraping...")
        result = get_fixture_data()
        if result:
            logger.info("Fixtures scraping completed successfully")
        else:
            logger.error("Fixtures scraping failed")
        return result
    
    def scrape_players(self):
        """Scrape and save players data"""
        logger.info("Starting players data scraping...")
        result = get_bootstrap_data()
        if result:
            logger.info("Players scraping completed successfully")
        else:
            logger.error("Players scraping failed")
        return result
    
    def scrape_all(self):
        """Scrape all FPL data"""
        logger.info("Starting full FPL data scraping...")
        
        fixtures_success = self.scrape_fixtures()
        players_success = self.scrape_players()
        
        if fixtures_success and players_success:
            logger.info("All FPL data scraping completed successfully")
            return True
        else:
            logger.warning("Some FPL data scraping operations failed")
            return False
        
    def scrape_and_process_all(self):
        """Scrape raw data and generate descriptions"""
        logger.info("Starting full FPL data scraping and processing...")
        
        # Scrape raw data
        scraping_success = self.scrape_all()
        
        if scraping_success:
            # Process data and generate descriptions
            processing_success = self.processor.process_all_data()
            
            if processing_success:
                logger.info("FPL scraping and processing completed successfully")
                return True
            else:
                logger.warning("FPL scraping succeeded but processing failed")
                return False
        else:
            logger.error("FPL scraping failed")
            return False
        
    
    def scrape_process_and_upload(self):
        """Complete pipeline: scrape -> process -> upload to PostgreSQL"""
        try:
            logger.info("Starting complete FPL pipeline (scrape + process + upload)...")
            
            # Scrape and process data
            scrape_process_success = self.scrape_and_process_all()
            if not scrape_process_success:
                logger.error("Scraping and processing failed - aborting pipeline")
                return False
            
            # Upload to PostgreSQL
            logger.info("Step 2: Uploading to PostgreSQL database...")
            upload_success = upload_fpl_data_to_postgres()
            if not upload_success:
                logger.error("Database upload failed")
                return False
            
            logger.info("Complete FPL pipeline completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Complete FPL pipeline failed: {str(e)}")
            return False
        
if __name__ == "__main__":
    scraper = FPLScraper()

    #scrapes, processes and as well uploads in postgres
    scraper.scrape_process_and_upload()   