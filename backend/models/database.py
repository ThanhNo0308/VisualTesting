import mysql.connector
from mysql.connector import Error
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseConfig:
    """Cấu hình kết nối MySQL"""
    HOST = 'localhost'
    USER = 'root'
    PASSWORD = '123456'
    DATABASE = 'visual_testing'
    PORT = 3306

DATABASE_URL = f"mysql+pymysql://{DatabaseConfig.USER}:{DatabaseConfig.PASSWORD}@{DatabaseConfig.HOST}:{DatabaseConfig.PORT}/{DatabaseConfig.DATABASE}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency để lấy database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_connection():
    """Kết nối tới MySQL và trả về connection (legacy)"""
    try:
        connection = mysql.connector.connect(
            host=DatabaseConfig.HOST,
            user=DatabaseConfig.USER,
            password=DatabaseConfig.PASSWORD,
            database=DatabaseConfig.DATABASE,
            port=DatabaseConfig.PORT
        )
        
        if connection.is_connected():
            print(f"Kết nối MySQL thành công: {DatabaseConfig.DATABASE}")
            return connection
        else:
            print("Không thể kết nối MySQL")
            return None
            
    except Error as e:
        print(f"Lỗi kết nối MySQL: {e}")
        return None

def close_connection(connection):
    """Đóng kết nối MySQL"""
    if connection and connection.is_connected():
        connection.close()
        print("✅ Đã đóng kết nối MySQL")