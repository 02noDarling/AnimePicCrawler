import cloudscraper
import re
import os

# 检查并安装 cloudscraper 库（如果尚未安装）
# try:
#     import cloudscraper
# except ImportError:
#     print("cloudscraper 库未安装，正在尝试安装...")
#     os.system('pip install cloudscraper')
#     import cloudscraper
#     print("cloudscraper 安装完成。")

scraper = cloudscraper.create_scraper()  # 能绕过 Cloudflare 5s challenge

# 定义文件路径
OUTPUT_FILENAME = "download_urls.txt"

def extract_post_ids(html: str) -> list[int]:
    """从列表页HTML中提取所有帖子的ID。"""
    # 匹配 href=["./]?posts/(\d+)
    pattern = r'href=["\'](?:\.?/)?posts/(\d+)'
    return list(map(int, re.findall(pattern, html)))

def extract_download_url(html: str) -> str | None:
    """从帖子详情页HTML中提取原图下载链接。"""
    # 匹配以 https://api.anime-pictures.net/pictures/download_image/ 开头的链接
    pattern = r'https://api\.anime-pictures\.net/pictures/download_image/[^\"]+'
    match = re.search(pattern, html)
    return match.group(0) if match else None

def get_download_url_for_page(page_url: str) -> list[str]:
    """
    获取单个列表页中所有图片的下载链接。
    
    Args:
        page_url: 列表页的URL。
        
    Returns:
        一个包含所有下载链接的列表。
    """
    print(f"\n--- 正在处理列表页: {page_url} ---")
    
    # 1. 访问列表页
    try:
        resp = scraper.get(page_url)
        print(f"列表页状态码: {resp.status_code}")
        if resp.status_code != 200:
            print(f"访问列表页失败，跳过。")
            return []
    except Exception as e:
        print(f"访问列表页时发生错误: {e}")
        return []

    # 2. 提取帖子ID
    ids = extract_post_ids(resp.text)
    ids = ids[:80] # 根据原代码逻辑，这里可以限制数量，但如果想获取全部，可以去掉或调整
    print(f"提取到 {len(ids)} 个帖子ID。")
    
    final_urls = []
    
    # 3. 遍历帖子ID，访问详情页并提取下载链接
    for i, id in enumerate(ids):
        # 构造详情页URL
        pic_url = f"https://anime-pictures.net/posts/{id}?by_tag=21508&lang=zh-cn"
        
        try:
            resp_pic = scraper.get(pic_url)
            # print(f"  - 帖子 {id} 状态码: {resp_pic.status_code}")
            
            if resp_pic.status_code == 200:
                download_url = extract_download_url(resp_pic.text)
                if download_url:
                    final_urls.append(download_url)
                else:
                    # print(f"  - 帖子 {id} 未找到下载链接。")
                    pass
            
        except Exception as e:
            print(f"访问帖子 {id} 时发生错误: {e}")
            
        # 打印进度
        if (i + 1) % 10 == 0 or (i + 1) == len(ids):
            print(f"  -> 已处理 {i + 1}/{len(ids)} 个帖子，已收集 {len(final_urls)} 个链接。")

    return final_urls

def run_scraper_and_save(start_page: int, end_page: int, base_url_template: str):
    """
    循环遍历指定页码范围，获取所有下载链接并保存到文件。
    """
    all_download_urls = []
    
    for page in range(start_page, end_page + 1):
        # 构造当前页的URL
        current_url = base_url_template.format(page=page)
        
        # 获取当前页的所有下载链接
        urls_for_page = get_download_url_for_page(current_url)
        
        # 将结果添加到总列表中
        all_download_urls.extend(urls_for_page)
        
    print(f"\n==========================================")
    print(f"✅ 所有页面处理完成。")
    print(f"总共收集到 {len(all_download_urls)} 个下载链接。")
    
    # 将所有链接写入文件
    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        # 使用 set 去重后再写入
        unique_urls = set(all_download_urls)
        for url in unique_urls:
            if url: # 确保链接非空
                f.write(url + '\n')

    print(f"🔗 所有唯一的下载链接已保存到文件: **{OUTPUT_FILENAME}**")
    print(f"文件中共有 {len(unique_urls)} 个唯一的链接。")


# --- 运行主程序 ---
# 列表页的基础URL模板，{page} 会被替换
BASE_URL_TEMPLATE = "https://anime-pictures.net/posts?page={page}&search_tag=girl&order_by=rating&ldate=4&lang=zh-cn"

# 运行循环从 page 12 到 20 (包含 20)
run_scraper_and_save(start_page=21, end_page=50, base_url_template=BASE_URL_TEMPLATE)