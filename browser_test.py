from playwright.sync_api import sync_playwright
import time
import os
from datetime import datetime

BASE = "http://127.0.0.1:8000"
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = []

def record(test_name, status, detail=""):
    results.append({"test": test_name, "status": status, "detail": detail})
    icon = "PASS" if status == "pass" else "FAIL"
    print(f"  [{icon}] {test_name}" + (f" - {detail}" if detail else ""))

def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=False)
    print(f"  [Screenshot] {name}.png")

def safe_goto(page, url):
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        return True
    except:
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            return True
        except Exception as e:
            print(f"  [WARN] Navigation failed: {e}")
            return False

print("=" * 70)
print("  Browser Automation Test - Real Frontend Functional Testing")
print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 70)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--start-maximized"])
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    page.set_default_timeout(20000)

    # ============================================================
    # Test 1: Main Page - Homepage
    # ============================================================
    print("\n[Test 1] Main Page - Homepage")
    try:
        if safe_goto(page, f"{BASE}/static/index.html"):
            time.sleep(2)
            screenshot(page, "browser_01_homepage")
            record("Homepage", "pass")
        else:
            record("Homepage", "fail", "Navigation failed")
    except Exception as e:
        record("Homepage", "fail", str(e))

    # ============================================================
    # Test 2: Main Page - Fill Test Form
    # ============================================================
    print("\n[Test 2] Main Page - Fill Test Form")
    try:
        if safe_goto(page, f"{BASE}/static/index.html#test-section"):
            time.sleep(2)
            page.locator("#target").fill("http://127.0.0.1:8000")
            page.locator("#requirements").fill("对本地Web服务进行全面安全评估")
            page.locator("#toolStrategy").select_option("quick")
            screenshot(page, "browser_02_test_form_filled")
            record("Test Form Fill", "pass")
        else:
            record("Test Form Fill", "fail", "Navigation failed")
    except Exception as e:
        record("Test Form Fill", "fail", str(e))

    # ============================================================
    # Test 3: Main Page - Submit Test & Loading Modal
    # ============================================================
    print("\n[Test 3] Main Page - Submit Test (Loading Modal)")
    try:
        page.locator('button[type="submit"]').click()
        time.sleep(3)
        loading_modal = page.locator("#loadingModal")
        if loading_modal.is_visible():
            screenshot(page, "browser_03_test_loading")
            record("Test Loading Modal", "pass")
        else:
            record("Test Loading Modal", "fail", "Loading modal not visible")
    except Exception as e:
        record("Test Loading Modal", "fail", str(e))

    # ============================================================
    # Test 4: Main Page - Wait for Report Result (long timeout)
    # ============================================================
    print("\n[Test 4] Main Page - Report Result Preview")
    try:
        result_modal = page.locator("#resultModal")
        result_modal.wait_for(state="visible", timeout=180000)
        time.sleep(3)
        screenshot(page, "browser_04_report_preview")
        record("Report Preview", "pass")
    except Exception as e:
        record("Report Preview", "fail", str(e))
        try:
            screenshot(page, "browser_04_report_error")
        except:
            pass

    # ============================================================
    # Test 5: Main Page - Close Modal & View History
    # ============================================================
    print("\n[Test 5] Main Page - History Reports")
    try:
        try:
            close_btn = page.locator("#closeModalBtn")
            if close_btn.is_visible(timeout=3000):
                close_btn.click()
                time.sleep(1)
        except:
            pass

        history_link = page.locator('a:has-text("历史报告")')
        history_link.click()
        time.sleep(3)
        screenshot(page, "browser_05_history_reports")
        record("History Reports", "pass")
    except Exception as e:
        record("History Reports", "fail", str(e))

    # ============================================================
    # Test 6: Main Page - View History Report Detail
    # ============================================================
    print("\n[Test 6] Main Page - View Report Detail")
    try:
        view_btn = page.locator('button:has-text("查看")').first
        if view_btn.is_visible(timeout=5000):
            view_btn.click(force=True)
            time.sleep(3)
            result_modal = page.locator("#resultModal")
            result_modal.wait_for(state="visible", timeout=10000)
            time.sleep(2)
            screenshot(page, "browser_06_report_detail")
            record("Report Detail View", "pass")
        else:
            record("Report Detail View", "fail", "No view button")
    except Exception as e:
        record("Report Detail View", "fail", str(e))

    # ============================================================
    # Test 7: Dashboard Page
    # ============================================================
    print("\n[Test 7] Dashboard Page - Full View")
    try:
        if safe_goto(page, f"{BASE}/static/dashboard.html"):
            time.sleep(3)
            screenshot(page, "browser_07_dashboard")
            record("Dashboard Page", "pass")
        else:
            record("Dashboard Page", "fail", "Navigation failed")
    except Exception as e:
        record("Dashboard Page", "fail", str(e))

    # ============================================================
    # Test 8: Dashboard - Security Audit
    # ============================================================
    print("\n[Test 8] Dashboard - Security Audit")
    try:
        page.locator("#auditTarget").fill("http://127.0.0.1:8000/health")
        page.locator("#auditBtn").click()
        print("  Waiting for audit...")
        time.sleep(20)
        screenshot(page, "browser_08_audit_result")
        record("Dashboard Audit", "pass")
    except Exception as e:
        record("Dashboard Audit", "fail", str(e))

    # ============================================================
    # Test 9: Dashboard - Security Headers
    # ============================================================
    print("\n[Test 9] Dashboard - Security Headers")
    try:
        page.locator('button:has-text("安全头")').click()
        time.sleep(8)
        screenshot(page, "browser_09_headers")
        record("Security Headers", "pass")
    except Exception as e:
        record("Security Headers", "fail", str(e))

    # ============================================================
    # Test 10: Dashboard - CORS Check
    # ============================================================
    print("\n[Test 10] Dashboard - CORS Check")
    try:
        page.locator('button:has-text("CORS")').click()
        time.sleep(8)
        screenshot(page, "browser_10_cors")
        record("CORS Check", "pass")
    except Exception as e:
        record("CORS Check", "fail", str(e))

    # ============================================================
    # Test 11: Dashboard - WAF Detection
    # ============================================================
    print("\n[Test 11] Dashboard - WAF Detection")
    try:
        page.locator('button:has-text("WAF")').click()
        time.sleep(8)
        screenshot(page, "browser_11_waf")
        record("WAF Detection", "pass")
    except Exception as e:
        record("WAF Detection", "fail", str(e))

    # ============================================================
    # Test 12: Dashboard - Tech Detection
    # ============================================================
    print("\n[Test 12] Dashboard - Technology Detection")
    try:
        page.locator('button:has-text("技术栈")').click()
        time.sleep(8)
        screenshot(page, "browser_12_tech")
        record("Tech Detection", "pass")
    except Exception as e:
        record("Tech Detection", "fail", str(e))

    # ============================================================
    # Test 13: Dashboard - Port Scan
    # ============================================================
    print("\n[Test 13] Dashboard - Port Scan")
    try:
        page.locator('button:has-text("端口")').click()
        time.sleep(10)
        screenshot(page, "browser_13_ports")
        record("Port Scan", "pass")
    except Exception as e:
        record("Port Scan", "fail", str(e))

    # ============================================================
    # Test 14: Chat Page - Full View
    # ============================================================
    print("\n[Test 14] Chat Page - Full View")
    try:
        if safe_goto(page, f"{BASE}/static/chat.html"):
            time.sleep(3)
            screenshot(page, "browser_14_chat")
            record("Chat Page", "pass")
        else:
            record("Chat Page", "fail", "Navigation failed")
    except Exception as e:
        record("Chat Page", "fail", str(e))

    # ============================================================
    # Test 15: Chat Page - Send Message
    # ============================================================
    print("\n[Test 15] Chat Page - AI Response")
    try:
        page.locator("#chatInput").fill("什么是SQL注入？请简要说明防御方法")
        page.locator("#sendBtn").click()
        print("  Waiting for AI response...")
        time.sleep(15)
        screenshot(page, "browser_15_chat_response")
        record("Chat AI Response", "pass")
    except Exception as e:
        record("Chat AI Response", "fail", str(e))

    # ============================================================
    # Test 16: Chat Page - Quick Action
    # ============================================================
    print("\n[Test 16] Chat Page - Quick Action")
    try:
        if safe_goto(page, f"{BASE}/static/chat.html"):
            time.sleep(2)
            page.locator('button:has-text("MCP工具")').click()
            print("  Waiting for AI response...")
            time.sleep(15)
            screenshot(page, "browser_16_quick_action")
            record("Chat Quick Action", "pass")
        else:
            record("Chat Quick Action", "fail", "Navigation failed")
    except Exception as e:
        record("Chat Quick Action", "fail", str(e))

    # ============================================================
    # Test 17: API Documentation
    # ============================================================
    print("\n[Test 17] API Documentation")
    try:
        if safe_goto(page, f"{BASE}/docs"):
            time.sleep(3)
            screenshot(page, "browser_17_api_docs")
            record("API Documentation", "pass")
        else:
            record("API Documentation", "fail", "Navigation failed")
    except Exception as e:
        record("API Documentation", "fail", str(e))

    # ============================================================
    # Test 18: Navigation Test
    # ============================================================
    print("\n[Test 18] Navigation - Index to Dashboard to Chat")
    try:
        if safe_goto(page, f"{BASE}/static/index.html"):
            time.sleep(2)
            page.locator('a:has-text("仪表盘")').click()
            time.sleep(3)
            if "dashboard" in page.url:
                page.locator('a:has-text("AI对话")').click()
                time.sleep(3)
                if "chat" in page.url:
                    screenshot(page, "browser_18_navigation")
                    record("Navigation Flow", "pass")
                else:
                    record("Navigation Flow", "fail", f"chat URL not reached: {page.url}")
            else:
                record("Navigation Flow", "fail", f"dashboard URL not reached: {page.url}")
        else:
            record("Navigation Flow", "fail", "Navigation failed")
    except Exception as e:
        record("Navigation Flow", "fail", str(e))

    browser.close()

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("  BROWSER AUTOMATION TEST SUMMARY")
print("=" * 70)

passed = sum(1 for r in results if r["status"] == "pass")
failed = sum(1 for r in results if r["status"] == "fail")
total = len(results)

print(f"\n  Total: {total}  |  Passed: {passed}  |  Failed: {failed}")
if total > 0:
    print(f"  Success Rate: {passed/total*100:.1f}%\n")

for r in results:
    icon = "OK" if r["status"] == "pass" else "FAIL"
    print(f"  [{icon}] {r['test']}" + (f" - {r['detail']}" if r["detail"] else ""))

summary_path = os.path.join(SCREENSHOT_DIR, "browser_test_summary.txt")
with open(summary_path, "w", encoding="utf-8") as f:
    f.write(f"Browser Automation Test Summary\n")
    f.write(f"{'='*60}\n")
    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Total: {total} | Passed: {passed} | Failed: {failed}\n")
    if total > 0:
        f.write(f"Success Rate: {passed/total*100:.1f}%\n\n")
    for r in results:
        icon = "PASS" if r["status"] == "pass" else "FAIL"
        f.write(f"[{icon}] {r['test']}" + (f" - {r['detail']}" if r["detail"] else "") + "\n")

print(f"\n  Screenshots saved to: {SCREENSHOT_DIR}")
print("=" * 70)
