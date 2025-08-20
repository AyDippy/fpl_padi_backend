from app.core.logging import logger
from app.models.chat import ChatMessage
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
from sqlalchemy import select
from app.agent.fpl_agent import graph
from langchain_core.messages import HumanMessage

async def create_chat(db: AsyncSession, message: str, thread_id: str, user_id: str):
    """
    Create a new chat conversation by storing user message and getting agent response
    
    Args:
        db: Database session
        message: User's message content
        thread_id: Thread identifier for conversation continuity
        user_id: User identifier
        
    Returns:
        dict: Contains user_message and agent_response ChatMessage objects
        
    Raises:
        Exception: If chat creation fails
    """
    try:
        logger.info(f"Creating chat - Thread: {thread_id[:8]}..., User: {user_id}, Message length: {len(message)}")
        
        user_message = message

        # Create and store user message
        user_msg = ChatMessage(
            thread_id=thread_id,
            user_id=user_id,
            content=user_message,
            role="user",
            timestamp=datetime.utcnow()
        )

        logger.debug(f"Created user message object for thread {thread_id[:8]}...")
        db.add(user_msg)

        # Get agent response
        logger.info(f"Invoking FPL agent for thread {thread_id[:8]}...")
        
        config = {"configurable": {"thread_id": thread_id}}
        input_state = {"messages": [HumanMessage(content=user_message)]}
        
        # Invoke the agent
        response_state = graph.invoke(input_state, config=config)
        agent_response = response_state["messages"][-1].content

        logger.info(f"Agent response received - Thread: {thread_id[:8]}..., Response length: {len(agent_response)}")

        # Create and store agent response
        agent_msg = ChatMessage(
            thread_id=thread_id,
            user_id=user_id,
            content=agent_response,
            role="assistant",
            timestamp=datetime.utcnow()
        )

        logger.debug(f"Created agent message object for thread {thread_id[:8]}...")
        db.add(agent_msg)

        # Commit both messages
        await db.commit()
        logger.info(f"Successfully committed chat messages to database - Thread: {thread_id[:8]}...")
        
        await db.refresh(user_msg)
        await db.refresh(agent_msg)

        logger.info(f"Chat creation completed successfully - Thread: {thread_id[:8]}..., Messages: 2")

        return {
            "user_message": user_msg,
            "agent_response": agent_msg,
            "thread_id": thread_id,
            "success": True
        }

    except Exception as e:
        logger.error(f"Error creating chat - Thread: {thread_id[:8] if thread_id else 'Unknown'}..., Error: {str(e)}")
        
        # Rollback any partial database changes
        try:
            await db.rollback()
            logger.info(f"Database rollback completed for thread {thread_id[:8] if thread_id else 'Unknown'}...")
        except Exception as rollback_error:
            logger.error(f"Failed to rollback database transaction: {str(rollback_error)}")
        
        # Re-raise the original exception with context
        raise Exception(f"Failed to create chat for thread {thread_id}: {str(e)}")
    

