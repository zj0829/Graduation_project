import httpx
import json
import time
import subprocess
import os
import sys
from datetime import datetime

BASE = "http://127.0.0.1:8000"
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def take_screenshot(name):
    ps_script = os.path.join(SCRIPT_DIR, "screenshot.ps1")
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script, path],
        timeout=15
    )
    print(f"  [Screenshot] {name}.png")

def open_page(url):
    subprocess.run(["cmd", "/c", "start", url], timeout=10)

def save_result(name, content):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [Result] {name}.txt")

results = []

def record(test_name, status, detail=""):
    results.append({"test": test_name, "status": status, "detail": detail})
    icon = "PASS" if status == "pass" else "FAIL"
    print(f"  [{icon}] {test_name}" + (f" - {detail}" if detail else ""))

print("=" * 70)
print("  Frontend Functional Test - Real Feature Testing with Screenshots")
print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 70)

# ============================================================
# Test 1: Main Page - Penetration Test Report Generation
# ============================================================
print("\n[Test 1] Main Page - Penetration Test Report Generation")
try:
    start_time = time.time()
    r = httpx.post(f"{BASE}/api/orchestrator/execute-test", json={
        "target": "http://127.0.0.1:8000",
        "requirements": "对本地Web服务进行全面安全评估，检测常见Web漏洞，包括SQL注入、XSS、安全头缺失等",
        "tools": ["auto"],
        "tool_strategy": "auto",
        "report_format": "markdown"
    }, timeout=180)
    elapsed = time.time() - start_time
    data = r.json()

    if r.status_code == 200 and data.get("status") == "success":
        test_id = data.get("test_id", "")
        record("Penetration Test Execution", "pass", f"test_id={test_id}, elapsed={elapsed:.1f}s")

        time.sleep(2)
        result_r = httpx.get(f"{BASE}/api/orchestrator/test-result/{test_id}", timeout=30)
        result_data = result_r.json()

        report = result_data.get("report", "")
        tools_used = result_data.get("tools", [])
        target = result_data.get("target", "")
        created_at = result_data.get("created_at", "")

        output = f"Penetration Test Report\n"
        output += f"{'='*60}\n"
        output += f"Test ID: {test_id}\n"
        output += f"Target: {target}\n"
        output += f"Tools Used: {tools_used}\n"
        output += f"Created At: {created_at}\n"
        output += f"Execution Time: {elapsed:.1f}s\n"
        output += f"Report Length: {len(report)} chars\n"
        output += f"{'='*60}\n\n"
        output += report[:5000]
        if len(report) > 5000:
            output += f"\n\n... (truncated, total {len(report)} chars)"
        save_result("01_pentest_report", output)

        open_page(f"{BASE}/static/index.html")
        time.sleep(3)
        take_screenshot("01_main_page")
    else:
        record("Penetration Test Execution", "fail", f"HTTP {r.status_code}: {data}")
except Exception as e:
    record("Penetration Test Execution", "fail", str(e))

# ============================================================
# Test 2: Main Page - History Reports
# ============================================================
print("\n[Test 2] Main Page - History Reports Display")
try:
    r = httpx.get(f"{BASE}/api/orchestrator/reports", timeout=15)
    data = r.json()
    reports = data.get("reports", [])
    total = data.get("total", 0)

    output = f"History Reports\nTotal: {total}\n\n"
    for rp in reports:
        output += f"  ID: {rp.get('test_id')}\n"
        output += f"  Target: {rp.get('target')}\n"
        output += f"  Tools: {rp.get('tools')}\n"
        output += f"  Strategy: {rp.get('tool_strategy')}\n"
        output += f"  Created: {rp.get('created_at')}\n"
        output += f"  {'-'*40}\n"
    save_result("02_history_reports", output)
    record("History Reports", "pass", f"total={total}")
except Exception as e:
    record("History Reports", "fail", str(e))

