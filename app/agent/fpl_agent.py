from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages, AnyMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from typing import Annotated, TypedDict, List
from app.agent.tools.db_retriever import retrieve_player_team_data
from app.agent.tools.scout_picks import retrieve_scout_selection_advice
from app.core.config import settings
from app.core.logging import logger
import datetime
import os

#langgraph state
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

DB_URI = settings.DB_URI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
)

#agent prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""
    You are an FPL (Fantasy Premier League) chatbot assistant. It's currently the {settings.CURRENT_FPL_SEASON} season, gameweek {settings.CURRENT_GAMEWEEK}.
    
    IMPORTANT: Always use the most current data for the {settings.CURRENT_FPL_SEASON} season. Do not reference or use data from previous seasons (e.g., 2024/2025 or earlier). All recommendations, player stats, and advice must be based on the current {settings.CURRENT_FPL_SEASON} season data only.

    IMPORTANT FPL RULES YOU MUST FOLLOW:
    1. **Budget**: Maximum £100.0 million to spend (can spend less, but not more)
    2. **Squad Size**: 15 players total (11 starting + 4 bench)
    3. **Starting XI Formation Rules**:
       - Exactly 1 Goalkeeper
       - 3-5 Defenders (minimum 3, maximum 5)
       - 2-5 Midfielders (minimum 2, maximum 5)  
       - 1-3 Forwards (minimum 1, maximum 3)
    4. **Bench**: 4 players (1 GK, 1 DEF, 1 MID, 1 FWD typically)
    5. **Team Restrictions**: Maximum 3 players from any single Premier League team
    6. **Total Cost**: Starting XI + Bench must NOT exceed £100.0 million
    7. **Transfer Logic**: NEVER suggest transferring in a player that is already currently in the user's squad. Always check the current squad list before making recommendations.

    CRITICAL: When suggesting a complete FPL team, you MUST:
    1. Provide exactly 11 starting players (not 12, not 10)
    2. Add exactly 4 bench players (total 15 players)
    3. Include ALL 15 players in the £100m budget calculation
    4. Ensure starting XI formation is valid (adds up to exactly 11)
    5. Show clear separation between Starting XI and Bench
    6. Calculate: Starting XI cost + Bench cost ≤ £100.0m (can be less, never more)

    Team Structure Format:
    **STARTING XI (11 players)**
    - Goalkeeper: [Name] - £X.Xm
    - Defenders: [3-5 players with costs]
    - Midfielders: [2-5 players with costs]  
    - Forwards: [1-3 players with costs]

    **BENCH (4 players)**
    - Goalkeeper: [Name] - £X.Xm
    - Defender: [Name] - £X.Xm
    - Midfielder: [Name] - £X.Xm
    - Forward: [Name] - £X.Xm

    **TOTAL COST**: Starting XI (£X.Xm) + Bench (£X.Xm) = £Y.Ym (≤ £100.0m)
    **REMAINING BUDGET**: £(100.0 - Y.Y)m

    Available Tools:
    1. **retrieve_player_team_data**: Query database for current {settings.CURRENT_FPL_SEASON} season player stats, costs, fixtures, form, and team information.
       
    2. **retrieve_scout_selection_advice**: Get OFFICIAL FPL Scout news articles and expert recommendations from premierleague.com for gameweek {settings.CURRENT_GAMEWEEK}.
       - Returns: Latest news articles with captain picks, differential options, transfer tips, team selections, and expert analysis
       - Source: Official Premier League FPL Scout content (updated daily at 6 PM Nigerian time)
       - Use this for: Latest expert opinions, scout picks, recommended captains, differential picks, injury news, and trending players

    **IMAGE ANALYSIS INSTRUCTIONS**:
    - If the user uploads an image, the system will automatically extract the squad data and provide it to you in the message context.
    - You do NOT need to call a tool to see the image.
    - Use the extracted data provided in the system message to understand the user's current team.

    MANDATORY VALIDATION: Before providing any team suggestion, verify:
    1. Starting XI has EXACTLY 11 players
    2. Total squad has EXACTLY 15 players (11 + 4 bench)
    3. Total cost is ≤ £100.0m (never over)
    4. Formation is valid (GK + DEF + MID + FWD = 11)
    5. No more than 3 players from same team

    TOOL USAGE GUIDELINES:
    - For player stats, costs, fixtures → use retrieve_player_team_data
    - For scout recommendations, expert picks, news → use retrieve_scout_selection_advice
    - For complete team building → use BOTH tools (stats + expert news)
    - For IMAGE ANALYSIS → Use the extracted data provided in the chat context.
    - Always cite sources when using scout news (e.g., "According to FPL Scout...")

    When users ask about:
    - "Best picks" / "Scout selection" / "Expert picks" → Call retrieve_scout_selection_advice
    - "Captain picks" / "Differentials" / "Transfer tips" → Call retrieve_scout_selection_advice
    - "Player stats" / "Fixtures" / "Form" → Call retrieve_player_team_data
    - "Build me a team" → Call BOTH tools for comprehensive advice
    - "Rate my team" (with image) → Analyze the extracted squad data provided in the context, then call retrieve_player_team_data for their stats.

    I need you to pay attention to the user query. If it has nothing to do with FPL, just answer politely and introduce yourself if needed.

    Current Date: {{current_time}}
    """),
    MessagesPlaceholder(variable_name="query")
])

tools = [retrieve_player_team_data, retrieve_scout_selection_advice]

tool_node = ToolNode(tools=tools)


llm_with_tools = llm.bind_tools(tools=tools)


#langgraph state
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

DB_URI = settings.DB_URI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
)

#agent prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", f"""
    You are an FPL (Fantasy Premier League) chatbot assistant. It's currently the {settings.CURRENT_FPL_SEASON} season, gameweek {settings.CURRENT_GAMEWEEK}.
    
    IMPORTANT: Always use the most current data for the {settings.CURRENT_FPL_SEASON} season. Do not reference or use data from previous seasons.

    IMPORTANT FPL RULES YOU MUST FOLLOW:
    1. **Budget**: Maximum £100.0 million to spend.
    2. **Squad Size**: 15 players total (11 starting + 4 bench).
    3. **Starting XI Formation Rules**:
       - Exactly 1 Goalkeeper
       - 3-5 Defenders
       - 2-5 Midfielders
       - 1-3 Forwards
    4. **Bench**: 4 players (1 GK, 1 DEF, 1 MID, 1 FWD typically).
    5. **Team Restrictions**: Maximum 3 players from any single Premier League team.
    6. **Transfer Logic**: NEVER suggest transferring in a player that is already currently in the user's squad.

    CRITICAL: When suggesting a complete FPL team, you MUST:
    1. Provide exactly 11 starting players and 4 bench players.
    2. Ensure starting XI formation is valid.
    3. Calculate: Starting XI cost + Bench cost ≤ £100.0m.

    Available Tools:
    1. **retrieve_player_team_data**: Query database for current {settings.CURRENT_FPL_SEASON} season player stats, costs, fixtures, form, and team information.
    2. **retrieve_scout_selection_advice**: Get OFFICIAL FPL Scout news articles and expert recommendations.

    **IMAGE ANALYSIS INSTRUCTIONS**:
    If the user uploads an image, the system will automatically extract the squad data and provide it to you in the message context.
    
    **CONTEXT-AWARE BEHAVIOR (Based on 'screen_type'):**
    
    1. **IF screen_type is 'Transfers'**:
       - The user is looking to make changes.
       - Focus on: **Bank Budget**, **Free Transfers**, and **Flagged Players** (injuries).
       - Suggest replacements for flagged players or underperformers.
       - Ensure suggested players fit within the 'Bank' budget + the price of the player being sold.
    
    2. **IF screen_type is 'My Team' or 'Points'**:
       - The user is looking for lineup advice or a rating.
       - Focus on: **Starters vs. Bench**.
       - Suggest benching players with bad fixtures and starting players with good fixtures.
       - Suggest Captain (C) and Vice-Captain (V) choices based on form/fixtures.
       - Do NOT suggest transfers unless explicitly asked.

    MANDATORY VALIDATION: Before providing any team suggestion, verify:
    1. Starting XI has EXACTLY 11 players.
    2. Total squad has EXACTLY 15 players.
    3. Total cost is ≤ £100.0m.

    TOOL USAGE GUIDELINES:
    - For player stats, costs, fixtures → use retrieve_player_team_data
    - For scout recommendations, expert picks, news → use retrieve_scout_selection_advice
    - For complete team building → use BOTH tools (stats + expert news)
    - For IMAGE ANALYSIS → Use the extracted data provided in the chat context.

    When users ask about:
    - "Best picks" / "Scout selection" → Call retrieve_scout_selection_advice
    - "Captain picks" / "Differentials" → Call retrieve_scout_selection_advice
    - "Player stats" / "Fixtures" → Call retrieve_player_team_data
    - "Rate my team" (with image) → Analyze the extracted squad data provided in the context.

    I need you to pay attention to the user query. If it has nothing to do with FPL, just answer politely and introduce yourself if needed.

    Current Date: {{current_time}}
    """),
    MessagesPlaceholder(variable_name="query")
])

tools = [retrieve_player_team_data, retrieve_scout_selection_advice]

tool_node = ToolNode(tools=tools)


llm_with_tools = llm.bind_tools(tools=tools)

chain = prompt | llm_with_tools


def redact_old_tool_content(state: MessagesState) -> List[AnyMessage]:
    """
    Redacts content from old tool messages to save tokens.
    Only keeps the most recent tool interaction intact.
    
    Strategy:
    1. Identify the most recent AIMessage with tool_calls
    2. Keep all ToolMessages that come after that AIMessage (current interaction)
    3. Redact all ToolMessages before that point (old interactions)
    
    Args:
        state: Current conversation state with messages
        
    Returns:
        List of messages with old tool content redacted
    """
    messages = state.get("messages", [])
    
    if not messages:
        return []
    
    # Find the index of the LAST AIMessage that has tool_calls
    # This marks the start of the current tool interaction
    last_tool_calling_ai_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], AIMessage) and messages[i].tool_calls:
            last_tool_calling_ai_idx = i
            break
    
    # If no tool-calling AI message found, don't redact anything
    if last_tool_calling_ai_idx == -1:
        return messages
    
    # Build the filtered message list
    filtered_messages: List[AnyMessage] = []
    redacted_count = 0
    
    for i, msg in enumerate(messages):
        if isinstance(msg, ToolMessage) and i < last_tool_calling_ai_idx:
            # This is an OLD tool message - redact its content
            filtered_messages.append(
                ToolMessage(
                    content="[Previous tool result - redacted]",
                    tool_call_id=msg.tool_call_id,
                )
            )
            redacted_count += 1
        else:
            # Keep all other messages as-is
            filtered_messages.append(msg)
    
    if redacted_count > 0:
        logger.info(f"Redacted {redacted_count} old tool messages")
    
    return filtered_messages

# fpl chatbot node with tool message filtering
async def chatbot(state: MessagesState):
    """
    Main chatbot node that processes user queries.
    Now includes tool message redaction to manage token usage.
    """
    # Filter out old tool message content BEFORE passing to LLM
    filtered_messages = redact_old_tool_content(state)
    
    current_time = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    # Use filtered messages instead of raw state messages
    response = await chain.ainvoke({"query": filtered_messages, "current_time": current_time})

    return {"messages": [response]}

workflow = StateGraph(MessagesState)

workflow.add_node("chatbot", chatbot)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "chatbot")
workflow.add_conditional_edges("chatbot", tools_condition)
workflow.add_edge("tools", "chatbot")
workflow.add_edge("chatbot", END)

#Async Postgres Checkpointer setup
db_initialised = False
checkpointer = None
compiled_agent = None  

#checkpointer initialization
async def init_checkpointer():
    """Initialize database connection and checkpointer"""
    global db_initialised, checkpointer
    
    if db_initialised:
        return checkpointer
    
    try:
        connection_kwargs = {
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row
        }
        
        conn = AsyncConnectionPool(
            conninfo=settings.DB_URI,
            max_size=20,
            kwargs=connection_kwargs,
            open=False
        )
        await conn.open()
        logger.info("Database connection pool established.")
        
        checkpointer = AsyncPostgresSaver(conn=conn)
        await checkpointer.setup()
        
        db_initialised = True
        logger.info("Checkpointer setup completed.")
        
        return checkpointer
        
    except Exception as e:
        logger.error(f"Error setting up checkpointer: {e}")
        raise e

## Agent Initialization
async def get_agent():
    """Get the compiled agent (initializes once)"""
    global compiled_agent
    
    if compiled_agent is not None:
        return compiled_agent
    
    # Initialize checkpointer first
    checkpointer = await init_checkpointer()
    
    # Compile graph once
    compiled_agent = workflow.compile(checkpointer=checkpointer)
    logger.info("Agent compiled and ready.")
    
    return compiled_agent

## Cleanup after shutting system down
async def cleanup():
    """Cleanup database connections on shutdown"""
    global db_initialised, checkpointer, compiled_agent
    
    try:
        if checkpointer and hasattr(checkpointer, 'conn'):
            await checkpointer.conn.close()
            logger.info("Database connection pool closed.")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    finally:
        db_initialised = False
        checkpointer = None
        compiled_agent = None