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
任务管理命令行工具。
使用方式: python task_manager/cli.py [command] [options]

可用命令:
  list     列出所有任务
  add      添加新任务
  update   更新任务状态
  delete   删除任务
  show     显示任务详细信息

示例:
  python task_manager/cli.py list
  python task_manager/cli.py add --platform xhs --type search --keywords "编程,副业"
  python task_manager/cli.py add --platform dy --type creator --ids "MS4wLjABAAAA5ZrIWYg..."
  python task_manager/cli.py show --id 1
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
from task_manager.db_task import TaskDB
from task_manager.models import SearchTaskModel, CreatorTaskModel, DetailTaskModel, TaskStatus
from tools import utils


async def list_tasks(args):
    """列出所有任务"""
    await db.init_db()

    # 构建查询语句
    query = "SELECT * FROM crawl_tasks"
    conditions = []
    params = []
    
    if args.platform:
        conditions.append("platform = %s")
        params.append(args.platform)
    
    if args.status:
        conditions.append("status = %s")
        params.append(args.status)
    
    if args.type:
        conditions.append("task_type = %s")
        params.append(args.type)
    
    # 添加条件
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # 添加排序
    query += " ORDER BY created_at DESC"
    
    # 添加限制
    if args.limit:
        query += " LIMIT %s"
        params.append(args.limit)
    
    # 执行查询
    tasks = await TaskDB.execute_query(query, tuple(params) if params else None)
    
    # 打印任务列表
    if not tasks:
        print("没有找到任务。")
        return
    
    print(f"找到 {len(tasks)} 个任务：")
    print("-" * 100)
    print(f"{'ID':<5} {'平台':<8} {'类型':<10} {'状态':<10} {'优先级':<6} {'创建时间':<20} {'计划时间':<20}")
    print("-" * 100)
    
    for task in tasks:
        created_at = task["created_at"].strftime("%Y-%m-%d %H:%M:%S") if task["created_at"] else "N/A"
        scheduled_at = task["scheduled_at"].strftime("%Y-%m-%d %H:%M:%S") if task["scheduled_at"] else "立即执行"
        
        print(f"{task['id']:<5} {task['platform']:<8} {task['task_type']:<10} {task['status']:<10} "
              f"{task['priority']:<6} {created_at:<20} {scheduled_at:<20}")
    
    print("-" * 100)
    await db.close()


async def add_task(args):
    """添加新任务"""
    await db.init_db()
    
    # 设置计划时间
    scheduled_at = None
    if args.schedule:
        try:
            days, hours, minutes = 0, 0, 0
            if "d" in args.schedule:
                days = int(args.schedule.split("d")[0])
                remainder = args.schedule.split("d")[1]
            else:
                remainder = args.schedule
                
            if "h" in remainder:
                hours = int(remainder.split("h")[0])
                remainder = remainder.split("h")[1]
            
            if "m" in remainder:
                minutes = int(remainder.split("m")[0])
            
            scheduled_at = datetime.now() + timedelta(days=days, hours=hours, minutes=minutes)
        except Exception:
            print("无效的计划时间格式。请使用类似 '1d12h30m' 的格式。")
            return
    
    # 创建任务
    task_id = None
    if args.type == "search":
        if not args.keywords:
            print("搜索任务需要提供关键词参数 --keywords")
            return
        
        keywords = args.keywords.split(",")
        task = SearchTaskModel(
            platform=args.platform,
            keywords=keywords,
            priority=args.priority,
            scheduled_at=scheduled_at
        )
        task_id = await TaskDB.add_task(task)
        
    elif args.type == "creator":
        if not args.ids:
            print("创作者任务需要提供创作者ID参数 --ids")
            return
        
        creator_ids = args.ids.split(",")
        task = CreatorTaskModel(
            platform=args.platform,
            creator_ids=creator_ids,
            priority=args.priority,
            scheduled_at=scheduled_at
        )
        task_id = await TaskDB.add_task(task)
        
    elif args.type == "detail":
        if not args.ids:
            print("详情任务需要提供帖子ID参数 --ids")
            return
        
        post_ids = args.ids.split(",")
        task = DetailTaskModel(
            platform=args.platform,
            post_ids=post_ids,
            priority=args.priority,
            scheduled_at=scheduled_at
        )
        task_id = await TaskDB.add_task(task)
    
    if task_id:
        print(f"成功添加任务，ID: {task_id}")
        if scheduled_at:
            print(f"计划执行时间: {scheduled_at}")
        else:
            print("任务将立即执行")
    
    await db.close()


async def update_task(args):
    """更新任务状态"""
    await db.init_db()
    
    await TaskDB.update_task_status(args.id, args.status)
    print(f"成功更新任务 {args.id} 的状态为 {args.status}")
    
    await db.close()


