# config.py
import logging
from sqlalchemy import create_engine

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# 数据库连接配置（MySQL in Docker）
DB_URL = "mysql+mysqlconnector://lol_user:lol_pass@127.0.0.1:3306/lol_stats"
engine = create_engine(DB_URL)
