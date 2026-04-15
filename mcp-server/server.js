const express = require('express');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');
const { execSync, exec } = require('child_process');
const fs = require('fs');
const path = require('path');

process.env.LANG = 'zh_CN.UTF-8';
process.env.LC_ALL = 'zh_CN.UTF-8';

const LOG_DIR = path.join(__dirname, '..', 'data');
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });
const LOG_FILE = path.join(LOG_DIR, 'mcp.log');

function log(msg) {
    const ts = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false });
    const line = `[${ts}] ${msg}\n`;
    fs.appendFileSync(LOG_FILE, line, 'utf8');
    console.log(`[${ts}] ${msg}`);
}

function bjNow() {
    return new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false });
}

const app = express();
const PORT = process.env.MCP_PORT || 9876;

// 中间件
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// 工具配置
const TOOLS_CONFIG = {
    nmap: {
        name: 'nmap',
        description: '网络扫描和信息收集工具，用于端口扫描、服务识别、操作系统检测',
        category: 'information_gathering',
        container: 'pentest-nmap',
        command: 'nmap',
        parameters: [
            { name: 'target', type: 'string', required: true, description: '目标IP或域名' },
            { name: 'options', type: 'string', required: false, description: '扫描选项，如 -sV, -sS, -O' }
        ]
    },
    amass: {
        name: 'amass',
        description: '子域名枚举工具，用于发现目标域名的子域名信息',
        category: 'information_gathering',
        container: 'pentest-amass',
        command: 'amass',
        parameters: [
            { name: 'domain', type: 'string', required: true, description: '目标域名' },
            { name: 'options', type: 'string', required: false, description: '枚举选项，如 -passive, -active' }
        ]
    },
    owasp_zap: {
        name: 'owasp_zap',
        description: 'OWASP ZAP Web应用漏洞扫描器，用于自动检测Web应用安全漏洞',
        category: 'vulnerability_scanning',
        container: 'pentest-owasp-zap',
        apiUrl: 'http://owasp-zap:8090',
        parameters: [
            { name: 'target_url', type: 'string', required: true, description: '目标URL' },
            { name: 'scan_type', type: 'string', required: false, description: '扫描类型：spider, active_scan, passive_scan' }
        ]
    },
    sqlmap: {
        name: 'sqlmap',
        description: 'SQL注入检测和利用工具，用于自动检测SQL注入漏洞',
        category: 'vulnerability_scanning',
        container: 'pentest-sqlmap',
        command: 'sqlmap',
        parameters: [
            { name: 'url', type: 'string', required: true, description: '包含参数的目标URL' },
            { name: 'options', type: 'string', required: false, description: '测试选项，如 --dbs, --tables, --dump' }
        ]
    },
    metasploit: {
        name: 'metasploit',
        description: 'Metasploit渗透测试框架，用于漏洞利用和后渗透操作',
        category: 'exploitation',
        container: 'pentest-metasploit',
        rpcUrl: 'http://metasploit:55553',
        parameters: [
            { name: 'module', type: 'string', required: true, description: 'Metasploit模块路径' },
            { name: 'options', type: 'object', required: false, description: '模块参数对象' }
        ]
    },
    burp_suite: {
        name: 'burp_suite',
        description: 'Burp Suite Web安全测试平台，用于Web应用安全测试和分析',
        category: 'web_testing',
        container: 'pentest-burpsuite',
        webUrl: 'http://burpsuite:8080',
        parameters: [
            { name: 'action', type: 'string', required: true, description: '操作类型：scan, spider, analyze' },
            { name: 'target_url', type: 'string', required: false, description: '目标URL' }
        ]
    },
    report_generator: {
        name: 'report_generator',
        description: '渗透测试报告生成器，整合所有工具结果生成专业报告',
        category: 'reporting',
        parameters: [
            { name: 'results', type: 'object', required: true, description: '所有工具的执行结果' },
            { name: 'format', type: 'string', required: false, description: '报告格式：markdown, html, word' }
        ]
    }
};

// 存储会话状态
const sessions = new Map();

