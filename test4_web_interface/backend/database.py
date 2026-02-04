import mysql.connector
from mysql.connector import pooling
from typing import Optional, List, Dict, Any
import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ans_database"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci",
    "use_unicode": True,
}

connection_pool = None

def init_pool():
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="ans_pool",
                pool_size=5,
                **DB_CONFIG
            )
        except mysql.connector.Error as e:
            print(f"Erro ao criar pool de conexões: {e}")
            raise

class Database:
    @staticmethod
    def get_connection():
        if connection_pool is None:
            init_pool()
        return connection_pool.get_connection()
    
    @staticmethod
    def execute_query(query: str, params: tuple = None, fetch: bool = True) -> List[Dict[str, Any]]:
        conn = None
        try:
            conn = Database.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                results = cursor.fetchall()
                cursor.close()
                return results
            else:
                conn.commit()
                cursor.close()
                return []
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def execute_query_with_count(query: str, count_query: str, params: tuple = None, count_params: tuple = None) -> tuple:
        conn = None
        try:
            conn = Database.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(count_query, count_params or ())
            count_result = cursor.fetchone()
            total = count_result['total'] if count_result else 0
            
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            
            cursor.close()
            return results, total
        except Exception as e:
            raise e
        finally:
            if conn:
                conn.close()
