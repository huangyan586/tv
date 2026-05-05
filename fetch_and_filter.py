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
        lines = r.text.splitlines()
        temp_lines.extend(lines)
        print(f"✅ 成功抓取 {url} -> 获得 {len(lines)} 行")
        # 打印前3行样例，帮你判断格式
        print("📄 样例内容（前3行）：")
        for i, sample in enumerate(lines[:3]):
            print(f"   {i+1}: {sample[:100]}")
    except Exception as e:
        print(f"❌ 抓取失败 {url}: {e}")

print(f"📦 总共收集到 {len(temp_lines)} 行文本")

# ---------- 2. 读取模板 ----------
def read_template(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

prog_template = read_template("节目模板.txt")
multi_template = read_template("多名模板.txt")

min_len = min(len(prog_template), len(multi_template))
prog_template = prog_template[:min_len]
multi_template = multi_template[:min_len]

print(f"📋 节目模板数量: {len(prog_template)}，多名模板数量: {len(multi_template)}")
print("📄 节目模板前5项:", prog_template[:5])
print("📄 多名模板前5项:", multi_template[:5])

# ---------- 3. 匹配逻辑（简化版，更容易命中）----------
matched_lines = []

# 你可以在这里直接改成“包含”匹配，忽略大小写，只要频道名出现在行里就算
for prog, multi in zip(prog_template, multi_template):
    # 规则：如果多名模板非空且长度>8，使用多名；否则使用节目名
    keyword = multi if len(multi) > 8 else prog
    keyword_lower = keyword.lower()
    for line in temp_lines:
        if keyword_lower in line.lower():
            if line not in matched_lines:
                matched_lines.append(line)
            # 可选：打印匹配到的示例
            # print(f"✅ 匹配: '{keyword}' -> {line[:60]}")

print(f"🎯 总共匹配到 {len(matched_lines)} 行（去重后）")

# ---------- 4. 强制输出 ipvt-1.txt，不再依赖80%条件 ----------
with open("ipvt-1.txt", "w", encoding="utf-8") as out:
    for line in matched_lines:
        out.write(line + "\n")
print(f"✅ 已写入 ipvt-1.txt，共 {len(matched_lines)} 行")

# 如果一条都没匹配上，也生成一个空文件（避免git报错）
if len(matched_lines) == 0:
    print("⚠️ 没有匹配到任何频道，请检查模板内容是否与抓取的内容一致")
