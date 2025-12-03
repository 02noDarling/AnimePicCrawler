from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
import os
import time
from urllib.parse import urlparse, unquote # 导入用于解析URL的库
import re

# --- 1. 配置参数 ---
# 确保这个路径与 options 中设置的路径一致
DOWNLOAD_DIRECTORY = r"D:\VsCodeProjects\Dataset\2Dimages"
FILENAME = "download_urls.txt"
TIMEOUT = 300  # 最大等待下载完成的时间 (秒)
POLL_INTERVAL = 1  # 检查下载目录的间隔时间 (秒)


def read_download_urls(filename: str) -> list[str]:
    # (保持你原有的 read_download_urls 函数不变)
    if not os.path.exists(filename):
        print(f"❌ 错误: 文件 '{filename}' 不存在。")
        return []

    url_list = []
    print(f"--- 正在读取文件: {filename} ---")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url:
                    url_list.append(url)
        
        print(f"✅ 文件读取成功。总共读取到 {len(url_list)} 个 URL。")
        return url_list
        
    except Exception as e:
        print(f"⚠️ 读取文件时发生错误: {e}")
        return []


def is_downloading(download_dir: str) -> bool:
    """
    检查下载目录中是否存在正在下载的临时文件（如 .crdownload, .tmp）。
    """
    for filename in os.listdir(download_dir):
        # 检查常见的临时文件扩展名
        if filename.endswith(('.crdownload', '.tmp', '.partial')):
            return True
    return False

def wait_for_download_complete(download_dir: str, timeout: int = 60, poll_interval: int = 1) -> bool:
    """
    等待下载目录中没有临时文件，表示下载完成。
    """
    start_time = time.time()
    
    # 第一次检查，确保文件开始下载
    # 这一步对于检查是否存在临时文件是必要的，给浏览器一个开始下载的时间
    time.sleep(poll_interval) 

    while is_downloading(download_dir):
        if time.time() - start_time > timeout:
            print(f"🔴 错误: 等待下载超时 ({timeout}秒)。")
            return False
        
        print(f"  ... 正在等待下载完成 ({int(time.time() - start_time)}s / {timeout}s)")
        time.sleep(poll_interval)
        
    # 增加一个短暂的等待，以确保文件系统操作完成
    time.sleep(1) 
    return True

def extract_post_id_from_url(url: str) -> str | None:
    """
    从 anime-pictures 的下载 URL 中提取帖子 ID。
    """
    match = re.search(r'/download_image/(\d+)-', url)
    if match:
        return match.group(1)
    return None

# --- 修改后的函数签名和逻辑 ---
def wait_for_specific_download_complete(
    download_dir: str, 
    post_id: str, 
    timeout: int = 300, 
    poll_interval: int = 1
) -> bool:
    """
    等待下载目录中出现包含特定 post_id 的完整文件，表示下载完成。
    
    Args:
        download_dir: 下载文件夹路径。
        post_id: 正在下载图片的唯一 ID。
        timeout: 最大等待时间（秒）。
        poll_interval: 检查间隔（秒）。
        
    Returns:
        如果文件在超时前出现则返回 True，否则返回 False。
    """
    start_time = time.time()
    
    # 增加一个初始等待，确保浏览器开始写入文件
    time.sleep(poll_interval * 2) 
    
    print(f"  ... 正在等待 ID {post_id} 完整下载到 {download_dir} ...")

    while time.time() - start_time < timeout:
        
        # 遍历下载目录中的所有文件
        for filename in os.listdir(download_dir):
            # 1. 检查文件名中是否包含该 ID
            if post_id in filename:
                # 2. 检查文件是否不是临时文件 (.crdownload 或 .tmp)
                if not filename.endswith(('.crdownload', '.tmp', '.partial')):
                    # 找到了完整的目标文件
                    time.sleep(1) # 增加短暂等待，确保文件写入完成
                    return True

        # 如果没有找到完整文件，继续等待
        print(f"  ... 正在等待下载完成 ({int(time.time() - start_time)}s / {timeout}s)")
        time.sleep(poll_interval)
        
    # 超时退出
    print(f"🔴 错误: 等待 ID {post_id} 下载超时 ({timeout}秒)。")
    return False

