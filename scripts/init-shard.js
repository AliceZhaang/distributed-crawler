// 初始化分片副本集
rs.initiate({
  _id: "shardrs",
  members: [{ _id: 0, host: "mongodb-shard:27018" }]
});

// 等待副本集初始化完成
let status;
do {
  sleep(1000);
  status = rs.status();
  print("等待分片副本集初始化完成...");
} while (status.ok !== 1);

print("分片副本集初始化完成");