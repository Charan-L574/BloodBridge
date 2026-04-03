"""
MySQL Database Setup Script
Creates the bloodbridge database if it doesn't exist
"""
import pymysql
from config import settings

def create_database():
    """Create MySQL database if it doesn't exist"""
    try:
        # Connect to MySQL server without specifying database
        connection = pymysql.connect(
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            port=settings.DB_PORT
        )
        
        with connection.cursor() as cursor:
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Database '{settings.DB_NAME}' created successfully (or already exists)")
            
        connection.commit()
        connection.close()
        
        print(f"✅ MySQL connection successful!")
        print(f"   Host: {settings.DB_HOST}:{settings.DB_PORT}")
        print(f"   Database: {settings.DB_NAME}")
        
        return True
        
    except pymysql.Error as e:
        print(f"❌ MySQL Error: {e}")
        print("\n⚠️ Please check:")
        print("   1. MySQL service is running")
        print("   2. Username and password are correct in config.py or .env")
        print("   3. MySQL is listening on the correct port")
        return False

if __name__ == "__main__":
    create_database()
