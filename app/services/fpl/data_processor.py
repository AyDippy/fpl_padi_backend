# app/services/fpl/data_processor.py
import pandas as pd
import os
from app.core.logging import logger

class FPLDataProcessor:
    def __init__(self):
        self.raw_data_path = "app/data/raw"
        self.processed_data_path = "app/data/processed"
        
    def create_player_description(self, player):
        """Generate natural language description for a player"""
        news_detail = f" due to {player['news']}" if player['news'] and str(player['news']).strip() != '' else ""
        
        description = (
            f"{player['first_name']} {player['second_name']} is a {player['position']} "
            f"playing for {player['team']}. Currently, they are {'available' if player['status'] == 'a' else 'not available'}{news_detail}. "
            f"Their cost is £{player['now_cost']} million. "
            f"They have scored {player['goals_scored']} goals and provided {player['assists']} assists this season, "
            f"accumulating {player['total_points']} fantasy points with an average of {player['points_per_game']} points per game. "
            f"They are selected by {player['selected_by_percent']}% of teams and have a current form rating of {player['form']}. "
            f"In terms of advanced metrics, their expected goals is {player['expected_goals']} and expected assists is {player['expected_assists']}. "
            f"Their ICT index is {player['ict_index']} (influence: {player['influence']}, creativity: {player['creativity']}, threat: {player['threat']}). "
            f"They have played {player['minutes']} minutes this season."
        )
        return description

    def generate_fixture_description(self, row):
        """Generate natural language description for a fixture"""
        kickoff_dt = pd.to_datetime(row['Kickoff Time'])
        
        description = (
            f"In Gameweek {row['Gameweek']}, {row['Home Team']} will host {row['Away Team']} "
            f"on {kickoff_dt.strftime('%A, %B %d, %Y')} at {kickoff_dt.strftime('%H:%M')} UTC. "
            f"From a Fantasy Premier League perspective, {row['Home Team']} has a '{row['Home Difficulty']}' difficulty rating at home, "
            f"while {row['Away Team']} faces a '{row['Away Difficulty']}' difficulty when playing away. "
            f"This fixture is scheduled for Gameweek {row['Gameweek']} of the Fantasy Premier League season."
        )
        return description

    def process_players_data(self):
        """Process raw player data and add descriptions"""
        try:
            # Ensure processed directory exists
            os.makedirs(self.processed_data_path, exist_ok=True)
            
            # Load raw data
            raw_file = f"{self.raw_data_path}/players/fpl_players.csv"
            player_data = pd.read_csv(raw_file)
            
            # Generate descriptions
            player_data["description"] = player_data.apply(self.create_player_description, axis=1)
            
            # Save processed data
            processed_file = f"{self.processed_data_path}/fpl_players_with_descriptions.csv"
            player_data.to_csv(processed_file, index=False)
            
            logger.info(f"Player descriptions generated and saved to {processed_file}")
            logger.info(f"Total players processed: {len(player_data)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing player data: {str(e)}")
            return False

    def process_fixtures_data(self):
        """Process raw fixture data and add descriptions"""
        try:
            # Ensure processed directory exists
            os.makedirs(self.processed_data_path, exist_ok=True)
            
            # Load raw data
            raw_file = f"{self.raw_data_path}/fixtures/fpl_fixtures.csv"
            fixture_data = pd.read_csv(raw_file)
            
            # Generate descriptions
            fixture_data["description"] = fixture_data.apply(self.generate_fixture_description, axis=1)
            
            # Save processed data
            processed_file = f"{self.processed_data_path}/fpl_fixtures_with_descriptions.csv"
            fixture_data.to_csv(processed_file, index=False)
            
            logger.info(f"Fixture descriptions generated and saved to {processed_file}")
            logger.info(f"Total fixtures processed: {len(fixture_data)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing fixture data: {str(e)}")
            return False

    def process_all_data(self):
        """Process all FPL data"""
        logger.info("Starting FPL data processing...")
        
        players_success = self.process_players_data()
        fixtures_success = self.process_fixtures_data()
        
        if players_success and fixtures_success:
            logger.info("All FPL data processing completed successfully")
            return True
        else:
            logger.warning("Some FPL data processing operations failed")
            return False