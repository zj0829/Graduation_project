import httpx
import json
import time
import os
import subprocess
from datetime import datetime

BASE = "http://127.0.0.1:8000"
MCP = "http://127.0.0.1:9876"
LOCAL_URL = "http://127.0.0.1:8000/health"
LOCAL_DOMAIN = "127.0.0.1"

screenshot_dir = "screenshots"
os.makedirs(screenshot_dir, exist_ok=True)

def save_result(name, content):
    filepath = os.path.join(screenshot_dir, f"{name}.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"=== {name} ===\n")
        f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(content)
    print(f"  Saved: {filepath}")

print("=" * 60)
print("  Capturing functional test results as text screenshots")
print("=" * 60)

print("\n[1] Docker Container Status...")
r = subprocess.run(["docker", "ps", "-a", "--format", "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"],
    capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
save_result("01_docker_containers", r.stdout)

print("[2] Docker Stats...")
r = subprocess.run(["docker", "stats", "--no-stream", "--format", "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}"],
    capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
save_result("02_docker_stats", r.stdout)

print("[3] MCP Health & Tools...")
try:
    r = httpx.get(f"{MCP}/health", timeout=10)
    data = r.json()
    save_result("03_mcp_health", json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    save_result("03_mcp_health", f"Error: {e}")

print("[4] Backend Health...")
try:
    r = httpx.get(f"{BASE}/health", timeout=10)
    save_result("04_backend_health", json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    save_result("04_backend_health", f"Error: {e}")

print("[5] Security Headers Check...")
try:
    r = httpx.post(f"{BASE}/api/recon/security-headers", json={"url": LOCAL_URL}, timeout=30)
    data = r.json()
    output = f"Status: {data.get('status')}\n"
    output += f"Score: {data.get('score')}/100\n"
    output += f"Missing: {data.get('missing_count')} headers\n"
    output += f"Server: {data.get('server')}\n"
    output += f"URL: {data.get('url')}\n\n"
    for k, v in data.get("security_headers", {}).items():
        status = "PRESENT" if v.get("present") else "MISSING"
        output += f"  [{status}] {v.get('name')} - {v.get('severity')}\n"
    save_result("05_security_headers", output)
except Exception as e:
    save_result("05_security_headers", f"Error: {e}")

print("[6] CORS Check...")
try:
    r = httpx.post(f"{BASE}/api/recon/cors-check", json={"url": LOCAL_URL}, timeout=30)
    data = r.json()
    output = f"Vulnerable: {data.get('vulnerable')}\n"
    output += f"ACAO: {data.get('access_control_allow_origin')}\n"
    output += f"ACAC: {data.get('access_control_allow_credentials')}\n\n"
    for i in data.get("issues", []):
        output += f"  [{i.get('severity')}] {i.get('detail')}\n"
    save_result("06_cors_check", output)
except Exception as e:
    save_result("06_cors_check", f"Error: {e}")

print("[7] Cookie Check...")
try:
    r = httpx.post(f"{BASE}/api/recon/cookie-check", json={"url": LOCAL_URL}, timeout=30)
    data = r.json()
    output = f"Total Cookies: {data.get('total_cookies')}\n"
    output += f"Total Issues: {data.get('total_issues')}\n\n"
    for c in data.get("cookies", []):
        output += f"  Cookie: {c.get('name')}\n"
        output += f"    HttpOnly: {c.get('flags', {}).get('HttpOnly')}\n"
        output += f"    Secure: {c.get('flags', {}).get('Secure')}\n"
        output += f"    SameSite: {c.get('flags', {}).get('SameSite')}\n"
        for i in c.get("issues", []):
            output += f"    [{i.get('severity')}] {i.get('detail')}\n"
    save_result("07_cookie_check", output)
except Exception as e:
    save_result("07_cookie_check", f"Error: {e}")

print("[8] Tech Detect...")
try:
    r = httpx.post(f"{BASE}/api/recon/tech-detect", json={"url": LOCAL_URL}, timeout=30)
    data = r.json()
    output = f"Total Detected: {data.get('total_detected')}\n\n"
    for t in data.get("technologies", []):
        output += f"  [{t.get('category')}] {t.get('name')}: {t.get('value')}\n"
    save_result("08_tech_detect", output)
except Exception as e:
    save_result("08_tech_detect", f"Error: {e}")

print("[9] Port Check...")
try:
    r = httpx.post(f"{BASE}/api/recon/port-check", json={"target": LOCAL_DOMAIN}, timeout=30)
    data = r.json()
    output = f"Host: {data.get('host')}\n"
    output += f"Checked: {data.get('total_checked')} ports\n"
    output += f"Open Ports: {len(data.get('open_ports', []))}\n\n"
    for p in data.get("open_ports", []):
        output += f"  {p.get('port')}/{p.get('service')}\n"
    save_result("09_port_check", output)
except Exception as e:
    save_result("09_port_check", f"Error: {e}")

print("[10] WAF Detect...")
try:
    r = httpx.post(f"{BASE}/api/recon/waf-detect", json={"url": LOCAL_URL}, timeout=30)
    data = r.json()
    output = f"WAF Detected: {data.get('waf_detected')}\n"
    for w in data.get("wafs", []):
        output += f"  {w.get('name')} (evidence: {w.get('evidence')})\n"
    save_result("10_waf_detect", output)
except Exception as e:
    save_result("10_waf_detect", f"Error: {e}")

print("[11] XSS Payloads...")
try:
    r = httpx.post(f"{BASE}/api/recon/xss-payloads", json={"target": "basic"}, timeout=30)
    data = r.json()
    output = f"Total Payloads: {data.get('total_payloads')}\n\n"
    for cat, items in data.get("payloads", {}).items():
        output += f"  [{cat}] ({len(items)} payloads)\n"
        for p in items:
            output += f"    {p}\n"
        output += "\n"
    save_result("11_xss_payloads", output)
except Exception as e:
    save_result("11_xss_payloads", f"Error: {e}")

print("[12] Full Audit...")
try:
    r = httpx.post(f"{BASE}/api/recon/full-audit", json={"url": LOCAL_URL}, timeout=60)
    data = r.json()
    output = f"Overall Score: {data.get('overall_score')}/100\n\n"
    for key, val in data.get("results", {}).items():
        output += f"  [{key}]\n"
        if isinstance(val, dict):
            for k, v in val.items():
                output += f"    {k}: {v}\n"
        else:
            output += f"    {val}\n"
        output += "\n"
    save_result("12_full_audit", output)
except Exception as e:
    save_result("12_full_audit", f"Error: {e}")

print("[13] Docker Tool Execution...")
tool_tests = [
    ("Nmap", "pentest-nmap", "nmap --version"),
    ("Amass", "pentest-amass", "amass -version"),
    ("SQLmap", "pentest-sqlmap", "python3 /opt/sqlmap/sqlmap.py --version"),
    ("Nikto", "pentest-nikto", "perl /usr/bin/nikto.pl -Version"),
    ("Dirsearch", "pentest-dirsearch", "dirsearch --help 2>&1 | head -5"),
    ("SSLscan", "pentest-sslscan", "sslscan --help 2>&1 | head -5"),
]
tool_output = ""
for name, container, cmd in tool_tests:
    start = time.time()
    try:
        r = subprocess.run(["docker", "exec", container, "sh", "-c", cmd],
            capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace")
        elapsed = round((time.time() - start) * 1000)
        out = (r.stdout + r.stderr).strip()[:200]
        tool_output += f"[{name}] ({container}) - {elapsed}ms\n  {out}\n\n"
    except Exception as e:
        tool_output += f"[{name}] ({container}) - FAILED: {e}\n\n"
save_result("13_docker_tools", tool_output)

print("[14] Chat Models...")
try:
    r = httpx.get(f"{BASE}/api/chat/models", timeout=10)
    data = r.json()
    save_result("14_chat_models", json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    save_result("14_chat_models", f"Error: {e}")

print("\n" + "=" * 60)
print("  All functional results captured!")
print(f"  Saved to: {os.path.abspath(screenshot_dir)}")
print("=" * 60)
