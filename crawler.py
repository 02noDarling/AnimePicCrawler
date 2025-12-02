"""
爬取页面,例如 0-1-100 从第0页开始到第一页，每页100张
"""

import time
import random
import undetected_chromedriver as uc #防cf检测浏览器对象
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import login
import set_maxpage


url = "https://anime-pictures.net/posts?page={}&search_tag=girl&order_by=rating&ldate=4&lang=zh-cn"


class photos:
    def __init__(self,url,number,last_number,lodin_flag=0,start=0,end=1):#初始化
        self.number = number
        self.url = url
        self.start = start
        self.end = end
        self.last_number = last_number
        
        options = uc.ChromeOptions()
        # 手动指定 Chrome 路径
        options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # 根据实际情况调整路径
        
        # 设置下载路径
        prefs = {
            "download.default_directory": r"D:\VsCodeProject\2Dimages", # 更改为你希望的路径
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)

        self.driver = uc.Chrome(options=options)  #driver_executable_path=r".\chromedriver.exe"
        self.wait = WebDriverWait(self.driver, 60, 0.2)
        self.driver.implicitly_wait(10)
        if login_flag == 1:
            username,password = input("输入账号密码(username-password):").split("-")
            login.login(driver=self.driver,username=username,password=password)
            time.sleep(random.uniform(2, 4))
            set_maxpage.set(driver=self.driver, number=self.number)

        time.sleep(random.uniform(2, 4))
        #运行隐藏参数js
        # self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': js})
    def page(self,count):
        #加载页面
        self.driver.get(self.url.format(count))
        # 等待页面加载
        print(f"________________________{count}________________________")
        time.sleep(random.uniform(1, 2))

    def all(self, last_number):
        # 等待图片区域加载
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#svelte picture img")))
        
        # 获取所有缩略图的 <a> 链接
        links = self.driver.find_elements(By.XPATH, '//*[@id="svelte"]//a[.//picture/img]')
        
        # 从 last_number 开始（用户输入的是“上次张数”，即已下载到第几张）
        for i in range(last_number - 1, min(len(links), self.number)):
            try:
                link = links[i]
                # 滚动到元素位置（确保不在屏幕外）
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link)
                time.sleep(random.uniform(0.5, 1))
                
                # 使用 JS 点击缩略图链接
                self.driver.execute_script("arguments[0].click();", link)

                # 等待并点击原图下载链接
                original_link = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, '//a[@rel="external nofollow"]'))
                )
                # 使用 JS 点击原图下载链接
                self.driver.execute_script("arguments[0].click();", original_link)

                self.driver.back()
                time.sleep(random.uniform(1, 2))

                # 重要：重新获取 links，避免 StaleElementReferenceException
                links = self.driver.find_elements(By.XPATH, '//*[@id="svelte"]//a[.//picture/img]')
                print(i + 1, end=" ")
            except Exception as e:
                print(f"\nError on {i+1}: {str(e)[:50]}")
                self.driver.back()
                time.sleep(1)
                links = self.driver.find_elements(By.XPATH, '//*[@id="svelte"]//a[.//picture/img]')
        print()

    def run(self):

        for count in range(self.start,self.end):
            self.page(count)
            self.all(self.last_number)
            self.last_number = 1
        time.sleep(10)
        input("完毕！")
        self.driver.quit()



if __name__ == "__main__":
    end = 100
    login_flag = eval(input("是否注册(0:否,1:是):"))
    start, last_number, number = map(eval, input("上次页数-上次张数-每页张数:").split("-"))
    web_crawler = photos(url, number, last_number, login_flag, start, end)
    web_crawler.run()
    exit()

