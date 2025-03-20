import os
import sys
import time
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from douban.spiders.book_spider import BookSpider
import redis
import pymongo
import logging
logging.getLogger('pymongo').setLevel(logging.WARNING)

def check_services():
    """检查必要服务是否可用"""
    services_ok = True
    
    # 检查 Redis
    try:
        redis_cli = redis.Redis(host='localhost', port=6379)
        redis_cli.ping()
    except Exception as e:
        print(f"Redis 连接失败: {e}")
        services_ok = False
    
    # 检查 MongoDB
    try:
        client = pymongo.MongoClient('mongodb://localhost:27017/')
        client.admin.command('ping')
    except Exception as e:
        print(f"MongoDB 连接失败: {e}")
        services_ok = False
    
    return services_ok

def run_spider():
    # 检查服务
    if not check_services():
        print("必要服务未启动，请先启动 Redis 和 MongoDB")
        return

    # 设置环境变量
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['MONGO_URI'] = 'mongodb://localhost:27017'
    
    # 获取项目设置
    settings = get_project_settings()
    
    # 添加日志配置
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'spider', 'scrapy')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'douban_spider_{time.strftime("%Y%m%d_%H%M%S")}.log')
    settings.set('LOG_FILE', log_file)
    settings.set('LOG_LEVEL', 'DEBUG')
    
    # 修改部分设置以适应本地环境
    settings.set('LOG_LEVEL', 'DEBUG')
    settings.set('CONCURRENT_REQUESTS', 1)
    settings.set('DOWNLOAD_DELAY', 5)
    
    try:
        # 创建爬虫进程
        process = CrawlerProcess(settings)
        
        # 添加起始URL到Redis
        redis_cli = redis.Redis(host='localhost', port=6379, decode_responses=True)
        redis_cli.lpush('douban:book:start_urls', 'https://book.douban.com/tag/')
        
        # 运行爬虫
        process.crawl(BookSpider)
        process.start()
    except Exception as e:
        print(f"爬虫运行出错: {e}")

if __name__ == '__main__':
    run_spider()