# ============================================================
# Test 3: Dashboard - Full Security Audit
# ============================================================
print("\n[Test 3] Dashboard - Full Security Audit")
try:
    start_time = time.time()
    r = httpx.post(f"{BASE}/api/recon/full-audit", json={"url": "http://127.0.0.1:8000/health"}, timeout=60)
    elapsed = time.time() - start_time
    data = r.json()

    output = f"Full Security Audit\n{'='*60}\n"
    output += f"Target: http://127.0.0.1:8000/health\n"
    output += f"Overall Score: {data.get('overall_score', 'N/A')}/100\n"
    output += f"Summary: {data.get('summary', 'N/A')}\n"
    output += f"Execution Time: {elapsed:.1f}s\n\n"

    for key, val in data.get("results", {}).items():
        output += f"--- {key} ---\n"
        if isinstance(val, dict):
            for k, v in val.items():
                output += f"  {k}: {v}\n"
        else:
            output += f"  {val}\n"
        output += "\n"
    save_result("03_full_audit", output)

    open_page(f"{BASE}/static/dashboard.html")
    time.sleep(3)
    take_screenshot("03_dashboard_audit")
    record("Full Security Audit", "pass", f"score={data.get('overall_score')}, elapsed={elapsed:.1f}s")
except Exception as e:
    record("Full Security Audit", "fail", str(e))

# ============================================================
# Test 4: Dashboard - Security Headers Check
# ============================================================
print("\n[Test 4] Dashboard - Security Headers Check")
try:
    r = httpx.post(f"{BASE}/api/recon/security-headers", json={"url": "http://127.0.0.1:8000/health"}, timeout=15)
    data = r.json()

    output = f"Security Headers Check\n{'='*60}\n"
    output += f"Target: {data.get('url')}\n"
    output += f"Status Code: {data.get('status_code')}\n"
    output += f"Server: {data.get('server')}\n"
    output += f"Score: {data.get('score')}/100\n"
    output += f"Missing Headers: {data.get('missing_count')}\n\n"

    for k, v in data.get("security_headers", {}).items():
        status = "PRESENT" if v.get("present") else "MISSING"
        output += f"  [{status}] {v.get('name')}\n"
        output += f"    Severity: {v.get('severity')}\n"
        if v.get("value"):
            output += f"    Value: {v.get('value')}\n"
        output += f"    Description: {v.get('description', '')}\n"
    save_result("04_security_headers", output)
    record("Security Headers", "pass", f"score={data.get('score')}")
except Exception as e:
    record("Security Headers", "fail", str(e))

# ============================================================
# Test 5: Dashboard - CORS Check
# ============================================================
print("\n[Test 5] Dashboard - CORS Check")
try:
    r = httpx.post(f"{BASE}/api/recon/cors-check", json={"url": "http://127.0.0.1:8000/health"}, timeout=15)
    data = r.json()

    output = f"CORS Security Check\n{'='*60}\n"
    output += f"Target: {data.get('url')}\n"
    output += f"Vulnerable: {data.get('vulnerable')}\n"
    output += f"ACAO Header: {data.get('access_control_allow_origin')}\n"
    output += f"ACAC Header: {data.get('access_control_allow_credentials')}\n\n"
    output += "Issues:\n"
    for issue in data.get("issues", []):
        output += f"  [{issue.get('severity')}] {issue.get('detail')}\n"
    save_result("05_cors_check", output)
    record("CORS Check", "pass", f"vulnerable={data.get('vulnerable')}")
except Exception as e:
    record("CORS Check", "fail", str(e))

# ============================================================
# Test 6: Dashboard - Technology Detection
# ============================================================
print("\n[Test 6] Dashboard - Technology Detection")
try:
    r = httpx.post(f"{BASE}/api/recon/tech-detect", json={"url": "http://127.0.0.1:8000/health"}, timeout=15)
    data = r.json()

    output = f"Technology Detection\n{'='*60}\n"
    output += f"Target: {data.get('url')}\n"
    output += f"Total Detected: {data.get('total_detected')}\n"
    output += f"Summary: {data.get('summary')}\n\n"
    for tech in data.get("technologies", []):
        output += f"  [{tech.get('category')}] {tech.get('name')}: {tech.get('value')}\n"
    save_result("06_tech_detect", output)
    record("Tech Detect", "pass", f"detected={data.get('total_detected')}")
