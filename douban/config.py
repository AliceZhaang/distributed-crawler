# Douban Cookies 配置池
DOUBAN_COOKIES_POOL = [
    {
        'cookie': 'your_cookie_1',
        'user_id': 'your_user_id_1',
        'user_name': 'your_user_name_1'
    },
]

# 浏览器 User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'

# 代理IP池配置
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

# Cookie 轮换配置
COOKIE_ROTATE_INTERVAL = 300  # 5分钟轮换一次Cookie
COOKIE_FAIL_THRESHOLD = 3     # Cookie失败3次后更换

# 更新节点配置
NODE_CONFIGS = {
    'master': {
        'cookie_start_index': 0,
        'cookie_end_index': 0,    # 使用前3个Cookie
    },
    'worker1': {
        'cookie_start_index': 1,
        'cookie_end_index': 1,    # 使用中间3个Cookie
    },
    'worker2': {
        'cookie_start_index': 2,
        'cookie_end_index': 2,    # 使用后3个Cookie
    }
}



# 代理服务配置
PROXY_SERVICE_URL = None  # 如果使用代理服务API，在这里配置URL

# Redis密码（如果有）
REDIS_PASSWORD = None  # 建议从环境变量获取: os.environ.get('REDIS_PASSWORD', None)
