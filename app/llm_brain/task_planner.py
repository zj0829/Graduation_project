import json
from app.llm_brain.llm_interface import LLMInterface

class TaskPlanner:
    def __init__(self):
        self.llm = LLMInterface()
    
    def plan(self, requirement):
        """
        生成测试计划
        
        Args:
            requirement (dict): 解析后的需求信息
            
        Returns:
            dict: 生成的测试计划
        """
        try:
            # 提取需求信息
            target = requirement.get('target', '')
            test_type = requirement.get('test_type', 'comprehensive')
            test_scope = requirement.get('test_scope', 'web_application')
            description = requirement.get('description', '')
            
            # 构建需求描述
            requirement_desc = f"测试类型: {test_type}\n测试范围: {test_scope}\n描述: {description}"
            
            # 使用LLM生成测试计划
            response = self.llm.generate_test_plan(requirement_desc, target)
            
            if response:
                # 解析JSON响应
                test_plan = json.loads(response)
                
                # 验证和补全测试计划
                test_plan = self._validate_and_complete(test_plan, requirement)
                
                return test_plan
            else:
                return self._default_test_plan(requirement)
        except Exception as e:
            print(f"测试计划生成失败: {e}")
            return self._default_test_plan(requirement)
    
    def _validate_and_complete(self, test_plan, requirement):
        """
        验证和补全测试计划
        
        Args:
            test_plan (dict): 生成的测试计划
            requirement (dict): 解析后的需求信息
            
        Returns:
            dict: 验证和补全后的测试计划
        """
        # 确保必要字段存在
        required_fields = ['target', 'test_type', 'test_scope', 'steps']
        for field in required_fields:
            if field not in test_plan:
                if field in requirement:
                    test_plan[field] = requirement[field]
                else:
                    test_plan[field] = self._get_default_value(field)
        
        # 验证步骤格式
        if 'steps' in test_plan:
            for i, step in enumerate(test_plan['steps']):
                # 确保步骤包含必要字段
                step_required_fields = ['id', 'name', 'description', 'tools', 'expected_result']
                for field in step_required_fields:
                    if field not in step:
                        step[field] = self._get_default_step_value(field, i)
        else:
            test_plan['steps'] = []
        
        return test_plan
    
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
            'test_scope': 'web_application',
            'steps': []
        }
        return defaults.get(field, '')
    
    def _get_default_step_value(self, field, index):
        """
        获取步骤字段的默认值
        
        Args:
            field (str): 字段名
            index (int): 步骤索引
            
        Returns:
            any: 默认值
        """
        defaults = {
            'id': index + 1,
            'name': f'步骤 {index + 1}',
            'description': f'测试步骤 {index + 1}',
            'tools': [],
            'expected_result': '完成测试步骤'
        }
        return defaults.get(field, '')
    
    def _default_test_plan(self, requirement):
        """
        生成默认测试计划
        
        Args:
            requirement (dict): 解析后的需求信息
            
        Returns:
            dict: 默认测试计划
        """
        target = requirement.get('target', '')
        test_type = requirement.get('test_type', 'comprehensive')
        test_scope = requirement.get('test_scope', 'web_application')
        
        return {
            'target': target,
            'test_type': test_type,
            'test_scope': test_scope,
            'steps': [
                {
                    'id': 1,
                    'name': '信息收集',
                    'description': '收集目标的基本信息，包括域名、IP地址、端口等',
                    'tools': ['nmap', 'amass'],
                    'expected_result': '获取目标的基本信息'
                },
                {
                    'id': 2,
                    'name': '漏洞扫描',
                    'description': '扫描目标的潜在漏洞',
                    'tools': ['owasp_zap'],
                    'expected_result': '发现潜在漏洞'
                },
                {
                    'id': 3,
                    'name': '漏洞验证',
                    'description': '验证发现的漏洞是否真实存在',
                    'tools': ['sqlmap', 'metasploit'],
                    'expected_result': '验证漏洞存在性'
                },
                {
                    'id': 4,
                    'name': '渗透测试',
                    'description': '执行具体的渗透测试操作',
                    'tools': ['metasploit', 'burp_suite'],
                    'expected_result': '完成渗透测试'
                },
                {
                    'id': 5,
                    'name': '报告生成',
                    'description': '生成渗透测试报告',
                    'tools': ['report_generator'],
                    'expected_result': '生成详细的渗透测试报告'
                }
            ]
        }