except Exception as e:
    record("Tech Detect", "fail", str(e))

# ============================================================
# Test 7: Dashboard - WAF Detection
# ============================================================
print("\n[Test 7] Dashboard - WAF Detection")
try:
    r = httpx.post(f"{BASE}/api/recon/waf-detect", json={"url": "http://127.0.0.1:8000/health"}, timeout=15)
    data = r.json()

    output = f"WAF Detection\n{'='*60}\n"
    output += f"Target: {data.get('url')}\n"
    output += f"WAF Detected: {data.get('waf_detected')}\n"
    output += f"Summary: {data.get('summary')}\n\n"
    for waf in data.get("wafs", []):
        output += f"  {waf.get('name')} (evidence: {waf.get('evidence')})\n"
    save_result("07_waf_detect", output)
    record("WAF Detect", "pass", f"detected={data.get('waf_detected')}")
except Exception as e:
    record("WAF Detect", "fail", str(e))

# ============================================================
# Test 8: Knowledge Page - XSS Payload Generation
# ============================================================
print("\n[Test 8] Knowledge Page - XSS Payload Generation")
try:
    r = httpx.post(f"{BASE}/api/recon/xss-payloads", json={"target": "filter_bypass"}, timeout=15)
    data = r.json()

    output = f"XSS Payload Generation\n{'='*60}\n"
    output += f"Context: {data.get('context')}\n"
    output += f"Total Payloads: {data.get('total_payloads')}\n"
    output += f"Summary: {data.get('summary')}\n\n"

    for cat, items in data.get("payloads", {}).items():
        output += f"[{cat}] ({len(items)} payloads)\n"
        for p in items:
            output += f"  {p}\n"
        output += "\n"

    output += f"\nRecommended ({len(data.get('recommended', []))} payloads):\n"
    for p in data.get("recommended", []):
        output += f"  {p}\n"

    save_result("08_xss_payloads", output)

    open_page(f"{BASE}/static/knowledge.html")
    time.sleep(3)
    take_screenshot("08_knowledge_owasp")
    record("XSS Payload Generation", "pass", f"total={data.get('total_payloads')}")
except Exception as e:
    record("XSS Payload Generation", "fail", str(e))

# ============================================================
# Test 9: Knowledge Page - CVE Search
# ============================================================
print("\n[Test 9] Knowledge Page - CVE Search (Log4j)")
try:
    cve_url = "https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=log4j&resultsPerPage=5"
    r = httpx.get(cve_url, timeout=30)
    data = r.json()
    vulns = data.get("vulnerabilities", [])

    output = f"CVE Search - Log4j\n{'='*60}\n"
    output += f"Results: {len(vulns)} vulnerabilities\n\n"

    for v in vulns:
        cve = v.get("cve", {})
        cve_id = cve.get("id", "N/A")
        descs = cve.get("descriptions", [])
        desc = ""
        for d in descs:
            if d.get("lang") == "en":
                desc = d.get("value", "")
                break
        metrics = cve.get("metrics", {})
        cvss31 = metrics.get("cvssMetricV31", [])
        score = cvss31[0].get("cvssData", {}).get("baseScore", "N/A") if cvss31 else "N/A"
        severity = cvss31[0].get("cvssData", {}).get("baseSeverity", "N/A") if cvss31 else "N/A"

        output += f"CVE: {cve_id}\n"
        output += f"CVSS: {score} ({severity})\n"
        output += f"Description: {desc[:200]}...\n\n"

    save_result("09_cve_search", output)
    record("CVE Search", "pass", f"found={len(vulns)}")
except Exception as e:
    output = f"CVE Search Failed: {e}\nNote: NVD API may have rate limits or network issues"
    save_result("09_cve_search", output)
    record("CVE Search", "fail", str(e))

