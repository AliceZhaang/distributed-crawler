// 等待配置服务器和分片服务器准备就绪
sleep(15000);

// 添加分片到集群
sh.addShard("shardrs/mongodb-shard:27018");

// 启用数据库分片
sh.enableSharding("douban");

// 创建索引
db = db.getSiblingDB('douban');
db.books.createIndex({ book_id: 1 }, { unique: true });

// 对集合进行分片
sh.shardCollection("douban.books", { book_id: 1 });

print("MongoDB 路由器初始化完成");