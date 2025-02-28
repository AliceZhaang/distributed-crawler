import dns.resolver
import time
from threading import Lock

class DNSResolver:
    def __init__(self, cache_size=1000, cache_ttl=3600):
        self.cache = {}
        self.cache_size = cache_size
        self.cache_ttl = cache_ttl
        self.lock = Lock()
        
    def resolve(self, domain):
        with self.lock:
            if domain in self.cache:
                record = self.cache[domain]
                if time.time() - record['timestamp'] < self.cache_ttl:
                    return record['ip']
                
            try:
                answers = dns.resolver.resolve(domain, 'A')
                ip = str(answers[0])
                self.cache[domain] = {
                    'ip': ip,
                    'timestamp': time.time()
                }
                return ip
            except Exception as e:
                return None 