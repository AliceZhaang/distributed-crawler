# 简易分布式爬虫系统

## 项目介绍

这是一个基于Docker的scrapy-redis分布式爬虫系统，专门用于爬取豆瓣图书信息。系统采用了主从架构，使用Redis作为任务队列，MongoDB分片集群作为数据存储，实现了高效、可扩展的分布式爬虫功能。

### 主要特点

- **分布式架构**：采用主从架构，支持多个爬虫节点并行工作
- **容器化部署**：基于Docker和Docker Compose，一键部署整个系统
- **数据持久化**：使用MongoDB分片集群存储数据，支持大规模数据存储
- **任务调度**：基于Redis的分布式任务队列，实现任务的均衡分配
- **反爬处理**：内置多种反爬策略，包括随机User-Agent、Cookie池、代理IP等
- **自动重试**：遇到错误自动重试，提高爬取成功率
- **日志管理**：完善的日志记录系统，方便问题排查

## 系统架构

```
+----------------+     +----------------+     +----------------+
|                |     |                |     |                |
|  Master Node   |     |   Worker 1     |     |   Worker 2     |
|                |     |                |     |                |
+-------+--------+     +-------+--------+     +-------+--------+
        |                      |                      |
        v                      v                      v
+-------+--------------------------------------------+--------+
|                                                             |
|                         Redis Queue                         |
|                                                             |
+------------------------------+------------------------------+
                               |
                               v
+------------------------------+------------------------------+
|                                                             |
|                     MongoDB Sharded Cluster                 |
|                                                             |
+-------------------------------------------------------------+
```

### 组件说明

- **Master Node**：主控节点，负责初始化爬虫任务，监控系统状态
- **Worker Nodes**：工作节点，执行实际的爬取任务
- **Redis**：分布式任务队列，存储待爬取的URL
- **MongoDB**：分片集群，用于存储爬取的数据
  - Config Server：配置服务器，存储集群元数据
  - Shard Server：分片服务器，存储实际数据
  - Router：路由服务器，负责请求路由

## 环境要求

- Docker 和 Docker Compose
- Windows 操作系统（支持bat脚本）
- 网络连接（用于访问网站）

## 快速开始

### 部署系统

1. 克隆项目到本地

2. 运行部署脚本

```bash
douban.bat deploy
```

这将执行以下操作：
- 构建所有服务的Docker镜像
- 启动MongoDB配置服务器和分片服务器
- 初始化MongoDB集群
- 启动Redis服务

### 启动爬虫

```bash
douban.bat spider
```

这将启动主控节点和工作节点，开始爬取豆瓣图书数据。

### 查看系统状态

```bash
docker-compose ps
```

### 停止系统

```bash
douban.bat stop
```

## 数据查询

系统提供了简单的数据查询脚本：

```bash
python query_data.py
```

该脚本可以：
- 显示爬取的图书总数
- 显示评分最高的5本书
- 显示最近爬取的5本书
- 支持按关键词搜索图书

## 系统管理

### 清理数据

```bash
douban.bat clean
```

提供以下清理选项：
- 清理所有数据
- 只清理MongoDB数据
- 只清理Redis数据
- 清理日志文件
- 清理爬虫状态文件

## 项目结构

```
├── Dockerfile.master      # 主节点Docker构建文件
├── Dockerfile.worker      # 工作节点Docker构建文件
├── docker-compose.yml     # Docker Compose配置文件
├── douban.bat             # 系统控制脚本
├── douban/                # 爬虫核心代码
│   ├── __init__.py
│   ├── config.py          # 配置文件
│   ├── items.py           # 数据项定义
│   ├── middlewares.py     # 中间件
│   ├── pipelines.py       # 数据处理管道
│   ├── settings.py        # 爬虫设置
│   └── spiders/           # 爬虫实现
│       ├── __init__.py
│       └── book_spider.py # 图书爬虫
├── master_node.py         # 主节点实现
├── query_data.py          # 数据查询脚本
├── requirements.txt       # 依赖列表
├── scrapy.cfg             # Scrapy配置
├── scripts/               # MongoDB初始化脚本
├── stop.bat               # 快速停止脚本
└── worker_node.py         # 工作节点实现
```

## 配置说明

### 代理配置

在`douban/config.py`中配置代理IP池：

```python
PROXY_POOL = {
    'master': [
        'http://host.docker.internal:7890',
    ],
    'worker1': [
        'http://host.docker.internal:7890',
    ],
    'worker2': [
        'http://host.docker.internal:7890',
    ]
}
```

### Cookie配置

在`douban/config.py`中配置Cookie池：

```python
DOUBAN_COOKIES_POOL = [
    {
        'bid': 'xxx',
        'dbcl2': 'xxx',
        # 其他Cookie字段
    },
    # 更多Cookie
]
```

### 爬虫设置

在`douban/settings.py`中配置爬虫参数：

```python
# 并发请求设置
CONCURRENT_REQUESTS = 1  
CONCURRENT_REQUESTS_PER_DOMAIN = 1 

# 下载延迟
DOWNLOAD_DELAY = 5  
RANDOMIZE_DOWNLOAD_DELAY = True
```

## 注意事项

1. 请遵守豆瓣网站的robots.txt规则和使用条款
2. 适当调整爬取速度，避免对目标网站造成过大压力
3. 定期备份重要数据
4. 如遇到反爬措施，可以调整代理设置和Cookie池

## 故障排除

1. 如果爬虫无法启动，检查Redis和MongoDB服务是否正常运行
2. 如果爬取速度过慢，可以适当增加工作节点数量
3. 如果遇到大量反爬，可以增加代理IP和Cookie数量
4. 查看日志文件（logs目录）以获取详细错误信息