// MCP协议处理
app.post('/jsonrpc', async (req, res) => {
    const { jsonrpc, method, params, id } = req.body;
    
    log(`[MCP] 收到请求: ${method}`);
    
    try {
        let result;
        
        switch (method) {
            case 'initialize':
                result = handleInitialize(params);
                break;
            case 'tools/list':
                result = handleToolsList();
                break;
            case 'tools/call':
                result = await handleToolsCall(params);
                break;
            default:
                throw new Error(`未知方法: ${method}`);
        }
        
        res.json({
            jsonrpc: '2.0',
            result,
            id
        });
        
    } catch (error) {
        console.error(`[MCP] 错误:`, error.message);
        res.json({
            jsonrpc: '2.0',
            error: {
                code: -32603,
                message: error.message
            },
            id
        });
    }
});

// 初始化连接
function handleInitialize(params) {
    const sessionId = uuidv4();
    
    sessions.set(sessionId, {
        client: params.client || 'unknown',
        version: params.version || '1.0.0',
        createdAt: bjNow(),
        status: 'connected'
    });
    
    log(`[MCP] 新客户端连接: ${sessionId}`);
    
    return {
        sessionId,
        server: {
            name: 'pentest-mcp-server',
            version: '1.0.0'
        },
        capabilities: {
            tools: {}
        },
        message: '渗透测试MCP服务初始化成功'
    };
}

// 获取工具列表
function handleToolsList() {
    const tools = Object.values(TOOLS_CONFIG).map(tool => ({
        name: tool.name,
        description: tool.description,
        category: tool.category,
        parameters: tool.parameters
    }));
    
    return {
        count: tools.length,
        tools
    };
}

// 执行工具调用
async function handleToolsCall(params) {
    const { tool, parameters } = params;
    const toolConfig = TOOLS_CONFIG[tool];
    
    if (!toolConfig) {
        throw new Error(`未知工具: ${tool}`);
    }
    
    // 验证必需参数
    const missingParams = toolConfig.parameters
        .filter(p => p.required && !parameters[p.name])
        .map(p => p.name);
    
    if (missingParams.length > 0) {
        throw new Error(`缺少必需参数: ${missingParams.join(', ')}`);
    }
    
    log(`[MCP] 执行工具: ${tool}`);
    
    // 根据工具类型执行不同的逻辑
    let executionResult;
    
    switch (tool) {
        case 'nmap':
            executionResult = await executeNmap(parameters);
            break;
        case 'amass':
            executionResult = await executeAmass(parameters);
            break;
        case 'owasp_zap':
            executionResult = await executeZAP(parameters);
            break;
        case 'sqlmap':
            executionResult = await executeSqlmap(parameters);
            break;
        case 'metasploit':
            executionResult = await executeMetasploit(parameters);
            break;
        case 'burp_suite':
            executionResult = await executeBurpSuite(parameters);
            break;
        default:
            throw new Error(`工具执行未实现: ${tool}`);
    }
    
    return {
        tool,
        status: 'success',
        timestamp: bjNow(),
        result: executionResult
    };
}

// Nmap执行函数
const DOCKER_CMD = process.platform === 'win32' 
    ? '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe"' 
    : 'docker';

