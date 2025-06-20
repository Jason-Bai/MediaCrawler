# MediaCrawler 数据库任务管理与调度系统

本文档介绍了 MediaCrawler 新增的数据库任务管理和调度功能，使爬虫任务可以存储在数据库中并支持定时调度执行。

## 新增功能概述

- **数据库存储爬取配置**：关键词、创作者ID、帖子ID 等配置可存储在数据库中
- **任务调度系统**：支持根据优先级和计划时间自动执行任务
- **命令行任务管理**：提供便捷的命令行接口管理数据库中的任务
- **任务状态追踪**：记录任务执行状态和详细日志

## 快速开始

### 1. 创建任务表

首先需要在数据库中创建任务相关表：

```bash
mysql -u your_username -p your_database_name < schema/task_tables.sql
```

### 2. 启动调度器

以调度器模式启动程序：

```bash
python main.py --run_mode scheduler --save_data_option db
```

### 3. 添加爬取任务

使用命令行工具添加任务：

```bash
# 添加搜索任务
python task_manager/cli.py add --platform xhs --type search --keywords "编程,Python"

# 添加创作者爬取任务
python task_manager/cli.py add --platform dy --type creator --ids "用户ID1,用户ID2"

# 添加帖子详情爬取任务
python task_manager/cli.py add --platform xhs --type detail --ids "帖子ID1,帖子ID2"
```

## 详细文档

完整使用说明请参考：[数据库任务调度系统使用指南](docs/db_task_scheduling.md)

## 目录结构

```
├── task_manager/          # 任务管理模块
│   ├── __init__.py        # 模块入口
│   ├── models.py          # 数据模型
│   ├── db_task.py         # 数据库操作
│   ├── scheduler.py       # 任务调度器
│   └── cli.py             # 命令行接口
├── schema/
│   └── task_tables.sql    # 任务表结构
└── examples/
    └── add_task_example.py # 编程式添加任务示例
```

## 使用场景

1. **定时爬取**：设置特定时间执行爬取任务
2. **批量管理**：统一管理和监控多个平台的爬取任务
3. **优先级控制**：对重要任务设置更高的优先级
4. **失败重试**：对失败的任务进行分析和重试

## 注意事项

- 调度器模式需要数据库支持，确保 `config/db_config.py` 中的数据库配置正确
- 定时任务的最小时间粒度为分钟
- 任务状态包括：pending（待处理）、running（运行中）、completed（已完成）和failed（失败）
