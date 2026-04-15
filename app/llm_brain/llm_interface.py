import requests
import os
import json
from dotenv import load_dotenv
from app.common.logger import get_logger

# 加载环境变量
load_dotenv()

# 获取日志记录器
logger = get_logger(__name__)

class LLMInterface:
    def __init__(self):
        # 从环境变量中获取DeepSeek API密钥和模型名称
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
    
    def generate_response(self, prompt, temperature=0.7, max_tokens=1000):
        """
        生成LLM响应
        
        Args:
            prompt (str): 提示词
            temperature (float): 生成温度
            max_tokens (int): 最大令牌数
            
        Returns:
            str: LLM生成的响应
        """
        try:
            logger.info(f"调用LLM API, 模型: {self.model}, 最大令牌数: {max_tokens}")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是一个专业的渗透测试专家，精通各种安全测试工具和方法。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 处理代码块中的JSON
            if content.startswith("```json") and content.endswith("```"):
                content = content[7:-3].strip()
            
            logger.info(f"LLM API调用成功, 生成内容: {content}")
            return content
        except Exception as e:
            logger.error(f"LLM API调用失败: {e}")
            return None

    def chat(self, messages, model=None, temperature=0.7, max_tokens=2000):
        try:
            use_model = model or self.model
            use_base_url = self.base_url
            use_api_key = self.api_key

            if use_model and use_model.startswith("glm"):
                use_base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
                use_api_key = os.getenv("GLM_API_KEY", self.api_key)

            logger.info(f"Chat API调用, 模型: {use_model}")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {use_api_key}"
            }
            data = {
                "model": use_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            response = requests.post(use_base_url, headers=headers, json=data, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Chat API调用失败: {e}")
            return f"对话服务暂时不可用: {str(e)}"

    def chat_stream(self, messages, model=None, temperature=0.7, max_tokens=600):
        use_model = model or self.model
        use_base_url = self.base_url
        use_api_key = self.api_key

        if use_model and use_model.startswith("glm"):
            use_base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            use_api_key = os.getenv("GLM_API_KEY", self.api_key)

        logger.info(f"Chat Stream API调用, 模型: {use_model}")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {use_api_key}"
        }
        data = {
            "model": use_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }

        try:
            resp = requests.post(use_base_url, headers=headers, json=data, timeout=120, stream=True)
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    payload = decoded[6:]
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Chat Stream API调用失败: {e}")
            yield f"[错误] 对话服务暂时不可用: {str(e)}"

    def parse_requirement(self, requirement):
        """
        解析用户测试需求
        
        Args:
            requirement (str): 用户输入的测试需求
            
        Returns:
            dict: 解析后的需求信息
        """
        prompt = f"你是一名专业的渗透测试需求分析师，负责将用户的自然语言需求转换为结构化的测试需求。请分析以下渗透测试需求，提取并结构化以下关键信息：\n\n【需要提取的信息】\n- 测试目标：明确的测试对象（如网站URL、IP地址等）\n- 测试类型：如全面测试、漏洞扫描、渗透测试等\n- 测试范围：具体的测试范围和边界\n- 测试重点：用户关注的重点领域（如SQL注入、XSS、认证绕过等）\n- 测试时间：预计的测试时间范围（如果提及）\n- 特殊要求：用户提出的其他特殊要求（如果有）\n\n【输入需求】\n{requirement}\n\n请以JSON格式返回解析结果，确保信息准确、完整、结构化。JSON格式应包含上述所有字段，值为空的字段也应包含在JSON中。"
        response = self.generate_response(prompt)
        return response
    
    def generate_test_plan(self, requirement, target):
        """
        生成测试计划
        
        Args:
            requirement (str): 用户输入的测试需求
            target (str): 测试目标
            
        Returns:
            dict: 生成的测试计划
        """
        prompt = f"你是一名专业的渗透测试计划制定专家，负责为渗透测试项目制定详细、专业的测试计划。请基于以下信息，生成一份结构化的测试计划：\n\n【测试信息】\n测试目标: {target}\n测试需求: {requirement}\n\n【计划内容要求】\n1. 测试目标：明确的测试对象和目标\n2. 测试范围：详细的测试范围和边界\n3. 测试方法：采用的测试方法和技术\n4. 测试步骤：详细的测试步骤，包括：\n   - 步骤名称\n   - 步骤描述\n   - 使用工具\n   - 预期结果\n   - 执行时间估计\n5. 测试工具：计划使用的工具及其版本\n6. 风险评估：测试过程中可能面临的风险\n7. 测试时间计划：总体时间安排\n\n请以JSON格式返回测试计划，确保计划详细、专业、可执行。JSON结构应清晰，包含上述所有部分。"
        response = self.generate_response(prompt)
        return response
    
    def analyze_results(self, results):
        """
        分析测试结果
        
        Args:
            results (str): 测试结果
            
        Returns:
            dict: 分析结果
        """
        prompt = f"你是一名专业的渗透测试结果分析师，负责分析测试结果并识别漏洞。请分析以下渗透测试结果，完成以下任务：\n\n【分析任务】\n1. 漏洞识别：识别所有潜在的安全漏洞\n2. 漏洞分类：按照类型（如SQL注入、XSS、CSRF等）对漏洞进行分类\n3. 严重程度评估：为每个漏洞评估严重程度（高、中、低）\n4. 影响分析：分析每个漏洞的潜在影响范围和业务影响\n5. 漏洞证据：提取支持每个漏洞存在的证据\n6. 风险评估：基于所有漏洞，评估总体风险等级\n7. 修复建议：为每个漏洞提供初步的修复建议\n\n【测试结果】\n{results}\n\n请以JSON格式返回分析结果，确保分析全面、准确、专业。JSON结构应清晰，包含上述所有分析内容。"
        response = self.generate_response(prompt)
        return response
    
    def generate_report(self, test_plan, results, analysis):
        """
        生成渗透测试报告
        
        Args:
            test_plan (str): 测试计划
            results (str): 测试结果
            analysis (str): 分析结果
            
        Returns:
            str: 生成的报告
        """
        prompt = (
            "你是一名专业的渗透测试专家，负责生成规范、专业的渗透测试报告。\n\n"
            "【重要】直接输出报告正文，不要输出任何前言、寒暄、解释、确认或总结性语句（如'好的'、'我将'、'以下是'等）。报告以一级标题开头，例如：# 渗透测试报告。\n\n"
            "【报告结构要求】\n"
            "1. 执行摘要（150-200字）：简要概述测试目标、范围、方法和总体结果，突出关键发现和风险等级。\n"
            "2. 测试过程（300-400字）：详细描述测试步骤、使用的工具、执行方法和过程，按时间顺序或逻辑顺序组织。\n"
            "3. 发现的漏洞（每个漏洞200-300字）：针对每个漏洞，详细描述其名称、类型、严重程度、影响范围、技术细节和证据。\n"
            "4. 风险评估（200-250字）：基于漏洞的严重程度和影响范围，评估总体风险等级，分析潜在的业务影响。\n"
            "5. 修复建议（每个建议100-150字）：针对每个漏洞提供具体、可操作的修复建议，包括技术方案和实施步骤。\n"
            "6. 附录：列出使用的测试工具及其版本，测试环境信息。\n\n"
            "【语言格式要求】\n"
            "- 语言：使用正式、专业的技术语言，避免口语化表达。\n"
            "- 格式：使用Markdown格式，标题层级清晰（#、##、###），段落间距适当。\n"
            "- 术语：使用标准的网络安全和渗透测试术语，确保术语使用准确一致。\n"
            "- 客观性：基于事实和证据进行描述，避免主观臆断和夸张表述。\n"
            "- 详细度：提供足够的技术细节，确保报告的可操作性和可验证性。\n\n"
            f"【输入信息】\n测试计划: {test_plan}\n测试结果: {results}\n分析结果: {analysis}"
        )
        response = self.generate_response(prompt, max_tokens=4000)
        return response