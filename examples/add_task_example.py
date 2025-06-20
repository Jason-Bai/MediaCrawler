# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  

"""
这是一个添加爬取任务到数据库的示例脚本。
使用方法：
python examples/add_task_example.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
import os

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from task_manager.db_task import TaskDB
from task_manager.models import SearchTaskModel, CreatorTaskModel, DetailTaskModel


async def add_search_task():
    """添加关键词搜索任务示例"""
    # 初始化数据库连接
    await db.init_db()
    
    # 创建一个搜索任务，计划1小时后执行
    scheduled_time = datetime.now() + timedelta(hours=1)
    
    # 搜索任务包含多个关键词
    search_task = SearchTaskModel(
        platform="xhs",                      # 平台: xhs, dy, ks, bili, wb, tieba, zhihu
        keywords=["编程副业", "Python学习"],   # 要搜索的关键词列表
        priority=8,                         # 优先级 (1-10)
        scheduled_at=scheduled_time,        # 计划执行时间
    )
    
    # 将任务添加到数据库
    task_id = await TaskDB.add_task(search_task)
    print(f"成功添加搜索任务，ID: {task_id}，计划执行时间: {scheduled_time}")
    
    await db.close()


async def add_creator_task():
    """添加创作者爬取任务示例"""
    # 初始化数据库连接
    await db.init_db()
    
    # 创建一个创作者爬取任务，立即执行
    creator_task = CreatorTaskModel(
        platform="dy",                     # 平台: xhs, dy, ks, bili, wb, tieba, zhihu
        creator_ids=["MS4wLjABAAAA5ZrIWYgCQOKwBFyGMhmEZxXPZZXfAdlZPAtlZ1XbDzdwgCD9q3hGS5FJGLWsZFX6"], # 创作者ID列表
        priority=5,                        # 优先级 (1-10)
        # 不设置scheduled_at表示立即执行
    )
    
    # 将任务添加到数据库
    task_id = await TaskDB.add_task(creator_task)
    print(f"成功添加创作者爬取任务，ID: {task_id}，立即执行")
    
    await db.close()


async def add_detail_task():
    """添加帖子详情爬取任务示例"""
    # 初始化数据库连接
    await db.init_db()
    
    # 创建一个帖子详情爬取任务，计划明天执行
    scheduled_time = datetime.now() + timedelta(days=1)
    
    detail_task = DetailTaskModel(
        platform="xhs",                  # 平台: xhs, dy, ks, bili, wb, tieba, zhihu
        post_ids=["64820a69000000002303ccbe"], # 帖子ID列表
        priority=3,                      # 优先级 (1-10)
        scheduled_at=scheduled_time,     # 计划执行时间
    )
    
    # 将任务添加到数据库
    task_id = await TaskDB.add_task(detail_task)
    print(f"成功添加帖子详情爬取任务，ID: {task_id}，计划执行时间: {scheduled_time}")
    
    await db.close()


async def main():
    """运行所有示例"""
    await add_search_task()
    await add_creator_task()
    await add_detail_task()


if __name__ == "__main__":
    asyncio.run(main())