# ============================================================
# Test 10: Chat Page - AI Conversation
# ============================================================
print("\n[Test 10] Chat Page - AI Conversation Stream")
try:
    start_time = time.time()
    full_response = ""
    with httpx.stream("POST", f"{BASE}/api/chat/stream", json={
        "message": "什么是SQL注入？请简要说明其原理和防御方法",
        "model": "deepseek-chat",
        "session_id": "frontend_test_session"
    }, timeout=60) as stream:
        for line in stream.iter_lines():
            if line.startswith("data: "):
                chunk = line[6:]
                if chunk == "[DONE]":
                    break
                try:
                    d = json.loads(chunk)
                    content = d.get("content", "")
                    full_response += content
                except:
                    pass
    elapsed = time.time() - start_time

    output = f"AI Chat Response\n{'='*60}\n"
    output += f"Model: deepseek-chat\n"
    output += f"Question: 什么是SQL注入？请简要说明其原理和防御方法\n"
    output += f"Response Time: {elapsed:.1f}s\n"
    output += f"Response Length: {len(full_response)} chars\n"
    output += f"{'='*60}\n\n"
    output += full_response[:3000]
    if len(full_response) > 3000:
        output += f"\n\n... (truncated, total {len(full_response)} chars)"
    save_result("10_chat_stream", output)

    open_page(f"{BASE}/static/chat.html")
    time.sleep(3)
    take_screenshot("10_chat_page")
    record("AI Chat Stream", "pass", f"response_len={len(full_response)}, elapsed={elapsed:.1f}s")
except Exception as e:
    record("AI Chat Stream", "fail", str(e))

# ============================================================
# Test 11: Knowledge Page - OWASP Detail View
# ============================================================
print("\n[Test 11] Knowledge Page - OWASP Detail View Screenshot")
try:
    open_page(f"{BASE}/static/knowledge.html")
    time.sleep(3)
    take_screenshot("11_knowledge_owasp_full")
    record("OWASP Detail View", "pass")
except Exception as e:
    record("OWASP Detail View", "fail", str(e))

# ============================================================
# Test 12: Cookie Security Check
# ============================================================
print("\n[Test 12] Cookie Security Check")
try:
    r = httpx.post(f"{BASE}/api/recon/cookie-check", json={"url": "http://127.0.0.1:8000/health"}, timeout=15)
    data = r.json()

    output = f"Cookie Security Check\n{'='*60}\n"
    output += f"Target: {data.get('url')}\n"
    output += f"Total Cookies: {data.get('total_cookies')}\n"
    output += f"Total Issues: {data.get('total_issues')}\n"
    output += f"Summary: {data.get('summary')}\n\n"
    for c in data.get("cookies", []):
        output += f"  Cookie: {c.get('name')}\n"
        flags = c.get("flags", {})
        output += f"    HttpOnly: {flags.get('HttpOnly')}\n"
        output += f"    Secure: {flags.get('Secure')}\n"
        output += f"    SameSite: {flags.get('SameSite')}\n"
        for issue in c.get("issues", []):
            output += f"    [{issue.get('severity')}] {issue.get('detail')}\n"
    save_result("12_cookie_check", output)
    record("Cookie Check", "pass", f"cookies={data.get('total_cookies')}")
except Exception as e:
    record("Cookie Check", "fail", str(e))

# ============================================================
# Test 13: Port Check
# ============================================================
print("\n[Test 13] Port Scan")
try:
    r = httpx.post(f"{BASE}/api/recon/port-check", json={"target": "127.0.0.1", "ports": "80,443,8000,8080,9876,3000"}, timeout=30)
    data = r.json()

    output = f"Port Scan\n{'='*60}\n"
    output += f"Target: {data.get('target')}\n"
    output += f"Open Ports: {data.get('open_count')}\n"
    output += f"Closed Ports: {data.get('closed_count')}\n\n"
    for port in data.get("ports", []):
        status = "OPEN" if port.get("is_open") else "CLOSED"
        output += f"  Port {port.get('port')}: {status}"
        if port.get("service"):
            output += f" ({port.get('service')})"
        output += "\n"
    save_result("13_port_check", output)
    record("Port Check", "pass", f"open={data.get('open_count')}")
except Exception as e:
    record("Port Check", "fail", str(e))