def extract_post_id_from_url(url: str) -> str | None:
    """
    从 anime-pictures 的下载 URL 中提取帖子 ID。
    URL 格式通常为: .../download_image/ID-widthxheight-tags...
    """
    # 匹配 /download_image/ 后面的第一个数字串 (即 ID)
    match = re.search(r'/download_image/(\d+)-', url)
    if match:
        return match.group(1)
    return None

# --- 主程序执行 ---

# 确保下载目录存在
if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)
    print(f"创建下载目录: {DOWNLOAD_DIRECTORY}")

# 1. 读取 URL 列表
urls = read_download_urls(FILENAME)

if not urls:
    print("没有 URL 可供下载，程序结束。")
else:
    # 2. 配置 Edge 浏览器选项
    options = EdgeOptions()
    options.add_argument("--start-maximized")

    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIRECTORY,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True 
    })
    
    # 3. 启动驱动
    driver = webdriver.Edge(options=options)
    
    # 首先访问一个正常的页面
    driver.get("https://anime-pictures.net/posts?page=4&search_tag=girl&order_by=rating&ldate=4&lang=zh-cn")
    
    print(f"\n--- 开始批量下载到目录: {DOWNLOAD_DIRECTORY} ---")

    # 4. 循环下载并等待 (增加跳过逻辑)
    for i, target_url in enumerate(urls):
        
        # --- 新增的跳过逻辑 START ---
        path = urlparse(target_url).path
        filename_with_encoding = os.path.basename(path)
        # URL中的文件名通常是URL编码过的，需要解码
        expected_filename = unquote(filename_with_encoding) 
        if not expected_filename.startswith("ANIME-PICTURES.NET_-_"):
            expected_filename = "ANIME-PICTURES.NET_-_" + expected_filename
            
        post_id = extract_post_id_from_url(target_url)
    
        if not post_id:
            print(f"⚠️ 警告: 无法从 URL 提取 ID，跳过此 URL ({i+1}/{len(urls)}): {target_url}")
            continue
            
        # b. 检查下载目录中是否存在包含此 ID 的文件
        found_existing = False
        
        # 遍历下载目录中的所有文件
        for filename in os.listdir(DOWNLOAD_DIRECTORY):
            # 检查文件名中是否包含该 ID
            # 即使文件名开头是 ANIME-PICTURES.NET_- 或其他，只要包含 ID 就认为已存在
            if post_id in filename:
                # 确保这不是一个临时文件 (.crdownload 或 .tmp)
                if not filename.endswith(('.crdownload', '.tmp', '.partial')):
                    print(f"🟢 跳过: 文件已存在 ({i+1}/{len(urls)}) [ID: {post_id}]，本地文件名: {filename}")
                    found_existing = True
                    break
        
        if found_existing:
            continue # 跳过当前循环，进入下一个 URL
        
        # --- 新增的跳过逻辑 END ---
        
        print(f"\n▶️ 正在下载第 {i+1}/{len(urls)} 张图片: {expected_filename}")
        
        # 触发下载
        driver.get(target_url)
        
        # 等待当前下载完成
        # if wait_for_download_complete(DOWNLOAD_DIRECTORY, timeout=TIMEOUT, poll_interval=POLL_INTERVAL):
        #     print(f"✅ 第 {i+1} 张图片下载完成。")
        # else:
        #     print(f"❌ 第 {i+1} 张图片下载失败或超时，跳过。")

        if wait_for_specific_download_complete(
            DOWNLOAD_DIRECTORY, 
            post_id, 
            timeout=TIMEOUT, 
            poll_interval=POLL_INTERVAL
        ):
            print(f"✅ 第 {i+1} 张图片下载完成。")
        else:
            print(f"❌ 第 {i+1} 张图片下载失败或超时，跳过。")
            
    # 5. 清理和退出
    driver.quit()
    print("\n所有下载任务已处理完毕。")