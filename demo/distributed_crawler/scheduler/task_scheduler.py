import redis
from urllib.parse import urlparse
from scrapy_redis.scheduler import Scheduler
from scrapy.utils.misc import load_object
from scrapy_redis.queue import PriorityQueue
from bloom_filter import BloomFilter
import time

class TaskScheduler:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
    def add_url(self, url):
        """添加URL到Redis队列"""
        if self._is_valid_url(url):
            self.redis_client.lpush('spider:urls', url)
            return True
        return False
    
    def _is_valid_url(self, url):
        """验证URL是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

class CustomScheduler(Scheduler):
    def __init__(self, server, persist, queue_key, queue_cls, dupefilter_key, dupefilter_cls, *args, **kwargs):
        super().__init__(server, persist, queue_key, queue_cls, dupefilter_key, dupefilter_cls, *args, **kwargs)
        self.bf = BloomFilter(max_elements=1000000, error_rate=0.001)
        
    def enqueue_request(self, request):
        # 使用布隆过滤器进行URL去重
        if request.url not in self.bf:
            self.bf.add(request.url)
            return super().enqueue_request(request)
        return False

    def next_request(self):
        # 实现优先级调度
        request = super().next_request()
        if request:
            # 添加请求追踪
            request.meta['schedule_time'] = time.time()
        return request 