from jinja2 import Template
import markdown
import json
import os
from datetime import datetime, timezone, timedelta

BJ_TZ = timezone(timedelta(hours=8))

def bj_now():
    return datetime.now(BJ_TZ).strftime("%Y-%m-%d %H:%M:%S")

class ReportGenerator:
    def __init__(self):
        # 报告模板
        self.report_template = """
# 渗透测试报告

## 执行摘要

**测试目标**: {{ target }}
**测试类型**: {{ test_type }}
**测试范围**: {{ test_scope }}
**测试日期**: {{ test_date }}
**测试工具**: {{ tools | join(', ') }}

### 风险评估

**总体风险等级**: {{ risk_assessment.overall_risk }}
**受影响组件**: {{ risk_assessment.affected_components | join(', ') }}
**潜在影响**: {{ risk_assessment.potential_impact }}

## 测试过程

{% for step in test_plan.steps %}
### {{ step.name }}

**描述**: {{ step.description }}
**使用工具**: {{ step.tools | join(', ') }}
**预期结果**: {{ step.expected_result }}

{% if step.results %}
**执行结果**:
```
{{ step.results }}
```
{% endif %}

{% endfor %}

## 发现的漏洞

{% if vulnerabilities %}
{% for vuln in vulnerabilities %}
### {{ vuln.name }}

**ID**: {{ vuln.id }}
**描述**: {{ vuln.description }}
**严重程度**: {{ vuln.severity }}
**证据**:
```
{{ vuln.evidence }}
```
{% endfor %}
{% else %}
未发现漏洞
{% endif %}

## 修复建议

{% if recommendations %}
{% for recommendation in recommendations %}
- {{ recommendation }}
{% endfor %}
{% else %}
无建议
{% endif %}

## 附录

### 测试工具版本

{% for tool, version in tool_versions.items() %}
- {{ tool }}: {{ version }}
{% endfor %}

### 测试环境

- 操作系统: {{ environment.os }}
- 执行用户: {{ environment.user }}
- 执行时间: {{ environment.execution_time }}
        """
    
    def generate_report(self, test_plan, results, analysis, template=None):
        """
        生成渗透测试报告
        
        Args:
            test_plan (dict): 测试计划
            results (dict): 测试结果
            analysis (dict): 分析结果
            template (str): 自定义模板
            
        Returns:
            str: 生成的报告
        """
        # 使用自定义模板或默认模板
        if template:
            report_template = template
        else:
            report_template = self.report_template
        
        # 准备模板数据
        template_data = {
            "target": test_plan.get("target", ""),
            "test_type": test_plan.get("test_type", "comprehensive"),
            "test_scope": test_plan.get("test_scope", "web_application"),
            "test_date": bj_now(),
            "tools": self._extract_tools(test_plan),
            "risk_assessment": analysis.get("risk_assessment", {}),
            "test_plan": self._enrich_test_plan(test_plan, results),
            "vulnerabilities": analysis.get("vulnerabilities", []),
            "recommendations": analysis.get("recommendations", []),
            "tool_versions": self._get_tool_versions(),
            "environment": self._get_environment_info()
        }
        
        # 渲染模板
        template = Template(report_template)
        report = template.render(**template_data)
        
        return report
    
    def generate_html_report(self, test_plan, results, analysis, template=None):
        """
        生成HTML格式的渗透测试报告
        
        Args:
            test_plan (dict): 测试计划
            results (dict): 测试结果
            analysis (dict): 分析结果
            template (str): 自定义模板
            
        Returns:
            str: 生成的HTML报告
        """
        # 生成Markdown报告
        markdown_report = self.generate_report(test_plan, results, analysis, template)
        
        # 转换为HTML
        html_report = markdown.markdown(markdown_report)
        
        # 添加HTML模板
        full_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>渗透测试报告</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            color: #333;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        ul {
            list-style-type: disc;
            margin-left: 20px;
        }
        .risk-high {
            color: #e74c3c;
            font-weight: bold;
        }
        .risk-medium {
            color: #f39c12;
            font-weight: bold;
        }
        .risk-low {
            color: #27ae60;
            font-weight: bold;
        }
    </style>
</head>
<body>
    {html_report}
</body>
</html>
        """.format(html_report=html_report)
        
        return full_html
    
    def _extract_tools(self, test_plan):
        """
        从测试计划中提取工具列表
        
        Args:
            test_plan (dict): 测试计划
            
        Returns:
            list: 工具列表
        """
        tools = set()
        for step in test_plan.get("steps", []):
            tools.update(step.get("tools", []))
        return list(tools)
    
    def _enrich_test_plan(self, test_plan, results):
        """
        丰富测试计划，添加执行结果
        
        Args:
            test_plan (dict): 测试计划
            results (dict): 测试结果
            
        Returns:
            dict: 丰富后的测试计划
        """
        enriched_plan = test_plan.copy()
        for step in enriched_plan.get("steps", []):
            # 这里简化处理，实际实现中需要根据结果结构进行匹配
            step["results"] = json.dumps(results, indent=2, ensure_ascii=False)
        return enriched_plan
    
    def _get_tool_versions(self):
        """
        获取工具版本信息
        
        Returns:
            dict: 工具版本信息
        """
        # 这里简化处理，实际实现中需要执行工具获取版本信息
        return {
            "nmap": "7.94",
            "amass": "3.23",
            "owasp_zap": "2.14",
            "sqlmap": "1.7",
            "metasploit": "6.3",
            "burp_suite": "2024.2"
        }
    
    def _get_environment_info(self):
        """
        获取环境信息
        
        Returns:
            dict: 环境信息
        """
        import platform
        import getpass
        
        return {
            "os": platform.platform(),
            "user": getpass.getuser(),
            "execution_time": bj_now()
        }
    
    def save_report(self, report, output_path):
        """
        保存报告到文件
        
        Args:
            report (str): 报告内容
            output_path (str): 输出路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            return True
        except Exception as e:
            print(f"保存报告失败: {e}")
            return False