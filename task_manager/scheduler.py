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
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable

import config
from base.base_crawler import AbstractCrawler
from factory.crawler_factory import CrawlerFactory
from tools import utils
from .db_task import TaskDB
from .models import TaskStatus, TaskExecutionLog
from .task_config import SearchTaskConfig, CreatorTaskConfig, DetailTaskConfig, TaskConfig


class TaskScheduler:
    """
    任务调度器，负责从数据库查询待执行任务并调度执行
    """
    def __init__(self, check_interval: int = 60):
        """
        初始化任务调度器
        
        Args:
            check_interval: 检查任务间隔（秒）
        """
        self.check_interval = check_interval
        self.running = False
        self.current_task = None
        self.task_lock = asyncio.Lock()
        
    async def start(self) -> None:
        """启动任务调度器"""
        self.running = True
        utils.logger.info("[TaskScheduler.start] Task scheduler started")
        
        while self.running:
            try:
                await self.check_and_run_tasks()
            except Exception as e:
                utils.logger.error(f"[TaskScheduler.start] Error checking tasks: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self) -> None:
        """停止任务调度器"""
        self.running = False
        utils.logger.info("[TaskScheduler.stop] Task scheduler stopped")
    
    async def check_and_run_tasks(self) -> None:
        """检查并运行待执行的任务"""
        async with self.task_lock:
            if self.current_task:
                # 已有任务在执行
                return
            
            # 获取待执行的任务
            pending_tasks = await TaskDB.get_pending_tasks(limit=1)
            if not pending_tasks:
                return
            
            # 执行任务
            task = pending_tasks[0]
            self.current_task = task
            asyncio.create_task(self.execute_task(task))
    
    async def execute_task(self, task: Dict[str, Any]) -> None:
        """
        执行任务
        
        Args:
            task: 任务信息
        """
        task_id = task["id"]
        platform = task["platform"]
        task_type = task["task_type"]
        
        utils.logger.info(f"[TaskScheduler.execute_task] Executing task {task_id} - {platform} - {task_type}")
        
        # 更新任务状态为运行中
        await TaskDB.update_task_status(task_id, TaskStatus.RUNNING.value)
        
        # 创建执行日志
        log = TaskExecutionLog(task_id=task_id, status="running")
        log_id = await TaskDB.log_task_execution(log)
        
        try:
            # 获取任务详细信息
            task_info, task_details = await TaskDB.get_task_details(task_id)
            if not task_info:
                raise ValueError(f"Task {task_id} not found")
            
            # 创建任务配置对象
            task_config = self.create_task_config(task_info, task_details)
            
            # 创建并运行爬虫，传入任务配置对象
            crawler = CrawlerFactory.create_crawler(platform=platform, task_config=task_config)
            await crawler.start()
            
            # 更新任务状态
            await TaskDB.update_task_status(task_id, TaskStatus.COMPLETED.value)
            await TaskDB.update_log_status(log_id, "completed", log_message="Task completed successfully")
            
        except Exception as e:
            error_message = f"Error executing task: {str(e)}"
            utils.logger.error(f"[TaskScheduler.execute_task] {error_message}")
            
            # 更新任务状态
            await TaskDB.update_task_status(task_id, TaskStatus.FAILED.value, error_message)
            await TaskDB.update_log_status(log_id, "failed", log_message=error_message)
        
        finally:
            # 清理当前任务
            async with self.task_lock:
                self.current_task = None
    
    def create_task_config(self, task_info: Dict[str, Any], task_details: List[str]) -> TaskConfig:
        """
        根据任务信息创建任务配置对象
        
        Args:
            task_info: 任务基本信息
            task_details: 任务详细参数
            
        Returns:
            TaskConfig: 任务配置对象
        """
        platform = task_info["platform"]
        task_type = task_info["task_type"]
        
        # 通用参数
        common_params = {
            "platform": platform,
            "login_type": task_info.get("login_type", "qrcode"),
            "cookies": task_info.get("cookies", ""),
            "save_data_option": "db",  # 任务系统默认使用数据库存储
            "enable_get_comments": task_info.get("enable_get_comments", True),
            "enable_get_sub_comments": task_info.get("enable_get_sub_comments", False),
        }
        
        # 根据任务类型创建相应的配置对象
        if task_type == "search":
            # 搜索任务
            return SearchTaskConfig(
                keywords=task_details,
                **common_params
            )
            
        elif task_type == "creator":
            # 创作者任务
            return CreatorTaskConfig(
                creator_ids=task_details,
                **common_params
            )
            
        elif task_type == "detail":
            # 帖子详情任务
            return DetailTaskConfig(
                post_ids=task_details,
                **common_params
            )
            
        # 默认返回基本配置
        return TaskConfig(
            task_type=task_type,
            **common_params
        )


# 使用单例模式创建调度器实例
scheduler = TaskScheduler()

async def start_scheduler():
    """启动任务调度器"""
    await scheduler.start()

def stop_scheduler():
    """停止任务调度器"""
    scheduler.stop()
