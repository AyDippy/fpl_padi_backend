# test_db_connection.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Test different connection methods
def test_connection_method_1():
    """Test with individual parameters"""
    try:
        print("Testing connection method 1 (individual parameters)...")
        conn = psycopg2.connect(
            host="shuttle.proxy.rlwy.net",
            dbname="railway",
            user="postgres",
            password="VmJHoEMlrkWtBJOTNXvvcuMulUGkVKxp",
            port="25974",
            connect_timeout=10
        )
        print("✅ Method 1: Connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Method 1 failed: {e}")
        return False

def test_connection_method_2():
    """Test with connection string"""
    try:
        print("Testing connection method 2 (connection string)...")
        conn = psycopg2.connect(
            "postgresql://postgres:VmJHoEMlrkWtBJOTNXvvcuMulUGkVKxp@shuttle.proxy.rlwy.net:25974/railway"
        )
        print("✅ Method 2: Connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Method 2 failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing database connectivity...\n")
    
    success1 = test_connection_method_1()
    print()
    success2 = test_connection_method_2()
    
    if success1 or success2:
        print("\n🎉 Database connection is working!")
    else:
        print("\n💥 Both connection methods failed!")