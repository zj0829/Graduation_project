class MCPConfig:
    """
    MCP服务配置
    """
    # MCP服务基础URL
    BASE_URL = "http://localhost:9876"
    
    # MCP服务API路径
    API_PATH = "/api/mcp/command"
    
    # 连接超时时间（秒）
    CONNECTION_TIMEOUT = 30
    
    # 扫描超时时间（秒）
    SCAN_TIMEOUT = 3600
    
    # 轮询间隔（秒）
    POLLING_INTERVAL = 5
    
    # 默认代理端口
    DEFAULT_PROXY_PORT = 8080
    
    # 默认报告格式
    DEFAULT_REPORT_FORMAT = "html"
    
    @classmethod
    def get_base_url(cls):
        """
        获取MCP服务基础URL
        
        Returns:
            str: MCP服务基础URL
        """
        return cls.BASE_URL
    
    @classmethod
    def get_api_url(cls):
        """
        获取MCP服务API URL
        
        Returns:
            str: MCP服务API URL
        """
        return f"{cls.BASE_URL}{cls.API_PATH}"
    
    @classmethod
    def get_connection_timeout(cls):
        """
        获取连接超时时间
        
        Returns:
            int: 连接超时时间（秒）
        """
        return cls.CONNECTION_TIMEOUT
    
    @classmethod
    def get_scan_timeout(cls):
        """
        获取扫描超时时间
        
        Returns:
            int: 扫描超时时间（秒）
        """
        return cls.SCAN_TIMEOUT
    
    @classmethod
    def get_polling_interval(cls):
        """
        获取轮询间隔
        
        Returns:
            int: 轮询间隔（秒）
        """
        return cls.POLLING_INTERVAL
    
    @classmethod
    def get_default_proxy_port(cls):
        """
        获取默认代理端口
        
        Returns:
            int: 默认代理端口
        """
        return cls.DEFAULT_PROXY_PORT
    
    @classmethod
    def get_default_report_format(cls):
        """
        获取默认报告格式
        
        Returns:
            str: 默认报告格式
        """
        return cls.DEFAULT_REPORT_FORMAT