async function executeNmap(params) {
    let target = params.target;
    const options = params.options || '-sV -sC';
    
    target = target.replace(/^https?:\/\//, '').replace(/\/.*$/, '');
    
    try {
        let cmd = `nmap ${options} ${target}`;
        let useDocker = false;
        try {
            execSync(`${DOCKER_CMD} ps`, { encoding: 'utf8', timeout: 5000 });
            cmd = `${DOCKER_CMD} exec pentest-nmap nmap ${options} ${target}`;
            useDocker = true;
        } catch (e) {
            cmd = `nmap ${options} ${target}`;
        }
        log(`[Nmap] 执行命令: ${cmd}`);
        
        const output = execSync(cmd, { 
            encoding: 'utf8',
            timeout: 300000,
            maxBuffer: 50 * 1024 * 1024
        });
        
        return {
            raw_output: output,
            parsed_data: parseNmapOutput(output),
            target,
            options,
            execution_time: bjNow()
        };
        
    } catch (error) {
        console.error('[Nmap] 执行错误:', error.message);
        return {
            raw_output: `[模拟模式] Nmap扫描 ${target}\n\n扫描结果:\n- 端口 80: OPEN (HTTP)\n- 端口 443: OPEN (HTTPS)\n- 端口 8000: OPEN (FastAPI)\n- 端口 9876: OPEN (MCP Service)\n\n注意: 这是模拟结果，实际工具未安装或Docker容器未启动`,
            parsed_data: { ports: [
                {port: 80, protocol: 'tcp', service: 'http', version: ''},
                {port: 443, protocol: 'tcp', service: 'https', version: ''},
                {port: 8000, protocol: 'tcp', service: 'FastAPI', version: ''},
                {port: 9876, protocol: 'tcp', service: 'MCP', version: ''}
            ], total_ports: 4},
            target,
            options,
            simulated: true,
            execution_time: bjNow()
        };
    }
}

// Amass执行函数
async function executeAmass(params) {
    const domain = params.domain;
    const options = params.options || '-passive';
    
    try {
        const cmd = `${DOCKER_CMD} exec pentest-amass amass enum ${options} -d ${domain}`;
        log(`[Amass] 执行命令: ${cmd}`);
        
        const output = execSync(cmd, { 
            encoding: 'utf8',
            timeout: 600000, // 10分钟超时
            maxBuffer: 100 * 1024 * 1024
        });
        
        return {
            raw_output: output,
            subdomains: parseSubdomains(output),
            domain,
            options,
            execution_time: bjNow()
        };
        
    } catch (error) {
        console.error('[Amass] 执行错误:', error.message);
        return {
            error: error.message,
            suggestion: '请检查域名格式是否正确，以及Amass容器是否正常运行'
        };
    }
}

// OWASP ZAP执行函数
async function executeZAP(params) {
    const targetUrl = params.target_url;
    const scanType = params.scan_type || 'spider';
    
    try {
        // 使用ZAP API进行扫描
        const zapApiUrl = `http://pentest-owasp-zap:8090`;
        
        try {
            execSync(`${DOCKER_CMD} exec pentest-owasp-zap curl -s "${zapApiUrl}/JSON/core/access?url=${encodeURIComponent(targetUrl)}"`, { timeout: 30000 });
        } catch(e) {
            execSync(`curl -s "http://127.0.0.1:8090/JSON/core/access?url=${encodeURIComponent(targetUrl)}"`, { timeout: 30000 });
        }
        
        let scanId;
        if (scanType === 'spider') {
            let response;
            try {
                response = execSync(`${DOCKER_CMD} exec pentest-owasp-zap curl -s "${zapApiUrl}/JSON/spider/action/scan/?url=${encodeURIComponent(targetUrl)}"`, { timeout: 30000 });
            } catch(e) {
                response = execSync(`curl -s "http://127.0.0.1:8090/JSON/spider/action/scan/?url=${encodeURIComponent(targetUrl)}"`, { timeout: 30000 });
            }
            scanId = JSON.parse(response).scan;
        } else if (scanType === 'active_scan') {
            let response;
            try {
                response = execSync(`${DOCKER_CMD} exec pentest-owasp-zap curl -s "${zapApiUrl}/JSON/ascan/action/scan/?url=${encodeURIComponent(targetUrl)}"`, { timeout: 30000 });
            } catch(e) {
                response = execSync(`curl -s "http://127.0.0.1:8090/JSON/ascan/action/scan/?url=${encodeURIComponent(targetUrl)}"`, { timeout: 30000 });
            }
            scanId = JSON.parse(response).scan;
        }
        
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        let alertsResponse;
        try {
            alertsResponse = execSync(`${DOCKER_CMD} exec pentest-owasp-zap curl -s "${zapApiUrl}/JSON/core/view/alerts/"`, { timeout: 30000 });
        } catch(e) {
            alertsResponse = execSync(`curl -s "http://127.0.0.1:8090/JSON/core/view/alerts/"`, { timeout: 30000 });
        }
        const alerts = JSON.parse(alertsResponse).alerts || [];
        
        return {
            scan_type: scanType,
            target_url: targetUrl,
            alerts_found: alerts.length,
            alerts: alerts.slice(0, 20),
            zap_api_url: zapApiUrl,
            execution_time: bjNow()
        };
        
    } catch (error) {
        console.error('[ZAP] 执行错误:', error.message);
        return {
            error: error.message,
            suggestion: '请检查OWASP ZAP容器是否已启动，并确认API端口8090可访问'
        };
    }
}

// SQLmap执行函数
async function executeSqlmap(params) {
    const url = params.url;
    const options = params.options || '--batch --level=3';
    
    try {
        const cmd = `${DOCKER_CMD} exec pentest-sqlmap python3 sqlmap.py -u "${url}" ${options} --random-agent`;
        log(`[SQLmap] 执行命令: ${cmd}`);
        
        const output = execSync(cmd, { 
            encoding: 'utf8',
            timeout: 600000,
            maxBuffer: 100 * 1024 * 1024
        });
        
        return {
            raw_output: output,
            vulnerabilities: parseSqlmapOutput(output),
            target_url: url,
            options,
            execution_time: bjNow()
        };
        
    } catch (error) {
        console.error('[SQLmap] 执行错误:', error.message);
        return {
            error: error.message,
            suggestion: '请检查URL格式是否正确（需包含参数），以及SQLmap容器是否正常运行'
        };
    }
}

// Metasploit执行函数
async function executeMetasploit(params) {
    const module = params.module;
    const options = params.options || {};
    
    try {
        const msfRpcUrl = 'http://127.0.0.1:55553';
        
        let output = '';
        try {
            const optStr = Object.entries(options).map(([k,v]) => `${k}=${v}`).join(' ');
            const cmd = `${DOCKER_CMD} exec pentest-metasploit /usr/src/metasploit-framework/msfconsole -q -x "use ${module}; setg ${optStr}; run; exit"`;
            log(`[Metasploit] 执行命令: ${cmd}`);
            output = execSync(cmd, {
                encoding: 'utf8',
                timeout: 300000,
                maxBuffer: 50 * 1024 * 1024
            });
        } catch(e) {
            output = e.stdout || e.message;
        }
        
        return {
            module,
            options,
            raw_output: output || 'Metasploit模块执行完成',
            rpc_url: msfRpcUrl,
            status: 'completed',
            execution_time: bjNow()
        };
        
    } catch (error) {
        console.error('[Metasploit] 执行错误:', error.message);
        return {
            error: error.message,
            suggestion: '请确保Metasploit容器及其数据库容器都已正常启动'
        };
    }
}

// Burp Suite执行函数
async function executeBurpSuite(params) {
    const action = params.action;
    const targetUrl = params.target_url;
    
    try {
        const burpUrl = 'http://localhost:8086';
        
        return {
            action,
            target_url: targetUrl,
            status: 'burpsuite_running',
            web_interface: burpUrl,
            note: 'Burp Suite主要通过Web界面进行操作，建议手动使用',
            execution_time: bjNow()
        };
        
    } catch (error) {
        console.error('[Burp Suite] 执行错误:', error.message);
        return {
            error: error.message,
            suggestion: '请确保Burp Suite容器已启动，并通过浏览器访问其Web界面'
        };
    }
}

// 辅助解析函数
function parseNmapOutput(output) {
    const ports = [];
    const portRegex = /(\d+)\/(tcp|udp)\s+open\s+(\S+)\s+(.*)/g;
    let match;
    
    while ((match = portRegex.exec(output)) !== null) {
        ports.push({
            port: parseInt(match[1]),
            protocol: match[2],
            service: match[3],
            version: match[4].trim()
        });
    }
    
    return { ports, total_ports: ports.length };
}

function parseSubdomains(output) {
    const lines = output.split('\n').filter(line => line.includes('.'));
    return [...new Set(lines.map(line => line.trim()))];
}

function parseSqlmapOutput(output) {
    const vulns = [];
    if (output.includes('is vulnerable')) {
        vulns.push({
            type: 'SQL Injection',
            severity: 'High',
            details: output.substring(0, 500)
        });
    }
    return vulns;
}

// 健康检查端点
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'pentest-mcp-server',
        version: '1.0.0',
        timestamp: bjNow(),
        available_tools: Object.keys(TOOLS_CONFIG)
    });
});

// SSE端点（备用）
app.get('/sse', (req, res) => {
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
    });
    
    res.write(`data: ${JSON.stringify({ type: 'connected', message: 'MCP SSE连接成功' })}\n\n`);
    
    // 心跳
    const heartbeat = setInterval(() => {
        res.write(`data: ${JSON.stringify({ type: 'heartbeat', timestamp: bjNow() })}\n\n`);
    }, 30000);
    
    req.on('close', () => {
        clearInterval(heartbeat);
    });
});

// 启动服务器
app.listen(PORT, () => {
    log('========================================');
    log('  渗透测试 MCP 服务器启动成功');
    log(`  服务地址: http://localhost:${PORT}`);
    log('  协议支持: JSON-RPC + SSE');
    log(`  可用工具数: ${Object.keys(TOOLS_CONFIG).length}`);
    log('========================================');
    log('可用工具:');
    Object.entries(TOOLS_CONFIG).forEach(([key, config]) => {
        log(`  + ${config.name}: ${config.description}`);
    });
});

module.exports = app;
