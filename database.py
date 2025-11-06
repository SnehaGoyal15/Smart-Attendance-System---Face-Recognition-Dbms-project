import pymysql
import time

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Sneha1419@',
    'database': 'smart_attendance_system',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    try:
        conn = pymysql.connect(**db_config)
        return conn
    except pymysql.Error as e:
        print(f"❌ MySQL Connection Error: {e}")
        return None

def init_db():
    """Database connection verify karo"""
    conn = get_db_connection()
    if conn:
        print("✅ Connected to database successfully!")
        conn.close()
    else:
        print("❌ Failed to connect to database!")

def execute_with_retry(query, params=None, max_retries=3):
    """Database operations with retry mechanism for lock timeout"""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed"
    
    cursor = conn.cursor()
    
    for attempt in range(max_retries):
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            return cursor, "Success"
            
        except pymysql.Error as e:
            if e.args[0] == 1205:  # Lock wait timeout
                print(f"⚠️ Lock timeout detected, retrying... ({attempt + 1}/{max_retries})")
                time.sleep(1)  # Wait 1 second before retry
                continue
            else:
                conn.rollback()
                return None, f"Database error: {e}"
        except Exception as e:
            conn.rollback()
            return None, f"Unexpected error: {e}"
        finally:
            cursor.close()
            conn.close()
    
    return None, "Max retries exceeded, lock timeout"