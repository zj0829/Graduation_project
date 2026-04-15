import requests
import json
import time

BASE = "http://127.0.0.1:8000"

print("=" * 60)
print("  真实网站渗透测试 - 完整流程")
print("  目标: testphp.vulnweb.com (OWASP合法靶场)")
print("=" * 60)

test_data = {
    "target": "testphp.vulnweb.com",
    "requirements": "对该网站进行全面安全扫描，检测开放端口、服务版本和SQL注入漏洞",
    "tools": ["nmap", "sqlmap"],
    "tool_strategy": "custom",
    "report_format": "markdown"
}

print("\n[1/3] 发送测试请求（Nmap + SQLmap）...")
try:
    r = requests.post(BASE + "/api/orchestrator/execute-test", json=test_data, timeout=600)
    print(f"  HTTP状态码: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        test_id = data.get("test_id")
        print(f"  测试ID: {test_id}")
        
        print("\n[2/3] 等待测试完成，获取结果...")
        time.sleep(3)
        rr = requests.get(BASE + f"/api/orchestrator/test-result/{test_id}", timeout=60)
        
        if rr.status_code == 200:
            result = rr.json()
            report = result.get("report", "")
            
            with open("sample_report.md", "w", encoding="utf-8") as f:
                f.write(report)
            
            print("\n[3/3] 报告已保存到 sample_report.md")
            print(f"  报告长度: {len(report)} 字符")
            print()
            print("=" * 60)
            print(report)
            print("=" * 60)
        else:
            print(f"  获取结果失败: {rr.text[:300]}")
    else:
        print(f"  错误: {r.text[:500]}")
except Exception as e:
    print(f"  异常: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 60)
