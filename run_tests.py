import httpx
import json
import time
import psutil
import os
import socket
import subprocess
import sys
from datetime import datetime

BASE = "http://127.0.0.1:8000"
MCP = "http://127.0.0.1:9876"
LOCAL_URL = "http://127.0.0.1:8000/health"
LOCAL_DOMAIN = "127.0.0.1"

results = []
system_metrics = {}


def measure_api(name, method, url, body=None, timeout=30):
    start = time.time()
    mem_before = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    try:
        if method == "GET":
            r = httpx.get(url, timeout=timeout, follow_redirects=True)
        else:
            r = httpx.post(url, json=body, timeout=timeout)
        elapsed = round((time.time() - start) * 1000, 2)
        mem_after = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        ct = r.headers.get("content-type", "")
        data = r.json() if "json" in ct else None
        size = len(r.content)
        result = {
            "name": name, "method": method, "url": url,
            "status": r.status_code, "pass": r.status_code == 200,
            "elapsed_ms": elapsed, "response_bytes": size,
            "mem_delta_mb": round(mem_after - mem_before, 2),
        }
        if data:
            result["data"] = data
        return result
    except Exception as e:
        elapsed = round((time.time() - start) * 1000, 2)
        return {
            "name": name, "method": method, "url": url,
            "status": 0, "pass": False, "elapsed_ms": elapsed,
            "error": str(e)[:100], "response_bytes": 0, "mem_delta_mb": 0,
        }


def collect_system_info():
    cpu_percent = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    net = psutil.net_io_counters()
    return {
        "cpu_percent": cpu_percent,
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        "mem_total_gb": round(mem.total / 1024**3, 2),
        "mem_used_gb": round(mem.used / 1024**3, 2),
        "mem_percent": mem.percent,
        "disk_total_gb": round(disk.total / 1024**3, 2),
        "disk_used_gb": round(disk.used / 1024**3, 2),
        "disk_percent": disk.percent,
        "net_bytes_sent": net.bytes_sent,
        "net_bytes_recv": net.bytes_recv,
    }


def collect_process_info():
    procs = {}
    for p in psutil.process_iter(["name", "pid", "memory_info", "cpu_percent"]):
        try:
            name = p.info["name"].lower()
            if name in ("python.exe", "node.exe", "docker.exe"):
                if name not in procs:
                    procs[name] = {"count": 0, "total_mem_mb": 0, "pids": []}
                procs[name]["count"] += 1
                mem = p.info["memory_info"].rss / 1024 / 1024 if p.info["memory_info"] else 0
                procs[name]["total_mem_mb"] += mem
                procs[name]["pids"].append(p.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return procs


def collect_docker_info():
    try:
        r = subprocess.run(
            ["docker", "ps", "-a", "--format",
             "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"],
            capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace"
        )
        containers = []
        for line in r.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|")
            c = {"name": parts[0], "image": parts[1], "status": parts[2]}
            if len(parts) > 3:
                c["ports"] = parts[3]
            c["running"] = "Up" in parts[2]
            containers.append(c)
        return containers
    except Exception:
        return []


def collect_docker_stats():
    try:
        r = subprocess.run(
            ["docker", "stats", "--no-stream", "--format",
             "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.NetIO}}|{{.BlockIO}}"],
            capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace"
        )
        stats = []
        for line in r.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) >= 6:
                stats.append({
                    "name": parts[0], "cpu": parts[1], "mem_usage": parts[2],
                    "mem_percent": parts[3], "net_io": parts[4], "block_io": parts[5],
                })
        return stats
    except Exception:
        return []


