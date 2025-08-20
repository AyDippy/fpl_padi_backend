# app/tools/fpl_query_tool.py
import psycopg2
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from app.core.config import settings
from app.core.logging import logger


@tool
def retrieve_player_team_data(user_input: str) -> dict:
    """
    Query FPL data from PostgreSQL database. Examples:
    - "Show top 10 goalscorers"
    - "Find Arsenal defenders"
    - "List fixtures for gameweek 25"
    - "Best midfielders by points"
    - "Chelsea home games"
    - "Compare Salah and Haaland"

    Args:
        user_input: Natural language query about FPL data

    Returns:
        {
            'results': List of matched data,
            'status': 'success' or 'error',
            'count': Number of results,
            'query': Generated SQL query
        }
    """
    
    try:
        logger.info(f"FPL Query: {user_input}")
        
        # Database connection using your current settings
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            dbname=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
        
        cur = conn.cursor()
        
        # Initialize OpenAI LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
        
        # Updated prompt template with your current database structure
        prompt = ChatPromptTemplate.from_template(
            """
            You are a PostgreSQL query generator assistant. Generate SQL queries to filter FPL data from two tables:
            
            PLAYERS TABLE: "players"
            Columns: id, code, first_name, second_name, web_name, team, position, status, news, 
            chance_of_playing_next_round, chance_of_playing_this_round, now_cost, cost_change_event,
            cost_change_start, total_points, points_per_game, minutes, goals_scored, assists, 
            clean_sheets, goals_conceded, own_goals, penalties_saved, penalties_missed, yellow_cards,
            red_cards, saves, bonus, bps, influence, creativity, threat, ict_index, form, 
            dreamteam_count, selected_by_percent, transfers_in, transfers_out, transfers_in_event,
            transfers_out_event, ep_next, ep_this, starts, expected_goals, expected_assists, 
            expected_goal_involvements, expected_goals_conceded, influence_rank, creativity_rank,
            threat_rank, ict_index_rank, starts_per_90, expected_goals_per_90, expected_assists_per_90,
            expected_goal_involvements_per_90, expected_goals_conceded_per_90, clean_sheets_per_90, 
            goals_conceded_per_90, description
            
            Teams: Arsenal, Aston Villa, Bournemouth, Brentford, Brighton, Chelsea, Crystal Palace, 
            Everton, Fulham, Ipswich, Leicester, Liverpool, Man City, Man Utd, Newcastle, 
            Nott'm Forest, Southampton, Spurs, West Ham, Wolves
            
            Positions: Midfielder, Forward, Defender, Goalkeeper
            
            FIXTURES TABLE: "fixtures"
            Columns: id, gameweek, home_team, away_team, home_difficulty, away_difficulty, 
            kickoff_time, description
            
            Difficulty levels: Very Easy, Easy, Medium, Hard, Very Hard
            Gameweeks: 1-38
            
            Rules:
            1. Always include 'description' column in SELECT for rich context
            2. Use appropriate WHERE, ORDER BY, and LIMIT clauses
            3. For comparisons, use single query with multiple conditions
            4. No explanations - only SQL query
            5. Handle player names with web_name or combine first_name + second_name
            
            Examples:
            - Top scorers: SELECT web_name, goals_scored, description FROM players WHERE goals_scored > 0 ORDER BY goals_scored DESC LIMIT 10
            - Team players: SELECT web_name, position, description FROM players WHERE team = 'Arsenal'
            - Fixtures: SELECT home_team, away_team, gameweek, description FROM fixtures WHERE gameweek = 25
            
            Query: {query}
            """
        )
        
        chain = prompt | llm
        
        # Generate SQL query
        sql_query = chain.invoke({"query": user_input}).content
        logger.info(f"Generated SQL: {sql_query}")
        
        # Clean the SQL query
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        sql_query = " ".join(line.strip() for line in sql_query.splitlines())
        
        # Execute query
        cur.execute(sql_query)
        results = cur.fetchall()
        
        # Get column names for better formatting
        column_names = [desc[0] for desc in cur.description]
        
        # Format results as list of dictionaries
        formatted_results = []
        for row in results:
            row_dict = dict(zip(column_names, row))
            formatted_results.append(row_dict)
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Query executed successfully. Results: {len(formatted_results)} rows")
        
        return {
            'results': formatted_results,
            'status': 'success',
            'count': len(formatted_results),
            'query': sql_query,
            'columns': column_names
        }
        
    except Exception as e:
        logger.error(f"Error in FPL query tool: {str(e)}")
        
        # Close connections if they exist
        try:
            if 'cur' in locals():
                cur.close()
            if 'conn' in locals():
                conn.close()
        except:
            pass
            
        return {
            'results': [],
            'status': 'error',
            'error': str(e),
            'count': 0
        }
