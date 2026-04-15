import time

class StatusManager:
    def __init__(self):
        # 任务状态
        self.tasks = {}
        # 系统状态
        self.system_status = {
            "status": "healthy",
            "last_updated": time.time()
        }
    
    def update_task_status(self, task_id, status, result=None):
        """
        更新任务状态
        
        Args:
            task_id (str): 任务ID
            status (str): 任务状态
            result (dict): 任务结果
        """
        # 如果任务不存在，创建新任务记录
        if task_id not in self.tasks:
            self.tasks[task_id] = {
                "id": task_id,
                "status": status,
                "created_at": time.time(),
                "updated_at": time.time()
            }
        else:
            # 更新任务状态
            self.tasks[task_id]["status"] = status
            self.tasks[task_id]["updated_at"] = time.time()
        
        # 如果有结果，添加结果
        if result:
            self.tasks[task_id]["result"] = result
    
    def get_task_status(self, task_id):
        """
        获取任务状态
        
        Args:
            task_id (str): 任务ID
            
        Returns:
            dict: 任务状态
        """
        return self.tasks.get(task_id, None)
    
    def get_all_tasks(self):
        """
        获取所有任务
        
        Returns:
            dict: 所有任务
        """
        return self.tasks
    
    def get_tasks_by_status(self, status):
        """
        根据状态获取任务
        
        Args:
            status (str): 任务状态
            
        Returns:
            list: 任务列表
        """
        return [task for task in self.tasks.values() if task["status"] == status]
    
    def update_system_status(self, status):
        """
        更新系统状态
        
        Args:
            status (str): 系统状态
        """
        self.system_status["status"] = status
        self.system_status["last_updated"] = time.time()
    
    def get_system_status(self):
        """
        获取系统状态
        
        Returns:
            dict: 系统状态
        """
        return self.system_status
    
    def get_task_statistics(self):
        """
        获取任务统计信息
        
        Returns:
            dict: 任务统计信息
        """
        # 初始化统计信息
        stats = {
            "total": len(self.tasks),
            "queued": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        # 统计各状态的任务数
        for task in self.tasks.values():
            status = task.get("status")
            if status in stats:
                stats[status] += 1
        
        return stats