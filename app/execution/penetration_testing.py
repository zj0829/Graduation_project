from app.execution.tool_adapter import ToolAdapter

class PenetrationTesting:
    def __init__(self):
        self.tool_adapter = ToolAdapter()
    
    def run_burp_suite(self, target, proxy_port=None):
        """
        运行Burp Suite
        
        Args:
            target (str): 目标URL
            proxy_port (str): 代理端口
            
        Returns:
            dict: 执行结果
        """
        parameters = {
            "target": target
        }
        
        if proxy_port:
            parameters["proxy_port"] = proxy_port
        
        return self.tool_adapter.execute("burp_suite", parameters)
    
    def run_penetration_test(self, target, tools=None):
        """
        执行渗透测试
        
        Args:
            target (str): 目标
            tools (list): 要使用的工具列表
            
        Returns:
            dict: 测试结果
        """
        results = {}
        
        # 如果没有指定工具，使用默认工具
        if not tools:
            tools = ["burp_suite"]
        
        # 执行每个工具
        for tool in tools:
            if tool == "burp_suite":
                results[tool] = self.run_burp_suite(target)
        
        return results