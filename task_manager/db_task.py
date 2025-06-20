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
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import aiomysql

from config import db_config
from tools import utils
from .models import (
    TaskModel,
    SearchTaskModel,
    CreatorTaskModel,
    DetailTaskModel,
    TaskStatus,
    TaskExecutionLog
)


class TaskDB:
    """
    数据库任务操作类，用于任务的增删改查
    """
    _pool = None

    @classmethod
    async def get_db_pool(cls):
        """获取数据库连接池"""
        if cls._pool is None:
            try:
                cls._pool = await aiomysql.create_pool(
                    host=db_config.RELATION_DB_HOST,
                    port=int(db_config.RELATION_DB_PORT),
                    user=db_config.RELATION_DB_USER,
                    password=db_config.RELATION_DB_PWD,
                    db=db_config.RELATION_DB_NAME,
                    autocommit=True
                )
            except Exception as e:
                utils.logger.error(f"[TaskDB.get_db_pool] Create db pool failed: {e}")
                raise e
        return cls._pool

    @classmethod
    async def execute_query(cls, query: str, params: tuple = None) -> List[Dict]:
        """执行SQL查询"""
        pool = await cls.get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                result = await cursor.fetchall()
                return list(result)

    @classmethod
    async def execute(cls, query: str, params: tuple = None) -> int:
        """执行SQL语句，返回影响的行数或自增ID"""
        pool = await cls.get_db_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                if query.strip().upper().startswith('INSERT'):
                    return cursor.lastrowid
                return cursor.rowcount

    @classmethod
    async def add_task(cls, task: TaskModel) -> int:
        """
        添加任务到数据库
        
        Args:
            task: 任务模型
            
        Returns:
            int: 任务ID
        """
        query = """
        INSERT INTO crawl_tasks
        (platform, task_type, status, priority, scheduled_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        task_id = await cls.execute(
            query,
            (
                task.platform,
                task.task_type,
                task.status.value if isinstance(task.status, TaskStatus) else task.status,
                task.priority,
                task.scheduled_at
            )
        )

        # 根据任务类型添加详细信息
        if isinstance(task, SearchTaskModel) and task.keywords:
            await cls.add_search_keywords(task_id, task.keywords)
        elif isinstance(task, CreatorTaskModel) and task.creator_ids:
            await cls.add_creator_ids(task_id, task.creator_ids)
        elif isinstance(task, DetailTaskModel) and task.post_ids:
            await cls.add_post_ids(task_id, task.post_ids)

        return task_id

    @classmethod
    async def add_search_keywords(cls, task_id: int, keywords: List[str]) -> None:
        """添加搜索关键词"""
        if not keywords:
            return
        
        for keyword in keywords:
            query = "INSERT INTO search_keyword_tasks (task_id, keyword) VALUES (%s, %s)"
            await cls.execute(query, (task_id, keyword))

    @classmethod
    async def add_creator_ids(cls, task_id: int, creator_ids: List[str]) -> None:
        """添加创作者ID"""
        if not creator_ids:
            return
        
        for creator_id in creator_ids:
            query = "INSERT INTO creator_tasks (task_id, creator_id) VALUES (%s, %s)"
            await cls.execute(query, (task_id, creator_id))

    @classmethod
    async def add_post_ids(cls, task_id: int, post_ids: List[str]) -> None:
        """添加帖子ID"""
        if not post_ids:
            return
        
        for post_id in post_ids:
            query = "INSERT INTO post_detail_tasks (task_id, post_id) VALUES (%s, %s)"
            await cls.execute(query, (task_id, post_id))

    @classmethod
    async def get_pending_tasks(cls, limit: int = 10) -> List[Dict]:
        """
        获取待处理的任务
        
        Args:
            limit: 获取任务数量上限
            
        Returns:
            List[Dict]: 任务列表
        """
        query = """
        SELECT * FROM crawl_tasks
        WHERE status = 'pending' AND (scheduled_at IS NULL OR scheduled_at <= NOW())
        ORDER BY priority DESC, scheduled_at ASC, created_at ASC
        LIMIT %s
        """
        return await cls.execute_query(query, (limit,))

    @classmethod
    async def update_task_status(cls, task_id: int, status: str, error_message: str = None) -> None:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息（如果有）
        """
        params = [status]
        query = "UPDATE crawl_tasks SET status = %s"

        if status == TaskStatus.COMPLETED.value or status == TaskStatus.COMPLETED:
            query += ", completed_at = NOW()"
        
        if error_message:
            query += ", error_message = %s"
            params.append(error_message)

        query += " WHERE id = %s"
        params.append(task_id)
        
        await cls.execute(query, tuple(params))

    @classmethod
    async def get_task_details(cls, task_id: int) -> Tuple[Dict, List[str]]:
        """
        获取任务详细信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Tuple[Dict, List[str]]: (任务基本信息, 任务参数列表)
        """
        task_query = "SELECT * FROM crawl_tasks WHERE id = %s"
        tasks = await cls.execute_query(task_query, (task_id,))
        if not tasks:
            return None, []
        
        task = tasks[0]
        task_type = task["task_type"]
        
        # 根据任务类型获取详细信息
        if task_type == "search":
            table_name = "search_keyword_tasks"
            field_name = "keyword"
        elif task_type == "creator":
            table_name = "creator_tasks"
            field_name = "creator_id"
        elif task_type == "detail":
            table_name = "post_detail_tasks"
            field_name = "post_id"
        else:
            return task, []

        details_query = f"SELECT {field_name} FROM {table_name} WHERE task_id = %s"
        details = await cls.execute_query(details_query, (task_id,))
        return task, [detail[field_name] for detail in details]

    @classmethod
    async def log_task_execution(cls, log: TaskExecutionLog) -> int:
        """
        记录任务执行日志
        
        Args:
            log: 执行日志对象
            
        Returns:
            int: 日志ID
        """
        query = """
        INSERT INTO task_execution_log
        (task_id, status, items_processed, log_message)
        VALUES (%s, %s, %s, %s)
        """
        return await cls.execute(
            query, 
            (log.task_id, log.status, log.items_processed, log.log_message)
        )

    @classmethod
    async def update_log_status(cls, log_id: int, status: str, 
                               items_processed: int = None, 
                               log_message: str = None) -> None:
        """
        更新日志状态
        
        Args:
            log_id: 日志ID
            status: 新状态
            items_processed: 处理的项目数
            log_message: 日志信息
        """
        params = [status]
        query = "UPDATE task_execution_log SET status = %s"

        if status == "completed" or status == "failed":
            query += ", end_time = NOW()"
        
        if items_processed is not None:
            query += ", items_processed = %s"
            params.append(items_processed)
            
        if log_message:
            query += ", log_message = %s"
            params.append(log_message)

        query += " WHERE id = %s"
        params.append(log_id)
        
        await cls.execute(query, tuple(params))
        
    @classmethod
    async def close(cls):
        """关闭数据库连接池"""
        if cls._pool:
            cls._pool.close()
            await cls._pool.wait_closed()
            cls._pool = None
