# init_db.py
from web.match_storage import connect_mysql, init_tables_if_missing

if __name__ == "__main__":
    try:
        conn = connect_mysql()
        init_tables_if_missing(conn)
        print("✅ Database tables initialized successfully.")
    except Exception as e:
        print("❌ Failed to initialize tables:", e)
