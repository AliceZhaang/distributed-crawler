#!/usr/bin/env python
import os
import time
import redis
import logging
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 修改爬虫导入路径
from douban.spiders.book_spider import BookSpider

# 配置日志
node_id = os.environ.get("NODE_ID", "worker")
log_dir = os.environ.get("LOG_DIR", "./logs")  # 简化日志路径
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"{node_id}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            # 等待Redis和主控节点就绪
            redis_host = os.environ.get("REDIS_HOST", "redis")
            redis_port = 6379
            logger.info(f"连接到Redis: {redis_host}:{redis_port}")
            
            # 尝试连接Redis
            max_retries = 30
            for i in range(max_retries):
                try:
                    r = redis.Redis(
                        host=redis_host, 
                        port=redis_port, 
                        decode_responses=True,
                        socket_timeout=5
                    )
                    r.ping()
                    logger.info("Redis连接成功")
                    break
                except redis.ConnectionError as e:
                    logger.warning(f"等待Redis服务就绪... {i+1}/{max_retries}")
                    logger.debug(f"连接错误: {str(e)}")
                    time.sleep(1)
                    if i == max_retries - 1:
                        logger.error("无法连接到Redis，退出")
                        return
            
            key = "douban:book:start_urls"
            url_count = r.llen(key)
            if url_count > 0:
                urls = r.lrange(key, 0, -1)
                logger.info(f"检测到{url_count}个起始URL: {urls}，开始爬取...")
            else:
                logger.info("未检测到起始URL，将由爬虫自行处理")
            
            # 获取项目设置并设置Redis配置
            settings = get_project_settings()
            
            # 直接设置Scrapy-Redis所需的配置
            settings.set('REDIS_HOST', redis_host)
            settings.set('REDIS_PORT', redis_port)
            settings.set('REDIS_URL', f"redis://{redis_host}:{redis_port}")
            
            # 修改 SPIDER_MODULES 设置
            settings.set('SPIDER_MODULES', ["douban.spiders"])
            
            # 确保自定义中间件和管道被加载
            logger.info("从settings.py加载完整配置")
            
            # 打印当前配置，用于调试
            logger.info(f"当前下载器中间件: {settings.get('DOWNLOADER_MIDDLEWARES')}")
            logger.info(f"当前管道配置: {settings.get('ITEM_PIPELINES')}")
            
            # 确保代理中间件被启用
            if settings.getbool('PROXY_ENABLED'):
                logger.info("代理中间件已启用")
            else:
                logger.warning("代理中间件未启用，请检查settings.py中的PROXY_ENABLED设置")
            
            # 创建爬虫进程
            logger.info("启动爬虫进程...")
            process = CrawlerProcess(settings)
            process.crawl(BookSpider)
            process.start()
            
            # 如果执行到这里，说明爬虫正常结束
            logger.info("爬虫进程正常结束")
            break
            
        except Exception as e:
            retry_count += 1
            logger.error(f"爬虫运行出错 (尝试 {retry_count}/{max_retries}): {str(e)}", exc_info=True)
            if retry_count < max_retries:
                wait_time = 60 * retry_count  # 递增等待时间
                logger.info(f"将在 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                logger.critical("达到最大重试次数，退出程序")
                raise

if __name__ == "__main__":
    main()