from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv
from os import getenv
from typing import Optional

_env_path = find_dotenv()  # locate a .env file in this folder or parent folders
if _env_path:
    load_dotenv(_env_path)


class Settings(BaseSettings):
    # Api keys
    SHODAN_API_KEY: str = getenv('SHODAN_API_KEY')
    VIRUS_TOTAL_API_KEY: str = getenv('VIRUS_TOTAL_API_KEY')
    OTX_API_KEY: str = getenv('OTX_API_KEY')
    
    # Database related
    DB_HOST_IP: str = getenv('DB_HOST_IP')
    DB_USER: str = getenv('DB_USER')
    DB_PASSWORD: str = getenv('DB_PASSWORD')
    DB_NAME: str = getenv('DB_NAME')
    
    # Notification webhooks (optional)
    # These may be unset in environments where notifications aren't configured.
    SLACK_WEBHOOK_URL: Optional[str] = getenv('SLACK_WEBHOOK_URL')
    DISCORD_WEBHOOK_URL: Optional[str] = getenv('DISCORD_WEBHOOK_URL')
        
settings = Settings()