import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    MODEL: str = os.getenv("MODEL", "")
    BASE_URL: str = os.getenv("BASE_URL", "")

    class Config:
        env_file = ".env"
       

settings = Settings()
