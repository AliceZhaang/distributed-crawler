BOT_NAME = 'distributed_crawler'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

# Redis设置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# MongoDB设置
MONGO_URI = 'mongodb://localhost:27017'
MONGO_DATABASE = 'crawler_db'

# 启用Redis调度器
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# 启用Redis管道
ITEM_PIPELINES = {
    'crawler.pipelines.MongoDBPipeline': 300,
    'scrapy_redis.pipelines.RedisPipeline': 400,
} 