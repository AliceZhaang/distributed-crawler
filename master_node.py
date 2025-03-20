#!/usr/bin/env python
import redis
import time
import os
import json
import logging
from datetime import datetime
import pymongo
from douban.settings import MONGO_URI, MONGO_DATABASE
from douban.config import PROXY_POOL

# 配置日志
log_dir = os.environ.get("LOG_DIR", "./logs")  # 简化日志路径
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "master.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("master")

class MasterNode:
    def __init__(self):
        self.redis_host = os.environ.get("REDIS_HOST", "redis")
        self.redis_port = 6379
        self.redis_client = None
        self.worker_containers = []
        self.alert_threshold = 5  # 告警阈值（分钟）
        self.start_urls_key = "douban:book:start_urls"
    
    def connect_redis(self):
        """连接Redis服务"""
        max_retries = 30
        for i in range(max_retries):
            try:
                self.redis_client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("成功连接到Redis")
                break
            except redis.ConnectionError:
                logger.warning(f"等待Redis服务就绪... {i+1}/{max_retries}")
                time.sleep(1)
                if i == max_retries - 1:
                    logger.error("无法连接到Redis，退出")
                    raise

    def init_start_urls(self):
        """初始化起始URL"""
        # 清理旧的URL队列
        self.redis_client.delete(self.start_urls_key)
        
        # 添加豆瓣图书分类页面
        base_urls = [
            "https://book.douban.com/tag/"
        ]
        
        # 将URL添加到Redis队列
        for url in base_urls:
            self.redis_client.lpush(self.start_urls_key, url)
        
        url_count = self.redis_client.llen(self.start_urls_key)
        logger.info(f"成功添加{url_count}个起始URL到Redis队列")
        
        # 添加日志以确认键名
        logger.info(f"使用的Redis键名: {self.start_urls_key}")

    def check_mongodb(self):
        """检查MongoDB连接状态"""
        try:
            mongo_uri = os.environ.get("MONGO_URI", "mongodb://mongodb-router:27017")
            client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            logger.info("MongoDB连接成功")
            return True
        except Exception as e:
            logger.error(f"MongoDB连接失败: {str(e)}")
            return False

    def run(self):
        """运行主控节点"""
        try:
            # 连接Redis
            self.connect_redis()
            
            # 检查MongoDB
            mongodb_ready = False
            for i in range(30):
                if self.check_mongodb():
                    mongodb_ready = True
                    break
                logger.warning(f"等待MongoDB就绪... {i+1}/30")
                time.sleep(2)
            
            if not mongodb_ready:
                logger.error("MongoDB未就绪，但将继续执行")
            
            # 初始化起始URL
            self.init_start_urls()
            
            # 持续监控
            while True:
                time.sleep(60)  # 每分钟检查一次
                
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭...")
        except Exception as e:
            logger.error(f"发生错误: {e}")
            raise

if __name__ == "__main__":
    master = MasterNode()
    master.run()
