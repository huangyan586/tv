import requests
import time
import re
from datetime import datetime

# ===================== 配置（和你VBA完全对应）=====================
# 爬取源地址
URL_SOURCE_URL = "https://github.com/huangyan586/tv/blob/main/%E7%94%B5%E5%9D%80%E5%88%97%E8%A1%A8.txt"
# 模板关键词地址
TEMPLATE_URL = "https://github.com/huangyan586/tv/blob/main/%E8%8A%82%E7%9B%AE%E6%A8%A1%E6%9D%BF.txt"

# 黑名单（VBA bh数组）
BLACK_LIST = ["061899.xyz", "bkpcp.top", "myalicdn.com"]

# M3U8 标识
M3U_MARK = "#EXTINF"
HTTP_MARK = "http"
# =================================================================

def get_raw_text(url):
    """获取github网页里的原始文本"""
    try:
        raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        resp = requests.get(raw_url, timeout=15)
        resp.encoding = "utf-8"
        return resp.text.strip()
    except:
        return ""

def parse_content(html):
    """解析内容：自动识别txt/m3u8并统一格式"""
    lines = re.split(r"\n|\r\n", html)
    lines = [line.strip() for line in lines if line.strip()]
    
    result = []
    is_m3u8 = any(M3U_MARK in line for line in lines[:20])
    
    if not is_m3u8:
        # 普通txt直接返回
        return lines
    
    # m3u8 转 txt（和VBA逻辑一样）
    for i in range(len(lines) - 1):
        curr = lines[i]
        next_line = lines[i + 1]
        if M3U_MARK in curr and HTTP_MARK in next_line:
            if "," in curr:
                name = curr.split(",", 1)[1].strip()
                url = next_line.replace("#", "").strip()
                result.append(f"{name},{url}")
    return result

def filter_lines(lines, black_list, keywords):
    """过滤：黑名单 + 模板匹配"""
    final = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 跳过黑名单
        if any(b in line for b in black_list):
            continue
        
        # 必须匹配模板关键词
        if any(k in line for k in keywords):
            final.append(line)
    return final

def main():
    print("开始执行 IPTV 自动更新...", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # 1. 获取网址列表
    url_text = get_raw_text(URL_SOURCE_URL)
    url_list = [u.strip() for u in url_text.splitlines() if u.strip()]
    
    # 2. 批量爬取
    all_lines = []
    for url in url_list:
        if not url.startswith("http"):
            continue
        try:
            print(f"爬取: {url}")
            html = get_raw_text(url)
            lines = parse_content(html)
            all_lines.extend(lines)
            time.sleep(1)
        except:
            continue
    
    # 3. 去重（字典去重）
    unique_lines = list(dict.fromkeys([l.strip() for l in all_lines if l.strip()]))
    print(f"去重后总数: {len(unique_lines)}")
    
    # 4. 获取模板关键词
    template_text = get_raw_text(TEMPLATE_URL)
    keywords = [k.strip() for k in template_text.splitlines() if k.strip()]
    
    # 5. 过滤（黑名单 + 关键词匹配）
    final_lines = filter_lines(unique_lines, BLACK_LIST, keywords)
    print(f"最终有效数据: {len(final_lines)}")
    
    # 6. 输出到 临时.txt
    with open("临时.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_lines))
    
    print("执行完成！文件：临时.txt")

if __name__ == "__main__":
    main()
