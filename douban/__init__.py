# 导入配置模块，使其可以被其他模块访问
from . import config
from . import middlewares
from . import pipelines
from . import items
from .spiders.book_spider import BookSpider
from .items import BookItem
from .pipelines import BatchMongoPipeline

__all__ = [
    'BookSpider',
    'BookItem',
    'BatchMongoPipeline',
    'DOUBAN_COOKIES_POOL',
    'PROXY_POOL',
    'REDIS_PASSWORD'
]

# 导出常用配置变量，方便直接导入
from .config import DOUBAN_COOKIES_POOL, PROXY_POOL, REDIS_PASSWORD

# 设置版本信息
__version__ = '1.0.0'

