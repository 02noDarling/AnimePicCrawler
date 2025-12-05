from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import os

def download_image_with_selenium(img_url, save_path):
    # 配置 Edge 浏览器
    edge_options = Options()
    # edge_options.add_argument('--headless')  # 先不用无头模式，方便调试
    edge_options.add_argument('--disable-blink-features=AutomationControlled')
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    edge_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Edge(options=edge_options)
    
    # 隐藏 webdriver 特征
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        '''
    })
    
    try:
        # 1. 先访问列表页，通过 Cloudflare 验证
        print("正在访问列表页（等待 Cloudflare 验证）...")
        list_url = 'https://anime-pictures.net/posts?page=4&search_tag=girl&order_by=rating&ldate=4&lang=zh-cn'
        driver.get(list_url)
        
        # 等待页面加载完成（Cloudflare 验证通常需要几秒）
        time.sleep(5)
        
        # 检查是否通过验证
        if "Just a moment" in driver.page_source or "Checking your browser" in driver.page_source:
            print("等待 Cloudflare 验证...")
            time.sleep(10)  # 额外等待
        
        print("✓ 列表页访问成功")
        
        # 2. 获取 cookies
        cookies = driver.get_cookies()
        print(f"\n获取到的 Cookies:")
        for cookie in cookies:
            print(f"  {cookie['name']} = {cookie['value'][:50]}...")
        
        # 3. 使用 requests 下载图片（带上 cookies）
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain'))
        
        headers = {
            'User-Agent': driver.execute_script("return navigator.userAgent"),
            'Referer': list_url,
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://anime-pictures.net',
        }
        
        print(f"\n正在下载图片...")
        print(f"请求头:")
        for k, v in headers.items():
            print(f"  {k}: {v[:80]}...")
        
        response = session.get(img_url, headers=headers, timeout=30)
        
        print(f"\n图片响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ 下载成功: {save_path} ({len(response.content)} bytes)")
            return True
        else:
            print(f"✗ 下载失败: {response.status_code}")
            print(f"响应头: {response.headers}")
            return False
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        driver.quit()

# 测试
url = "https://api.anime-pictures.net/pictures/download_image/888175-5403x7641-original-haruhiruri-single-long+hair-tall+image-looking+at+viewer.jpg"
download_image_with_selenium(url, "test_image.jpg")