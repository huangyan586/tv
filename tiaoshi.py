import requests
import os
from datetime import datetime

# --- 配置 ---
# 请求头，用于伪装成浏览器，避免被反爬
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
# 请求超时时间（秒）
TIMEOUT = 15

# 黑名单域名，包含这些域名的URL将被过滤
# --- 配置 ---
# 黑名单文件路径（每行一个域名）
BLACKLIST_FILE = "黑名单.txt"

def load_blacklist(file_path):
    """从文件读取黑名单域名，返回列表（忽略空行和#开头的注释）"""
    blacklist = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    blacklist.append(line)
    except FileNotFoundError:
        print(f"警告：黑名单文件 '{file_path}' 未找到，将不使用黑名单过滤")
    return blacklist

# 加载黑名单
BLACKLIST_DOMAINS = load_blacklist(BLACKLIST_FILE)

# 可从环境变量获取数据源，以便在GitHub Actions中灵活配置
URL_LIST_FILE = os.environ.get("URL_LIST_FILE", "网址列表.txt")
TEMPLATE_FILE = os.environ.get("TEMPLATE_FILE", "节目模板.txt")
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "临时.txt")

# --- 工具函数 ---
def fetch_url(url):
    """请求URL并返回文本内容，失败时返回空字符串"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        # 自动处理中文编码，防止乱码
        resp.encoding = resp.apparent_encoding
        return resp.text
    except Exception as e:
        print(f"请求失败 {url}: {e}")
        return ""

def parse_content(html):
    """
    解析响应文本，智能判断是M3U格式还是TXT格式
    返回一个包含所有有效节目条目的列表
    """
    entries = []
    # 清洗文本：移除回车符，合并多余空行
    cleaned = html.replace('\r', '')
    lines = cleaned.split('\n')
    # 过滤掉空行
    lines = [line.strip() for line in lines if line.strip()]

    # 判断是否为M3U格式（检查前20行是否包含 #EXTINF）
    is_m3u = any("#EXTINF" in line for line in lines[:20])

    if not is_m3u:
        # TXT格式：直接保留所有行
        entries = lines
    else:
        # M3U格式：提取频道名和URL
        for i in range(len(lines) - 1):
            line = lines[i]
            next_line = lines[i + 1]
            if line.startswith("#EXTINF") and next_line.startswith("http"):
                # 提取频道名：#EXTINF:-1,频道名
                parts = line.split(",", 1)
                channel_name = parts[1].strip() if len(parts) > 1 else ""
                # 移除下一行URL的#注释符（如果存在）
                url = next_line.replace("#", "").strip()
                entries.append(f"{channel_name},{url}")
    return entries

def remove_duplicates(data):
    """使用字典去重，并保持原始顺序"""
    return list(dict.fromkeys(data))

def apply_blacklist(entries):
    """应用黑名单过滤：移除包含特定域名的节目URL"""
    filtered = []
    for entry in entries:
        # 检查节目URL（逗号后的部分）是否包含黑名单域名
        if "," in entry:
            _, url = entry.split(",", 1)
            if any(domain in url for domain in BLACKLIST_DOMAINS):
                continue
        filtered.append(entry)
    return filtered

def apply_whitelist(entries, whitelist_keywords):
    """应用白名单过滤：仅保留频道名包含指定关键词的节目"""
    if not whitelist_keywords:
        return entries  # 如果没有提供白名单，则不过滤
    filtered = []
    for entry in entries:
        if "," in entry:
            name, _ = entry.split(",", 1)
            if any(keyword in name for keyword in whitelist_keywords):
                filtered.append(entry)
    return filtered

# --- 主流程 ---
def main():
    print(f"[{datetime.now()}] IPTV抓取任务开始")

    # 1. 读取URL列表
    try:
        with open(URL_LIST_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"成功读取 {len(urls)} 个源URL")
    except FileNotFoundError:
        print(f"错误：URL列表文件 '{URL_LIST_FILE}' 未找到！")
        return
    except Exception as e:
        print(f"错误：读取URL列表时发生异常：{e}")
        return

    # 2. 读取白名单关键词（节目模板）
    whitelist_keywords = []
    try:
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
            # 假设每行一个关键词
            whitelist_keywords = [line.strip() for line in f if line.strip()]
        print(f"成功读取 {len(whitelist_keywords)} 个白名单关键词")
    except FileNotFoundError:
        print(f"警告：模板文件 '{TEMPLATE_FILE}' 未找到，将跳过白名单过滤。")
    except Exception as e:
        print(f"错误：读取模板文件时发生异常：{e}")

    # 3. 采集与解析
    all_entries = []
    for idx, url in enumerate(urls, 1):
        print(f"正在抓取 ({idx}/{len(urls)}): {url}")
        html = fetch_url(url)
        if not html:
            continue
        entries = parse_content(html)
        all_entries.extend(entries)
        print(f"  从该源提取到 {len(entries)} 条节目")

    print(f"总计提取到 {len(all_entries)} 条原始节目")

    # 4. 数据清洗与过滤
    # 4.1 去重
    unique_entries = remove_duplicates(all_entries)
    print(f"去重后剩余 {len(unique_entries)} 条")

    # 4.2 黑名单过滤
    after_blacklist = apply_blacklist(unique_entries)
    print(f"黑名单过滤后剩余 {len(after_blacklist)} 条")

    # 4.3 白名单过滤
    after_whitelist = apply_whitelist(after_blacklist, whitelist_keywords)
    final_count = len(after_whitelist)
    print(f"白名单过滤后剩余 {final_count} 条")

    # 5. 输出结果
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for entry in after_whitelist:
                f.write(entry + "\n")
        print(f"结果已保存至 '{OUTPUT_FILE}'，共 {final_count} 条记录。")
    except Exception as e:
        print(f"错误：写入输出文件时发生异常：{e}")

if __name__ == "__main__":
    main()
