// 初始化配置服务器副本集
rs.initiate({
  _id: "configrs",
  configsvr: true,
  members: [{ _id: 0, host: "mongodb-config:27019" }]
});

// 等待副本集初始化完成
let status;
do {
  sleep(1000);
  status = rs.status();
  print("等待副本集初始化完成...");
} while (status.ok !== 1);

print("配置服务器副本集初始化完成");

// 初始化分片副本集
db = db.getSiblingDB('admin');
db.runCommand({
  _id: "shardrs",
  shardsvr: true,
  members: [{ _id: 0, host: "mongodb-shard:27018" }]
});

print("分片服务器副本集初始化完成");