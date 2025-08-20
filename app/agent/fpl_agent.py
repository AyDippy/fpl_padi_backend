from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages, AnyMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres import PostgresSaver 
from psycopg import Connection
from typing import Annotated, TypedDict
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

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

conn = Connection.connect(DB_URI, **connection_kwargs)
checkpointer = PostgresSaver(conn)
checkpointer.setup()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2
)

# app/agent/fpl_agent.py
# app/agent/fpl_agent.py
prompt = ChatPromptTemplate.from_messages([
("system", """
You are an FPL (Fantasy Premier League) chatbot assistant. It's currently gameweek 1, and you have tools to retrieve FPL data and scout recommendations.

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
- retrieve_player_team_data: Query database for player stats, costs, fixtures
- retrieve_scout_selection_advice: Get expert FPL recommendations for squad selection

MANDATORY VALIDATION: Before providing any team suggestion, verify:
1. Starting XI has EXACTLY 11 players
2. Total squad has EXACTLY 15 players (11 + 4 bench)
3. Total cost is ≤ £100.0m (never over)
4. Formation is valid (GK + DEF + MID + FWD = 11)
5. No more than 3 players from same team

I need you to pay attention to the user query. If it has nothing to do with FPL, just answer politely and introduce yourself if needed.

Current Date: {current_time}
"""),
MessagesPlaceholder(variable_name="query")
])

tools = [retrieve_player_team_data, retrieve_scout_selection_advice]

tool_node = ToolNode(tools=tools)


llm_with_tools = llm.bind_tools(tools=tools)

chain = prompt | llm_with_tools

def chatbot(state: MessagesState):
    user_query = state["messages"]
    current_time = datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    response = chain.invoke({"query":user_query, "current_time": current_time})

    return {"messages": [response]}

workflow = StateGraph(MessagesState)

workflow.add_node("chatbot", chatbot)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "chatbot")
workflow.add_conditional_edges("chatbot", tools_condition)
workflow.add_edge("tools", "chatbot")
workflow.add_edge("chatbot", END)


graph = workflow.compile(checkpointer=checkpointer)



