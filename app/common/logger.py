import logging
import os
from logging.handlers import RotatingFileHandler

# 日志目录
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件路径
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)

# 创建日志记录器
def get_logger(name):
    """
    获取日志记录器
    
    Args:
        name (str): 记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name)

# 示例用法
# logger = get_logger(__name__)
# logger.info("This is an info message")
# logger.error("This is an error message")