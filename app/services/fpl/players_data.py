import requests
import pandas as pd
from app.core.logging import logger
import os


# Function to get player data
def get_bootstrap_data():
    try:
        os.makedirs("app/data/raw/players", exist_ok=True)

        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Error fetching bootstrap data: HTTP {response.status_code}")
            return False

        data = response.json()

        # Mapping team IDs to team names and positions to names
        teams = {team["id"]: team["name"] for team in data["teams"]}
        positions = {1: "Goalkeeper", 2: "Defender", 3: "Midfielder", 4: "Forward"}

        # Process player data with all attributes
        players_data = []
        for player in data["elements"]:
            player_info = {
                "id": player["id"],
                "code": player["code"],
                "first_name": player["first_name"],
                "second_name": player["second_name"],
                "web_name": player["web_name"],
                "team": teams.get(player["team"], "Unknown"),
                "position": positions.get(player["element_type"], "Unknown"),
                "status": player["status"],
                "news": player["news"],
                "chance_of_playing_next_round": player.get("chance_of_playing_next_round", None),
                "chance_of_playing_this_round": player.get("chance_of_playing_this_round", None),
                "now_cost": player["now_cost"] / 10,
                "cost_change_event": player["cost_change_event"],
                "cost_change_start": player["cost_change_start"],
                "total_points": player["total_points"],
                "points_per_game": player["points_per_game"],
                "minutes": player["minutes"],
                "goals_scored": player["goals_scored"],
                "assists": player["assists"],
                "clean_sheets": player["clean_sheets"],
                "goals_conceded": player["goals_conceded"],
                "own_goals": player["own_goals"],
                "penalties_saved": player["penalties_saved"],
                "penalties_missed": player["penalties_missed"],
                "yellow_cards": player["yellow_cards"],
                "red_cards": player["red_cards"],
                "saves": player["saves"],
                "bonus": player["bonus"],
                "bps": player["bps"],
                "influence": player["influence"],
                "creativity": player["creativity"],
                "threat": player["threat"],
                "ict_index": player["ict_index"],
                "form": player["form"],
                "dreamteam_count": player["dreamteam_count"],
                "selected_by_percent": player["selected_by_percent"],
                "transfers_in": player["transfers_in"],
                "transfers_out": player["transfers_out"],
                "transfers_in_event": player["transfers_in_event"],
                "transfers_out_event": player["transfers_out_event"],
                "ep_next": player["ep_next"],
                "ep_this": player["ep_this"],
                "starts": player["starts"],
                "expected_goals": player["expected_goals"],
                "expected_assists": player["expected_assists"],
                "expected_goal_involvements": player["expected_goal_involvements"],
                "expected_goals_conceded": player["expected_goals_conceded"],
                "influence_rank": player["influence_rank"],
                "creativity_rank": player["creativity_rank"],
                "threat_rank": player["threat_rank"],
                "ict_index_rank": player["ict_index_rank"],
                "starts_per_90": player["starts_per_90"],
                "expected_goals_per_90": player["expected_goals_per_90"],
                "expected_assists_per_90": player["expected_assists_per_90"],
                "expected_goal_involvements_per_90": player["expected_goal_involvements_per_90"],
                "expected_goals_conceded_per_90": player["expected_goals_conceded_per_90"],
                "clean_sheets_per_90": player["clean_sheets_per_90"],
                "goals_conceded_per_90": player["goals_conceded_per_90"],
            }
            players_data.append(player_info)

        # Convert player data to DataFrame and save to CSV
        players_df = pd.DataFrame(players_data)
        filename = "app/data/raw/players/fpl_players.csv"
        players_df.to_csv(filename, index=False)
        
        logger.info(f"Player data successfully scraped and saved to {filename}")
        logger.info(f"Total players scraped: {len(players_df)}")
        
        return True

    except Exception as e:
        logger.error(f"Error scraping player data: {str(e)}")
        return False




