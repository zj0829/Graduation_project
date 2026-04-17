from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from app.report.report_generator import ReportGenerator
from app.orchestrator.db import get_report

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


@router.get("/print/{test_id}", response_class=HTMLResponse)
def print_report(test_id: str):
    report_data = get_report(test_id)
    if not report_data:
        raise HTTPException(status_code=404, detail="报告不存在")
    report_content = report_data.get("report", "") or report_data.get("analysis", "")
    target = report_data.get("target", "Unknown")
    created = report_data.get("created_at", "")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>渗透测试报告 - {target}</title>
<style>
body {{ font-family: 'Microsoft YaHei', 'SimHei', sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 30px; color: #1a1a2e; line-height: 1.8; font-size: 14px; }}
h1 {{ color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 8px; font-size: 22px; }}
h2 {{ color: #334155; margin-top: 24px; font-size: 18px; border-left: 4px solid #1e40af; padding-left: 10px; }}
h3 {{ color: #475569; font-size: 15px; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
th {{ background: #1e40af; color: white; padding: 8px 12px; text-align: left; }}
td {{ padding: 8px 12px; border: 1px solid #e2e8f0; }}
tr:nth-child(even) {{ background: #f8fafc; }}
code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 13px; font-family: Consolas, monospace; }}
pre {{ background: #1e293b; color: #e2e8f0; padding: 14px; border-radius: 8px; overflow-x: auto; font-size: 13px; }}
pre code {{ background: none; color: inherit; padding: 0; }}
blockquote {{ border-left: 3px solid #1e40af; padding: 4px 12px; background: #eff6ff; margin: 8px 0; }}
.meta {{ color: #64748b; font-size: 12px; margin-bottom: 20px; }}
@media print {{ body {{ padding: 20px; }} }}
</style>
</head>
<body>
<div class="meta">目标: {target} | 生成时间: {created}</div>
<div id="content">{report_content}</div>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script>
document.getElementById('content').innerHTML = marked.parse(document.getElementById('content').textContent);
setTimeout(() => window.print(), 500);
</script>
</body>
</html>"""
    return html