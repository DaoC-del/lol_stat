# db.py
import pandas as pd
from sqlalchemy import inspect, text
from config.config import engine
from rich.console import Console

console = Console()

def insert_data(table_name: str, df: pd.DataFrame):
    df.to_sql(table_name, engine, if_exists='append', index=False)
    console.print(f"✅ Inserted {len(df)} rows into '{table_name}' table")

def show_status():
    inspector = inspect(engine)
    for tbl in inspector.get_table_names():
        count = pd.read_sql(f"SELECT COUNT(*) AS cnt FROM `{tbl}`", engine)['cnt'][0]
        console.print(f"{tbl}: {count:,} rows")

def clear_tables():
    inspector = inspect(engine)
    with engine.begin() as conn:
        for tbl in inspector.get_table_names():
            conn.execute(text(f"TRUNCATE TABLE `{tbl}`"))
            console.print(f"✅ Cleared '{tbl}'")
