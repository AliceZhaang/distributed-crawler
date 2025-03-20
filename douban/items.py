# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BookItem(scrapy.Item):
    # 书籍基本信息
    book_id = scrapy.Field()  # 豆瓣图书ID
    title = scrapy.Field()  # 书名
    subtitle = scrapy.Field()  # 副标题
    original_title = scrapy.Field()  # 原作名
    author = scrapy.Field()  # 作者
    translator = scrapy.Field()  # 译者
    publisher = scrapy.Field()  # 出版社
    series = scrapy.Field()  # 丛书信息
    publish_date = scrapy.Field()  # 出版年
    pages = scrapy.Field()  # 页数
    price = scrapy.Field()  # 定价
    binding = scrapy.Field()  # 装帧
    isbn = scrapy.Field()  # ISBN
    
    # 书籍评分信息
    rating_score = scrapy.Field()  # 评分
    rating_people = scrapy.Field()  # 评价人数
    
    # 元数据
    url = scrapy.Field()  # 详情页URL
    cover_url = scrapy.Field()  # 封面图片URL
    crawl_time = scrapy.Field()  # 爬取时间
    
    # 新增字段
    js_tags = scrapy.Field()  # JavaScript中的标签
    error_info = scrapy.Field()  # 错误信息
    comments_count = scrapy.Field()  # 短评数量
    reviews_count = scrapy.Field()  # 书评数量
    ebook_price = scrapy.Field()  # 电子书价格
    ebook_url = scrapy.Field()  # 电子书链接
