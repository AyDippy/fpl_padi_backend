from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
import uuid
from datetime import datetime

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, index=True)
    user_id = Column(String, nullable=True, index=True)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    timestamp = Column(DateTime, default=datetime.utcnow)

# class ChatSession(Base):
#     __tablename__ = "chat_sessions"
    
#     id = Column(Integer, primary_key=True, index=True)
#     thread_id = Column(String, unique=True, index=True)
#     user_id = Column(String, nullable=True, index=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow)
#     message_count = Column(Integer, default=0)