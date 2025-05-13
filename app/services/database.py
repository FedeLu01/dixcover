import pymysql
from app.config.config import Config
from dbutils.pooled_db import PooledDB

class DatabaseManager:
    pool = None
    
    @classmethod
    def initialize_pool(cls):
        try:
            if cls.pool is None:
                cls.pool = PooledDB(
                    creator=pymysql,
                    maxconnections=10,  # máximo número de conexiones
                    mincached=2,  # número mínimo de conexiones en el pool
                    maxcached=5,  # número máximo de conexiones en el pool
                    blocking=True,  # bloquea si no hay conexiones disponibles
                    host="172.25.128.1", # Tengo que usar state de fastapi aca
                    port=3306,
                    user="dev_dixcover",
                    password="dixcover",
                    database="dev_dixcover"
                    )
        except pymysql.MySQLError as e:
            print(f"Error initializing database pool: {e}")
            raise
    
    def __init__(self):
        if DatabaseManager.pool is None:
            DatabaseManager.initialize_pool()
        
    def execute_query(self, query, params=None):
        connection = DatabaseManager.pool.connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                connection.commit()
                return cursor.lastrowid
        except pymysql.MySQLError as e:
            print(f"Error ejecutando query: {e}")
            return None


    def insert_data(self, subdomain, registered_on, detected_at):
        """ Ejecuta una consulta INSERT """
        query = """
        INSERT INTO subdomains (subdomain, registered_on, detected_at) 
        VALUES (%s, %s, %s)
        """
        params = (subdomain, registered_on, detected_at)
        return self.execute_query(query, params)
        