print("=" * 60)
print("  Web Pentest System - Comprehensive Test Suite")
print("  Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)

print("\n[1/6] Collecting system information...")
system_metrics = collect_system_info()
process_info = collect_process_info()
print(f"  CPU: {system_metrics['cpu_percent']}% | RAM: {system_metrics['mem_percent']}% | Disk: {system_metrics['disk_percent']}%")

print("\n[2/6] Collecting Docker information...")
docker_containers = collect_docker_info()
docker_stats = collect_docker_stats()
running = sum(1 for c in docker_containers if c["running"])
print(f"  Containers: {running}/{len(docker_containers)} running")

print("\n[3/6] Testing Python Recon API endpoints...")
recon_tests = [
    ("WHOIS", "POST", BASE + "/api/recon/whois", {"target": LOCAL_DOMAIN}),
    ("DNS", "POST", BASE + "/api/recon/dns", {"target": LOCAL_DOMAIN}),
    ("Security Headers", "POST", BASE + "/api/recon/security-headers", {"url": LOCAL_URL}),
    ("Port Check", "POST", BASE + "/api/recon/port-check", {"target": LOCAL_DOMAIN}),
    ("CORS Check", "POST", BASE + "/api/recon/cors-check", {"url": LOCAL_URL}),
    ("Cookie Check", "POST", BASE + "/api/recon/cookie-check", {"url": LOCAL_URL}),
    ("Tech Detect", "POST", BASE + "/api/recon/tech-detect", {"url": LOCAL_URL}),
    ("Subdomain Enum", "POST", BASE + "/api/recon/subdomain-enum", {"target": LOCAL_DOMAIN}),
    ("WAF Detect", "POST", BASE + "/api/recon/waf-detect", {"url": LOCAL_URL}),
    ("XSS Payloads", "POST", BASE + "/api/recon/xss-payloads", {"target": "basic"}),
    ("Full Audit", "POST", BASE + "/api/recon/full-audit", {"url": LOCAL_URL}),
]
for t in recon_tests:
    r = measure_api(*t)
    results.append(r)
    status = "PASS" if r["pass"] else "FAIL"
    print(f"  [{status}] {r['name']}: {r['status']} ({r['elapsed_ms']}ms)")

print("\n[4/6] Testing Core API endpoints...")
core_tests = [
    ("Health Check", "GET", BASE + "/health"),
    ("Reports List", "GET", BASE + "/api/orchestrator/reports"),
    ("Chat Models", "GET", BASE + "/api/chat/models"),
    ("Chat Sessions", "GET", BASE + "/api/chat/sessions"),
    ("MCP Health", "GET", MCP + "/health"),
    ("MCP Tools List", "POST", MCP + "/jsonrpc",
     {"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2}),
]
for t in core_tests:
    r = measure_api(*t)
    results.append(r)
    status = "PASS" if r["pass"] else "FAIL"
    print(f"  [{status}] {r['name']}: {r['status']} ({r['elapsed_ms']}ms)")

print("\n[5/6] Testing Frontend pages...")
page_tests = [
    ("Index Page", "GET", BASE + "/static/index.html"),
    ("Chat Page", "GET", BASE + "/static/chat.html"),
    ("Dashboard Page", "GET", BASE + "/static/dashboard.html"),
    ("Knowledge Page", "GET", BASE + "/static/knowledge.html"),
]
for t in page_tests:
    r = measure_api(*t)
    results.append(r)
    status = "PASS" if r["pass"] else "FAIL"
    print(f"  [{status}] {r['name']}: {r['status']} ({r['response_bytes']} bytes, {r['elapsed_ms']}ms)")

print("\n[6/6] Testing Docker container tool execution...")
tool_exec_results = []
tool_tests = [
    ("Nmap Version", "pentest-nmap", "nmap --version"),
    ("Amass Version", "pentest-amass", "amass -version"),
    ("SQLmap Version", "pentest-sqlmap", "python3 /opt/sqlmap/sqlmap.py --version"),
    ("Nikto Version", "pentest-nikto", "perl /usr/bin/nikto.pl -Version"),
    ("Dirsearch Help", "pentest-dirsearch", "dirsearch --help"),
    ("SSLscan Help", "pentest-sslscan", "sslscan --help"),
]
for name, container, cmd in tool_tests:
    start = time.time()
    try:
        r = subprocess.run(
            ["docker", "exec", container, "sh", "-c", cmd],
            capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace"
        )
        elapsed = round((time.time() - start) * 1000, 2)
        output = (r.stdout + r.stderr).strip()[:200]
        passed = r.returncode == 0 or len(r.stdout) > 0
        tool_exec_results.append({
            "name": name, "container": container, "passed": passed,
            "elapsed_ms": elapsed, "output": output, "returncode": r.returncode,
        })
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name} ({container}): {elapsed}ms")
    except subprocess.TimeoutExpired:
        elapsed = round((time.time() - start) * 1000, 2)
        tool_exec_results.append({
            "name": name, "container": container, "passed": False,
            "elapsed_ms": elapsed, "output": "TIMEOUT", "returncode": -1,
        })
        print(f"  [FAIL] {name} ({container}): TIMEOUT")
    except Exception as e:
        elapsed = round((time.time() - start) * 1000, 2)
        tool_exec_results.append({
            "name": name, "container": container, "passed": False,
            "elapsed_ms": elapsed, "output": str(e)[:100], "returncode": -2,
        })
        print(f"  [FAIL] {name} ({container}): {str(e)[:60]}")

passed = sum(1 for r in results if r["pass"])
failed = sum(1 for r in results if not r["pass"])
total_time = sum(r["elapsed_ms"] for r in results)
tool_passed = sum(1 for r in tool_exec_results if r["passed"])

print("\n" + "=" * 60)
print(f"  API Tests: {passed}/{len(results)} passed, {failed} failed")
print(f"  Docker Tools: {tool_passed}/{len(tool_exec_results)} passed")
print(f"  Total Time: {total_time:.0f}ms")
print(f"  Containers: {running}/{len(docker_containers)} running")
print("=" * 60)

all_data = {
    "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "system": system_metrics,
    "process_info": process_info,
    "docker_containers": docker_containers,
    "docker_stats": docker_stats,
    "api_results": results,
    "tool_exec_results": tool_exec_results,
    "summary": {
        "api_passed": passed,
        "api_failed": failed,
        "api_total": len(results),
        "tool_passed": tool_passed,
        "tool_total": len(tool_exec_results),
        "total_time_ms": total_time,
        "containers_running": running,
        "containers_total": len(docker_containers),
    },
}

with open("test_results.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2, default=str)

print("\nResults saved to test_results.json")
