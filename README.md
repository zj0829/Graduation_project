# 基于大模型的Web应用渗透测试智能辅助系统

## 项目简介

本项目是一个基于大语言模型（LLM）的Web应用渗透测试智能辅助系统，采用三层架构设计，利用大语言模型的自然语言理解与任务规划能力，动态解析测试需求、生成操作序列，并通过MCP智能调度中间件无缝集成和驱动各类安全测试工具。

## 技术栈

- **LLM服务**：DeepSeek Chat / DeepSeek Reasoner / GLM-4.7-Flash
- **开发框架**：FastAPI + Node.js Express（MCP Gateway）
- **编程语言**：Python 3.10+ / JavaScript
- **数据库**：SQLite
- **容器化**：Docker + Docker Compose
- **前端**：原生HTML + CSS + JavaScript（marked.js Markdown渲染）
- **通信协议**：MCP JSON-RPC / SSE 流式传输
- **安全工具**：Nmap, Amass, OWASP ZAP, SQLmap, Metasploit Framework, Burp Suite, Nikto, Dirsearch, SSLscan

## 系统架构

系统采用三层架构设计：

1. **智能决策层（LLM Brain）**：基于DeepSeek/GLM大模型，负责需求解析、测试规划、结果分析与报告生成
2. **调度控制层（MCP Orchestrator）**：基于MCP JSON-RPC协议的智能调度中间件，管理工具注册、任务分发与数据流转
3. **工具执行层（Docker Containers + Python Recon）**：各安全工具运行在独立Docker容器中，通过pentest-network桥接网络互联；Python内置侦察工具提供轻量级安全检测

## 项目结构

```
├── app/
│   ├── llm_brain/           # 智能决策层 - LLM接口与提示词工程
│   │   └── llm_interface.py # 多模型路由（DeepSeek/GLM）
│   ├── orchestrator/        # 调度控制层 - 任务调度与数据持久化
│   │   ├── routes.py        # FastAPI路由（测试流程API）
│   │   ├── db.py            # SQLite持久化（报告+聊天记录）
│   │   └── mcp_config.py    # MCP连接配置
│   ├── chat/                # AI对话模块
│   │   └── routes.py        # 对话API（SSE流式 + 会话存储）
│   ├── recon/               # 侦察工具模块（Python内置）
│   │   └── routes.py        # 9种Web安全侦察API
│   ├── report/              # 报告生成模块
│   │   └── report_generator.py
│   └── common/              # 公共模块（日志等）
├── mcp-server/
│   └── server.js            # MCP Gateway（JSON-RPC工具调度）
├── static/
│   ├── index.html           # 主页 - 渗透测试控制台
│   ├── chat.html            # AI安全对话页（流式输出）
│   ├── dashboard.html       # 安全仪表盘（综合审计+评分）
│   ├── knowledge.html       # 漏洞知识库（OWASP/CVE/XSS/检查清单）
│   └── guide.html           # 系统使用指南
├── tools/
│   └── sqlmap/Dockerfile    # 自定义SQLmap镜像
├── data/
│   └── pentest.db           # SQLite数据库（自动创建）
├── main.py                  # FastAPI应用入口
├── docker-compose.yml       # Docker容器编排
├── start.bat / stop.bat     # 一键启动/停止脚本
├── .env                     # 环境变量配置
└── requirements.txt         # Python依赖
```

## 快速开始

### 1. 环境准备

- Python 3.10+（推荐Anaconda）
- Node.js 16+
- Docker Desktop（运行中）
- DeepSeek API Key（必填）
- GLM API Key（可选）

### 2. 安装依赖

```bash
pip install -r requirements.txt
cd mcp-server && npm install && cd ..
```

### 3. 配置环境变量

编辑 `.env` 文件，填写API密钥：

```
DEEPSEEK_API_KEY=sk-your-deepseek-key
GLM_API_KEY=your-glm-key
```

### 4. 启动系统

**方式一：一键启动**
```bash
start.bat
```

