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
- **安全工具**：Nmap, Amass, OWASP ZAP, SQLmap, Metasploit Framework, Burp Suite

## 系统架构

系统采用三层架构设计：

1. **智能决策层（LLM Brain）**：基于DeepSeek/GLM大模型，负责需求解析、测试规划、结果分析与报告生成
2. **调度控制层（MCP Orchestrator）**：基于MCP JSON-RPC协议的智能调度中间件，管理工具注册、任务分发与数据流转
3. **工具执行层（Docker Containers）**：各安全工具运行在独立Docker容器中，通过pentest-network桥接网络互联

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
│   ├── report/              # 报告生成模块
│   │   └── report_generator.py
│   └── common/              # 公共模块（日志等）
├── mcp-server/
│   └── server.js            # MCP Gateway（JSON-RPC工具调度）
├── static/
│   ├── index.html           # 主页 - 渗透测试控制台
│   ├── chat.html            # AI安全对话页（流式输出）
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
- **AI对话**：http://localhost:8000/static/chat.html
- **API文档**：http://localhost:8000/docs

## 核心功能

### 渗透测试控制台（主页）
- 输入目标URL和测试需求，一键启动自动化渗透测试
- 支持工具策略选择：自动 / 仅Nmap+SQLmap / 全工具
- 5步进度条实时展示测试流程
- Markdown格式专业渗透测试报告，支持下载
- 历史报告查看、加载、删除
- 报告下载命名格式：`目标地址_日期时间.md`

### AI安全对话
- 基于MCP工具集的专业网络安全对话
- SSE流式输出，实时逐字生成回复
- 支持3种AI模型切换：DeepSeek Chat / DeepSeek Reasoner / GLM-4.7-Flash
- 对话历史持久化存储（SQLite）
- 会话管理：新建、切换、删除对话
- MCP连接状态实时指示

### MCP工具调度
- JSON-RPC协议通信，端口9876
- 工具注册与发现
- Docker容器化工具执行
- 工具列表：nmap, amass, owasp_zap, sqlmap, metasploit, burp_suite

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

## Docker容器

| 容器名 | 镜像 | 说明 |
|--------|------|------|
| nmap | instrumentisto/nmap | 端口扫描 |
| amass | caffix/amass | 子域名枚举 |
| zap | zaproxy/zap-stable | Web应用扫描 |
| sqlmap | pentest-sqlmap（自建） | SQL注入检测 |
| metasploit | metasploitframework/metasploit-framework | 漏洞利用 |
| postgres | postgres:15-alpine | 数据库服务 |

## 停止系统

```bash
stop.bat
# 或手动停止
docker stop nmap amass zap sqlmap metasploit postgres
```

## 许可证

本项目采用MIT许可证。