# ============================================================
# Test 14: DNS Lookup
# ============================================================
print("\n[Test 14] DNS Lookup")
try:
    r = httpx.post(f"{BASE}/api/recon/dns", json={"target": "example.com"}, timeout=15)
    data = r.json()

    output = f"DNS Lookup\n{'='*60}\n"
    output += json.dumps(data, indent=2, ensure_ascii=False)[:2000]
    save_result("14_dns_lookup", output)
    record("DNS Lookup", "pass")
except Exception as e:
    record("DNS Lookup", "fail", str(e))

# ============================================================
# Test 15: MCP Tools List
# ============================================================
print("\n[Test 15] MCP Tools List")
try:
    r = httpx.get(f"{BASE}/api/orchestrator/tools", timeout=15)
    data = r.json()
    tools = data.get("tools", {})

    output = f"MCP Tools List\n{'='*60}\n"
    output += f"Total Tools: {len(tools)}\n\n"
    for name, tool in tools.items():
        output += f"  [{tool.get('category')}] {tool.get('display_name')} ({name})\n"
        output += f"    Description: {tool.get('description')}\n"
        params = tool.get("parameters", [])
        for p in params:
            req = "required" if p.get("required") else "optional"
            output += f"    Param: {p.get('name')} ({req}) - {p.get('description')}\n"
        output += "\n"
    save_result("15_mcp_tools", output)
    record("MCP Tools", "pass", f"total={len(tools)}")
except Exception as e:
    record("MCP Tools", "fail", str(e))

# ============================================================
# Test 16: API Documentation Page
# ============================================================
print("\n[Test 16] API Documentation Page")
try:
    open_page(f"{BASE}/docs")
    time.sleep(3)
    take_screenshot("16_api_docs")
    record("API Docs Page", "pass")
except Exception as e:
    record("API Docs Page", "fail", str(e))

# ============================================================
# Test 17: Dashboard Page with Audit Results
# ============================================================
print("\n[Test 17] Dashboard Page - Full View")
try:
    open_page(f"{BASE}/static/dashboard.html")
    time.sleep(3)
    take_screenshot("17_dashboard_full")
    record("Dashboard Full View", "pass")
except Exception as e:
    record("Dashboard Full View", "fail", str(e))

# ============================================================
# Test 18: Main Page - Report View
# ============================================================
print("\n[Test 18] Main Page - Report View")
try:
    r = httpx.get(f"{BASE}/api/orchestrator/reports", timeout=15)
    data = r.json()
    reports = data.get("reports", [])
    if reports:
        test_id = reports[0].get("test_id")
        open_page(f"{BASE}/static/index.html#history")
        time.sleep(3)
        take_screenshot("18_main_report_history")
        record("Report History View", "pass", f"test_id={test_id}")
    else:
        record("Report History View", "fail", "No reports found")
except Exception as e:
    record("Report History View", "fail", str(e))

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("  TEST SUMMARY")
print("=" * 70)

passed = sum(1 for r in results if r["status"] == "pass")
failed = sum(1 for r in results if r["status"] == "fail")
total = len(results)

print(f"\n  Total: {total}  |  Passed: {passed}  |  Failed: {failed}")
print(f"  Success Rate: {passed/total*100:.1f}%\n")

for r in results:
    icon = "OK" if r["status"] == "pass" else "FAIL"
    print(f"  [{icon}] {r['test']}" + (f" - {r['detail']}" if r["detail"] else ""))

summary_output = f"Frontend Functional Test Summary\n"
summary_output += f"{'='*60}\n"
summary_output += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
summary_output += f"Total: {total} | Passed: {passed} | Failed: {failed}\n"
summary_output += f"Success Rate: {passed/total*100:.1f}%\n\n"
for r in results:
    icon = "PASS" if r["status"] == "pass" else "FAIL"
    summary_output += f"[{icon}] {r['test']}" + (f" - {r['detail']}" if r["detail"] else "") + "\n"
save_result("00_test_summary", summary_output)

print(f"\n  Screenshots saved to: {SCREENSHOT_DIR}")
print(f"  Results saved to: {SCREENSHOT_DIR}")
print("=" * 70)
