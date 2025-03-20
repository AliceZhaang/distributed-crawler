from scrapy_redis.spiders import RedisSpider
from scrapy import Request
import json

class BaseSpider(RedisSpider):
    name = 'base_spider'
    redis_key = 'spider:urls'
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 1,
    }
    
    def parse(self, response):
        try:
            # 基础解析逻辑
            item = {
                'url': response.url,
                'title': response.css('title::text').get(),
                'content': ' '.join(response.css('p::text').getall()),
                'links': response.css('a::attr(href)').getall()
            }
            
            # 提取新的URL并加入队列
            for link in item['links']:
                yield Request(url=response.urljoin(link), callback=self.parse)
                
            yield item
            
        except Exception as e:
            self.logger.error(f'Parse error on {response.url}: {str(e)}') 