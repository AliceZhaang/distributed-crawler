from scrapy.exceptions import DropItem
import pymongo
from elasticsearch import Elasticsearch

class MongoDBPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spider):
        collection = self.db[spider.name]
        collection.insert_one(dict(item))
        return item

    def close_spider(self, spider):
        self.client.close()

class ElasticsearchPipeline:
    def __init__(self, es_hosts):
        self.es_hosts = es_hosts

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            es_hosts=crawler.settings.get('ES_HOSTS')
        )

    def open_spider(self, spider):
        self.es = Elasticsearch(self.es_hosts)

    def process_item(self, item, spider):
        self.es.index(
            index=spider.name,
            body=dict(item)
        )
        return item 