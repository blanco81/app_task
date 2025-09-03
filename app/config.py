import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME")    
    DB_DRIVER: str ="postgresql+asyncpg"
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: int = int(os.getenv("DB_PORT")) 
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_DATABASE: str = os.getenv("DB_DATABASE")
    ALGORITHM: str = os.getenv("ALGORITHM")  
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")) 
    DB_SECRET_KEY: str = os.getenv("DB_SECRET_KEY")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    
    DEFAULT_LIMIT: int = int(os.getenv("DEFAULT_LIMIT", 100))
    MAX_LIMIT: int = int(os.getenv("MAX_LIMIT", 500))        
    
    DATABASE_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}" 
    

settings = Settings()



print("----ENV DB Settings----")
print(f"DB_USER: {settings.DB_USER}")
print(f"DB_PASSWORD: {settings.DB_PASSWORD}")
print(f"DB_HOST: {settings.DB_HOST}")
print(f"DB_PORT: {settings.DB_PORT}")
print(f"DB_DATABASE: {settings.DB_DATABASE}")