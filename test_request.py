#!/usr/bin/env python
import requests
import logging
import sys
import os
import time
import random

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("proxy_test")

def get_random_ua():
    """获取随机User-Agent"""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
    ]
    return random.choice(user_agents)

def test_proxy(proxy):
    """测试单个代理IP的可用性并返回页面源码"""
    test_url = 'https://book.douban.com/tag/'
    headers = {
        'User-Agent': get_random_ua(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Host': 'book.douban.com',
        'Referer': 'https://www.douban.com/',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-site',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        logger.info(f"正在测试代理: {proxy}")
        response = requests.get(
            test_url,
            proxies={'http': proxy, 'https': proxy},
            timeout=10,
            headers=headers,
            verify=False  # 忽略SSL证书验证
        )
        
        # 保存响应内容到文件
        with open('debug_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        if response.status_code == 200:
            logger.info(f"✅ 代理可用: {proxy}")
            logger.info(f"页面大小: {len(response.text)} 字节")
            logger.info(f"响应已保存到 debug_response.html")
            return True
        else:
            logger.warning(f"❌ 代理响应异常: {proxy}, 状态码: {response.status_code}")
            logger.info(f"错误响应已保存到 debug_response.html")
            return False
    except Exception as e:
        logger.error(f"❌ 代理测试失败: {proxy}, 错误: {str(e)}")
        return False

def main():
    """主函数"""
    try:
        # 导入代理配置
        from douban.config import PROXY_POOL
        
        if not PROXY_POOL:
            logger.error("代理池为空")
            return
        
        logger.info(f"开始测试 {len(PROXY_POOL)} 个代理IP")
        working_proxies = []
        
        for index, proxy in enumerate(PROXY_POOL, 1):
            logger.info(f"测试进度: [{index}/{len(PROXY_POOL)}]")
            if test_proxy(proxy):
                working_proxies.append(proxy)
                # 找到可用代理后立即退出
                break
            time.sleep(2)  # 延迟避免请求过快
        
        # 输出测试结果统计
        logger.info("\n==== 测试结果统计 ====")
        logger.info(f"总共测试代理: {len(PROXY_POOL)} 个")
        logger.info(f"可用代理数量: {len(working_proxies)} 个")
        logger.info(f"可用率: {(len(working_proxies)/len(PROXY_POOL))*100:.1f}%")
        
        if working_proxies:
            logger.info("\n可用代理列表:")
            for i, proxy in enumerate(working_proxies, 1):
                logger.info(f"{i}. {proxy}")
        
    except ImportError as e:
        logger.error(f"导入代理配置失败: {e}")
        return

if __name__ == "__main__":
    # 禁用 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()