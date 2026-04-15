import json
from app.llm_brain.llm_interface import LLMInterface

class RequirementParser:
    def __init__(self):
        self.llm = LLMInterface()
    
    def parse(self, requirement, target):
        """
        解析用户测试需求
        
        Args:
            requirement (str): 用户输入的测试需求
            target (str): 测试目标
            
        Returns:
            dict: 解析后的需求信息
        """
        try:
            # 使用LLM解析需求
            response = self.llm.parse_requirement(requirement)
            
            if response:
                # 解析JSON响应
                parsed_data = json.loads(response)
                
                # 添加目标信息
                parsed_data['target'] = target
                
                # 验证和补全必要字段
                parsed_data = self._validate_and_complete(parsed_data)
                
                return parsed_data
            else:
                return self._default_requirement(target)
        except Exception as e:
            print(f"需求解析失败: {e}")
            return self._default_requirement(target)
    
    def _validate_and_complete(self, data):
        """
        验证和补全需求数据
        
        Args:
            data (dict): 解析后的需求数据
            
        Returns:
            dict: 验证和补全后的需求数据
        """
        # 确保必要字段存在
        required_fields = ['target', 'test_type', 'test_scope']
        for field in required_fields:
            if field not in data:
                data[field] = self._get_default_value(field)
        
        # 标准化测试类型
        data['test_type'] = self._standardize_test_type(data['test_type'])
        
        # 标准化测试范围
        data['test_scope'] = self._standardize_test_scope(data['test_scope'])
        
        return data
    
    def _get_default_value(self, field):
        """
        获取字段的默认值
        
        Args:
            field (str): 字段名
            
        Returns:
            any: 默认值
        """
        defaults = {
            'target': '',
            'test_type': 'comprehensive',
            'test_scope': 'web_application'
        }
        return defaults.get(field, '')
    
    def _standardize_test_type(self, test_type):
        """
        标准化测试类型
        
        Args:
            test_type (str): 测试类型
            
        Returns:
            str: 标准化后的测试类型
        """
        test_types = {
            '全面测试': 'comprehensive',
            '安全扫描': 'security_scan',
            '漏洞验证': 'vulnerability_validation',
            '渗透测试': 'penetration_test',
            '代码审计': 'code_audit',
            '配置审计': 'configuration_audit'
        }
        
        # 转换为小写并去除空格
        test_type = test_type.lower().strip()
        
        # 查找标准化的测试类型
        for key, value in test_types.items():
            if key.lower() in test_type:
                return value
        
        return 'comprehensive'
    
    def _standardize_test_scope(self, test_scope):
        """
        标准化测试范围
        
        Args:
            test_scope (str): 测试范围
            
        Returns:
            str: 标准化后的测试范围
        """
        scopes = {
            'web应用': 'web_application',
            '网络设备': 'network_devices',
            '服务器': 'servers',
            '数据库': 'databases',
            '移动应用': 'mobile_apps',
            'API': 'api'
        }
        
        # 转换为小写并去除空格
        test_scope = test_scope.lower().strip()
        
        # 查找标准化的测试范围
        for key, value in scopes.items():
            if key.lower() in test_scope:
                return value
        
        return 'web_application'
    
    def _default_requirement(self, target):
        """
        生成默认需求
        
        Args:
            target (str): 测试目标
            
        Returns:
            dict: 默认需求
        """
        return {
            'target': target,
            'test_type': 'comprehensive',
            'test_scope': 'web_application',
            'description': '全面的Web应用渗透测试',
            'priority': 'medium'
        }