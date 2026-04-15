from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import uvicorn

# 导入路由
from app.llm_brain.routes import router as llm_router
from app.orchestrator.routes import router as orchestrator_router
from app.report.routes import router as report_router
from app.common.routes import router as logs_router
from app.chat.routes import router as chat_router

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI(
    title="LLM-Penetration-Testing",
    description="基于大模型的Web应用渗透测试智能辅助系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(llm_router)
app.include_router(orchestrator_router)
app.include_router(report_router)
app.include_router(logs_router)
app.include_router(chat_router)

# 健康检查端点
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# 根路径
@app.get("/")
def read_root():
    return {"message": "Welcome to LLM-Penetration-Testing API"}

# 前端页面
@app.get("/ui")
def get_ui():
    return {"message": "请访问 /static/index.html 查看前端页面"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)