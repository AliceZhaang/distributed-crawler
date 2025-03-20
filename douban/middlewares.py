# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import random
import sys  
from fake_useragent import UserAgent
import time
import os
import string  
import logging 
from DrissionPage import ChromiumPage
from DrissionPage import ChromiumOptions
from itemadapter import is_item, ItemAdapter
from douban.config import DOUBAN_COOKIES_POOL, NODE_CONFIGS  # 修改这行，直接从 config 导入 NODE_CONFIGS
from selenium import webdriver
from scrapy.http import HtmlResponse
from scrapy.utils.project import get_project_settings


class RandomDelayMiddleware:
    def __init__(self, delay_min=1, delay_max=3):
        self.delay_min = delay_min
        self.delay_max = delay_max

    @classmethod
    def from_crawler(cls, crawler):
        delay_min = crawler.settings.getfloat('RANDOM_DELAY_MIN', 1)
        delay_max = crawler.settings.getfloat('RANDOM_DELAY_MAX', 3)
        return cls(delay_min, delay_max)

    def process_request(self, request, spider):
        # 生成随机延迟
        delay = random.uniform(self.delay_min, self.delay_max)
        spider.logger.debug(f'随机延迟: {delay}秒')
        time.sleep(delay)

class DrissionPageMiddleware:
    def __init__(self):
        self.browser = None
        self.logger = logging.getLogger('DrissionPage')
        self.settings = get_project_settings()
        self.node_name = os.environ.get('SPIDER_NODE', 'master')
        self.init_browser()

    def init_browser(self):
        """初始化浏览器"""
        try:
            options = ChromiumOptions()
            options.set_paths(browser_path=None)
            
            options.set_argument('--headless=new')
            options.set_argument('--no-sandbox')
            options.set_argument('--disable-gpu')
            options.set_argument('--disable-dev-shm-usage')
            options.set_argument('--disable-extensions')
            
            self.browser = ChromiumPage(options)
            version = self.browser.run_cdp('Browser.getVersion')
            self.logger.info(f"浏览器版本信息: {version}")
            
            # 启用网络功能并清除所有 Cookie
            self.browser.run_cdp('Network.enable')
            self.browser.run_cdp('Network.clearBrowserCookies')
            
            self._add_cookies()
            self.logger.info(f"节点[{self.node_name}]浏览器初始化成功")
        except Exception as e:
            self.logger.error(f"浏览器初始化失败: {str(e)}")
            self.logger.exception(e)

    def _add_cookies(self):
        """添加 Cookie"""
        try:
            # 获取当前节点的 Cookie
            node_config = NODE_CONFIGS.get(self.node_name, {'cookie_start_index': 0, 'cookie_end_index': 0})
            start_idx = node_config['cookie_start_index']
            end_idx = node_config['cookie_end_index']
            cookies = DOUBAN_COOKIES_POOL[start_idx:end_idx + 1]
            
            for cookie_dict in cookies:
                # 将配置中的 Cookie 转换为浏览器可用的格式
                for name, value in cookie_dict.items():
                    js_code = f'''
                    document.cookie = "{name}={value}; \
                    domain=.douban.com; \
                    path=/";
                    '''
                    self.browser.run_js(js_code)
            
            # 验证 Cookie 设置
            cookies_result = self.browser.run_cdp('Network.getAllCookies')
            current_cookies = cookies_result.get('cookies', [])
            self.logger.info(f"Cookie设置完成，当前数量: {len(current_cookies)}")
            
        except Exception as e:
            self.logger.error(f"设置Cookie失败: {str(e)}")
            self.logger.exception(e)

    def process_request(self, request, spider):
        """处理请求"""
        try:
            # 随机延迟
            delay = random.uniform(3, 8)
            time.sleep(delay)
            
            # 访问页面
            self.browser.get(request.url)
            time.sleep(2)
            
            # 检查重定向
            current_url = self.browser.url
            if 'login' in current_url or 'sec.douban.com' in current_url:
                spider.logger.warning(f"被重定向到登录页: {current_url}")
                self._add_cookies()  # 重新设置 Cookie
                return None
            
            # 获取页面内容
            html = self.browser.html
            if not html:
                spider.logger.error("获取页面内容失败")
                return None
                
            return HtmlResponse(
                url=request.url,
                body=html.encode(),
                encoding='utf-8',
                request=request
            )
        except Exception as e:
            spider.logger.error(f'DrissionPage处理失败: {str(e)}')
            return None

    def spider_closed(self, spider):
        """关闭浏览器"""
        if self.browser:
            self.browser.quit()
            self.logger.info("浏览器已关闭")

class DistributedProxyMiddleware:
    def __init__(self):
        self.proxies = []
        self.logger = logging.getLogger('proxy')
        self.node_id = os.environ.get('NODE_ID', 'master')

    def spider_opened(self, spider):
        """加载代理配置"""
        try:
            self._load_proxies(spider)
            self.logger.info(f'从配置文件加载了{len(self.proxies)}个代理')
        except Exception as e:
            self.logger.error(f'加载代理配置失败: {e}')

    def _load_proxies(self, spider):
        """从配置文件加载代理池"""
        try:
            from douban.config import PROXY_POOL
            self.proxies = PROXY_POOL.get(self.node_id, [])
            spider.logger.info(f"节点[{self.node_id}]加载了{len(self.proxies)}个代理")
        except ImportError:
            spider.logger.error("无法从配置文件加载代理")
            self.proxies = []

    def _get_node_proxies(self):
        """获取当前节点的代理列表"""
        return self.proxies

    def process_request(self, request, spider):
        """处理每个请求"""
        if 'proxy' in request.meta:
            return None
            
        proxies = self._get_node_proxies()
        if not proxies:
            spider.logger.warning(f"节点[{self.node_id}]没有可用代理")
            return None
            
        proxy = random.choice(proxies)
        request.meta['proxy'] = proxy
        spider.logger.info(f"节点[{self.node_id}]使用代理: {proxy}")
        return None

class DistributedCookieMiddleware:
    """分布式Cookie管理中间件"""
    
    def __init__(self, settings):
        self.cookies_pool = DOUBAN_COOKIES_POOL
        self.node_id = os.environ.get('NODE_ID', 'master')
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
        
    def process_request(self, request, spider):
        """为每个请求添加随机Cookie"""
        if not self.cookies_pool:
            spider.logger.warning("Cookie池为空")
            return None
            
        # 随机选择一个Cookie
        cookie = random.choice(self.cookies_pool)
        
        # 更新请求的Cookie
        request.cookies.update(cookie)
        
        # 同时更新Cookie头
        cookie_str = '; '.join([f"{k}={v}" for k, v in cookie.items()])
        request.headers['Cookie'] = cookie_str
        
        spider.logger.debug(f"节点[{self.node_id}]使用Cookie: {cookie_str[:50]}...")

class DoubanSpiderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class CustomHeadersMiddleware:
    def process_request(self, request, spider):
        request.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1'
        })
