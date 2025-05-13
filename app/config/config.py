from os import getenv

class Config:
    SHODAN_API_KEY = getenv("SHODAN_API_KEY")
    VIRUSTOTAL_API_KEY = getenv("VIRUSTOTAL_API_KEY")
    #DB_HOST = getenv("DB_HOST")
    DB_USER = getenv("DB_USER")
    DB_PASSWORD = getenv("DB_PASSWORD")
    DB_NAME = getenv("DB_NAME")
    DB_HOST_IP = getenv("DB_HOST_IP")