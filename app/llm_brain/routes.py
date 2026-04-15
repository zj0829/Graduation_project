from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.llm_brain.requirement_parser import RequirementParser
from app.llm_brain.task_planner import TaskPlanner
from app.llm_brain.result_analyzer import ResultAnalyzer

# 创建路由器
router = APIRouter(prefix="/api/llm", tags=["LLM Brain"])

# 初始化模块
parser = RequirementParser()
planner = TaskPlanner()
analyzer = ResultAnalyzer()

# 数据模型
class TestRequest(BaseModel):
    target: str
    requirements: str

class TestResults(BaseModel):
    test_id: str
    results: dict

# 解析需求
@router.post("/parse")
def parse_requirement(request: TestRequest):
    try:
        # 解析需求
        requirement = parser.parse(request.requirements, request.target)
        return {"status": "success", "requirement": requirement}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"需求解析失败: {str(e)}")

# 生成测试计划
@router.post("/plan")
def generate_test_plan(request: TestRequest):
    try:
        # 解析需求
        requirement = parser.parse(request.requirements, request.target)
        # 生成测试计划
        test_plan = planner.plan(requirement)
        return {"status": "success", "test_plan": test_plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试计划生成失败: {str(e)}")

# 分析测试结果
@router.post("/analyze")
def analyze_results(request: TestResults):
    try:
        # 分析结果
        analysis = analyzer.analyze(request.results)
        return {"status": "success", "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"结果分析失败: {str(e)}")