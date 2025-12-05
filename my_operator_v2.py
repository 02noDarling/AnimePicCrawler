from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
import os
import time
from urllib.parse import urlparse, unquote
import re

# --- 1. 配置参数 ---
DOWNLOAD_DIRECTORY = r"D:\VsCodeProjects\Dataset\2Dimages"
FILENAME = "download_urls.txt"
TIMEOUT = 60  # 单次下载最大等待时间 (秒)
POLL_INTERVAL = 1  # 检查下载目录的间隔时间 (秒)
MAX_RETRY = 3  # 每个图片的最大重试次数
REFRESH_PAGE_URL = "https://anime-pictures.net/posts?page=4&search_tag=girl&order_by=rating&ldate=4&lang=zh-cn"
COOKIE_REFRESH_WAIT = 5  # 刷新 Cookie 时的等待时间（秒）


def read_download_urls(filename: str) -> list[str]:
    """读取下载 URL 列表"""
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
    """检查下载目录中是否存在正在下载的临时文件"""
    for filename in os.listdir(download_dir):
        if filename.endswith(('.crdownload', '.tmp', '.partial')):
            return True
    return False


def wait_for_specific_download_complete(
    download_dir: str, 
    post_id: str, 
    timeout: int = 300, 
    poll_interval: int = 1
) -> bool:
    """
    等待下载目录中出现包含特定 post_id 的完整文件，表示下载完成。
    
    Args:
        download_dir: 下载文件夹路径
        post_id: 正在下载图片的唯一 ID
        timeout: 最大等待时间（秒）
        poll_interval: 检查间隔（秒）
        
    Returns:
        如果文件在超时前出现则返回 True，否则返回 False
    """
    start_time = time.time()
    time.sleep(poll_interval * 2)  # 初始等待
    
    print(f"  ... 正在等待 ID {post_id} 完整下载...")

    while time.time() - start_time < timeout:
        for filename in os.listdir(download_dir):
            if post_id in filename:
                if not filename.endswith(('.crdownload', '.tmp', '.partial')):
                    time.sleep(1)  # 确保文件写入完成
                    return True

        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0:  # 每 10 秒输出一次
            print(f"  ... 正在等待下载完成 ({elapsed}s / {timeout}s)")
        time.sleep(poll_interval)
        
    print(f"🔴 错误: 等待 ID {post_id} 下载超时 ({timeout}秒)。")
    return False


def extract_post_id_from_url(url: str) -> str | None:
    """从 URL 中提取帖子 ID"""
    match = re.search(r'/download_image/(\d+)-', url)
    if match:
        return match.group(1)
    return None


def check_file_exists(download_dir: str, post_id: str) -> tuple[bool, str | None]:
    """
    检查文件是否已存在（通过 downloaded.txt 记录）
    
    Args:
        download_dir: 下载目录
        post_id: 图片 ID
    
    Returns:
        (是否存在, 提示信息)
    """
    downloaded_file = os.path.join(download_dir, "downloaded.txt")
    
    # 如果 downloaded.txt 不存在，说明没有下载过
    if not os.path.exists(downloaded_file):
        return False, None
    
    try:
        with open(downloaded_file, 'r', encoding='utf-8') as f:
            downloaded_ids = set(line.strip() for line in f if line.strip())
        
        if post_id in downloaded_ids:
            return True, f"已记录在 downloaded.txt 中"
        else:
            return False, None
            
    except Exception as e:
        print(f"⚠️ 读取 downloaded.txt 时出错: {e}")
        return False, None

def mark_as_downloaded(download_dir: str, post_id: str):
    """
    将成功下载的图片 ID 记录到 downloaded.txt
    
    Args:
        download_dir: 下载目录
        post_id: 图片 ID
    """
    downloaded_file = os.path.join(download_dir, "downloaded.txt")
    
    try:
        with open(downloaded_file, 'a', encoding='utf-8') as f:
            f.write(f"{post_id}\n")
        print(f"  ✓ 已记录 ID: {post_id} 到 downloaded.txt")
    except Exception as e:
        print(f"  ⚠️ 记录到 downloaded.txt 时出错: {e}")

def refresh_cookies(driver: webdriver.Edge, wait_time: int = 5) -> bool:
    """
    刷新 Cookies：重新访问列表页以通过 Cloudflare 验证
    
    Args:
        driver: Selenium WebDriver 实例
        wait_time: 等待 Cloudflare 验证的时间（秒）
        
    Returns:
        是否成功刷新
    """
    try:
        print("🔄 正在刷新 Cookies（重新访问列表页）...")
        driver.get(REFRESH_PAGE_URL)
        time.sleep(wait_time)
        
        # 检查是否还在 Cloudflare 验证页面
        if "Just a moment" in driver.page_source or "Checking your browser" in driver.page_source:
            print("  ... 等待 Cloudflare 验证完成...")
            time.sleep(wait_time * 2)  # 额外等待
        
        print("✅ Cookies 刷新成功")
        return True
        
    except Exception as e:
        print(f"⚠️ 刷新 Cookies 时出错: {e}")
        return False