async def delete_task(args):
    """删除任务"""
    await db.init_db()
    
    # 需要先删除关联的任务详情
    task_info, _ = await TaskDB.get_task_details(args.id)
    if not task_info:
        print(f"任务 {args.id} 不存在")
        await db.close()
        return
    
    task_type = task_info["task_type"]
    
    # 根据任务类型确定要删除的表
    if task_type == "search":
        await TaskDB.execute("DELETE FROM search_keyword_tasks WHERE task_id = %s", (args.id,))
    elif task_type == "creator":
        await TaskDB.execute("DELETE FROM creator_tasks WHERE task_id = %s", (args.id,))
    elif task_type == "detail":
        await TaskDB.execute("DELETE FROM post_detail_tasks WHERE task_id = %s", (args.id,))
    
    # 删除执行日志
    await TaskDB.execute("DELETE FROM task_execution_log WHERE task_id = %s", (args.id,))
    
    # 删除主任务
    await TaskDB.execute("DELETE FROM crawl_tasks WHERE id = %s", (args.id,))
    
    print(f"成功删除任务 {args.id}")
    
    await db.close()


async def show_task(args):
    """显示任务详细信息"""
    await db.init_db()
    
    task_info, task_details = await TaskDB.get_task_details(args.id)
    if not task_info:
        print(f"任务 {args.id} 不存在")
        await db.close()
        return
    
    print("-" * 50)
    print(f"任务ID: {task_info['id']}")
    print(f"平台: {task_info['platform']}")
    print(f"类型: {task_info['task_type']}")
    print(f"状态: {task_info['status']}")
    print(f"优先级: {task_info['priority']}")
    print(f"创建时间: {task_info['created_at']}")
    print(f"计划时间: {task_info['scheduled_at'] if task_info['scheduled_at'] else '立即执行'}")
    print(f"完成时间: {task_info['completed_at'] if task_info['completed_at'] else 'N/A'}")
    
    if task_info["error_message"]:
        print(f"错误信息: {task_info['error_message']}")
    
    # 显示任务详情
    task_type = task_info["task_type"]
    if task_type == "search":
        print("\n关键词列表:")
    elif task_type == "creator":
        print("\n创作者ID列表:")
    elif task_type == "detail":
        print("\n帖子ID列表:")
    
    for i, detail in enumerate(task_details, 1):
        print(f"{i}. {detail}")
    
    # 获取并显示执行日志
    logs = await TaskDB.execute_query(
        "SELECT * FROM task_execution_log WHERE task_id = %s ORDER BY start_time DESC",
        (args.id,)
    )
    
    if logs:
        print("\n执行日志:")
        print("-" * 50)
        for log in logs:
            start_time = log["start_time"].strftime("%Y-%m-%d %H:%M:%S")
            end_time = log["end_time"].strftime("%Y-%m-%d %H:%M:%S") if log["end_time"] else "N/A"
            print(f"开始时间: {start_time}")
            print(f"结束时间: {end_time}")
            print(f"状态: {log['status']}")
            print(f"处理项目: {log['items_processed']}")
            if log["log_message"]:
                print(f"日志: {log['log_message']}")
            print("-" * 30)
    
    print("-" * 50)
    await db.close()


def main():
    parser = argparse.ArgumentParser(description='任务管理命令行工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有任务')
    list_parser.add_argument('--platform', type=str, choices=["xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"], 
                            help='按平台过滤')
    list_parser.add_argument('--status', type=str, 
                            choices=["pending", "running", "completed", "failed"], 
                            help='按状态过滤')
    list_parser.add_argument('--type', type=str, 
                            choices=["search", "creator", "detail"], 
                            help='按类型过滤')
    list_parser.add_argument('--limit', type=int, help='限制返回的任务数量')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='添加新任务')
    add_parser.add_argument('--platform', type=str, required=True,
                           choices=["xhs", "dy", "ks", "bili", "wb", "tieba", "zhihu"], 
                           help='平台')
    add_parser.add_argument('--type', type=str, required=True,
                           choices=["search", "creator", "detail"], 
                           help='任务类型')
    add_parser.add_argument('--keywords', type=str, 
                           help='搜索关键词，用逗号分隔')
    add_parser.add_argument('--ids', type=str, 
                           help='创作者ID或帖子ID，用逗号分隔')
    add_parser.add_argument('--priority', type=int, default=5,
                           help='任务优先级 (1-10)')
    add_parser.add_argument('--schedule', type=str, 
                           help='计划执行时间，如 "1d12h30m" 表示1天12小时30分钟后')
    
    # update 命令
    update_parser = subparsers.add_parser('update', help='更新任务状态')
    update_parser.add_argument('--id', type=int, required=True,
                              help='任务ID')
    update_parser.add_argument('--status', type=str, required=True,
                              choices=["pending", "running", "completed", "failed"],
                              help='新状态')
    
    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除任务')
    delete_parser.add_argument('--id', type=int, required=True,
                              help='任务ID')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='显示任务详细信息')
    show_parser.add_argument('--id', type=int, required=True,
                            help='任务ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行相应的命令
    if args.command == 'list':
        asyncio.run(list_tasks(args))
    elif args.command == 'add':
        asyncio.run(add_task(args))
    elif args.command == 'update':
        asyncio.run(update_task(args))
    elif args.command == 'delete':
        asyncio.run(delete_task(args))
    elif args.command == 'show':
        asyncio.run(show_task(args))


if __name__ == '__main__':
    main()
