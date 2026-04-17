import httpx
import json

base = "http://127.0.0.1:8000"
target_url = "http://example.com"
target_domain = "example.com"

tests = [
    ("WHOIS", "POST", base + "/api/recon/whois", {"target": target_domain}),
    ("DNS", "POST", base + "/api/recon/dns", {"target": target_domain}),
    ("Security Headers", "POST", base + "/api/recon/security-headers", {"url": target_url}),
    ("Port Check", "POST", base + "/api/recon/port-check", {"target": target_domain}),
    ("CORS Check", "POST", base + "/api/recon/cors-check", {"url": target_url}),
    ("Cookie Check", "POST", base + "/api/recon/cookie-check", {"url": target_url}),
    ("Tech Detect", "POST", base + "/api/recon/tech-detect", {"url": target_url}),
    ("Subdomain Enum", "POST", base + "/api/recon/subdomain-enum", {"target": target_domain}),
    ("WAF Detect", "POST", base + "/api/recon/waf-detect", {"url": target_url}),
    ("XSS Payloads", "POST", base + "/api/recon/xss-payloads", {"target": "basic"}),
    ("Full Audit", "POST", base + "/api/recon/full-audit", {"url": target_url}),
    ("MCP Health", "GET", "http://127.0.0.1:9876/health", None),
    ("Dashboard Page", "GET", base + "/static/dashboard.html", None),
    ("Knowledge Page", "GET", base + "/static/knowledge.html", None),
    ("Chat Models", "GET", base + "/api/chat/models", None),
]

results = []
for name, method, url, body in tests:
    try:
        if method == "GET":
            r = httpx.get(url, timeout=30, follow_redirects=True)
        else:
            r = httpx.post(url, json=body, timeout=30)
        status = r.status_code
        ct = r.headers.get("content-type", "")
        is_json = "json" in ct
        data = r.json() if is_json else None

        extra = ""
        if name == "Security Headers" and data:
            extra = "Score={} Missing={}".format(data.get("score"), data.get("missing_count"))
        elif name == "CORS Check" and data:
            extra = "Vulnerable={} ACAO={}".format(data.get("vulnerable"), data.get("access_control_allow_origin", "N/A"))
        elif name == "Cookie Check" and data:
            extra = "Cookies={} Issues={}".format(data.get("total_cookies"), data.get("total_issues"))
        elif name == "Tech Detect" and data:
            extra = "Techs={}".format(data.get("total_detected"))
        elif name == "Subdomain Enum" and data:
            extra = "Found={}".format(data.get("total_found"))
        elif name == "WAF Detect" and data:
            extra = "WAF={}".format(data.get("waf_detected"))
        elif name == "XSS Payloads" and data:
            extra = "Total={}".format(data.get("total_payloads"))
        elif name == "Full Audit" and data:
            extra = "Score={}".format(data.get("overall_score"))
        elif name == "MCP Health" and data:
            extra = "Tools={}".format(len(data.get("available_tools", [])))
        elif name in ("Dashboard Page", "Knowledge Page"):
            extra = "Len={}".format(len(r.text))
        elif name == "Chat Models" and data:
            extra = "Models={}".format(len(data.get("models", [])))

        status_str = "PASS" if status == 200 else "FAIL"
        results.append((name, status_str, status, extra))
        print("[{}] {} - {} {}".format(status_str, name, status, extra))
    except Exception as e:
        results.append((name, "ERROR", 0, str(e)[:60]))
        print("[ERROR] {} - {}".format(name, str(e)[:60]))

passed = sum(1 for r in results if r[1] == "PASS")
failed = sum(1 for r in results if r[1] != "PASS")
print("\n=== Test Summary ===")
print("Passed: {}/{}".format(passed, len(results)))
print("Failed: {}/{}".format(failed, len(results)))
