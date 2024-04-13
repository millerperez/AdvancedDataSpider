# -*- coding: utf-8 -*-
# @Time    : 2024/4/12 下午6:47
# @Author  : MILLERPEREZ
# @Site    : 
# @File    : pasteurSpider.py
# @Software: PyCharm 
# @Comment : selenium框架 Mongodb数据库 法国巴斯德研究所(静态页面)
# 暂时缺少数据库去重功能 后续会使用redis数据库和hashlib进行去重

# 导包
import time
from datetime import datetime
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class PasteurSpider:
    def __init__(self):
        # 创建数据库对象
        self.mongo = MongoClient('localhost', 27017)
        self.collection = self.mongo['testdb']['pasteurSpider']
        # 配置浏览器禁止图片加载
        options = webdriver.ChromeOptions()
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        # 隐藏开发者警告
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # 驱动配置
        self.driver = webdriver.Chrome(options=options)
        self.driver.get("https://www.pasteur.fr/en/actualites-jdr")

    def __del__(self):
        print('driver正在关闭...')
        self.driver.quit()

    # 数据提取
    def get_info(self):
        url_list = []
        title_list = []
        date_list = []
        # 通过XPATH获取各字段信息
        title_link_list = self.driver.find_elements(
            By.XPATH, '//div[@class="views-field views-field-title"]/span[@class="field-content"]/a'
        )
        time_list = self.driver.find_elements(
            By.XPATH, '//span[@class="date-display-single"]'
        )
        # element元素是实体对象 页面刷新后失效 故用列表长期存储
        for info in title_link_list:
            link = info.get_attribute("href")
            url_list.append(link)
            title = info.text
            title_list.append(title)
        # 修改日期格式从01.01.2024更改为2024/01/01
        for info in time_list:
            the_time = info.text
            before_form = datetime.strptime(the_time, "%d.%m.%Y")
            new_form = before_form.strftime('%Y/%m/%d')
            date_list.append(new_form)
        # 此时浏览器会弹出一个窗口确认是否Accept All Cookies
        # 若使用selenium模拟点击会抛出异常
        # 而使用driver.get可以忽略弹窗正常爬取数据

        # 调用列表中的url获取各文章正文部分
        for link, title, date in zip(url_list, title_list, date_list):
            # 跳过首次访问时询问Accept All Cookies
            self.driver.get(link)
            time.sleep(3)
            text = self.get_text()
            time.sleep(3)
            item_dict = {
                "title": title,
                "author": '无',
                "info_type": 'T0',
                "post_agency": '法国/法国巴斯德研究所',
                "nation": '法国',
                "date": date,
                "link": link,
                "domain": '未知',
                "subject": '未知',
                "text": text
            }
            print(item_dict)
            self.insert_data(item_dict)

    # 数据存入Mongodb
    def insert_data(self, data):
        print('正在存入一条数据...')
        self.collection.insert_one(data)

    def get_text(self):
        # 获取段落内容并合并
        text_elements = self.driver.find_elements(By.XPATH, '//div[@class="article__content"]//p')
        text_list = [single_text.text for single_text in text_elements]
        text = ' '.join(text_list)
        return text


if __name__ == '__main__':
    spider = PasteurSpider()
    spider.get_info()
