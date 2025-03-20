from DrissionPage import ChromiumOptions, ChromiumPage
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_browser_setup():
    try:
        # 创建浏览器配置
        options = ChromiumOptions()
        options.set_paths(browser_path=None)
        
        # 设置无头模式和其他选项
        options.set_argument('--headless=new')
        options.set_argument('--no-sandbox')
        options.set_argument('--disable-gpu')
        options.set_argument('--disable-dev-shm-usage')
        options.set_argument('--disable-extensions')
        
        # 初始化浏览器
        browser = ChromiumPage(options)
        version = browser.run_cdp('Browser.getVersion')
        logger.info(f"浏览器版本信息: {version}")
        
        # 测试豆瓣登录
        browser.get('https://www.douban.com')
        logger.info(f"当前页面标题: {browser.title}")
        
        # 设置登录 Cookie
        cookies = [
            {
                'name': 'bid',
                'value': 'xxxx',
                'domain': '.douban.com',
                'path': '/'
            },
        ]
        
        # 先启用网络功能并清除所有 Cookie
        browser.run_cdp('Network.enable')
        browser.run_cdp('Network.clearBrowserCookies')
        
        # 使用 JavaScript 设置 Cookie
        for cookie in cookies:
            js_code = f'''
            document.cookie = "{cookie['name']}={cookie['value']}; \
            domain={cookie['domain']}; \
            path={cookie['path']}";
            '''
            browser.run_js(js_code)
        
        # 刷新页面使 Cookie 生效
        browser.refresh()
        time.sleep(2)
        
        # 验证 Cookie 设置
        cookies_result = browser.run_cdp('Network.getAllCookies')
        current_cookies = cookies_result.get('cookies', [])
        logger.info(f"Cookie设置完成，当前数量: {len(current_cookies)}")
        logger.info(f"Cookie详情: {current_cookies}")
        
        # 访问需要登录的页面进行测试
        browser.get('https://book.douban.com/mine')
        time.sleep(2)  # 等待页面加载
        
        # 检查是否成功登录
        current_url = browser.url
        logger.info(f"当前页面URL: {current_url}")
        logger.info(f"当前页面标题: {browser.title}")
        
        if 'login' in current_url or 'sec.douban.com' in current_url:
            logger.error("登录失败，被重定向到登录页面")
            return False
            
        # 尝试获取用户名等登录后才能获取的元素
        try:
            username = browser.run_js('return document.querySelector(".nav-user-account").innerText')
            logger.info(f"登录用户名: {username}")
        except Exception as e:
            logger.error(f"获取用户名失败: {str(e)}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        logger.exception(e)
        return False
    finally:
        if 'browser' in locals():
            browser.quit()

if __name__ == '__main__':
    test_browser_setup()