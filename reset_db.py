# reset_db.py
import pymysql

DB_NAME = "lol_stats"
DB_USER = "lol_user"
DB_PASS = "lol_pass"
DB_HOST = "localhost"
DB_PORT = 3306

if __name__ == "__main__":
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            charset="utf8mb4",
            autocommit=True
        )
        cursor = conn.cursor()

        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
       

        print("✅ Database reset successfully.")
    except Exception as e:
        print("❌ Failed to reset database:", e)
