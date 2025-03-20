# Scrapy settings for douban project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

# 日志配置
import os
from datetime import datetime


BOT_NAME = "douban"


SPIDER_MODULES = ["douban.spiders"]
NEWSPIDER_MODULE = "douban.spiders"

# User-Agent 设置
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# 并发请求设置
# 增加并发请求数
CONCURRENT_REQUESTS = 1  
CONCURRENT_REQUESTS_PER_DOMAIN = 1 

# 适当减少下载延迟
DOWNLOAD_DELAY = 5  
RANDOMIZE_DOWNLOAD_DELAY = True
RANDOM_DELAY_MIN = 4  
RANDOM_DELAY_MAX = 10 


# 错误处理配置
HTTPERROR_ALLOWED_CODES = [404, 403]  # 允许处理这些状态码
RETRY_ENABLED = True
RETRY_TIMES = 3  # 重试次数
RETRY_HTTP_CODES = [403, 408, 429, 500, 502, 503, 504, 404]  # 需要重试的状态码
RETRY_DELAY = 10

# 超时设置
DOWNLOAD_TIMEOUT = 60

# 请求头设置
# 不再使用固定请求头，改为使用随机请求头中间件
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

# 请求头模板池，供随机请求头中间件使用
REQUEST_HEADERS_TEMPLATES = [
    {
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Host': 'book.douban.com',
        'Referer': 'https://book.douban.com',
    },
    {
        'Sec-Ch-Ua': '"Microsoft Edge";v="122", "Chromium";v="122", "Not=A?Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Host': 'book.douban.com',
        'Referer': 'https://www.douban.com',
    },
    {
        'Sec-Ch-Ua': '"Not.A/Brand";v="8", "Chromium";v="121", "Google Chrome";v="121"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Host': 'book.douban.com',
        'Referer': 'https://search.douban.com',
    },
    {
        'Sec-Ch-Ua': '"Firefox";v="123", "Not;A=Brand";v="8"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Linux"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-site',
        'Host': 'book.douban.com',
        'Referer': 'https://movie.douban.com',
    },
    {
        'Sec-Ch-Ua': '"Safari";v="17", "Not;A=Brand";v="8", "Chromium";v="120"',
        'Sec-Ch-Ua-Mobile': '?1',
        'Sec-Ch-Ua-Platform': '"iOS"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Host': 'book.douban.com',
        'Referer': 'https://book.douban.com/tag/',
    },
]

# 代理设置
PROXY_ENABLED = True
PROXY_RETRY_TIMES = 3

# 合并后的下载器中间件配置
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': None,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None, 
    'douban.middlewares.DrissionPageMiddleware': 500,
}

SPIDER_MIDDLEWARES = {
    'douban.middlewares.DoubanSpiderMiddleware': 543,
}

ITEM_PIPELINES = {
    'douban.pipelines.BatchMongoPipeline': 300,
}

DRISSIONPAGE_SETTINGS = {
    'browser': 'chrome',  
    'headless': True,     
    'timeout': 30,        
    'proxy': None,        
    'download_path': 'downloads',
    'cookies': [
        # 第一个账号
        {
            'domain': '.douban.com',
            'name': 'bid',
            'value': 'jyVT9L6neGQ',
            'path': '/'
        },
        {
            'domain': '.douban.com',
            'name': '_vwo_uuid_v2',
            'value': 'D5386F810C9AA297E6EBF9B11C429704D|d8f90670a9e24d15ae6634d1243d3160',
            'path': '/'
        },
        {
            'domain': '.douban.com',
            'name': 'dbcl2',
            'value': '158821927:FePkbUye6IM',
            'path': '/'
        },
        {
            'domain': '.douban.com',
            'name': 'ck',
            'value': 'jPZZ',
            'path': '/'
        },
        # 第二个账号
        {
            'domain': '.douban.com',
            'name': 'dbcl2',
            'value': '130675800:fnIOujWhk5Q',
            'path': '/'
        },
        {
            'domain': '.douban.com',
            'name': 'ck',
            'value': 'ZnzW',
            'path': '/'
        },
        {
            'domain': '.douban.com',
            'name': 'frodotk_db',
            'value': '3706c0caec20207aa5144260c460616e',
            'path': '/'
        },
        # 第三个账号
        {
            'domain': '.douban.com',
            'name': 'dbcl2',
            'value': '287772298:GqjbInQrewQ',
            'path': '/'
        },
        {
            'domain': '.douban.com',
            'name': 'ck',
            'value': '5x75',
            'path': '/'
        },
        {
            'domain': '.douban.com',
            'name': 'frodotk_db',
            'value': 'b996d07871aad3392cc47169550079ab',
            'path': '/'
        }
    ],
    'save_cookies': True,
    'cookies_dir': 'cookies'
}

# Cookie设置
COOKIES_ENABLED = True
COOKIES_DEBUG = True

# 启用自动限速
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.2
AUTOTHROTTLE_DEBUG = True


# MongoDB连接设置
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongodb-router:27017")

# # 本地开发时使用
# MONGO_URI = "mongodb://localhost:27017"

MONGO_DATABASE = "douban"
MONGO_COLLECTION = "books"
MONGODB_PARAMS = {
    'maxPoolSize': 100,
    'minPoolSize': 20,
    'maxIdleTimeMS': 10000,
    'waitQueueTimeoutMS': 5000,
    'retryWrites': True,
}

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Scrapy-Redis配置 
# 启用Redis调度器
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# 确保所有爬虫通过Redis去重
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# 将爬取到的项目存储到Redis中
SCRAPY_REDIS_ITEMS_KEY = "%(spider)s:items"

# 选择持久化模式：
# 方案1：支持断点续爬（推荐）
SCHEDULER_PERSIST = True  # 持久化请求队列和指纹集合
SCHEDULER_FLUSH_ON_START = False  # 不清空Redis队列

# 方案2：每次重新爬取
# SCHEDULER_PERSIST = False  # 不持久化
# SCHEDULER_FLUSH_ON_START = True  # 每次启动时清空队列

# 使用优先级队列
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.SpiderPriorityQueue'

# 仅在开发调试时启用
DUPEFILTER_DEBUG = False
# 每次启动时清空去重集合
SCHEDULER_FLUSH_ON_START = False


# Redis连接设置
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")  # 使用Docker服务名
# REDIS_HOST = '127.0.0.1'  # 本地开发时使用
REDIS_PORT = 6379
REDIS_PARAMS = {
    'socket_timeout': 30,
    'socket_connect_timeout': 30,
    'retry_on_timeout': True,
    'encoding': 'utf-8',
    'password': os.environ.get('REDIS_PASSWORD', None),  # 从环境变量获取密码
    'db': 0,  # 添加默认数据库
    'decode_responses': False  # 对于Scrapy-Redis，不要解码响应
}

# 确保Scrapy-Redis使用正确的Redis配置
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"


LOG_LEVEL = 'INFO'  # 只显示 INFO 级别以上的日志
LOG_ENABLED = True
LOG_ENCODING = 'utf-8'
# 确保日志目录存在
# 修改日志配置，使用结构化的日志目录
log_dir = os.path.join(os.getcwd(), 'logs', 'spider', 'scrapy')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
LOG_FILE = os.path.join(log_dir, f'douban_spider_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# 关闭一些不必要的日志
LOG_STDOUT = False
HTTPCACHE_ENABLED = False

# 禁用证书验证
DOWNLOADER_CLIENT_TLS_VERIFY = False

# 设置新的请求指纹实现
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
