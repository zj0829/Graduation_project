from app.common.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.register_tools()
    
    def register_tools(self):
        """注册所有工具"""
        # 信息收集工具
        self.register_tool(
            name="nmap",
            display_name="Nmap",
            description="网络扫描工具，用于端口扫描和服务识别",
            category="information_gathering",
            executable="nmap",
            parameters=[
                {"name": "target", "required": True, "description": "目标IP或域名"},
                {"name": "ports", "required": False, "description": "端口范围"},
                {"name": "scan_type", "required": False, "description": "扫描类型"}
            ],
            output_format="text"
        )
        
        self.register_tool(
            name="amass",
            display_name="Amass",
            description="子域名枚举工具，用于发现和枚举子域名",
            category="information_gathering",
            executable="amass",
            parameters=[
                {"name": "domain", "required": True, "description": "目标域名"},
                {"name": "output", "required": False, "description": "输出文件"}
            ],
            output_format="text"
        )
        
        # 漏洞扫描工具
        self.register_tool(
            name="owasp_zap",
            display_name="OWASP ZAP",
            description="Web应用漏洞扫描工具",
            category="vulnerability_scanning",
            executable="zap-cli",
            parameters=[
                {"name": "target", "required": True, "description": "目标URL"},
                {"name": "scan_type", "required": False, "description": "扫描类型"}
            ],
            output_format="json"
        )
        
        # 漏洞验证工具
        self.register_tool(
            name="sqlmap",
            display_name="SQLmap",
            description="SQL注入漏洞验证工具",
            category="vulnerability_validation",
            executable="sqlmap",
            parameters=[
                {"name": "url", "required": True, "description": "目标URL"},
                {"name": "parameters", "required": False, "description": "参数"}
            ],
            output_format="json"
        )
        
        self.register_tool(
            name="metasploit",
            display_name="Metasploit Framework",
            description="综合渗透测试框架，用于漏洞验证和利用",
            category="vulnerability_validation",
            executable="msfconsole",
            parameters=[
                {"name": "module", "required": True, "description": "模块名称"},
                {"name": "options", "required": False, "description": "模块选项"}
            ],
            output_format="text"
        )
        
        # Web代理工具
        self.register_tool(
            name="burp_suite",
            display_name="Burp Suite",
            description="Web应用测试工具，用于拦截和修改请求",
            category="web_proxy",
            executable="D:\burpsuite\BurpSuiteCommunity\BurpSuiteCommunity.exe",
            parameters=[
                {"name": "target", "required": True, "description": "目标URL"},
                {"name": "proxy_port", "required": False, "description": "代理端口"}
            ],
            output_format="text"
        )
        
        # 报告生成工具
        self.register_tool(
            name="report_generator",
            display_name="Report Generator",
            description="渗透测试报告生成工具",
            category="reporting",
            executable="python",
            parameters=[
                {"name": "template", "required": True, "description": "报告模板"},
                {"name": "data", "required": True, "description": "报告数据"},
                {"name": "output", "required": False, "description": "输出文件"}
            ],
            output_format="text"
        )
    
    def register_tool(self, name, display_name, description, category, executable, parameters, output_format):
        """
        注册工具
        
        Args:
            name (str): 工具名称
            display_name (str): 工具显示名称
            description (str): 工具描述
            category (str): 工具类别
            executable (str): 可执行文件路径
            parameters (list): 工具参数
            output_format (str): 输出格式
        """
        self.tools[name] = {
            "name": name,
            "display_name": display_name,
            "description": description,
            "category": category,
            "executable": executable,
            "parameters": parameters,
            "output_format": output_format
        }
        logger.info(f"工具注册成功: {name}")
    
    def get_tool(self, name):
        """
        获取工具信息
        
        Args:
            name (str): 工具名称
            
        Returns:
            dict: 工具信息
        """
        return self.tools.get(name)
    
    def get_all_tools(self):
        """
        获取所有工具
        
        Returns:
            dict: 所有工具信息
        """
        return self.tools
    
    def get_tools_by_category(self, category):
        """
        根据类别获取工具
        
        Args:
            category (str): 工具类别
            
        Returns:
            list: 工具列表
        """
        return [tool for tool in self.tools.values() if tool["category"] == category]
    
    def update_tool(self, name, **kwargs):
        """
        更新工具信息
        
        Args:
            name (str): 工具名称
            **kwargs: 要更新的参数
        """
        if name in self.tools:
            self.tools[name].update(kwargs)
            logger.info(f"工具更新成功: {name}")
        else:
            logger.error(f"工具不存在: {name}")
    
    def remove_tool(self, name):
        """
        移除工具
        
        Args:
            name (str): 工具名称
        """
        if name in self.tools:
            del self.tools[name]
            logger.info(f"工具移除成功: {name}")
        else:
            logger.error(f"工具不存在: {name}")