import httpx
import json
import sys

BASE = "http://127.0.0.1:8000"

def test_api(name, method, url, payload=None):
    try:
        if method == "GET":
            r = httpx.get(f"{BASE}{url}", timeout=15)
        else:
            r = httpx.post(f"{BASE}{url}", json=payload, timeout=60)
        data = r.json()
        print(f"\n{'='*60}")
        print(f"[OK] {name} - HTTP {r.status_code}")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:1500])
        return data
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[FAIL] {name} - Error: {e}")
        return None

print("Testing all API endpoints...")

test_api("Health", "GET", "/health")
test_api("XSS Payloads", "POST", "/api/recon/xss-payloads", {"target": "basic"})
test_api("Security Headers", "POST", "/api/recon/security-headers", {"url": "http://127.0.0.1:8000/health"})
test_api("CORS Check", "POST", "/api/recon/cors-check", {"url": "http://127.0.0.1:8000/health"})
test_api("Tech Detect", "POST", "/api/recon/tech-detect", {"url": "http://127.0.0.1:8000/health"})
test_api("WAF Detect", "POST", "/api/recon/waf-detect", {"url": "http://127.0.0.1:8000/health"})
test_api("Cookie Check", "POST", "/api/recon/cookie-check", {"url": "http://127.0.0.1:8000/health"})
test_api("Port Check", "POST", "/api/recon/port-check", {"url": "127.0.0.1", "ports": "80,443,8000,8080"})
test_api("DNS Lookup", "POST", "/api/recon/dns", {"domain": "example.com"})
test_api("MCP Tools", "GET", "/api/orchestrator/tools")
test_api("Reports List", "GET", "/api/orchestrator/reports")

print("\n\nAll API tests completed!")
