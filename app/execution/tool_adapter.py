import subprocess
import json
import os

class ToolAdapter:
    def __init__(self):
        # 工具配置
        self.tool_configs = {
            "nmap": {
                "executable": "nmap",
                "args": [],
                "output_format": "text"
            },
            "amass": {
                "executable": "amass",
                "args": [],
                "output_format": "text"
            },
            "owasp_zap": {
                "executable": "zap-cli",
                "args": [],
                "output_format": "json"
            },
            "sqlmap": {
                "executable": "sqlmap",
                "args": [],
                "output_format": "json"
            },
            "metasploit": {
                "executable": "msfconsole",
                "args": [],
                "output_format": "text"
            },
            "burp_suite": {
                "executable": "burpsuite",
                "args": [],
                "output_format": "text"
            }
        }
    
    def execute(self, tool_name, parameters):
        """
        执行工具
        
        Args:
            tool_name (str): 工具名称
            parameters (dict): 工具参数
            
        Returns:
            dict: 执行结果
        """
        try:
            # 检查工具是否支持
            if tool_name not in self.tool_configs:
                return {"error": f"不支持的工具: {tool_name}"}
            
            # 获取工具配置
            config = self.tool_configs[tool_name]
            
            # 构建命令
            command = [config["executable"]]
            command.extend(config["args"])
            command.extend(self._build_args(tool_name, parameters))
            
            # 执行命令
            result = self._run_command(command)
            
            # 处理结果
            processed_result = self._process_result(result, config["output_format"])
            
            return processed_result
        except Exception as e:
            return {"error": str(e)}
    
    def _build_args(self, tool_name, parameters):
        """
        构建工具参数
        
        Args:
            tool_name (str): 工具名称
            parameters (dict): 工具参数
            
        Returns:
            list: 参数列表
        """
        args = []
        
        if tool_name == "nmap":
            # Nmap参数
            if "target" in parameters:
                args.append(parameters["target"])
            if "ports" in parameters:
                args.extend(["-p", parameters["ports"]])
            if "scan_type" in parameters:
                args.append(f"-{parameters['scan_type']}")
            # 添加输出参数
            args.extend(["-oN", "-"],)
        
        elif tool_name == "amass":
            # Amass参数
            if "domain" in parameters:
                args.extend(["enum", "-d", parameters["domain"]])
            if "output" in parameters:
                args.extend(["-o", parameters["output"]])
            else:
                args.extend(["-o", "-"])
        
        elif tool_name == "owasp_zap":
            # OWASP ZAP参数
            if "target" in parameters:
                args.extend(["quick-scan", parameters["target"]])
            if "scan_type" in parameters:
                args.extend(["--self-contained", parameters["scan_type"]])
            # 添加JSON输出
            args.extend(["--format", "json"])
        
        elif tool_name == "sqlmap":
            # SQLmap参数
            if "url" in parameters:
                args.extend(["-u", parameters["url"]])
            if "parameters" in parameters:
                args.extend(["--data", parameters["parameters"]])
            # 添加JSON输出
            args.extend(["--output-format", "json", "--stdout"])
        
        elif tool_name == "metasploit":
            # Metasploit参数
            if "module" in parameters:
                args.extend(["-x", parameters["module"]])
            if "options" in parameters:
                args.extend(["-o", parameters["options"]])
            # 添加非交互式模式
            args.extend(["-q", "-x", "exit"])
        
        elif tool_name == "burp_suite":
            # Burp Suite参数
            if "target" in parameters:
                args.extend(["--target", parameters["target"]])
            if "proxy_port" in parameters:
                args.extend(["--proxy-port", parameters["proxy_port"]])
        
        return args
    
    def _run_command(self, command):
        """
        执行命令
        
        Args:
            command (list): 命令列表
            
        Returns:
            str: 执行结果
        """
        try:
            # 执行命令
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            # 检查返回码
            if result.returncode != 0:
                raise Exception(f"命令执行失败: {result.stderr}")
            
            return result.stdout
        except subprocess.TimeoutExpired:
            raise Exception("命令执行超时")
        except Exception as e:
            raise Exception(f"执行命令时出错: {str(e)}")
    
    def _process_result(self, result, output_format):
        """
        处理执行结果
        
        Args:
            result (str): 执行结果
            output_format (str): 输出格式
            
        Returns:
            dict: 处理后的结果
        """
        try:
            if output_format == "json":
                # 尝试解析JSON
                return json.loads(result)
            else:
                # 文本格式直接返回
                return {"output": result}
        except json.JSONDecodeError:
            # JSON解析失败，返回原始结果
            return {"output": result, "error": "JSON解析失败"}
        except Exception as e:
            # 其他错误，返回原始结果
            return {"output": result, "error": str(e)}
    
    def check_tool_availability(self, tool_name):
        """
        检查工具是否可用
        
        Args:
            tool_name (str): 工具名称
            
        Returns:
            bool: 是否可用
        """
        try:
            # 检查工具是否支持
            if tool_name not in self.tool_configs:
                return False
            
            # 检查工具是否安装
            config = self.tool_configs[tool_name]
            executable = config["executable"]
            
            # 尝试执行工具的版本命令
            result = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
        except Exception:
            return False
    
    def get_supported_tools(self):
        """
        获取支持的工具列表
        
        Returns:
            list: 工具列表
        """
        return list(self.tool_configs.keys())