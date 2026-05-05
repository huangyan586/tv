import requests
import re
from datetime import datetime

# ---------- 1. 读取网址列表，抓取所有内容 ----------
urls_file = "网址列表.txt"
temp_lines = []   # 存放所有抓取到的行（原始内容）

print("📡 开始抓取网站数据...")
with open(urls_file, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

for url in urls:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        # 按行拆开，保留每行原始内容
        lines = r.text.splitlines()
        temp_lines.extend(lines)
        print(f"✅ 成功抓取 {url} -> 获得 {len(lines)} 行")
    except Exception as e:
        print(f"❌ 抓取失败 {url}: {e}")

print(f"📦 总共收集到 {len(temp_lines)} 行文本")

# ---------- 2. 读取两个模板文件 ----------
def read_template(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

prog_template = read_template("节目模板.txt")   # 标准频道名
multi_template = read_template("多名模板.txt")  # 别名

# 确保两个模板行数一致（以少的为准）
min_len = min(len(prog_template), len(multi_template))
prog_template = prog_template[:min_len]
multi_template = multi_template[:min_len]

# 是否跳过第一行（模仿VBA中的 For i=2 to ...）
skip_first = True
start_idx = 1 if skip_first else 0

print(f"📋 节目模板数量: {len(prog_template)}，多名模板数量: {len(multi_template)}，从第{start_idx+1}行开始匹配")

# ---------- 3. 匹配逻辑 ----------
def matches_any_rule(line, prog_name, multi_name):
    """
    判断一行文本是否匹配当前的「节目名+多名规则」
    规则（还原你的VBA意图）：
       - 如果多名模板长度 > 8，看看 line 中是否包含 multi_name
       - 否则，看看 line 中是否包含 prog_name
    实际临时txt中每行类似 "CCTV1,http://..."
    """
    if len(multi_name) > 8:
        # 用多名模板去匹配整行
        return multi_name.lower() in line.lower()
    else:
        # 用节目名去匹配
        return prog_name.lower() in line.lower()

matched_lines = []          # 存储所有匹配成功的临时行
template_hit = [False] * len(prog_template)   # 每个模板条目是否至少命中一次

# 遍历每个模板条目
for idx in range(start_idx, len(prog_template)):
    prog = prog_template[idx]
    multi = multi_template[idx]
    hit_this_template = False

    for line in temp_lines:
        if matches_any_rule(line, prog, multi):
            # 匹配成功，记录这一行
            if line not in matched_lines:   # 简单去重
                matched_lines.append(line)
            hit_this_template = True

    if hit_this_template:
        template_hit[idx] = True

# 计算命中率（分母为除第一行外的总数）
total_templates = len(prog_template) - (1 if skip_first else 0)
hit_count = sum(template_hit[start_idx:])
hit_rate = hit_count / total_templates if total_templates > 0 else 0

print(f"🎯 命中率: {hit_count}/{total_templates} = {hit_rate:.1%}")

# ---------- 4. 决定是否输出 ipvt-1.txt ----------
# ---------- 4. 输出 ipvt-1.txt ----------
with open("ipvt-1.txt", "w", encoding="utf-8") as out:
    for line in matched_lines:
        out.write(line + "\n")
print(f"✅ 已更新 ipvt-1.txt，共 {len(matched_lines)} 行，命中率: {hit_rate:.1%}")
