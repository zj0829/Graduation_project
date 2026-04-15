from app.execution.tool_adapter import ToolAdapter

class InformationGathering:
    def __init__(self):
        self.tool_adapter = ToolAdapter()
    
    def run_nmap(self, target, ports=None, scan_type=None):
        """
        运行Nmap扫描
        
        Args:
            target (str): 目标IP或域名
            ports (str): 端口范围
            scan_type (str): 扫描类型
            
        Returns:
            dict: 扫描结果
        """
        parameters = {
            "target": target
        }
        
        if ports:
            parameters["ports"] = ports
        
        if scan_type:
            parameters["scan_type"] = scan_type
        
        return self.tool_adapter.execute("nmap", parameters)
    
    def run_amass(self, domain, output=None):
        """
        运行Amass子域名枚举
        
        Args:
            domain (str): 目标域名
            output (str): 输出文件
            
        Returns:
            dict: 枚举结果
        """
        parameters = {
            "domain": domain
        }
        
        if output:
            parameters["output"] = output
        
        return self.tool_adapter.execute("amass", parameters)
    
    def gather_info(self, target):
        """
        综合信息收集
        
        Args:
            target (str): 目标IP或域名
            
        Returns:
            dict: 收集的信息
        """
        # 运行Nmap扫描
        nmap_result = self.run_nmap(target)
        
        # 尝试提取域名进行Amass枚举
        amass_result = None
        if "output" in nmap_result:
            # 简单尝试从Nmap输出中提取域名
            # 实际实现中可能需要更复杂的解析
            amass_result = {"output": "Amass scan not performed (domain extraction not implemented)"}
        
        return {
            "nmap": nmap_result,
            "amass": amass_result
        }