def download_image_with_retry(
    driver: webdriver.Edge, 
    url: str, 
    post_id: str, 
    download_dir: str,
    index: int,
    total: int,
    max_retry: int = MAX_RETRY
) -> bool:
    """
    带重试机制的图片下载函数
    
    Args:
        driver: Selenium WebDriver 实例
        url: 图片下载 URL
        post_id: 图片 ID
        download_dir: 下载目录
        index: 当前图片索引
        total: 总图片数
        max_retry: 最大重试次数
        
    Returns:
        是否下载成功
    """
    for attempt in range(1, max_retry + 1):
        print(f"\n▶️ 正在下载第 {index}/{total} 张图片 (尝试 {attempt}/{max_retry})")
        print(f"   URL: {url}")
        
        try:
            # 如果不是第一次尝试，先刷新 Cookies
            if attempt > 1:
                if not refresh_cookies(driver, COOKIE_REFRESH_WAIT):
                    print(f"⚠️ Cookie 刷新失败，继续尝试下载...")
                time.sleep(2)  # 短暂等待
            
            # 触发下载
            driver.get(url)
            
            # 等待下载完成
            if wait_for_specific_download_complete(
                download_dir, 
                post_id, 
                timeout=TIMEOUT, 
                poll_interval=POLL_INTERVAL
            ):
                print(f"✅ 第 {index} 张图片下载完成 [ID: {post_id}]")

                # ⭐ 新增：记录到 downloaded.txt
                mark_as_downloaded(download_dir, post_id)
                
                return True
            else:
                print(f"❌ 第 {index} 张图片下载超时 (尝试 {attempt}/{max_retry})")
                
                # 如果还有重试机会，继续
                if attempt < max_retry:
                    print(f"🔁 准备重试...")
                    time.sleep(2)
                    
        except Exception as e:
            print(f"❌ 下载时发生错误 (尝试 {attempt}/{max_retry}): {e}")
            if attempt < max_retry:
                print(f"🔁 准备重试...")
                time.sleep(2)
    
    # 所有重试都失败
    print(f"🔴 第 {index} 张图片下载失败，已重试 {max_retry} 次，跳过 [ID: {post_id}]")
    return False


def setup_edge_driver(download_dir: str) -> webdriver.Edge:
    """
    配置并启动 Edge 浏览器，增强反检测能力
    """
    options = EdgeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    
    driver = webdriver.Edge(options=options)
    
    # 隐藏 webdriver 特征
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    return driver


# --- 主程序执行 ---
def main():
    # 确保下载目录存在
    if not os.path.exists(DOWNLOAD_DIRECTORY):
        os.makedirs(DOWNLOAD_DIRECTORY)
        print(f"📁 创建下载目录: {DOWNLOAD_DIRECTORY}")

    # 1. 读取 URL 列表
    urls = read_download_urls(FILENAME)

    if not urls:
        print("❌ 没有 URL 可供下载，程序结束。")
        return

    # 2. 启动浏览器
    print("\n🚀 正在启动浏览器...")
    driver = setup_edge_driver(DOWNLOAD_DIRECTORY)
    
    try:
        # 3. 首次访问列表页，获取初始 Cookies
        print(f"\n🌐 首次访问列表页以通过 Cloudflare 验证...")
        driver.get(REFRESH_PAGE_URL)
        time.sleep(COOKIE_REFRESH_WAIT)
        
        if "Just a moment" in driver.page_source or "Checking your browser" in driver.page_source:
            print("  ... 等待 Cloudflare 验证...")
            time.sleep(COOKIE_REFRESH_WAIT * 2)
        
        print("✅ 初始化完成")
        print(f"\n{'='*60}")
        print(f"开始批量下载到目录: {DOWNLOAD_DIRECTORY}")
        print(f"总共 {len(urls)} 个文件")
        print(f"{'='*60}")

        # 4. 循环下载
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for i, target_url in enumerate(urls, 1):
            # 提取 ID
            post_id = extract_post_id_from_url(target_url)
            
            if not post_id:
                print(f"\n⚠️ 警告: 无法从 URL 提取 ID，跳过 ({i}/{len(urls)})")
                skip_count += 1
                continue
            
            # 检查文件是否已存在
            exists, existing_filename = check_file_exists(DOWNLOAD_DIRECTORY, post_id)
            if exists:
                print(f"\n🟢 跳过: 文件已存在 ({i}/{len(urls)}) [ID: {post_id}]")
                print(f"   本地文件名: {existing_filename}")
                skip_count += 1
                continue
            
            # 下载图片（带重试）
            if download_image_with_retry(
                driver, 
                target_url, 
                post_id, 
                DOWNLOAD_DIRECTORY,
                i,
                len(urls),
                MAX_RETRY
            ):
                success_count += 1
            else:
                fail_count += 1
        
        # 5. 输出统计信息
        print(f"\n{'='*60}")
        print(f"📊 下载统计:")
        print(f"   ✅ 成功: {success_count} 个")
        print(f"   🟢 跳过: {skip_count} 个")
        print(f"   ❌ 失败: {fail_count} 个")
        print(f"   📝 总计: {len(urls)} 个")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断下载")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 6. 清理和退出
        print("\n🧹 正在清理资源...")
        driver.quit()
        print("✅ 所有下载任务已处理完毕。")


if __name__ == "__main__":
    main()