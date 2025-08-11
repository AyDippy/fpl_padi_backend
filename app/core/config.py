from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings.
    
    These settings are loaded from environment variables or a .env file.
    """
    OPENAI_API_KEY: str
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

    class Config:
        env_file = ".env"

settings = Settings()