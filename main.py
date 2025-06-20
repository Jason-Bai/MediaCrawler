# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  


import asyncio
import sys
import time

import cmd_arg
import config
import db
from base.base_crawler import AbstractCrawler
from media_platform.bilibili import BilibiliCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.tieba import TieBaCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler
from media_platform.zhihu import ZhihuCrawler
from task_manager.scheduler import start_scheduler, stop_scheduler
from tools import utils


class CrawlerFactory:
    CRAWLERS = {
        "xhs": XiaoHongShuCrawler,
        "dy": DouYinCrawler,
        "ks": KuaishouCrawler,
        "bili": BilibiliCrawler,
        "wb": WeiboCrawler,
        "tieba": TieBaCrawler,
        "zhihu": ZhihuCrawler
    }

    @staticmethod
    def create_crawler(platform: str, task_config=None) -> AbstractCrawler:
        """
        创建爬虫实例
        
        Args:
            platform: 平台名称
            task_config: 任务配置对象，如果提供则使用此配置，否则使用全局配置
            
        Returns:
            AbstractCrawler: 爬虫实例
            
        Raises:
            ValueError: 如果平台不受支持
        """
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError("Invalid Media Platform Currently only supported xhs or dy or ks or bili ...")
        return crawler_class(task_config=task_config)


async def main():
    # parse cmd
    await cmd_arg.parse_cmd()

    # 确保调度器模式下使用数据库存储
    if config.RUN_MODE == "scheduler" and config.SAVE_DATA_OPTION != "db":
        utils.logger.warning("调度器模式必须使用数据库存储！自动将SAVE_DATA_OPTION设置为'db'")
        config.SAVE_DATA_OPTION = "db"

    # init db
    if config.SAVE_DATA_OPTION == "db":
        await db.init_db()
    
    # 根据运行模式执行不同的逻辑
    if config.RUN_MODE == "scheduler":
        utils.logger.info("Starting in scheduler mode...")
        try:
            # 启动任务调度器
            await start_scheduler()
        except KeyboardInterrupt:
            utils.logger.info("Scheduler stopped by user")
            stop_scheduler()
    else:
        # 传统模式：直接运行单个爬虫任务
        utils.logger.info(f"Starting in crawler mode for {config.PLATFORM}...")
        crawler = CrawlerFactory.create_crawler(platform=config.PLATFORM)
        await crawler.start()

    if config.SAVE_DATA_OPTION == "db":
        await db.close()


if __name__ == '__main__':
    try:
        # asyncio.run(main())
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        utils.logger.info("Program stopped by user")
        sys.exit()
