from .spiders.base_spider import BaseSpider
from .middlewares.ua import RandomUserAgentMiddleware
from .middlewares.proxy import ProxyMiddleware
from .pipelines import MongoDBPipeline, ElasticsearchPipeline 