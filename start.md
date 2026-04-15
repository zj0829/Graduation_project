步骤1: 启动Docker Desktop（手动双击图标）

步骤2: 创建网络 + 启动容器

docker network create pentest-network

docker start pentest-nmap pentest-amass pentest-sqlmap pentest-owasp-zap pentest-metasploit pentest-metasploit-db

（首次需用 docker run 创建，见文档）

步骤3: 启动MCP服务

cd mcp-server && node server.js

步骤4: 启动后端（新终端）

cd d:\Graduation\_project\Test && python main.py

步骤5: 打开浏览器

start <http://localhost:8000/static/index.html>
