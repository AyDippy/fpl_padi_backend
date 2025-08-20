from app.core.logging import logger
from app.db.session import db_session
from app.crud.chat import create_chat, get_session_history, get_user_sessions, delete_chat_session
from app.schemas.chat import ChatRequest, ChatResponse
from fastapi import Depends, APIRouter, Path, HTTPException
from app.api.v1.endpoints.users import get_current_user
from typing import Annotated
from app.schemas.user import UserResponse
import uuid

router =APIRouter(
    prefix='/chat',
    tags = ["chats"]
)

@router.post('/new')
async def new_chat(
    db: db_session, 
    chat: ChatRequest, 
    user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Start a new chat conversation"""
    try:
        user_message = chat.message
        user_id = str(user.id)
        thread_id = str(uuid.uuid4())

        logger.info(f"Starting new chat - User: {user_id}, Thread: {thread_id[:8]}..., Message length: {len(user_message)}")

        # Validate message content
        if not user_message or not user_message.strip():
            logger.warning(f"Empty message received from user {user_id}")
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Create chat using CRUD
        response = await create_chat(
            db=db, 
            message=user_message, 
            thread_id=thread_id, 
            user_id=user_id
        )

        logger.info(f"New chat created successfully - User: {user_id}, Thread: {thread_id[:8]}...")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in new_chat - User: {user_id if 'user_id' in locals() else 'Unknown'}, Error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to create new chat. Please try again."
        )

@router.post('/{session_id}')
async def continue_chat(
    db: db_session, 
    session_id: Annotated[str, Path(description="Thread ID for chat history")], 
    chat: ChatRequest, 
    user: Annotated[UserResponse, Depends(get_current_user)]
):
    """Continue existing chat conversation"""
    try:
        user_message = chat.message
        user_id = str(user.id)  # Fixed: Convert to string for consistency

        logger.info(f"Continuing chat - User: {user_id}, Session: {session_id[:8]}..., Message length: {len(user_message)}")

        try:
            uuid.UUID(session_id)
        except ValueError:
            logger.warning(f"Invalid session_id format from user {user_id}: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session_id format")

        # Validate message content
        if not user_message or not user_message.strip():
            logger.warning(f"Empty message received from user {user_id} for session {session_id[:8]}...")
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Continue chat using CRUD
        response = await create_chat(
            db=db, 
            message=user_message, 
            thread_id=session_id, 
            user_id=user_id
        )

        logger.info(f"Chat continued successfully - User: {user_id}, Session: {session_id[:8]}...")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in continue_chat - User: {user_id if 'user_id' in locals() else 'Unknown'}, Session: {session_id[:8] if 'session_id' in locals() else 'Unknown'}, Error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to continue chat. Please try again."
        )

@router.get('/history/{session_id}')
async def user_session_history(
    db: db_session, 
    session_id: Annotated[str, Path(description="Session ID to get history for")],
    user: Annotated[UserResponse, Depends(get_current_user)]
):
    try:
        user_id = str(user.id)
        logger.info(f"Getting history - User: {user_id}, Session: {session_id[:8]}...")
        
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            logger.warning(f"Invalid session_id format from user {user_id}: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session_id format")
        
        messages = await get_session_history(db, session_id)
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

@router.get('/sessions')
async def user_entire_sessions(
    db: db_session, 
    user: Annotated[UserResponse, Depends(get_current_user)]
):
    try:
        user_id = str(user.id)
        logger.info(f"Getting sessions - User: {user_id}")
        
        sessions = await get_user_sessions(db, user_id) 
        return sessions 
        
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user sessions")

@router.delete("/{session_id}")  
async def delete_user_chat_session(
    db: db_session, 
    session_id: Annotated[str, Path(description="Session ID to delete")],
    user: Annotated[UserResponse, Depends(get_current_user)]
):
    try:
        user_id = str(user.id)
        logger.info(f"Deleting session - User: {user_id}, Session: {session_id[:8]}...")
        
        # Validate session_id format
        try:
            uuid.UUID(session_id)
        except ValueError:
            logger.warning(f"Invalid session_id format from user {user_id}: {session_id}")
            raise HTTPException(status_code=400, detail="Invalid session_id format")
        
        deleted_session = await delete_chat_session(db, session_id, user_id)  
        return deleted_session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete session")