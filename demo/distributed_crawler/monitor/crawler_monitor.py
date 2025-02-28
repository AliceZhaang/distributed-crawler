from prometheus_client import start_http_server, Counter, Gauge
import time

class CrawlerMonitor:
    def __init__(self, port=8000):
        self.requests_total = Counter('crawler_requests_total', 'Total requests made')
        self.requests_failed = Counter('crawler_requests_failed', 'Failed requests')
        self.items_scraped = Counter('crawler_items_scraped', 'Items scraped')
        self.active_spiders = Gauge('crawler_active_spiders', 'Number of active spiders')
        
        # 启动Prometheus metrics服务器
        start_http_server(port)
    
    def record_request(self):
        self.requests_total.inc()
    
    def record_failure(self):
        self.requests_failed.inc()
    
    def record_item(self):
        self.items_scraped.inc()
    
    def update_spider_count(self, count):
        self.active_spiders.set(count) 