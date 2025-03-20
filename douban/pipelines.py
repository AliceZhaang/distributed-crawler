# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
from datetime import datetime
from itemadapter import ItemAdapter


class DoubanPipeline:
    def process_item(self, item, spider):
        return item


class BatchMongoPipeline:
    def __init__(self, mongo_uri, mongo_db, mongo_collection, batch_size=100, mongo_params=None):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.batch_size = batch_size
        self.mongo_params = mongo_params or {}
        self.items_buffer = []
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'douban'),
            mongo_collection=crawler.settings.get('MONGO_COLLECTION', 'books'),
            batch_size=crawler.settings.getint('MONGODB_BATCH_SIZE', 100),
            mongo_params=crawler.settings.get('MONGODB_PARAMS', {})
        )
        
    def open_spider(self, spider):
        try:
            # 连接到MongoDB路由服务器
            self.client = pymongo.MongoClient(self.mongo_uri, **self.mongo_params)
            self.db = self.client[self.mongo_db]
            self.collection = self.db[self.mongo_collection]
            
            # 确保分片键索引存在
            self.collection.create_index([('book_id', pymongo.ASCENDING)], unique=True)
            spider.logger.info('MongoDB分片集群连接成功')
        except Exception as e:
            spider.logger.error(f'MongoDB连接失败: {str(e)}')
            raise
        
    def process_item(self, item, spider):
        # 添加爬取时间
        if 'crawl_time' not in item:
            item['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        # 将item转换为字典并添加到缓冲区
        self.items_buffer.append(dict(ItemAdapter(item).asdict()))
        
        # 当缓冲区达到指定大小时执行批量写入
        if len(self.items_buffer) >= self.batch_size:
            self._write_to_mongo(spider)
        return item
    
    def _write_to_mongo(self, spider):
        if not self.items_buffer:
            return
            
        try:
            # 使用批量更新而不是插入，避免重复数据问题
            bulk_operations = []
            for item in self.items_buffer:
                bulk_operations.append(
                    pymongo.UpdateOne(
                        {'book_id': item['book_id']},
                        {'$set': item},
                        upsert=True
                    )
                )
            
            if bulk_operations:
                result = self.collection.bulk_write(bulk_operations, ordered=False)
                spider.logger.info(f"批量写入MongoDB: {len(bulk_operations)}条数据, "
                                  f"插入: {result.upserted_count}, 更新: {result.modified_count}")
        except pymongo.errors.BulkWriteError as e:
            # 处理批量写入错误，但不中断处理
            spider.logger.error(f"批量写入部分失败: {str(e)}")
            # 记录成功的操作数量
            if hasattr(e, 'details') and 'nInserted' in e.details:
                spider.logger.info(f"成功插入: {e.details.get('nInserted', 0)}, "
                                  f"成功更新: {e.details.get('nModified', 0)}")
        except Exception as e:
            spider.logger.error(f"批量写入错误: {str(e)}")
        
        # 清空缓冲区
        self.items_buffer = []
    
    def close_spider(self, spider):
        # 确保关闭爬虫时写入所有剩余数据
        self._write_to_mongo(spider)
        if self.client:
            self.client.close()
