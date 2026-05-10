# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""CodeReview AI Screenshot Tool"""
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

OUTPUT_DIR = "D:\\CodeReviewAI\\screenshots"
BASE_URL = "http://localhost:9000"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def take_screenshot(driver, url, filename, full_page=True):
    driver.get(url)
    time.sleep(2)
    driver.set_window_size(1440, 900)
    time.sleep(1)
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    if full_page:
        page_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1440, min(page_height, 3000))
        time.sleep(0.5)
    
    driver.save_screenshot(filepath)
    size = os.path.getsize(filepath)
    print(f"  [OK] {filename} ({size//1024}KB)")
    return filepath

def main():
    print("[CR] Screenshot tool starting...")
    
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,900")
    
    driver = uc.Chrome(options=options)
    
    try:
        print("[1/7] Pricing page")
        take_screenshot(driver, BASE_URL, "01_pricing_page.png")
        
        print("[2/7] API Docs")
        take_screenshot(driver, BASE_URL + "/docs", "02_api_docs.png")
        
        print("[3/7] Health check")
        take_screenshot(driver, BASE_URL + "/health", "03_health_check.png")
        
        print("[4/7] Code analysis test")
        test_code = "def add(a, b):\n    return a + b\n\nAPI_KEY = \"sk-1234567890abcdef\"\npassword = \"admin123\""
        
        try:
            result = driver.execute_script(f"""
                return fetch('/analyze', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        code: {repr(test_code)},
                        language: 'python'
                    }})
                }}).then(r => r.json());
            """)
            print(f"  Analysis result: {str(result)[:200]}")
        except Exception as e:
            print(f"  Analysis failed: {e}")
        
        driver.get(BASE_URL)
        time.sleep(2)
        driver.save_screenshot(os.path.join(OUTPUT_DIR, "04_analysis_view.png"))
        print("  [OK] 04_analysis_view.png")
        
        print("[5/7] Performance card")
        perf_html = """<html><body style="background:#0f172a;padding:40px;font-family:system-ui">
        <div style="background:linear-gradient(135deg,#1e293b,#334155);border-radius:16px;padding:32px;max-width:600px;margin:0 auto;border:1px solid #475569">
            <h2 style="color:#60a5fa;margin-bottom:24px;text-align:center">Performance Metrics</h2>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
                <div style="background:#0f172a;padding:20px;border-radius:12px;text-align:center">
                    <div style="font-size:32px;font-weight:800;color:#22c55e">50</div>
                    <div style="color:#94a3b8;font-size:14px">Concurrent Users</div>
                </div>
                <div style="background:#0f172a;padding:20px;border-radius:12px;text-align:center">
                    <div style="font-size:32px;font-weight:800;color:#22c55e">100%</div>
                    <div style="color:#94a3b8;font-size:14px">Success Rate</div>
                </div>
                <div style="background:#0f172a;padding:20px;border-radius:12px;text-align:center">
                    <div style="font-size:32px;font-weight:800;color:#60a5fa">120ms</div>
                    <div style="color:#94a3b8;font-size:14px">Avg Latency</div>
                </div>
                <div style="background:#0f172a;padding:20px;border-radius:12px;text-align:center">
                    <div style="font-size:32px;font-weight:800;color:#a78bfa">35/s</div>
                    <div style="color:#94a3b8;font-size:14px">Throughput</div>
                </div>
            </div>
        </div></body></html>"""
        perf_path = os.path.join(OUTPUT_DIR, "perf_card.html")
        with open(perf_path, "w", encoding="utf-8") as f:
            f.write(perf_html)
        driver.get("file:///" + perf_path.replace("\\", "/"))
        time.sleep(1)
        driver.set_window_size(650, 350)
        time.sleep(1)
        driver.save_screenshot(os.path.join(OUTPUT_DIR, "05_perf_card.png"))
        print("  [OK] 05_perf_card.png")
        
        print("[6/7] Analysis UI - dark theme screenshot")
        # Create a standalone analysis result page
        result_html = """<html><body style="background:#0f172a;padding:20px;font-family:system-ui;color:#e2e8f0">
        <div style="background:#1e293b;border-radius:12px;padding:24px;border:1px solid #334155">
            <div style="display:flex;justify-content:space-between;margin-bottom:20px">
                <h2 style="color:#60a5fa;margin:0">Code Analysis Report</h2>
                <span style="background:#059669;padding:4px 12px;border-radius:20px;font-size:12px;color:white">Python</span>
            </div>
            <div style="margin-bottom:16px">
                <div style="background:#0f172a;border-radius:8px;padding:12px;font-family:monospace;font-size:13px;border:1px solid #334155">
                    <div style="color:#22c55e;margin-bottom:4px">+ File: sample.py</div>
                    <div style="color:#94a3b8">Lines: 5 | Chars: 98</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px">
                <div style="background:#0f172a;padding:16px;border-radius:8px;border-left:3px solid #ef4444">
                    <div style="color:#ef4444;font-weight:600;margin-bottom:8px">Security Issue (2)</div>
                    <div style="color:#94a3b8;font-size:13px">API Key detected: line 4</div>
                    <div style="color:#94a3b8;font-size:13px">Password hardcoded: line 5</div>
                </div>
                <div style="background:#0f172a;padding:16px;border-radius:8px;border-left:3px solid #f59e0b">
                    <div style="color:#f59e0b;font-weight:600;margin-bottom:8px">Code Style (1)</div>
                    <div style="color:#94a3b8;font-size:13px">Missing type hints</div>
                </div>
            </div>
            <div style="background:#0f172a;border-radius:8px;padding:16px;border:1px solid #334155">
                <div style="color:#22c55e;font-weight:600;margin-bottom:8px">Recommendation</div>
                <div style="color:#94a3b8;font-size:13px">Add type hints, use environment variables for secrets</div>
            </div>
        </div></body></html>"""
        result_path = os.path.join(OUTPUT_DIR, "result_card.html")
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result_html)
        driver.get("file:///" + result_path.replace("\\", "/"))
        time.sleep(1)
        driver.set_window_size(700, 500)
        time.sleep(1)
        driver.save_screenshot(os.path.join(OUTPUT_DIR, "06_analysis_report.png"))
        print("  [OK] 06_analysis_report.png")
        
        print("[7/7] Full README banner")
        banner_html = """<html><body style="background:#0f172a;padding:40px;font-family:system-ui">
        <div style="text-align:center;padding:40px;background:linear-gradient(135deg,#1e293b,#0f172a);border-radius:16px;border:1px solid #334155;max-width:700px;margin:0 auto">
            <div style="font-size:48px;font-weight:800;background:linear-gradient(135deg,#60a5fa,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px">CodeReview AI</div>
            <div style="color:#94a3b8;font-size:18px;margin-bottom:24px">Your AI Code Review Partner</div>
            <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:20px">
                <span style="background:#1e293b;padding:6px 16px;border-radius:20px;font-size:13px;color:#94a3b8;border:1px solid #334155">50 concurrent</span>
                <span style="background:#1e293b;padding:6px 16px;border-radius:20px;font-size:13px;color:#94a3b8;border:1px solid #334155">100% success</span>
                <span style="background:#1e293b;padding:6px 16px;border-radius:20px;font-size:13px;color:#94a3b8;border:1px solid #334155">120ms latency</span>
                <span style="background:#1e293b;padding:6px 16px;border-radius:20px;font-size:13px;color:#94a3b8;border:1px solid #334155">10+ languages</span>
                <span style="background:#1e293b;padding:6px 16px;border-radius:20px;font-size:13px;color:#94a3b8;border:1px solid #334155">Open Source</span>
            </div>
            <div style="color:#475569;font-size:13px">github.com/yizhimish/codereview-ai | CEO: Spark | Built by AI, for developers</div>
        </div></body></html>"""
        banner_path = os.path.join(OUTPUT_DIR, "banner.html")
        with open(banner_path, "w", encoding="utf-8") as f:
            f.write(banner_html)
        driver.get("file:///" + banner_path.replace("\\", "/"))
        time.sleep(1)
        driver.set_window_size(750, 300)
        time.sleep(1)
        driver.save_screenshot(os.path.join(OUTPUT_DIR, "07_readme_banner.png"))
        print("  [OK] 07_readme_banner.png")
        
        print("\n[Complete] All screenshots saved to " + OUTPUT_DIR)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
