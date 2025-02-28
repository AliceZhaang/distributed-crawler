from .base_spider import BaseSpider

class WorkerSpider(BaseSpider):
    name = 'worker'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 