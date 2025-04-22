# export_matches.py（增强兼容版）

import pandas as pd
from web.match_storage import connect_mysql
import os

EXPORT_DIR = "exports"

def export_table_to_csv(table_name: str):
    filename = f"{table_name}_export.csv"
    filepath = os.path.join(EXPORT_DIR, filename)

    conn = connect_mysql()
    try:
        if not os.path.exists(EXPORT_DIR):
            os.makedirs(EXPORT_DIR)
        df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"✅ 导出成功：{filepath}（共 {len(df)} 条记录）")
    except Exception as e:
        print(f"❌ 导出失败（{table_name}）：{e}")
    finally:
        conn.close()

if __name__ == "__main__":
    for table in ["matches", "participants", "teams", "players"]:
        export_table_to_csv(table)
