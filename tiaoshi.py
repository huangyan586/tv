import requests
import os

# ---------- 1. 抓取所有网址内容 ----------
urls_file = "网址列表.txt"
temp_lines = []

print("📡 开始抓取网站数据...")
with open(urls_file, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

for url in urls:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        
        # 🐞 解决中文乱码：自动检测编码或手动指定（优先使用 apparent_encoding）
        #if r.encoding is None or r.encoding == 'ISO-8859-1':
        #    r.encoding = r.apparent_encoding or 'utf-8'
        
        lines = r.text.splitlines()
        temp_lines.extend(lines)
        print(f"✅ 成功抓取 {url} -> 获得 {len(lines)} 行")
        print("📄 样例内容（前3行）：")
        for i, sample in enumerate(lines[:3]):
            print(f"   {i+1}: {sample[:100]}")
    except Exception as e:
        print(f"❌ 抓取失败 {url}: {e}")

print(f"📦 总共收集到 {len(temp_lines)} 行文本")

# ---------- 🐞 新增：将所有抓取到的原始数据保存到“临时.txt”（用于调试查看，有则清空） ----------
temp_debug_file = "临时.txt"
with open(temp_debug_file, "w", encoding="utf-8") as debug_f:
    for line in temp_lines:
        debug_f.write(line + "\n")
print(f"🐞 调试文件已保存：{temp_debug_file}，共 {len(temp_lines)} 行")
