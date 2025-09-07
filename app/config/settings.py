from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from os import getenv

load_dotenv()

class Settings(BaseSettings):
    # Api keys
    SHODAN_API_KEY: str = getenv('SHODAN_API_KEY')
    VIRUS_TOTAL_API_KEY: str = getenv('VIRUS_TOTAL_API_KEY')
    OTX_API_KEY: str = getenv('OTX_API_KEY')
    
    # Database related
    DB_HOST_IP: str = getenv('DB_HOST_IP')
    DB_USER: str = getenv('DB_USER')
    DB_PORT: str = getenv('DB_PORT')
    DB_PASSWORD: str = getenv('DB_PASSWORD')
    DB_NAME: str = getenv('DB_NAME')
        
settings = Settings() 