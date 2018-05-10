# # -*- coding: utf-8 -*-
# import scrapy
# import urllib.parse
# from scrapy import Selector
# from scrapy.http import Request
# from scrapy.http.cookies import CookieJar
#
#
# class ChoutiSpider(scrapy.Spider):
#     """
#     自动登录点赞抽屉
#       - 1.发送一个 GET 请求,抽屉
#         - 获取 cookie
#       - 2.用户密码 POST 登录:携带上一次 cookie
#         - 返回值:999
#       - 3.为所欲为,携带 cookie
#     """
#     name = 'chouti'
#     allowed_domains = ['chouti.com']
#     start_urls = ['https://dig.chouti.com/']
#     cookie_dict = {}
#
#     def start_requests(self):
#         for url in self.start_urls:
#             # yield 只是放在调度器(都是需要调度器进行调度的)
#             # 只要执行 parse 函数既表示数据已经返回(调度器什么时候执行我们是不知道的)
#
#             yield Request(url, dont_filter=True, callback=self.parse)
#
#     def parse(self, response):
#         # response.text 首页
#
#         # 提取response.request 里的 cookie 并放入 cookie_jar 对象里
#         cookie_jar = CookieJar()  # 对象中封装了所有 cookie
#         cookie_jar.extract_cookies(response, response.request)
#
#         # 循环取出 cookie 并生成字典格式
#         for k, v in cookie_jar._cookies.items():
#             for i, j in v.items():
#                 for m, n in j.items():
#                     self.cookie_dict[m] = n.value
#
#         post_dict = {
#             'phone': '8615915455813',
#             'password': 'zxywhx875199',
#             'oneMonth': 1,
#         }
#
#         # 发送 POST 进行登录
#         yield Request(
#             url='https://dig.chouti.com/login',
#             method="POST",
#             cookies=self.cookie_dict,
#             body=urllib.parse.urlencode(post_dict),
#             headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
#             callback=self.parse2,
#         )
#
#     def parse2(self, response):
#
#         # 获取新闻列表
#         yield Request(
#             url='https://dig.chouti.com',
#             method="GET",
#             cookies=self.cookie_dict,
#             callback=self.parse3,
#         )
#
#     def parse3(self, response):
#         # 找 div class = part2 获取 share-linkid 这个属性
#         hxs = Selector(response)
#         link_id_list = hxs.xpath('//div[@class="part2"]/@share-linkid').extract()
#         print(link_id_list)
#
#
#         # 点赞(POST 的请求体可以不放数据)
#         """
#         for link_id in link_id_list:
#             # 获取每个 id 去点赞
#             base_url = "https://dig.chouti.com/link/vote?linksId=%s" % (link_id,)
#             print(base_url)
#             yield Request(url=base_url,
#                           method='POST',
#                           cookies=self.cookie_dict,
#                           callback=self.parse4)
#         """
#
#         # 取消点赞
#
#         for link_id in link_id_list:
#             yield Request(url='https://dig.chouti.com/vote/cancel/vote.do',
#                           body=urllib.parse.urlencode({'linksId': link_id}),
#                           method='POST',
#                           headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
#                           cookies=self.cookie_dict,
#                           callback=self.parse4)
#
#         page_list = hxs.xpath('//div[@id="page-area"]//a/@href').extract()
#         for page in page_list:
#             # https://dig.chouti.com + /all/hot/recent/2
#             page_url = "https://dig.chouti.com%s" % (page,)
#
#             yield Request(url=page_url, method="GET", cookies=self.cookie_dict, callback=self.parse3)
#
#     def parse4(self, response):
#         print(response.text)
#


import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# User-Agent 首部包含了一个特征字符串，用来让网络协议的对端来识别发起请求的用户代理软件的应用类型、操作系统、软件开发商以及版本号。
ua = UserAgent()
headers = {'User-Agent': ua.chrome}

# 发送请求获取 cookie
r0 = requests.get('https://dig.chouti.com', headers=headers)
r0_cookie_dict = r0.cookies.get_dict()
print(r0_cookie_dict)

# 登录
r1 = requests.post('https://dig.chouti.com/login',
                   data={
                      'phone': '8615915455813',
                      'password': 'zxywhx875199',
                      'oneMonth': 1,
                   },
                   headers=headers,
                   cookies=r0_cookie_dict,
                   )
# 获取授权后的 cookie
r1_cookie_dict = r1.cookies.get_dict()

# 点赞
"""
Request URL:https://dig.chouti.com/link/vote?linksId=17654151
Request Method:POST
Query String Parameters # 表示一下数据是放在链接里发送的
linksId:17654151
"""
cookie_dict = {}
cookie_dict.update(r0_cookie_dict)
cookie_dict.update(r1_cookie_dict)

r2 = requests.post('https://dig.chouti.com/link/vote?linksId=19422691', cookies=cookie_dict, headers=headers)


