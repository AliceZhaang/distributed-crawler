import pymongo
from datetime import datetime
from pprint import pprint

# 连接MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['douban']
collection = db['books']

def print_stats():
    """打印统计信息"""
    total = collection.count_documents({})
    print(f"\n总计爬取图书: {total} 本")
    
    # 按评分排序
    top_rated = collection.find().sort('rating_score', -1).limit(5)
    print("\n评分最高的5本书:")
    for book in top_rated:
        print(f"{book['title']} - 评分: {book['rating_score']} ({book['rating_people']}人评价)")
    
    # 最近爬取
    recent = collection.find().sort('crawl_time', -1).limit(5)
    print("\n最近爬取的5本书:")
    for book in recent:
        print(f"{book['title']} - 爬取时间: {book['crawl_time']}")

def search_book(keyword):
    """搜索图书"""
    query = {'title': {'$regex': keyword, '$options': 'i'}}
    results = collection.find(query)
    print(f"\n包含关键词 '{keyword}' 的图书:")
    for book in results:
        print(f"\n书名: {book['title']}")
        print(f"作者: {book['author']}")
        print(f"评分: {book['rating_score']} ({book['rating_people']}人评价)")
        print(f"标签: {', '.join(book['js_tags'])}")

if __name__ == '__main__':
    print_stats()
    
    # 搜索示例
    keyword = input("\n请输入要搜索的书名关键词(直接回车跳过): ")
    if keyword:
        search_book(keyword)