import requests
import pandas as pd
import os
from app.core.logging import logger

# Mapping difficulty levels to descriptive text
difficulty_mapping = {
    1: "Very Easy",
    2: "Easy",
    3: "Medium",
    4: "Hard",
    5: "Very Hard"
}

# Function to fetch fixture data
def get_fixture_data():
    try:
        
        os.makedirs("app/data/raw/fixtures", exist_ok=True)

        # URLs for bootstrap and fixtures
        bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        fixtures_url = "https://fantasy.premierleague.com/api/fixtures/"

        # Fetch team information from bootstrap
        bootstrap_response = requests.get(bootstrap_url)
        if bootstrap_response.status_code != 200:
            logger.error(f"Failed to fetch bootstrap data: HTTP {bootstrap_response.status_code}")
            return None

        bootstrap_data = bootstrap_response.json()
        teams = {team["id"]: team["name"] for team in bootstrap_data["teams"]}

        # Fetch fixtures data
        fixtures_response = requests.get(fixtures_url)
        if fixtures_response.status_code != 200:
            logger.error(f"Failed to fetch fixtures data: HTTP {fixtures_response.status_code}")
            return None

        fixtures = fixtures_response.json()

        # Process fixture data
        fixtures_data = []
        for fixture in fixtures:
            fixture_info = {
                "Gameweek": fixture["event"],
                "Home Team": teams.get(fixture["team_h"], "Unknown"),
                "Away Team": teams.get(fixture["team_a"], "Unknown"),
                "Home Difficulty": difficulty_mapping.get(fixture["team_h_difficulty"], "Unknown"),
                "Away Difficulty": difficulty_mapping.get(fixture["team_a_difficulty"], "Unknown"),
                "Kickoff Time": fixture["kickoff_time"]
            }
            fixtures_data.append(fixture_info)

        # Convert to DataFrame
        fixtures_df = pd.DataFrame(fixtures_data)
        filename = "app/data/raw/fixtures/fpl_fixtures.csv"
        fixtures_df.to_csv(filename, index=False)

        logger.info(f"Fixtures data successfully scraped and saved to {filename}")
        logger.info(f"Total fixtures scraped: {len(fixtures_df)}")

        return True
    
    except Exception as e:
        logger.error(f"Error scraping fixtures data: {str(e)}")
        return False
