from app.core.logging import logger
from app.models.chat import ChatMessage, ChatSession
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
from sqlalchemy import select
from app.agent.fpl_agent import get_agent
from langchain_core.messages import HumanMessage
from app.agent.tools.squad_vision import extract_squad_data
import json

async def create_chat(db: AsyncSession, message: str, thread_id: str, user_id: str, image_data: str = None):
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

        session = await get_or_create_session(db, thread_id, user_id)
        
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
        
        # Prepare input state with optional image
        if image_data:
            logger.info("Processing image with Gemini Vision...")
            
            # Call the new extraction function
            extraction_result = await extract_squad_data(image_data)
            
            # Add the structured data to the user message
            user_message += f"\n\n[SYSTEM: The user uploaded an image. I have extracted the following squad data: {json.dumps(extraction_result)}]"
            
            input_state = {"messages": [HumanMessage(content=user_message)]}
            logger.info(f"Attached extracted data to input for thread {thread_id[:8]}...")
        else:
            input_state = {"messages": [HumanMessage(content=user_message)]}

        #fpl padi agent
        agent = await get_agent()
        
        # Invoke the agent
        response_state = await agent.ainvoke(input_state, config=config)
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

        #updating the sessions column
        session.updated_at = datetime.utcnow() 
        session.message_count += 2 #updating both jser and agent messages

        # Commit both messages
        await db.commit()
        logger.info(f"Successfully committed chat messages to database - Thread: {thread_id[:8]}...")
        
        await db.refresh(user_msg)
        await db.refresh(agent_msg)
        await db.refresh(session)

        logger.info(f"Chat creation completed successfully - Thread: {thread_id[:8]}..., Messages: 2")

        return {
            "thread_id": thread_id,
            "response": agent_response,      
            "status": "success", 
            "timestamp": agent_msg.timestamp.isoformat(),
            "message_count": session.message_count
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
    
async def get_or_create_session(db: AsyncSession, thread_id: str, user_id: str):  # Fixed function name
    """
    Get existing chat session or create a new one
    
    Args:
        db: Database session
        thread_id: Thread identifier
        user_id: User identifier
        
    Returns:
        ChatSession: The session object
        
    Raises:
        Exception: If session management fails
    """
    try:
        logger.debug(f"Getting or creating session for thread {thread_id[:8]}...")
        
        stmt = select(ChatSession).where(ChatSession.thread_id == thread_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            logger.debug(f"Found existing session for thread {thread_id[:8]}...")
            return session
        else:
            logger.info(f"Creating new session for thread {thread_id[:8]}...")
            session = ChatSession(
                thread_id=thread_id,
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                message_count=0
            )

            db.add(session)
            # Don't commit here - will be committed with messages
            logger.debug(f"New session created for thread {thread_id[:8]}...")
            
            return session
            
    except Exception as e:
        logger.error(f"Error managing session for thread {thread_id[:8]}...: {str(e)}")
        raise Exception(f"Failed to manage chat session: {str(e)}")
    
async def get_user_sessions(db: AsyncSession, user_id: str, limit: int = 20):
    """
    Get user's recent chat sessions
    
    Args:
        db: Database session
        user_id: User identifier
        limit: Maximum number of sessions to return
        
    Returns:
        list: List of ChatSession objects or empty list
        
    Raises:
        Exception: If query fails
    """
    try:
        logger.info(f"Getting sessions for user {user_id}, limit: {limit}")
        
        if not user_id:
            logger.warning("Empty user_id provided to get_user_sessions")
            return []
            
        stmt = select(ChatSession).where(
            ChatSession.user_id == user_id
        ).order_by(
            ChatSession.updated_at.desc()
        ).limit(limit)
        
        result = await db.execute(stmt)
        sessions = result.scalars().all()

        logger.info(f"Retrieved {len(sessions)} sessions for user {user_id}")
        
        return sessions if sessions else []
        
    except Exception as e:
        logger.error(f"Error getting user sessions for user {user_id}: {str(e)}")
        raise Exception(f"Failed to get user sessions: {str(e)}")
    
    
async def get_session_history(db: AsyncSession, thread_id: str):
    """
    Get all messages for a specific thread
    
    Args:
        db: Database session
        thread_id: Thread identifier
        
    Returns:
        list: List of ChatMessage objects ordered by timestamp, or empty list
        
    Raises:
        Exception: If query fails
    """
    try:
        logger.info(f"Getting session history for thread {thread_id[:8]}...")
        
        if not thread_id:
            logger.warning("Empty thread_id provided to get_session_history")
            return []
            
        stmt = select(ChatMessage).where(
            ChatMessage.thread_id == thread_id
        ).order_by(ChatMessage.timestamp)

        result = await db.execute(stmt)
        messages = result.scalars().all()  # Fixed: Added parentheses

        logger.info(f"Retrieved {len(messages)} messages for thread {thread_id[:8]}...")
        
        # Return empty list instead of None for consistency
        return messages if messages else []
        
    except Exception as e:
        logger.error(f"Error getting session history for thread {thread_id[:8]}...: {str(e)}")
        raise Exception(f"Failed to get session history: {str(e)}")

async def delete_chat_session(db: AsyncSession, thread_id: str, user_id: str):
    """
    Delete a chat session and all its messages (with ownership check)
    
    Args:
        db: Database session
        thread_id: Thread identifier to delete
        user_id: User identifier for ownership verification
        
    Returns:
        dict: Deletion summary
        
    Raises:
        Exception: If deletion fails or user doesn't own session
    """
    try:
        logger.info(f"Deleting chat session {thread_id[:8]}... for user {user_id}")
        
    
        session_stmt = select(ChatSession).where(
            ChatSession.thread_id == thread_id,
            ChatSession.user_id == user_id
        )
        session_result = await db.execute(session_stmt)
        session = session_result.scalar_one_or_none()
        
        if not session:
            logger.warning(f"Session {thread_id[:8]}... not found or user {user_id} doesn't own it")
            raise Exception("Session not found or access denied")
        
        # Count messages before deletion for logging
        message_stmt = select(ChatMessage).where(ChatMessage.thread_id == thread_id)
        message_result = await db.execute(message_stmt)
        message_count = len(message_result.scalars().all())
        
        # Delete all messages for this thread
        await db.execute(
            ChatMessage.__table__.delete().where(ChatMessage.thread_id == thread_id)
        )
        
        # Delete the session
        await db.execute(
            ChatSession.__table__.delete().where(
                ChatSession.thread_id == thread_id,
                ChatSession.user_id == user_id
            )
        )
        
        await db.commit()
        
        logger.info(f"Successfully deleted session {thread_id[:8]}... - Messages: {message_count}")
        
        return {
            "thread_id": thread_id,
            "deleted_messages": message_count,
            "deleted_session": True,
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error deleting chat session {thread_id[:8]}...: {str(e)}")
        await db.rollback()
        raise Exception(f"Failed to delete chat session: {str(e)}")

