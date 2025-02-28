import redis
from urllib.parse import urlparse
from bloom_filter import BloomFilter

class URLManager:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        self.bf = BloomFilter(max_elements=1000000, error_rate=0.001)
        
    def add_url(self, url, priority=0):
        """添加URL到队列"""
        if self._is_valid_url(url) and url not in self.bf:
            self.bf.add(url)
            self.redis_client.zadd('spider:urls:queue', {url: priority})
            return True
        return False
    
    def _is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False 