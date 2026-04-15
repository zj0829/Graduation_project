import json
import requests
import asyncio
from app.orchestrator.mcp_config import MCPConfig
from app.common.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

class MCPService:
    def __init__(self):
        self.base_url = MCPConfig.get_base_url()
        self.api_url = MCPConfig.get_api_url()
        self.headers = {
            "Content-Type": "application/json"
        }
        self.timeout = MCPConfig.get_connection_timeout()
        self.scan_timeout = MCPConfig.get_scan_timeout()
        self.polling_interval = MCPConfig.get_polling_interval()
        self.session_id = None
        
        # 获取sessionId
        self._get_session_id()
        
        logger.info(f"MCP服务初始化完成，地址: {self.base_url}")
    
    def _get_session_id(self):
        """
        获取MCP服务的sessionId
        """
        try:
            # 建立SSE连接获取sessionId
            logger.info(f"连接MCP服务获取sessionId: {self.base_url}")
            response = requests.get(self.base_url, stream=True, timeout=self.timeout)
            
            logger.info(f"MCP服务响应状态: {response.status_code}")
            
            # 读取所有事件，查找sessionId
            session_id_found = False
            for i, line in enumerate(response.iter_lines()):
                if line:
                    decoded_line = line.decode('utf-8')
                    logger.info(f"收到SSE事件 {i}: {decoded_line}")
                    
                    # 查找sessionId
                    if 'sessionId' in decoded_line:
                        # 提取sessionId
                        if 'sessionId=' in decoded_line:
                            self.session_id = decoded_line.split('sessionId=')[1]
                            logger.info(f"获取到MCP sessionId: {self.session_id}")
                            session_id_found = True
                            break
            
            response.close()
            
            if not session_id_found:
                logger.error("未获取到MCP sessionId")
                # 不抛出异常，让系统继续运行
                # 后续命令执行时会尝试重新获取
            
        except Exception as e:
            logger.error(f"获取sessionId失败: {e}")
            # 不抛出异常，让系统继续运行
    
    async def send_command(self, command, params):
        """
        发送命令到MCP服务
        
        Args:
            command (str): 命令名称
            params (dict): 命令参数
            
        Returns:
            dict: 命令执行结果
        """
        try:
            # 确保有sessionId
            if not self.session_id:
                self._get_session_id()
            
            # 构建带sessionId的URL
            command_url = f"{self.base_url}?sessionId={self.session_id}"
            
            # 构建JSON-RPC格式的请求数据
            data = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": command,
                "params": params
            }
            
            logger.info(f"发送MCP命令: {command}, 参数: {params}")
            
            response = requests.post(command_url, headers=self.headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"MCP命令执行成功: {result}")
            
            return result
        except Exception as e:
            logger.error(f"MCP命令执行失败: {e}")
            raise
    
    async def start_scan(self, target):
        """
        启动BurpSuite扫描
        
        Args:
            target (str): 目标URL
            
        Returns:
            dict: 扫描结果
        """
        return await self.send_command("start_scan", {
            "target": target
        })
    
    async def stop_scan(self, scan_id):
        """
        停止BurpSuite扫描
        
        Args:
            scan_id (str): 扫描ID
            
        Returns:
            dict: 操作结果
        """
        return await self.send_command("stop_scan", {
            "scan_id": scan_id
        })
    
    async def get_scan_status(self, scan_id):
        """
        获取扫描状态
        
        Args:
            scan_id (str): 扫描ID
            
        Returns:
            dict: 扫描状态
        """
        return await self.send_command("get_scan_status", {
            "scan_id": scan_id
        })
    
    async def get_scan_results(self, scan_id):
        """
        获取扫描结果
        
        Args:
            scan_id (str): 扫描ID
            
        Returns:
            dict: 扫描结果
        """
        return await self.send_command("get_scan_results", {
            "scan_id": scan_id
        })
    
    async def configure_proxy(self, proxy_port=8080):
        """
        配置BurpSuite代理
        
        Args:
            proxy_port (int): 代理端口
            
        Returns:
            dict: 配置结果
        """
        return await self.send_command("configure_proxy", {
            "proxy_port": proxy_port
        })
    
    async def import_targets(self, targets):
        """
        导入目标
        
        Args:
            targets (list): 目标列表
            
        Returns:
            dict: 导入结果
        """
        return await self.send_command("import_targets", {
            "targets": targets
        })
    
    async def export_report(self, scan_id, report_format="html"):
        """
        导出报告
        
        Args:
            scan_id (str): 扫描ID
            report_format (str): 报告格式
            
        Returns:
            dict: 导出结果
        """
        return await self.send_command("export_report", {
            "scan_id": scan_id,
            "format": report_format
        })
    
    async def nmap_scan(self, target, ports=None, scan_type=None):
        """
        执行Nmap扫描
        
        Args:
            target (str): 目标IP或域名
            ports (str): 端口范围
            scan_type (str): 扫描类型
            
        Returns:
            dict: 扫描结果
        """
        return await self.send_command("nmap_scan", {
            "target": target,
            "ports": ports,
            "scan_type": scan_type
        })
    
    async def amass_enum(self, domain, output=None):
        """
        执行Amass子域名枚举
        
        Args:
            domain (str): 目标域名
            output (str): 输出文件
            
        Returns:
            dict: 枚举结果
        """
        return await self.send_command("amass_enum", {
            "domain": domain,
            "output": output
        })
    
    async def zap_scan(self, target, scan_type=None):
        """
        执行OWASP ZAP扫描
        
        Args:
            target (str): 目标URL
            scan_type (str): 扫描类型
            
        Returns:
            dict: 扫描结果
        """
        return await self.send_command("zap_scan", {
            "target": target,
            "scan_type": scan_type
        })
    
    async def sqlmap_scan(self, url, parameters=None):
        """
        执行SQLmap扫描
        
        Args:
            url (str): 目标URL
            parameters (str): 参数
            
        Returns:
            dict: 扫描结果
        """
        return await self.send_command("sqlmap_scan", {
            "url": url,
            "parameters": parameters
        })
    
    async def metasploit_execute(self, module, options=None):
        """
        执行Metasploit模块
        
        Args:
            module (str): 模块名称
            options (dict): 模块选项
            
        Returns:
            dict: 执行结果
        """
        return await self.send_command("metasploit_execute", {
            "module": module,
            "options": options
        })
    
    async def generate_report(self, template, data, output=None):
        """
        生成报告
        
        Args:
            template (str): 报告模板
            data (dict): 报告数据
            output (str): 输出文件
            
        Returns:
            dict: 生成结果
        """
        return await self.send_command("generate_report", {
            "template": template,
            "data": data,
            "output": output
        })