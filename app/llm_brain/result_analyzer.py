import json
from app.llm_brain.llm_interface import LLMInterface

class ResultAnalyzer:
    def __init__(self):
        self.llm = LLMInterface()
    
    def analyze(self, results):
        """
        分析测试结果
        
        Args:
            results (dict): 测试结果
            
        Returns:
            dict: 分析结果
        """
        try:
            # 转换结果为字符串
            results_str = json.dumps(results, ensure_ascii=False)
            
            # 使用LLM分析结果
            response = self.llm.analyze_results(results_str)
            
            if response:
                # 解析JSON响应
                analysis = json.loads(response)
                
                # 验证和补全分析结果
                analysis = self._validate_and_complete(analysis, results)
                
                return analysis
            else:
                return self._default_analysis(results)
        except Exception as e:
            print(f"结果分析失败: {e}")
            return self._default_analysis(results)
    
    def _validate_and_complete(self, analysis, results):
        """
        验证和补全分析结果
        
        Args:
            analysis (dict): 生成的分析结果
            results (dict): 测试结果
            
        Returns:
            dict: 验证和补全后的分析结果
        """
        # 确保必要字段存在
        required_fields = ['vulnerabilities', 'risk_assessment', 'recommendations']
        for field in required_fields:
            if field not in analysis:
                analysis[field] = self._get_default_value(field)
        
        # 验证漏洞格式
        if 'vulnerabilities' in analysis:
            for i, vuln in enumerate(analysis['vulnerabilities']):
                # 确保漏洞包含必要字段
                vuln_required_fields = ['id', 'name', 'description', 'severity', 'evidence']
                for field in vuln_required_fields:
                    if field not in vuln:
                        vuln[field] = self._get_default_vuln_value(field, i)
        else:
            analysis['vulnerabilities'] = []
        
        # 验证风险评估格式
        if 'risk_assessment' in analysis:
            # 确保风险评估包含必要字段
            risk_required_fields = ['overall_risk', 'affected_components', 'potential_impact']
            for field in risk_required_fields:
                if field not in analysis['risk_assessment']:
                    analysis['risk_assessment'][field] = self._get_default_risk_value(field)
        else:
            analysis['risk_assessment'] = {
                'overall_risk': 'low',
                'affected_components': [],
                'potential_impact': '无明显影响'
            }
        
        return analysis
    
    def _get_default_value(self, field):
        """
        获取字段的默认值
        
        Args:
            field (str): 字段名
            
        Returns:
            any: 默认值
        """
        defaults = {
            'vulnerabilities': [],
            'risk_assessment': {
                'overall_risk': 'low',
                'affected_components': [],
                'potential_impact': '无明显影响'
            },
            'recommendations': []
        }
        return defaults.get(field, '')
    
    def _get_default_vuln_value(self, field, index):
        """
        获取漏洞字段的默认值
        
        Args:
            field (str): 字段名
            index (int): 漏洞索引
            
        Returns:
            any: 默认值
        """
        defaults = {
            'id': index + 1,
            'name': f'漏洞 {index + 1}',
            'description': f'漏洞描述 {index + 1}',
            'severity': 'low',
            'evidence': '无证据'
        }
        return defaults.get(field, '')
    
    def _get_default_risk_value(self, field):
        """
        获取风险评估字段的默认值
        
        Args:
            field (str): 字段名
            
        Returns:
            any: 默认值
        """
        defaults = {
            'overall_risk': 'low',
            'affected_components': [],
            'potential_impact': '无明显影响'
        }
        return defaults.get(field, '')
    
    def _default_analysis(self, results):
        """
        生成默认分析结果
        
        Args:
            results (dict): 测试结果
            
        Returns:
            dict: 默认分析结果
        """
        return {
            'vulnerabilities': [],
            'risk_assessment': {
                'overall_risk': 'low',
                'affected_components': [],
                'potential_impact': '无明显影响'
            },
            'recommendations': ['定期进行安全测试', '及时更新系统和应用程序', '加强访问控制']
        }