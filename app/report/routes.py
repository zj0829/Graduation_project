from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.report.report_generator import ReportGenerator

# 创建路由器
router = APIRouter(prefix="/api/report", tags=["Report"])

# 初始化模块
report_generator = ReportGenerator()

# 数据模型
class ReportRequest(BaseModel):
    test_plan: dict
    results: dict
    analysis: dict
    format: str = "markdown"

class ReportSaveRequest(BaseModel):
    report: str
    output_path: str

# 生成报告
@router.post("/generate")
def generate_report(request: ReportRequest):
    try:
        if request.format == "html":
            # 生成HTML报告
            report = report_generator.generate_html_report(
                request.test_plan,
                request.results,
                request.analysis
            )
        else:
            # 生成Markdown报告
            report = report_generator.generate_report(
                request.test_plan,
                request.results,
                request.analysis
            )
        
        return {"status": "success", "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报告失败: {str(e)}")

# 保存报告
@router.post("/save")
def save_report(request: ReportSaveRequest):
    try:
        success = report_generator.save_report(request.report, request.output_path)
        if success:
            return {"status": "success", "message": "报告保存成功"}
        else:
            raise HTTPException(status_code=500, detail="报告保存失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存报告失败: {str(e)}")