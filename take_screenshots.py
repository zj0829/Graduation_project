import subprocess
import time
import os
from datetime import datetime

screenshot_dir = "screenshots"
os.makedirs(screenshot_dir, exist_ok=True)

pages = [
    ("index", "http://localhost:8000/static/index.html"),
    ("dashboard", "http://localhost:8000/static/dashboard.html"),
    ("knowledge", "http://localhost:8000/static/knowledge.html"),
    ("chat", "http://localhost:8000/static/chat.html"),
    ("api_docs", "http://localhost:8000/docs"),
]

print("Taking screenshots of web pages...")
print("Note: Using PowerShell to capture browser screenshots")
print("Please make sure the pages are accessible")

for name, url in pages:
    print(f"  Opening {name}: {url}")
    os.startfile(url)
    time.sleep(3)

print("\nPages opened in browser for manual screenshot.")
print("To take screenshots manually:")
print("  1. Press Win+Shift+S to use Snip & Sketch")
print("  2. Save screenshots to: " + os.path.abspath(screenshot_dir))
print()

print("Taking terminal output screenshots...")
commands = [
    ("docker_ps", 'docker ps -a --format "table {{.Names}}\\t{{.Image}}\\t{{.Status}}"'),
    ("docker_stats", 'docker stats --no-stream --format "table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}"'),
    ("mcp_health", 'curl -s http://127.0.0.1:9876/health'),
    ("backend_health", 'curl -s http://127.0.0.1:8000/health'),
    ("test_results", 'type test_results.json'),
]

for name, cmd in commands:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        output = result.stdout[:500] if result.stdout else result.stderr[:500]
        filepath = os.path.join(screenshot_dir, f"{name}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Command: {cmd}\n")
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Output:\n{output}\n")
        print(f"  Saved: {filepath}")
    except Exception as e:
        print(f"  Error ({name}): {e}")

print("\nDone! Terminal outputs saved as text files.")
print("Web pages are open in browser - use Win+Shift+S to capture screenshots.")
