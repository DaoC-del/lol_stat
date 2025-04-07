# communication/task_manager.py
import concurrent.futures
from web.websocket_client import call_api

# 建立一个固定大小的线程池，可根据需要调整 max_workers 数量
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

def submit_api_task(api_name):
    # 提交任务到线程池，每次任务调用都会重新建立 websocket 连接
    return executor.submit(call_api, api_name)
