from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.orchestrator.tool_registry import ToolRegistry
from app.orchestrator.task_scheduler import TaskScheduler
from app.orchestrator.status_manager import StatusManager
from app.orchestrator.db import save_report, get_report, list_reports, delete_report
from app.llm_brain.llm_interface import LLMInterface
from app.report.report_generator import ReportGenerator
import httpx
import time

router = APIRouter(prefix="/api/orchestrator", tags=["Orchestrator"])

tool_registry = ToolRegistry()
task_scheduler = TaskScheduler()
status_manager = StatusManager()
llm_interface = LLMInterface()
report_generator = ReportGenerator()

# 数据模型
class TaskRequest(BaseModel):
    tool: str
    parameters: dict

class TestPlanRequest(BaseModel):
    test_plan: dict
    tools: list

class ExecuteTestRequest(BaseModel):
    target: str
    requirements: str
    tools: list
    tool_strategy: str = "auto"
    report_format: str = "markdown"

# 获取所有工具
@router.get("/tools")
def get_all_tools():
    try:
        tools = tool_registry.get_all_tools()
        return {"status": "success", "tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具失败: {str(e)}")

# 获取工具信息
@router.get("/tools/{tool_name}")
def get_tool(tool_name: str):
    try:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 {tool_name} 不存在")
        return {"status": "success", "tool": tool}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取工具失败: {str(e)}")

# 调度任务
@router.post("/tasks")
async def schedule_task(request: TaskRequest):
    try:
        # 验证工具是否存在
        tool = tool_registry.get_tool(request.tool)
        if not tool:
            raise HTTPException(status_code=404, detail=f"工具 {request.tool} 不存在")
        
        # 验证参数
        for param in tool.get("parameters", []):
            if param.get("required") and param.get("name") not in request.parameters:
                raise HTTPException(status_code=400, detail=f"缺少必要参数: {param.get('name')}")
        
        # 调度任务
        task_id = await task_scheduler.schedule_task({
            "tool": request.tool,
            "parameters": request.parameters
        })
        
        return {"status": "success", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调度任务失败: {str(e)}")

# 获取任务状态
@router.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    try:
        task = status_manager.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        return {"status": "success", "task": task}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

# 获取所有任务
@router.get("/tasks")
def get_all_tasks():
    try:
        tasks = status_manager.get_all_tasks()
        return {"status": "success", "tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务失败: {str(e)}")

# 获取任务统计信息
@router.get("/tasks/statistics")
def get_task_statistics():
    try:
        stats = status_manager.get_task_statistics()
        return {"status": "success", "statistics": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务统计信息失败: {str(e)}")

# 获取系统状态
@router.get("/system/status")
def get_system_status():
    try:
        status = status_manager.get_system_status()
        return {"status": "success", "system_status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")

# 执行测试计划
@router.post("/test-plan")
async def execute_test_plan(request: TestPlanRequest):
    try:
        test_plan = request.test_plan
        steps = test_plan.get("steps", [])
        task_ids = []
        
        # 执行测试计划中的每个步骤
        for step in steps:
            tools = step.get("tools", [])
            for tool in tools:
                # 调度工具执行
                task_id = await task_scheduler.schedule_task({
                    "tool": tool,
                    "parameters": step.get("parameters", {})
                })
                task_ids.append(task_id)
        
        return {"status": "success", "task_ids": task_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行测试计划失败: {str(e)}")

# 执行测试
@router.post("/execute-test")
async def execute_test(request: ExecuteTestRequest):
    try:
        # 生成测试ID
        test_id = f"test_{int(time.time())}"
        
        # 连接到CherryStudio的MCP服务
        mcp_server = "http://127.0.0.1:9876"
        
        # 确定要调用的工具列表
        tools_to_call = request.tools
        if "auto" in tools_to_call or request.tool_strategy == "auto":
            tools_to_call = ["nmap", "sqlmap"]
        
        # 1. 初始化MCP连接
        async with httpx.AsyncClient(timeout=120.0) as client:
            initialize_response = await client.post(
                f"{mcp_server}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "client": "LLM-Penetration-Testing",
                        "version": "1.0.0"
                    },
                    "id": 1
                }
            )
            
            if initialize_response.status_code != 200:
                raise Exception(f"MCP服务初始化失败: {initialize_response.status_code}")
            
            initialize_data = initialize_response.json()
            
            # 2. 获取工具列表
            tools_list_response = await client.post(
                f"{mcp_server}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": 2
                }
            )
            
            if tools_list_response.status_code != 200:
                raise Exception(f"获取工具列表失败: {tools_list_response.status_code}")
            
            tools_list_data = tools_list_response.json()
            
            # 3. 调用选定的工具
            mcp_results = {
                "tools": tools_to_call,
                "target": request.target,
                "requirements": request.requirements,
                "status": "completed",
                "message": "MCP工具调用成功",
                "results": {}
            }
            
            for tool in tools_to_call:
                try:
                    tool_call_response = await client.post(
                        f"{mcp_server}/jsonrpc",
                        json={
                            "jsonrpc": "2.0",
                            "method": "tools/call",
                            "params": {
                                "tool": tool,
                                "parameters": {
                                    "target": request.target,
                                    "options": ""
                                }
                            },
                            "id": 3 + list(tools_to_call).index(tool)
                        }
                    )
                    
                    tool_call_data = tool_call_response.json()
                    
                    if "result" in tool_call_data:
                        mcp_results["results"][tool] = tool_call_data["result"]
                    else:
                        mcp_results["results"][tool] = "工具调用成功，但无返回结果"
                except Exception as tool_error:
                    mcp_results["results"][tool] = f"工具调用失败: {str(tool_error)}"
        
        # 4. 分析工具执行结果
        analysis = llm_interface.analyze_results(mcp_results)
        
        # 5. 生成报告（使用LLM直接生成Markdown报告）
        report = llm_interface.generate_report(
            test_plan=f"目标: {request.target}, 需求: {request.requirements}, 工具: {', '.join(tools_to_call)}",
            results=str(mcp_results),
            analysis=analysis or ""
        )
        
        if not report:
            report = f"# 渗透测试报告\n\n## 测试目标\n{request.target}\n\n## 分析结果\n{analysis}\n\n## 原始数据\n{mcp_results}"
        
        save_report(
            test_id=test_id,
            target=request.target,
            requirements=request.requirements,
            tools=tools_to_call,
            tool_strategy=request.tool_strategy,
            report_format=request.report_format,
            mcp_results=mcp_results,
            analysis=analysis,
            report=report,
        )
        
        return {
            "status": "success",
            "test_id": test_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行测试失败: {str(e)}")

@router.get("/test-result/{test_id}")
async def get_test_result(test_id: str):
    try:
        row = get_report(test_id)
        if not row:
            raise Exception("测试ID不存在")
        return {
            "status": "success",
            "results": row.get("mcp_results", {}),
            "analysis": row.get("analysis", ""),
            "report": row.get("report", ""),
            "target": row.get("target", ""),
            "tools": row.get("tools", []),
            "created_at": row.get("created_at", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取测试结果失败: {str(e)}")

@router.get("/reports")
async def get_reports(limit: int = 50, offset: int = 0):
    try:
        data = list_reports(limit=limit, offset=offset)
        return {"status": "success", **data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取报告列表失败: {str(e)}")

@router.delete("/reports/{test_id}")
async def remove_report(test_id: str):
    try:
        if not delete_report(test_id):
            raise Exception("报告不存在")
        return {"status": "success", "message": "报告已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除报告失败: {str(e)}")