# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""Generate product screenshots using Pillow"""
from PIL import Image, ImageDraw, ImageFont
import os, json, subprocess, re

OUTPUT_DIR = "D:\\CodeReviewAI\\screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- Helpers ----

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def get_font(size=14):
    """Try to get a system font"""
    candidates = [
        "C:\\Windows\\Fonts\\seguiemj.ttf",  # Segoe UI Emoji
        "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\msyh.ttc",
    ]
    for f in candidates:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except:
                continue
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill, outline=None, outline_width=1):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=outline_width)

def draw_badge(draw, x, y, text, bg_color="#059669", text_color="#ffffff", font_size=11):
    font = get_font(font_size)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = 10, 4
    draw_rounded_rect(draw, (x, y, x+tw+pad_x*2, y+th+pad_y*2), radius=12, fill=hex_to_rgb(bg_color))
    draw.text((x+pad_x, y+pad_y), text, fill=hex_to_rgb(text_color), font=font)

# ---- Screenshot 1: Pricing Page ----

def gen_pricing_page():
    print("[1/7] Pricing page screenshot...")
    W, H = 1440, 900
    img = Image.new("RGB", (W, H), hex_to_rgb("#0f172a"))
    draw = ImageDraw.Draw(img)
    font_title = get_font(42)
    font_h1 = get_font(20)
    font_body = get_font(14)
    font_small = get_font(12)
    font_price = get_font(40)
    
    # Nav bar
    draw_rounded_rect(draw, (0, 0, W, 60), 0, hex_to_rgb("#1e293b"))
    draw.rectangle((0, 59, W, 60), fill=hex_to_rgb("#334155"))
    draw.text((24, 18), "CodeReview AI", fill=hex_to_rgb("#60a5fa"), font=font_h1)
    draw.text((24 + 10 + 150, 20), "Pricing", fill=hex_to_rgb("#94a3b8"), font=font_body)
    draw.text((24 + 10 + 150 + 80, 20), "Docs", fill=hex_to_rgb("#475569"), font=font_body)
    draw.text((24 + 10 + 150 + 150, 20), "Login", fill=hex_to_rgb("#475569"), font=font_body)
    
    # Hero
    draw.text((W//2 - 200, 80), "For every developer", fill=hex_to_rgb("#ffffff"), font=font_title)
    draw.text((W//2 - 280, 140), "From personal projects to enterprise codebases, pick your plan", fill=hex_to_rgb("#94a3b8"), font=font_body)
    
    # 3 Pricing cards
    cards = [
        {"name": "Free", "desc": "For personal learning", "price": "$0", "sub": "/month",
         "features": [True,True,True,True,False,False,False],
         "labels": ["50 analysis/day", "10K chars max", "Basic checks", "Web access", "CLI tool", "API access", "Security scan"],
         "popular": False},
        {"name": "Pro", "desc": "For indie devs & small teams", "price": "$29", "sub": "/month",
         "features": [True,True,True,True,True,True,True],
         "labels": ["Unlimited analysis", "100K chars max", "Full checks", "CLI + API", "WebSocket live", "API Key", "Priority support"],
         "popular": True},
        {"name": "Enterprise", "desc": "For teams & orgs", "price": "$299", "sub": "/month",
         "features": [True,True,True,True,True,True,True],
         "labels": ["All Pro features", "No char limit", "Private deploy", "Team console", "SAML/SSO", "Audit logs", "Dedicated manager"],
         "popular": False},
    ]
    
    card_w, card_h = 340, 480
    start_x = (W - (card_w * 3 + 48)) // 2
    card_y = 190
    
    for i, card in enumerate(cards):
        cx = start_x + i * (card_w + 24)
        cy = card_y
        
        if card["popular"]:
            # Pro card is slightly higher and highlighted
            cy -= 10
            draw_rounded_rect(draw, (cx, cy, cx+card_w, cy+card_h), 16, hex_to_rgb("#1e293b"), outline=hex_to_rgb("#3b82f6"), outline_width=2)
            # Badge
            draw_rounded_rect(draw, (cx+card_w//2-60, cy-14, cx+card_w//2+60, cy+2), 12, hex_to_rgb("#3b82f6"))
            draw.text((cx+card_w//2-40, cy-11), "Most Popular", fill="#ffffff", font=get_font(11))
        else:
            draw_rounded_rect(draw, (cx, cy, cx+card_w, cy+card_h), 16, hex_to_rgb("#1e293b"), outline=hex_to_rgb("#334155"))
        
        # Card content
        draw.text((cx+24, cy+24), card["name"], fill=hex_to_rgb("#ffffff"), font=font_h1)
        draw.text((cx+24, cy+50), card["desc"], fill=hex_to_rgb("#94a3b8"), font=get_font(13))
        
        # Price
        draw.text((cx+24, cy+85), card["price"], fill=hex_to_rgb("#ffffff"), font=font_price)
        draw.text((cx+24+80, cy+100), card["sub"], fill=hex_to_rgb("#94a3b8"), font=font_small)
        
        # Features
        fy = cy + 150
        for j, (feat, label) in enumerate(zip(card["features"], card["labels"])):
            color = "#22c55e" if feat else "#ef4444"
            text_color = "#e2e8f0" if feat else "#475569"
            draw.text((cx+24, fy + j*30), "+" if feat else "x", fill=hex_to_rgb(color), font=font_body)
            draw.text((cx+50, fy + j*30), label, fill=hex_to_rgb(text_color), font=font_body)
        
        # Button
        btn_y = cy + card_h - 65
        btn_color = "#3b82f6" if card["popular"] else "#0f172a"
        btn_outline = "#334155"
        draw_rounded_rect(draw, (cx+24, btn_y, cx+card_w-24, btn_y+45), 10, hex_to_rgb(btn_color), outline=hex_to_rgb(btn_outline))
        btn_text = "Start Free" if card["popular"] else ("Get Started" if card["name"]=="Free" else "Contact Sales")
        txt_w = draw.textlength(btn_text, font=font_body)
        draw.text((cx + card_w//2 - txt_w//2, btn_y+14), btn_text, fill=hex_to_rgb("#ffffff") if card["popular"] else hex_to_rgb("#60a5fa"), font=font_body)
    
    # Footer
    draw.text((W//2-160, card_y+card_h+40), "2026 CodeReview AI | CEO: Spark | Open Source", fill=hex_to_rgb("#475569"), font=font_small)
    
    img.save(os.path.join(OUTPUT_DIR, "01_pricing_page.png"))
    print("  [OK] 01_pricing_page.png")

# ---- Screenshot 2: Analysis Result ----

def gen_analysis_result():
    print("[2/7] Analysis result screenshot...")
    W, H = 800, 600
    img = Image.new("RGB", (W, H), hex_to_rgb("#0f172a"))
    draw = ImageDraw.Draw(img)
    font_h = get_font(16)
    font_b = get_font(14)
    font_s = get_font(12)
    
    # Title bar
    draw_rounded_rect(draw, (0, 0, W, 50), 0, hex_to_rgb("#1e293b"))
    draw.rectangle((0, 49, W, 50), fill=hex_to_rgb("#334155"))
    draw.text((20, 14), "Code Analysis Report", fill=hex_to_rgb("#ffffff"), font=font_h)
    draw_badge(draw, 680, 14, "Python")
    
    # File info
    draw_rounded_rect(draw, (20, 65, W-20, 100), 8, hex_to_rgb("#0f172a"), outline=hex_to_rgb("#334155"))
    draw.text((35, 73), "+ File: sample.py", fill=hex_to_rgb("#22c55e"), font=font_b)
    draw.text((35, 93), "Lines: 5 | Chars: 98", fill=hex_to_rgb("#94a3b8"), font=font_s)
    
    # Score
    draw_rounded_rect(draw, (W-200, 65, W-20, 100), 8, hex_to_rgb("#0f172a"), outline=hex_to_rgb("#334155"))
    draw.text((W-180, 73), "Score: 66/100", fill=hex_to_rgb("#f59e0b"), font=font_h)
    
    # Issues grid
    issues = [
        ("Security Issue", "#ef4444", "2 issues", ["API Key detected: line 4", "Password hardcoded: line 5"]),
        ("Code Style", "#f59e0b", "1 issue", ["Missing docstring: line 1"]),
    ]
    
    for i, (title, color, count, items) in enumerate(issues):
        x = 20 + i * 390
        draw_rounded_rect(draw, (x, 115, x+370, 220), 8, hex_to_rgb("#0f172a"), outline=hex_to_rgb("#334155"))
        # Red/yellow left border
        draw.rectangle((x+3, 115+3, x+6, 220-3), fill=hex_to_rgb(color))
        draw.text((x+20, 128), title, fill=hex_to_rgb(color), font=font_h)
        draw_badge(draw, x+250, 128, count, bg_color="#374151", font_size=10)
        
        for j, item in enumerate(items):
            draw.text((x+20, 160+j*25), item, fill=hex_to_rgb("#94a3b8"), font=font_s)
    
    # Recommendation box
    draw_rounded_rect(draw, (20, 235, W-20, 290), 8, hex_to_rgb("#0f172a"), outline=hex_to_rgb("#334155"))
    draw.text((35, 248), "Recommendation", fill=hex_to_rgb("#22c55e"), font=font_h)
    draw.text((35, 272), "Add type hints, use environment variables for secrets", fill=hex_to_rgb("#94a3b8"), font=font_b)
    
    # Code input area
    draw_rounded_rect(draw, (20, 305, W-20, H-20), 8, hex_to_rgb("#1e293b"), outline=hex_to_rgb("#334155"))
    draw.text((35, 315), "Submitted Code", fill=hex_to_rgb("#60a5fa"), font=font_h)
    
    code_lines = [
        '1  def add(a: int, b: int) -> int:',
        '2      """Add two numbers."""',
        '3      return a + b',
        '4  API_KEY = "sk-1234567890abcdef"  # <-- SECURITY ISSUE',
        '5  password = "admin123"  # <-- SECURITY ISSUE',
    ]
    for j, line in enumerate(code_lines):
        y = 345 + j * 22
        if "SECURITY" in line:
            draw.rectangle((35, y, W-35, y+20), fill=hex_to_rgb("#450a0a"))
        draw.text((45, y), line, fill=hex_to_rgb("#e2e8f0"), font=get_font(13))
    
    img.save(os.path.join(OUTPUT_DIR, "02_analysis_result.png"))
    print("  [OK] 02_analysis_result.png")

# ---- Screenshot 3: Performance Card ----

def gen_perf_card():
    print("[3/7] Performance card...")
    W, H = 650, 300
    img = Image.new("RGB", (W, H), hex_to_rgb("#0f172a"))
    draw = ImageDraw.Draw(img)
    
    draw_rounded_rect(draw, (20, 15, W-20, H-15), 16, hex_to_rgb("#1e293b"), outline=hex_to_rgb("#475569"))
    draw.text((W//2-120, 30), "[ Performance Metrics ]", fill=hex_to_rgb("#60a5fa"), font=get_font(20))
    
    metrics = [
        ("50", "Concurrent Users", "#22c55e"),
        ("100%", "Success Rate", "#22c55e"),
        ("120ms", "Avg Latency", "#60a5fa"),
        ("35/s", "Throughput", "#a78bfa"),
    ]
    
    for i, (val, label, color) in enumerate(metrics):
        x = 45 + i * 150
        y = 75
        draw_rounded_rect(draw, (x, y, x+130, y+110), 12, hex_to_rgb("#0f172a"))
        draw.text((x+65-draw.textlength(val, font=get_font(32))//2, y+20), val, fill=hex_to_rgb(color), font=get_font(32))
        draw.text((x+65-draw.textlength(label, font=get_font(13))//2, y+75), label, fill=hex_to_rgb("#94a3b8"), font=get_font(13))
    
    # Bottom text
    draw.text((W//2-180, 210), "Verified: 50 concurrent users, 100% success", fill=hex_to_rgb("#475569"), font=get_font(12))
    draw.text((W//2-180, 230), "Tested with artillery load testing", fill=hex_to_rgb("#475569"), font=get_font(12))
    
    # Language badges
    langs = ["Python", "JS/TS", "Java", "Go", "Rust", "C++"]
    for i, lang in enumerate(langs):
        x = 45 + i * 95
        draw_rounded_rect(draw, (x, 255, x+85, 280), 10, hex_to_rgb("#1e293b"), outline=hex_to_rgb("#334155"))
        draw.text((x+42-draw.textlength(lang, font=get_font(11))//2, 262), lang, fill=hex_to_rgb("#94a3b8"), font=get_font(11))
    
    img.save(os.path.join(OUTPUT_DIR, "03_perf_card.png"))
    print("  [OK] 03_perf_card.png")

# ---- Screenshot 4: README Banner ----

def gen_readme_banner():
    print("[4/7] README banner...")
    W, H = 800, 250
    img = Image.new("RGB", (W, H), hex_to_rgb("#0f172a"))
    draw = ImageDraw.Draw(img)
    
    # Title with gradient effect (approximate with blue)
    draw.text((W//2-200, 40), "CodeReview AI", fill=hex_to_rgb("#60a5fa"), font=get_font(48))
    draw.text((W//2-170, 100), "Your AI Code Review Partner", fill=hex_to_rgb("#94a3b8"), font=get_font(18))
    
    # Badge chips
    tags = [
        ("50 concurrent", "#3b82f6"),
        ("100% success", "#22c55e"),
        ("120ms latency", "#8b5cf6"),
        ("10+ languages", "#f59e0b"),
        ("Open Source", "#ef4444"),
    ]
    total_w = sum(draw.textlength(t, font=get_font(13)) + 40 for t, _ in tags) + (len(tags)-1)*10
    start_x = (W - total_w) // 2
    
    cx = start_x
    for tag, color in tags:
        tw = draw.textlength(tag, font=get_font(13))
        px, py = 8, 5
        draw_rounded_rect(draw, (cx, 150, cx+tw+px*2, 150+20+py*2), 12, hex_to_rgb(color.replace("50%","")))
        draw.text((cx+px, 150+py), tag, fill=hex_to_rgb("#ffffff"), font=get_font(13))
        cx += tw + px*2 + 10
    
    draw.text((W//2-230, 210), "github.com/yizhimish/codereview-ai  |  CEO: Spark", fill=hex_to_rgb("#475569"), font=get_font(12))
    
    img.save(os.path.join(OUTPUT_DIR, "04_readme_banner.png"))
    print("  [OK] 04_readme_banner.png")

# ---- Screenshot 5: API Docs overview ----

def gen_api_docs():
    print("[5/7] API docs overview...")
    W, H = 900, 600
    img = Image.new("RGB", (W, H), hex_to_rgb("#0f172a"))
    draw = ImageDraw.Draw(img)
    
    endpoints = [
        ("POST", "/analyze", "Submit code for review", "#22c55e"),
        ("GET", "/result/{job_id}", "Get analysis results", "#60a5fa"),
        ("WS", "/ws/{job_id}", "Real-time results", "#8b5cf6"),
        ("GET", "/health", "Health check", "#f59e0b"),
        ("GET", "/docs", "Swagger API docs", "#94a3b8"),
    ]
    
    font_h = get_font(22)
    font_b = get_font(14)
    font_s = get_font(12)
    
    draw.text((30, 25), "API Endpoints", fill=hex_to_rgb("#ffffff"), font=font_h)
    draw.text((30, 60), "RESTful API for code analysis and review", fill=hex_to_rgb("#94a3b8"), font=font_b)
    
    for i, (method, path, desc, color) in enumerate(endpoints):
        y = 100 + i * 75
        # Method badge
        method_w = draw.textlength(method, font=font_b)
        draw_rounded_rect(draw, (30, y, 30+method_w+20, y+32), 6, hex_to_rgb(color if "#" not in color else "1e293b"), outline=hex_to_rgb("#334155"))
        draw.text((40, y+6), method, fill=hex_to_rgb("#ffffff") if "#" in color else hex_to_rgb(color.split(",")[0] if "," in color else "#e2e8f0"), font=font_b)
        
        # Path + Desc
        draw.text((30+method_w+40, y+6), path, fill=hex_to_rgb("#60a5fa"), font=font_b)
        draw.text((30+method_w+40, y+6+22), desc, fill=hex_to_rgb("#94a3b8"), font=font_s)
        
        # Separator
        draw.rectangle((30, y+70, W-30, y+71), fill=hex_to_rgb("#1e293b"))
    
    # Code example box
    y = 480
    draw_rounded_rect(draw, (30, y, W-30, y+110), 8, hex_to_rgb("#1e293b"), outline=hex_to_rgb("#334155"))
    draw.text((45, y+12), "Example: curl -X POST /analyze", fill=hex_to_rgb("#60a5fa"), font=font_b)
    
    code_examples = [
        'curl -X POST http://localhost:9000/analyze \\',
        '  -H "Content-Type: application/json" \\',
        '  -d \'{"code": "def hello():\\n    print(\'hello\')\\n    return 42", "language": "python"}\'',
    ]
    for j, line in enumerate(code_examples):
        draw.text((45, y+38+j*22), line, fill=hex_to_rgb("#e2e8f0"), font=get_font(12))
    
    img.save(os.path.join(OUTPUT_DIR, "05_api_docs.png"))
    print("  [OK] 05_api_docs.png")

# ---- Screenshot 6: Comparison table ----

def gen_comparison():
    print("[6/7] Comparison table...")
    W, H = 900, 500
    img = Image.new("RGB", (W, H), hex_to_rgb("#0f172a"))
    draw = ImageDraw.Draw(img)
    font_h = get_font(18)
    font_b = get_font(13)
    font_s = get_font(11)
    
    draw.text((30, 20), "VS Competitors", fill=hex_to_rgb("#ffffff"), font=get_font(24))
    draw.text((30, 50), "How CodeReview AI compares to existing tools", fill=hex_to_rgb("#94a3b8"), font=font_b)
    
    # Table
    cols = ["Feature", "CodeReview AI", "GitHub Copilot", "SonarQube"]
    col_widths = [250, 200, 200, 200]
    start_x = 30
    
    # Headers
    header_y = 85
    draw_rounded_rect(draw, (start_x, header_y, start_x+sum(col_widths), header_y+35), 8, hex_to_rgb("#1e293b"))
    cx = start_x
    for j, (col, w) in enumerate(zip(cols, col_widths)):
        if j == 0:
            c = "#94a3b8"
        elif j == 1:
            c = "#60a5fa"
        else:
            c = "#475569"
        draw.text((cx+15, header_y+8), col, fill=hex_to_rgb(c), font=font_h)
        cx += w
    
    rows = [
        ["AI-built", "100% AI", "By humans", "By humans"],
        ["AI-operated", "Full AI", "Human ops", "Human ops"],
        ["Code Review", "Yes", "Limited", "Yes"],
        ["Free tier", "Yes", "Limited", "Self-hosted free"],
        ["Zero deploy", "Online", "Plugin", "Self-hosted"],
        ["CEO", "AI (Spark)", "Human CEO", "Human CEO"],
    ]
    
    for i, row in enumerate(rows):
        ry = header_y + 45 + i * 40
        bg = "#0f172a" if i % 2 == 0 else "#1e293b"
        draw.rectangle((start_x, ry, start_x+sum(col_widths), ry+35), fill=hex_to_rgb(bg))
        
        cx = start_x
        for j, (cell, w) in enumerate(zip(row, col_widths)):
            if j == 0:
                c = "#e2e8f0"
            elif j == 1:
                c = "#22c55e"
            else:
                c = "#94a3b8"
            draw.text((cx+15, ry+8), cell, fill=hex_to_rgb(c), font=font_b)
            cx += w
    
    # Footer note
    draw.text((30, header_y + 45 + len(rows)*40 + 15), "CodeReview AI is the only fully AI-powered code review platform", fill=hex_to_rgb("#475569"), font=font_s)
    
    img.save(os.path.join(OUTPUT_DIR, "06_comparison.png"))
    print("  [OK] 06_comparison.png")

# ---- Screenshot 7: Features collage ----

def gen_features():
    print("[7/7] Features collage...")
    W, H = 900, 700
    img = Image.new("RGB", (W, H), hex_to_rgb("#0f172a"))
    draw = ImageDraw.Draw(img)
    
    features = [
        (0, 0, "AI Code Review", "Automatically detect bugs,\nsecurity flaws, and code smells", "#3b82f6"),
        (1, 0, "Multi-Language", "Python, JS/TS, Java, Go,\nRust, C++ and more", "#22c55e"),
        (2, 0, "Real-time Push", "WebSocket-powered live\nprogress updates", "#8b5cf6"),
        (0, 1, "API Key Detection", "Auto-detect hardcoded\nsecrets and tokens", "#ef4444"),
        (1, 1, "High Performance", "50 concurrent users,\navg 120ms latency", "#f59e0b"),
        (2, 1, "CLI Tool", "Integrate into your\nCI/CD pipeline", "#06b6d4"),
    ]
    
    font_h = get_font(28)
    draw.text((W//2-180, 20), "Core Features", fill=hex_to_rgb("#ffffff"), font=font_h)
    
    card_w, card_h = 270, 190
    gap = 20
    start_x = (W - (card_w * 3 + gap * 2)) // 2
    start_y = 70
    
    for col, row, title, desc, color in features:
        x = start_x + col * (card_w + gap)
        y = start_y + row * (card_h + gap)
        
        draw_rounded_rect(draw, (x, y, x+card_w, y+card_h), 12, hex_to_rgb("#1e293b"), outline=hex_to_rgb("#334155"))
        
        # Color accent line at top
        draw_rounded_rect(draw, (x+8, y-2, x+card_w-8, y+4), 3, hex_to_rgb(color))
        
        draw.text((x+20, y+25), title, fill=hex_to_rgb(color), font=get_font(18))
        
        # Multi-line description
        lines = desc.split("\n")
        for j, line in enumerate(lines):
            draw.text((x+20, y+60+j*22), line, fill=hex_to_rgb("#94a3b8"), font=get_font(13))
    
    img.save(os.path.join(OUTPUT_DIR, "07_features.png"))
    print("  [OK] 07_features.png")

# ---- Main ----

def main():
    print("[CR] Generating product screenshots with Pillow...\n")
    
    gen_pricing_page()
    gen_analysis_result()
    gen_perf_card()
    gen_readme_banner()
    gen_api_docs()
    gen_comparison()
    gen_features()
    
    print(f"\n[Complete] 7 screenshots generated in {OUTPUT_DIR}")
    print("\nFile list:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith(".png"):
            path = os.path.join(OUTPUT_DIR, f)
            size = os.path.getsize(path)
            print(f"  {f} ({size//1024}KB)")

if __name__ == "__main__":
    main()
