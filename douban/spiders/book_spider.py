import scrapy
import re
import time
import random
import string
from urllib.parse import urljoin  
from ..items import BookItem
from datetime import datetime
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError, TCPTimedOutError
from scrapy import signals
from scrapy_redis.spiders import RedisSpider
from ..config import DOUBAN_COOKIES_POOL

class BookSpider(RedisSpider):
    name = 'book'
    allowed_domains = ['book.douban.com']
    redis_key = 'douban:book:start_urls'  # Redis键名
    
    # 删除 start_urls
    # start_urls = ['https://book.douban.com/tag/']
    
    def __init__(self, *args, **kwargs):
        super(BookSpider, self).__init__(*args, **kwargs)
        # 图书详情页URL正则
        self.detail_pattern = re.compile(r'https://book.douban.com/subject/(\d+)/')
        self.retry_count = {}
        self.max_retries = 3
        # 直接使用上面导入的Cookie池
        try:
            self.cookies_pool = DOUBAN_COOKIES_POOL
            self.logger.info(f"已加载 {len(self.cookies_pool)} 个Cookie")
        except Exception as e:
            self.logger.error(f"加载Cookie失败: {str(e)}")
            self.cookies_pool = []

    def _generate_bid(self):
        """生成随机bid"""
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(11))  

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """注册信号"""
        spider = super(BookSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider
        
    def spider_closed(self):
        # DrissionPage 中间件会处理浏览器关闭
        pass

    def check_anti_spider(self, response):
        """检查是否被反爬"""
        try:
        # 先解码响应内容
            if response.headers.get('Content-Encoding') == b'br':
                import brotli
                text = brotli.decompress(response.body).decode()
            else:
                text = response.text
            
            # 检查反爬标记
            if '验证码' in text or '人机验证' in text:
                self.logger.warning(f"触发反爬: {response.url}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"检查反爬发生错误: {e}")
            return False

    def handle_anti_spider(self, response):
        """处理反爬 - 使用更多的请求头和代理策略"""
        url = response.url
        if url not in self.retry_count:
            self.retry_count[url] = 0
        
        if self.retry_count[url] >= self.max_retries:
            self.logger.error(f"达到最大重试次数: {url}")
            return None
        
        self.retry_count[url] += 1
        
        # 添加随机延迟
        delay = random.uniform(5, 15)
        self.logger.info(f"检测到反爬，等待 {delay:.2f} 秒后重试: {url}")
        time.sleep(delay)
        
        # 从Cookie池中随机选择一个Cookie
        cookie = random.choice(self.cookies_pool) if self.cookies_pool else {'bid': self._generate_bid()}
        cookie_str = '; '.join([f"{k}={v}" for k, v in cookie.items()])
        
        # 构建更丰富的请求头
        headers = {
            'User-Agent': self.get_random_ua(),
            'Referer': 'https://book.douban.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': cookie_str,
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Pragma': 'no-cache'
        }
        
        # 随机添加一些额外的请求头
        if random.random() > 0.5:
            headers['DNT'] = '1'
        
        # 使用 DrissionPage 中间件处理
        return scrapy.Request(
            url,
            callback=self.parse,
            dont_filter=True,
            meta={
                'dont_redirect': True,
                'handle_httpstatus_list': [302, 403, 404, 429],
                'use_drissionpage': True,  # 标记使用 DrissionPage 处理
                'download_timeout': 30,
                'retry_count': self.retry_count[url]
            },
            headers=headers,
            cookies=cookie
        )
        
    def get_random_ua(self):
        """获取随机User-Agent"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        ]
        return random.choice(user_agents)
    
    def start_requests(self):
        """让 RedisSpider 处理起始请求"""
        return []


    def make_request_from_data(self, data):
        """从Redis获取的数据创建请求"""
        url = data.decode('utf-8')
        self.logger.info(f"从Redis获取URL: {url}")
        
        # 从Cookie池中随机选择一个Cookie
        if self.cookies_pool:
            cookie = random.choice(self.cookies_pool)
            self.logger.info(f"使用Cookie: {cookie.get('bid', 'unknown')}")
            
            return scrapy.Request(
                url,
                dont_filter=True,
                callback=self.parse,
                errback=self.errback_handler,
                meta={
                    'dont_redirect': True,
                    'handle_httpstatus_list': [302, 403, 404, 429],
                    'download_timeout': 30,
                    'use_drissionpage': True,  # 标记使用 DrissionPage 处理
                },
                headers={
                    'User-Agent': self.get_random_ua(),
                    'Referer': 'https://book.douban.com/',
                },
                cookies=cookie
            )
        else:
            # 如果没有Cookie池，使用默认Cookie
            bid = self._generate_bid()
            self.logger.warning("Cookie池为空，使用默认Cookie")
            return scrapy.Request(
                url,
                callback=self.parse,
                errback=self.errback_handler,
                meta={
                    'dont_redirect': True,
                    'handle_httpstatus_list': [302, 403, 404, 429],
                    'download_timeout': 30,
                    'use_drissionpage': True,  # 标记使用 DrissionPage 处理
                },
                headers={
                    'User-Agent': self.get_random_ua(),
                    'Referer': 'https://book.douban.com/',
                },
                cookies={'bid': bid, 'll': '108288', 'ct': 'y'}
            )
    
    def parse(self, response):
        """解析图书标签页"""
        
        # 检查请求中的Cookie
        request_cookies = response.request.headers.get('Cookie', b'').decode('utf-8', errors='ignore')
        self.logger.info(f"Request Cookies: {request_cookies}")
        
        # 检查响应头
        self.logger.info(f"Response Headers: {dict(response.headers)}")
        
        # 如果响应内容太小，打印出来
        if len(response.body) < 1000:
            self.logger.warning(f"响应内容过小，可能被反爬: {len(response.body)} 字节")
            self.logger.info(f"Response Body: {response.text}")
        
        # 检查是否被反爬
        if response.status == 403:
            self.logger.warning(f"请求被拒绝(403): {response.url}")
            # 重试请求，添加随机延迟和新的 User-Agent
            time.sleep(random.uniform(3, 8))  # 添加随机延迟
            
            # 从Cookie池中随机选择一个Cookie
            cookie = random.choice(self.cookies_pool) if self.cookies_pool else {'bid': self._generate_bid()}
            cookie_str = '; '.join([f"{k}={v}" for k, v in cookie.items()])
            
            return scrapy.Request(
                response.url,
                callback=self.parse,
                dont_filter=True,
                meta={
                    'dont_redirect': True,
                    'handle_httpstatus_list': [302, 403, 404, 429],
                    'download_timeout': 30
                },
                headers={
                    'User-Agent': self.get_random_ua(),
                    'Referer': 'https://book.douban.com/',
                    'Cookie': cookie_str  # 添加Cookie
                },
                cookies=cookie  # 同时设置cookies字典
            )
        
        if self.check_anti_spider(response):
            self.logger.warning(f"检测到反爬虫: {response.url}")
            return self.handle_anti_spider(response)
            
        try:
            # 保存响应内容用于调试
            with open('debug_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            # 尝试多种选择器
            tags = response.css('table.tagCol td a::attr(href)').getall()
            if not tags:
                tags = response.css('div.article table td a::attr(href)').getall()
            if not tags:
                tags = response.xpath('//table[@class="tagCol"]//td/a/@href').getall()
                
            if not tags:
                self.logger.warning(f"未找到标签列表: {response.url}")
                self.logger.info(f"页面大小: {len(response.text)} 字节")
                self.logger.info(f"响应状态: {response.status}")
                return
                
            for tag_url in tags:
                tag_url = response.urljoin(tag_url)
                tag_url = response.urljoin(tag_url)
                
                # 从Cookie池中随机选择一个Cookie
                cookie = random.choice(self.cookies_pool) if self.cookies_pool else {'bid': self._generate_bid()}
                cookie_str = '; '.join([f"{k}={v}" for k, v in cookie.items()])
                
                yield scrapy.Request(
                    tag_url,
                    callback=self.parse_tag_list,
                    errback=self.errback_handler,
                    meta={
                        'dont_redirect': True,
                        'handle_httpstatus_list': [302, 403, 404, 429],
                        'download_timeout': 30
                    },
                    headers={
                        'Referer': response.url,
                        'User-Agent': self.get_random_ua(),
                        'Cookie': cookie_str  # 添加Cookie
                    },
                    cookies=cookie,  # 同时设置cookies字典
                    dont_filter=True
                )
        except Exception as e:
            self.logger.error(f"解析标签页出错: {response.url}, 错误: {str(e)}")
    
    def parse_tag_list(self, response):
        """解析标签下的图书列表页"""
        try:
            self.logger.info(f"解析图书列表页: {response.url}, 状态: {response.status}")
            
            # 保存响应内容用于调试
            with open('tag_list_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # 提取图书详情页链接
            book_links = response.css('div.info h2 a::attr(href)').getall()
            
            # 如果上面的选择器没有找到图书链接，尝试其他选择器
            if not book_links:
                book_links = response.css('li.subject-item div.info h2 a::attr(href)').getall()
            if not book_links:
                book_links = response.xpath('//li[contains(@class, "subject-item")]//div[@class="info"]/h2/a/@href').getall()
            
            if not book_links:
                self.logger.warning(f"未找到图书链接: {response.url}")
                return
            
            self.logger.info(f"找到 {len(book_links)} 本图书")
            
        # 批量处理图书链接
            for link in book_links:
                # 从Cookie池中随机选择一个Cookie
                cookie = random.choice(self.cookies_pool) if self.cookies_pool else {'bid': self._generate_bid()}
                cookie_str = '; '.join([f"{k}={v}" for k, v in cookie.items()])
                
                yield scrapy.Request(
                    link, 
                    callback=self.parse_detail,
                    errback=self.errback_handler,
                    meta={
                        'book_url': link,
                        'dont_merge_cookies': True,  # 避免cookie合并
                        'handle_httpstatus_list': [403, 404, 429],
                        'download_timeout': 20  # 减少超时时间
                    },
                    headers={
                        'User-Agent': self.get_random_ua(),
                        'Referer': response.url,
                        'Cookie': cookie_str  # 添加Cookie
                    },
                    cookies=cookie,  # 同时设置cookies字典
                    priority=1  # 设置优先级
                )
            
            # 提取下一页链接
            next_page = response.css('span.next a::attr(href)').get()
            if next_page:
                next_url = response.urljoin(next_page)
                self.logger.info(f"找到下一页: {next_url}")
                yield scrapy.Request(
                    next_url, 
                    callback=self.parse_tag_list,
                    errback=self.errback_handler
                )
        except Exception as e:
            self.logger.error(f"解析列表页出错: {response.url}, 错误: {str(e)}")

    def parse_detail(self, response):
        """解析图书详情页"""
        try:
            # 添加响应检查
            if not response.body or len(response.body) < 1000:
                self.logger.warning(f"响应内容异常: {response.url}")
                # 修改：使用yield替代return，并移除return语句
                request = self.handle_anti_spider(response)
                if request:
                    yield request
                return  # 这里的return不带值，用于提前结束函数，不会导致警告
                
            book = BookItem()
            
            # 提取URL和ID
            book['url'] = response.url
            match = self.detail_pattern.match(response.url)
            if match:
                book['book_id'] = match.group(1)
            else:
                book['book_id'] = f"unknown_{int(time.time())}"
                self.logger.warning(f"无法从URL提取图书ID: {response.url}")
            
            # 提取标题
            book['title'] = response.css('h1 span::text').get('').strip() or '未知标题'
            
            # 提取封面图片URL
            book['cover_url'] = response.css('div#mainpic a.nbg img::attr(src)').get() or ''
            
            # 提取评分信息 - 修复评分人数提取
            try:
                book['rating_score'] = response.css('strong.rating_num::text').get('').strip() or None
                # 修复：直接从评价链接中提取评分人数
                rating_people_text = response.css('a.rating_people span::text').get()
                if rating_people_text:
                    book['rating_people'] = int(rating_people_text)
                else:
                    # 备用方法
                    rating_people_text = response.css('div.rating_sum span::text').get('').strip()
                    if rating_people_text:
                        match = re.search(r'\d+', rating_people_text)
                        book['rating_people'] = int(match.group()) if match else 0
                    else:
                        book['rating_people'] = 0
            except Exception as e:
                self.logger.warning(f"提取评分信息出错: {response.url}, 错误: {str(e)}")
                book['rating_score'] = None
                book['rating_people'] = 0
            
            # 提取图书信息
            info_text = ''.join(response.css('div#info').getall()) or ''
            
            # 使用更精确的提取方法
            def safe_extract(pattern, text, default=''):
                match = re.search(pattern, text, re.DOTALL)
                return match.group(1).strip() if match else default
            
            # 提取作者信息 - 优化提取逻辑
            # 方法1: 使用更精确的CSS选择器
            authors = []
            # 修复：使用更准确的选择器
            author_links = response.css('span.pl:contains("作者") + a::text, span.pl:contains("作者") ~ a::text').getall()
            if author_links:
                authors = [a.strip() for a in author_links if a.strip()]
            
            # 方法2: 如果CSS选择器失败，尝试使用正则表达式
            if not authors:
                author_text = safe_extract(r'作者:</span>(.*?)(?:<br|<span class="pl">)', info_text, '')
                if author_text:
                    # 提取所有<a>标签中的文本
                    authors = re.findall(r'<a[^>]*>(.*?)</a>', author_text)
                    if not authors:
                        # 如果没有<a>标签，尝试提取纯文本
                        authors = [re.sub(r'<[^>]+>', '', author_text).strip()]
            
            # 清理作者信息
            authors = [a.replace('\n', '').replace(' ', '').strip() for a in authors if a.strip()]
            book['author'] = ' / '.join(authors) if authors else '未知'
            
            # 提取译者信息 - 优化提取逻辑
            translators = []
            # 修复：使用更准确的选择器
            translator_links = response.css('span.pl:contains("译者") + a::text, span.pl:contains("译者") ~ a::text').getall()
            if translator_links:
                translators = [t.strip() for t in translator_links if t.strip()]
            
            # 如果CSS选择器失败，尝试使用正则表达式
            if not translators:
                translator_text = safe_extract(r'译者:</span>(.*?)(?:<br|<span class="pl">)', info_text, '')
                if translator_text:
                    # 提取所有<a>标签中的文本
                    translators = re.findall(r'<a[^>]*>(.*?)</a>', translator_text)
                    if not translators:
                        # 如果没有<a>标签，尝试提取纯文本
                        translators = [re.sub(r'<[^>]+>', '', translator_text).strip()]
            
            # 清理译者信息
            translators = [t.replace('\n', '').replace(' ', '').strip() for t in translators if t.strip()]
            book['translator'] = ' / '.join(translators) if translators else ''
            
            # 提取出版社信息 - 修复：清理HTML标签
            publisher_raw = safe_extract(r'出版社:</span>\s*(.*?)<br', info_text, '未知')
            book['publisher'] = re.sub(r'<[^>]+>', '', publisher_raw).strip()
            
            # 提取出版年信息 
            book['publish_date'] = safe_extract(r'出版年:</span>\s*(.*?)<br', info_text, '').strip()
            
            # 提取页数信息 
            book['pages'] = safe_extract(r'页数:</span>\s*(.*?)<br', info_text, '').strip()
            
            # 提取定价信息 
            book['price'] = safe_extract(r'定价:</span>\s*(.*?)<br', info_text, '').strip()
            
            # 提取装帧信息 
            book['binding'] = safe_extract(r'装帧:</span>\s*(.*?)<br', info_text, '').strip()
            
            # 提取ISBN信息 
            book['isbn'] = safe_extract(r'ISBN:</span>\s*(.*?)(?:<br|</div>)', info_text, '').strip()
            
            # 提取副标题信息 
            book['subtitle'] = safe_extract(r'副标题:</span>\s*(.*?)<br', info_text, '').strip()
            
            # 提取原作名信息 - 
            book['original_title'] = safe_extract(r'原作名:</span>\s*(.*?)<br', info_text, '').strip()
            
            # 提取丛书信息
            series = safe_extract(r'丛书:</span>\s*<span[^>]*>(.*?)</span>', info_text, '')
            if not series:
                series = safe_extract(r'丛书:</span>\s*<a[^>]*>(.*?)</a>', info_text, '')
            book['series'] = series.strip()
            
            # 修复标签提取 - 从JavaScript中提取标签
            js_content = response.xpath('//script[contains(., "criteria")]').get() or ''
            criteria_match = re.search(r'criteria\s*=\s*[\'"]([^\'"]+)[\'"]', js_content)
            if criteria_match:
                criteria_str = criteria_match.group(1)
                # 分割并清理标签
                tags = [
                    tag.split(':')[-1] 
                    for tag in criteria_str.split('|') 
                    if ':' in tag and not tag.startswith('3:/')
                ]
                book['js_tags'] = tags
            else:
                book['js_tags'] = []
            
            # 提取评论和书评数量
            try:
                comments_count_text = response.css('div.mod-hd h2 a[href*="comments"] span::text').get()
                if comments_count_text:
                    comments_match = re.search(r'全部(\d+)条', comments_count_text)
                    if comments_match:
                        book['comments_count'] = int(comments_match.group(1))
                
                reviews_count_text = response.css('div.mod-hd h2 a[href*="reviews"] span::text').get()
                if reviews_count_text:
                    reviews_match = re.search(r'全部(\d+)条', reviews_count_text)
                    if reviews_match:
                        book['reviews_count'] = int(reviews_match.group(1))
            except Exception as e:
                self.logger.warning(f"提取评论和书评数量出错: {response.url}, 错误: {str(e)}")
            
            # 提取电子书信息
            try:
                ebook_info = response.css('div#buyinfo-printed li.ebook')
                if ebook_info:
                    ebook_price_text = ebook_info.css('span.buy-info a::text').get()
                    if ebook_price_text:
                        price_match = re.search(r'¥\s*(\d+\.\d+)', ebook_price_text)
                        if price_match:
                            book['ebook_price'] = price_match.group(1)
                    
                    ebook_url = ebook_info.css('span.buy-info a::attr(href)').get()
                    if ebook_url:
                        book['ebook_url'] = ebook_url
            except Exception as e:
                self.logger.warning(f"提取电子书信息出错: {response.url}, 错误: {str(e)}")
            
            # 添加爬取时间
            book['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            self.logger.info(f"成功解析图书: {book['title']}, 作者: {book['author']}, 标签: {book.get('js_tags', [])}")
            
            yield book
            
        except Exception as e:
            self.logger.error(f"解析详情页出错: {response.url}, 错误: {str(e)}")
            # 即使出错也尝试保存基本信息
            try:
                book = BookItem()
                book['url'] = response.url
                # 修复：将match变量移到try块内部
                match = self.detail_pattern.match(response.url)
                book['book_id'] = match.group(1) if match else f"error_{int(time.time())}"
                book['title'] = response.css('h1 span::text').get('').strip() or '解析出错'
                book['error_info'] = str(e)
                book['crawl_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                yield book
            except Exception as inner_e:
                self.logger.error(f"保存错误信息失败: {str(inner_e)}")
        
    def errback_handler(self, failure):
        """处理请求错误"""
        request = failure.request
        error_info = None
        
        if failure.check(HttpError):
            error_info = f'HTTP {failure.value.response.status}'
        elif failure.check(DNSLookupError):
            error_info = 'DNS解析失败'
        elif failure.check(TimeoutError, TCPTimedOutError):
            error_info = '请求超时'
        else:
            error_info = str(failure.value)
        
        self.logger.error(f'请求失败: {request.url}, 错误: {error_info}')
        
        match = self.detail_pattern.match(request.url)
        yield {
            'url': request.url,
            'book_id': match.group(1) if match else f"failed_{int(time.time())}",
            'title': '请求失败',
            'error_info': error_info,
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
