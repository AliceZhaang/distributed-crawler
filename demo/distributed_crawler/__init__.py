# 版本信息
__version__ = '1.0.0'

# 可以导出主要的类，方便使用
from .scheduler.task_scheduler import TaskScheduler
from .crawler.spiders.worker import WorkerSpider 