**方式二：手动启动**
```bash
# 1. 启动Docker容器
docker network create pentest-network
docker start nmap amass zap sqlmap metasploit postgres || docker-compose up -d

# 2. 启动MCP服务
cd mcp-server && node server.js

# 3. 启动后端
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. 访问系统

- **主页**：http://localhost:8000/static/index.html
- **安全仪表盘**：http://localhost:8000/static/dashboard.html
- **漏洞知识库**：http://localhost:8000/static/knowledge.html
- **AI对话**：http://localhost:8000/static/chat.html
- **API文档**：http://localhost:8000/docs

## 核心功能

### 渗透测试控制台（主页）
- 输入目标URL和测试需求，一键启动自动化渗透测试
- 支持工具策略选择：自动 / 仅Nmap+SQLmap / 全工具 / 自定义工具组合
- 9种MCP工具可选：Nmap, Amass, OWASP ZAP, SQLmap, Metasploit, Burp Suite, Nikto, Dirsearch, SSLscan
- 5步进度条实时展示测试流程
- Markdown格式专业渗透测试报告，支持下载
- 报告含风险评分表、CVE编号、CVSS评分、OWASP Top 10分类
- 历史报告查看、加载、删除
- 报告下载命名格式：`目标地址_日期时间.md`
- 支持PDF导出（浏览器打印）

### 安全仪表盘
- 系统统计概览：测试报告数、AI对话数、MCP工具数、系统状态
- **综合安全审计**：一键执行6项安全检测，生成综合评分（0-100分）
- 安全评分环形图：可视化展示目标安全等级
- 9种快速侦察工具：WHOIS、DNS、安全头、端口、CORS、Cookie、技术栈、子域名、WAF
- MCP工具状态实时展示
- 最近测试报告列表
- 工具覆盖范围总览：信息收集、漏洞扫描、安全分析、漏洞利用与辅助

### 漏洞知识库
- **OWASP Top 10 (2021)**：完整中文解读，含攻击示例、防御措施、推荐工具
- **CVE漏洞查询**：接入NVD国家漏洞数据库，支持CVE编号和关键词搜索
- **XSS Payload生成器**：5类23个Payload（基础/属性注入/DOM型/WAF绕过/高级利用）
- **Web安全检查清单**：6大类30+检查项（认证授权/数据保护/输入验证/HTTP安全头/Cookie安全/基础设施）

### AI安全对话
- 基于MCP工具集的专业网络安全对话
- SSE流式输出，实时逐字生成回复
- 支持3种AI模型切换：DeepSeek Chat / DeepSeek Reasoner / GLM-4.7-Flash
- 对话历史持久化存储（SQLite）
- 会话管理：新建、切换、删除对话
- MCP连接状态实时指示

### 侦察工具（Python内置，无需Docker）
- **WHOIS查询**：域名注册信息、DNS记录、IP解析
- **DNS解析**：A/NS/MX记录查询
- **安全头检测**：7项HTTP安全响应头检测与评分（HSTS/CSP/X-Frame-Options等）
- **端口快速检测**：23个常见端口扫描与服务识别
- **CORS检测**：跨域资源共享配置检测，识别Origin反射和凭证泄露风险
- **Cookie安全分析**：HttpOnly/Secure/SameSite标志检测，CSRF风险识别
- **技术指纹识别**：Web服务器、框架、CMS、JavaScript库等15+技术栈特征识别
- **子域名枚举**：DNS解析+证书透明度(crt.sh)双重发现
- **WAF检测**：8种主流WAF特征识别（Cloudflare/AWS/Akamai/Imperva等）
- **XSS Payload生成**：5类23个测试Payload，支持场景化推荐
- **综合安全审计**：一键执行6项检测，生成综合安全评分

### MCP工具调度
- JSON-RPC协议通信，端口9876
- 工具注册与发现（10个工具）
- Docker容器化工具执行
- 工具列表：nmap, amass, owasp_zap, sqlmap, metasploit, burp_suite, nikto, dirsearch, sslscan, report_generator

## API接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/orchestrator/test | 提交渗透测试任务 |
| GET | /api/orchestrator/reports | 获取历史报告列表 |
| GET | /api/orchestrator/reports/{id} | 获取指定报告 |
| DELETE | /api/orchestrator/reports/{id} | 删除指定报告 |
| POST | /api/chat/stream | AI对话（SSE流式） |
| POST | /api/chat/query | AI对话（非流式） |
| GET | /api/chat/models | 获取可用模型列表 |
| GET | /api/chat/sessions | 获取对话会话列表 |
| GET | /api/chat/sessions/{id} | 获取会话消息 |
| DELETE | /api/chat/sessions/{id} | 删除对话会话 |
| POST | /api/recon/whois | WHOIS域名查询 |
| POST | /api/recon/dns | DNS记录解析 |
| POST | /api/recon/security-headers | HTTP安全头检测与评分 |
| POST | /api/recon/port-check | 常见端口扫描 |
| POST | /api/recon/cors-check | CORS跨域配置检测 |
| POST | /api/recon/cookie-check | Cookie安全分析 |
| POST | /api/recon/tech-detect | Web技术指纹识别 |
| POST | /api/recon/subdomain-enum | 子域名枚举 |
| POST | /api/recon/waf-detect | WAF防火墙检测 |
| POST | /api/recon/xss-payloads | XSS Payload生成 |
| POST | /api/recon/full-audit | 综合安全审计 |
| GET | /api/report/print/{id} | 报告PDF打印页 |

## Docker容器

| 容器名 | 镜像 | 说明 |
|--------|------|------|
| nmap | instrumentisto/nmap | 端口扫描 |
| amass | caffix/amass | 子域名枚举 |
| zap | zaproxy/zap-stable | Web应用扫描 |
| sqlmap | pentest-sqlmap（自建） | SQL注入检测 |
| metasploit | metasploitframework/metasploit-framework | 漏洞利用 |
| postgres | postgres:15-alpine | 数据库服务 |
| nikto | frapsoft/nikto | Web服务器漏洞扫描 |
| dirsearch | pentest-dirsearch（自建） | 目录暴力扫描 |
| sslscan | pentest-sslscan（自建） | SSL/TLS安全扫描 |

## 停止系统

```bash
stop.bat
# 或手动停止
docker stop nmap amass zap sqlmap metasploit postgres
```

## 许可证

本项目采用MIT许可证。
