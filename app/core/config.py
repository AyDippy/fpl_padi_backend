from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """
    Application settings.
    
    These settings are loaded from environment variables or a .env file.
    """
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    TEMPLATE_FOLDER: str
    DB_HOST: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_PORT: str
    DB_URI: str
    TAVILY_API_KEY: str
    CURRENT_FPL_SEASON: str = "2025/2026"  
    CURRENT_GAMEWEEK: int = 7
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "fpl_padi"
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 300  # 5 minutes default cache time
    REDIS_SCOUT_CACHE_TTL: int = 3600  # 1 hour for scout picks
    DB_URI_FPL: str
    RESEND_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()

#langsmith
os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2
os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT