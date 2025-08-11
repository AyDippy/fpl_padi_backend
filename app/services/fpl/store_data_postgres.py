import psycopg2
from io import StringIO
import pandas as pd
import os
from app.core.config import settings
from app.core.logging import logger

class FPLDatabaseUploader:
    def __init__(self):
        self.processed_data_path = "app/data/processed"
        
    def get_connection(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(
                host=settings.DB_HOST,
                dbname=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                port=settings.DB_PORT
            )
            logger.info("Database connection established successfully")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def create_tables(self, cursor):
        """Create FPL tables if they don't exist"""
        try:
            # Drop existing tables to avoid conflicts (optional - remove if you want to keep existing data)
            cursor.execute("DROP TABLE IF EXISTS players CASCADE")
            cursor.execute("DROP TABLE IF EXISTS fixtures CASCADE")
            
            # Create players table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INT PRIMARY KEY,
                    code INT,
                    first_name VARCHAR(100),
                    second_name VARCHAR(100),
                    web_name VARCHAR(100),
                    team VARCHAR(50),
                    position VARCHAR(20),
                    status VARCHAR(20),
                    news TEXT,
                    chance_of_playing_next_round FLOAT,
                    chance_of_playing_this_round FLOAT,
                    now_cost FLOAT,
                    cost_change_event INT,
                    cost_change_start INT,
                    total_points INT,
                    points_per_game FLOAT,
                    minutes INT,
                    goals_scored INT,
                    assists INT,
                    clean_sheets INT,
                    goals_conceded INT,
                    own_goals INT,
                    penalties_saved INT,
                    penalties_missed INT,
                    yellow_cards INT,
                    red_cards INT,
                    saves INT,
                    bonus INT,
                    bps INT,
                    influence FLOAT,
                    creativity FLOAT,
                    threat FLOAT,
                    ict_index FLOAT,
                    form FLOAT,
                    dreamteam_count INT,
                    selected_by_percent FLOAT,
                    transfers_in INT,
                    transfers_out INT,
                    transfers_in_event INT,
                    transfers_out_event INT,
                    ep_next FLOAT,
                    ep_this FLOAT,
                    starts INT,
                    expected_goals FLOAT,
                    expected_assists FLOAT,
                    expected_goal_involvements FLOAT,
                    expected_goals_conceded FLOAT,
                    influence_rank INT,
                    creativity_rank INT,
                    threat_rank INT,
                    ict_index_rank INT,
                    starts_per_90 FLOAT,
                    expected_goals_per_90 FLOAT,
                    expected_assists_per_90 FLOAT,
                    expected_goal_involvements_per_90 FLOAT,
                    expected_goals_conceded_per_90 FLOAT,
                    clean_sheets_per_90 FLOAT,
                    goals_conceded_per_90 FLOAT,
                    description TEXT
                )
            """)
            logger.info("Players table created successfully")

            # Create fixtures table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fixtures (
                    id SERIAL PRIMARY KEY,
                    gameweek INT,
                    home_team VARCHAR(50),
                    away_team VARCHAR(50),
                    home_difficulty VARCHAR(20),
                    away_difficulty VARCHAR(20),
                    kickoff_time TIMESTAMP,
                    description TEXT
                )
            """)
            logger.info("Fixtures table created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise

    def upload_players_data(self, cursor):
        """Upload players data with descriptions"""
        try:
            # Correct path to your processed data
            players_file = os.path.join(self.processed_data_path, "fpl_players_with_descriptions.csv")
            
            if not os.path.exists(players_file):
                raise FileNotFoundError(f"Players file not found: {players_file}")
            
            # Read CSV file
            players_df = pd.read_csv(players_file, encoding='utf-8')
            logger.info(f"Loaded {len(players_df)} players from CSV")

            # Handle NaN values that might cause issues
            players_df = players_df.fillna('')
            
            # Convert DataFrame to CSV string for COPY command
            output = StringIO()
            players_df.to_csv(output, sep=',', header=False, index=False)
            output.seek(0)

            # Use COPY for efficient bulk insert
            cursor.copy_expert("""
                COPY players FROM STDIN WITH CSV DELIMITER ','
            """, output)
            
            logger.info("Players data uploaded successfully")
            return len(players_df)
            
        except Exception as e:
            logger.error(f"Error uploading players data: {str(e)}")
            raise

    def upload_fixtures_data(self, cursor):
        """Upload fixtures data with descriptions"""
        try:
            # Correct path to your processed data
            fixtures_file = os.path.join(self.processed_data_path, "fpl_fixtures_with_descriptions.csv")
            
            if not os.path.exists(fixtures_file):
                raise FileNotFoundError(f"Fixtures file not found: {fixtures_file}")
            
            # Read CSV file
            fixtures_df = pd.read_csv(fixtures_file, encoding='utf-8')
            logger.info(f"Loaded {len(fixtures_df)} fixtures from CSV")

            # Handle NaN values
            fixtures_df = fixtures_df.fillna('')
            
            # Convert DataFrame to CSV string for COPY command
            output = StringIO()
            fixtures_df.to_csv(output, sep=',', header=False, index=False)
            output.seek(0)

            # Use COPY for efficient bulk insert
            cursor.copy_expert("""
                COPY fixtures (gameweek, home_team, away_team, home_difficulty, away_difficulty, kickoff_time, description) 
                FROM STDIN WITH CSV DELIMITER ','
            """, output)
            
            logger.info("Fixtures data uploaded successfully")
            return len(fixtures_df)
            
        except Exception as e:
            logger.error(f"Error uploading fixtures data: {str(e)}")
            raise

    def upload_all_data(self):
        """Main method to upload all FPL data to PostgreSQL"""
        conn = None
        cursor = None
        
        try:
            logger.info("Starting FPL data upload to PostgreSQL...")
            
            # Get database connection
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create tables
            self.create_tables(cursor)
            
            # Upload data
            players_count = self.upload_players_data(cursor)
            fixtures_count = self.upload_fixtures_data(cursor)
            
            # Commit all changes
            conn.commit()
            
            logger.info(f"FPL data upload completed successfully!")
            logger.info(f"Uploaded {players_count} players and {fixtures_count} fixtures")
            
            return True
            
        except Exception as e:
            logger.error(f"FPL data upload failed: {str(e)}")
            if conn:
                conn.rollback()
                logger.info("Database changes rolled back")
            return False
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
                logger.info("Database connection closed")


def upload_fpl_data_to_postgres():
    """Convenience function to upload FPL data"""
    uploader = FPLDatabaseUploader()
    return uploader.upload_all_data()

