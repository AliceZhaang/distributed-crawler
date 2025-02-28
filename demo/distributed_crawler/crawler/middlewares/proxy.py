import random
from scrapy import signals

class ProxyMiddleware:
    def __init__(self):
        self.proxies = []  # 这里需要填入您的代理IP池
        
    def process_request(self, request, spider):
        if self.proxies:
            proxy = random.choice(self.proxies)
            request.meta['proxy'] = proxy 