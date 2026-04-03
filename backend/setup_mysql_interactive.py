"""
Interactive MySQL Setup for BloodBridge
"""
import pymysql
import getpass
import sys

def test_mysql_connection():
    """Interactive MySQL connection setup"""
    print("=" * 60)
    print("BloodBridge - MySQL Database Setup")
    print("=" * 60)
    print()
    
    # Get MySQL credentials
    print("Please enter your MySQL credentials:")
    db_host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    db_port = input("MySQL Port (default: 3306): ").strip() or "3306"
    db_user = input("MySQL Username (default: root): ").strip() or "root"
    db_password = getpass.getpass("MySQL Password: ")
    db_name = input("Database Name (default: bloodbridge): ").strip() or "bloodbridge"
    
    print("\nTesting connection...")
    
    try:
        # Connect to MySQL server
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            port=int(db_port)
        )
        
        print("✅ MySQL connection successful!")
        
        # Create database
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Database '{db_name}' created successfully!")
            
        connection.commit()
        connection.close()
        
        # Generate .env content
        print("\n" + "=" * 60)
        print("Configuration successful! Update your .env file with:")
        print("=" * 60)
        print(f"DB_USER={db_user}")
        print(f"DB_PASSWORD={db_password}")
        print(f"DB_HOST={db_host}")
        print(f"DB_PORT={db_port}")
        print(f"DB_NAME={db_name}")
        print("=" * 60)
        
        # Ask to update .env
        update = input("\nDo you want to automatically update .env file? (y/n): ").lower()
        if update == 'y':
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            # Update DB fields
            with open('.env', 'w') as f:
                for line in lines:
                    if line.startswith('DB_USER='):
                        f.write(f'DB_USER={db_user}\n')
                    elif line.startswith('DB_PASSWORD='):
                        f.write(f'DB_PASSWORD={db_password}\n')
                    elif line.startswith('DB_HOST='):
                        f.write(f'DB_HOST={db_host}\n')
                    elif line.startswith('DB_PORT='):
                        f.write(f'DB_PORT={db_port}\n')
                    elif line.startswith('DB_NAME='):
                        f.write(f'DB_NAME={db_name}\n')
                    else:
                        f.write(line)
            
            print("✅ .env file updated successfully!")
        
        print("\n🎉 Setup complete! You can now run: python main.py")
        return True
        
    except pymysql.Error as e:
        print(f"\n❌ MySQL Error: {e}")
        print("\n⚠️ Troubleshooting tips:")
        print("   1. Make sure MySQL service is running")
        print("   2. Check your username and password")
        print("   3. Verify MySQL is listening on the correct port")
        print("   4. Try: 'mysql -u root -p' in terminal to test manually")
        return False

if __name__ == "__main__":
    test_mysql_connection()
