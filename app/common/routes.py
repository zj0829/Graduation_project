from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from app.common.logger import LOG_FILE

# 创建路由器
router = APIRouter(prefix="/api/logs", tags=["Logs"])

# 数据模型
class LogRequest(BaseModel):
    lines: int = 100
    level: str = "all"

# 获取日志
@router.get("/")
def get_logs(lines: int = 100, level: str = "all"):
    try:
        # 检查日志文件是否存在
        if not os.path.exists(LOG_FILE):
            return {"status": "success", "logs": [], "message": "日志文件不存在"}
        
        # 读取日志文件
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            log_lines = f.readlines()
        
        # 限制返回的行数
        log_lines = log_lines[-lines:]
        
        # 根据级别过滤日志
        if level != "all":
            filtered_lines = []
            for line in log_lines:
                if f"-{level.upper()}-" in line:
                    filtered_lines.append(line.strip())
            log_lines = filtered_lines
        else:
            log_lines = [line.strip() for line in log_lines]
        
        return {"status": "success", "logs": log_lines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

# 清空日志
@router.delete("/")
def clear_logs():
    try:
        # 清空日志文件
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")
        
        return {"status": "success", "message": "日志已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空日志失败: {str(e)}")