import logging
import os

# 指定本地日誌文字檔路徑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_FILE_PATH = os.path.join(BASE_DIR, "tracebite_agent.log")

def setup_logger():
    logger = logging.getLogger("tracebite")
    # 設定最底層接收等級為 DEBUG，以便完整寫入 txt 檔案
    logger.setLevel(logging.DEBUG)
    
    # 避免重置 handler 導致重複輸出
    if not logger.handlers:
        # 設定標準日誌格式
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s"
        )
        
        # 1. Console Handler (輸出 INFO 以上等級)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 2. File Handler (輸出 DEBUG 以上等級，寫入本地 .log/.txt)
        try:
            log_dir = os.path.dirname(LOG_FILE_PATH)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # 降級輸出錯誤，但不阻斷執行
            print(f"[Warning] Failed to initialize file logger: {e}")
            
    return logger

# 導出全域 logger
logger = setup_logger()
