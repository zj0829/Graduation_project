import asyncio
import json
import uuid
from app.orchestrator.tool_registry import ToolRegistry
from app.orchestrator.status_manager import StatusManager
from app.orchestrator.data_bus import DataBus
from app.common.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

class TaskScheduler:
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.status_manager = StatusManager()
        self.data_bus = DataBus()
        self.task_queue = asyncio.Queue()
        self.running_tasks = {}
        
    async def start(self):
        """启动任务调度器"""
        logger.info("任务调度器启动")
        while True:
            task = await self.task_queue.get()
            await self._execute_task(task)
            self.task_queue.task_done()
    
    async def schedule_task(self, tool_name, parameters):
        """
        调度任务
        
        Args:
            tool_name (str): 工具名称
            parameters (dict): 工具参数
            
        Returns:
            str: 任务ID
        """
        task_id = f"task-{uuid.uuid4()}"
        task = {
            "id": task_id,
            "tool": tool_name,
            "parameters": parameters,
            "status": "pending",
            "created_at": asyncio.get_event_loop().time()
        }
        
        self.status_manager.set_task_status(task_id, "pending")
        await self.task_queue.put(task)
        logger.info(f"任务调度成功: {task_id}, 工具: {tool_name}")
        
        return task_id
    
    async def _execute_task(self, task):
        """
        执行任务
        
        Args:
            task (dict): 任务信息
        """
        task_id = task["id"]
        tool_name = task["tool"]
        parameters = task["parameters"]
        
        try:
            # 更新任务状态为运行中
            self.status_manager.set_task_status(task_id, "running")
            logger.info(f"开始执行任务: {task_id}, 工具: {tool_name}")
            
            # 获取工具信息
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                raise Exception(f"工具不存在: {tool_name}")
            
            # 执行工具
            result = await self._execute_tool(tool, parameters)
            
            # 更新任务状态为完成
            self.status_manager.set_task_status(task_id, "completed")
            logger.info(f"任务执行完成: {task_id}, 工具: {tool_name}")
            
            # 存储结果
            self.data_bus.store_result(task_id, result)
            
        except Exception as e:
            # 更新任务状态为失败
            self.status_manager.set_task_status(task_id, "failed")
            logger.error(f"任务执行失败: {task_id}, 工具: {tool_name}, 错误: {e}")
            
            # 存储错误信息
            self.data_bus.store_result(task_id, {"error": str(e)})
    
    async def _execute_tool(self, tool, parameters):
        """
        执行工具
        
        Args:
            tool (dict): 工具信息
            parameters (dict): 工具参数
            
        Returns:
            dict: 执行结果
        """
        executable = tool["executable"]
        tool_name = tool["name"]
        
        try:
            # 构建命令
            command = [executable]
            
            # 添加参数
            for param_name, param_value in parameters.items():
                if param_value:
                    command.extend([f"--{param_name}", str(param_value)])
            
            logger.info(f"执行命令: {command}")
            
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 等待命令执行完成
            stdout, stderr = await process.communicate()
            
            # 解析结果
            result = {
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "returncode": process.returncode
            }
            
            logger.info(f"命令执行成功, 结果: {result}")
            return result
            
        except Exception as e:
            logger.error(f"执行工具失败: {tool_name}, 错误: {e}")
            return {"error": str(e)}
    
    async def execute_test_plan(self, test_plan, tools):
        """
        执行测试计划
        
        Args:
            test_plan (dict): 测试计划
            tools (list): 选择的工具
            
        Returns:
            dict: 执行结果
        """
        test_id = f"test-{uuid.uuid4()}"
        results = {}
        
        try:
            logger.info(f"开始执行测试计划: {test_id}")
            
            # 执行每个工具
            for tool_name in tools:
                logger.info(f"执行工具: {tool_name}")
                
                # 构建工具参数
                parameters = {
                    "target": test_plan.get("target", ""),
                    "scope": test_plan.get("scope", ""),
                    "test_type": test_plan.get("test_type", "")
                }
                
                # 调度任务
                task_id = await self.schedule_task(tool_name, parameters)
                
                # 等待任务完成
                while self.status_manager.get_task_status(task_id) != "completed":
                    await asyncio.sleep(1)
                    if self.status_manager.get_task_status(task_id) == "failed":
                        break
                
                # 获取任务结果
                result = self.data_bus.get_result(task_id)
                results[tool_name] = result
            
            logger.info(f"测试计划执行完成: {test_id}")
            return {
                "test_id": test_id,
                "results": results,
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"执行测试计划失败: {test_id}, 错误: {e}")
            return {
                "test_id": test_id,
                "results": results,
                "status": "failed",
                "error": str(e)
            }
    
    def get_task_status(self, task_id):
        """
        获取任务状态
        
        Args:
            task_id (str): 任务ID
            
        Returns:
            str: 任务状态
        """
        return self.status_manager.get_task_status(task_id)
    
    def get_task_result(self, task_id):
        """
        获取任务结果
        
        Args:
            task_id (str): 任务ID
            
        Returns:
            dict: 任务结果
        """
        return self.data_bus.get_result(task_id)