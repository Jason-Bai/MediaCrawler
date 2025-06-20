# 数据库任务调度系统使用指南

本指南介绍如何使用 MediaCrawler 的数据库任务调度系统，该系统允许用户将爬取任务配置存储在数据库中，并支持定时执行和批量管理爬取任务。

## 功能概述

数据库任务调度系统提供以下功能：

1. 支持将爬取配置（关键词、创作者账号、帖子ID）存储在数据库中
2. 支持设置任务优先级和计划执行时间
3. 提供命令行工具管理爬取任务
4. 实现调度器模式，定期检查并执行数据库中的任务
5. 记录任务执行日志和状态

## 创建数据库表

首先，需要在 MySQL 数据库中创建任务表：

```bash
# 在项目根目录执行
mysql -u your_username -p your_database_name < schema/task_tables.sql
```

或者直接使用 MySQL 客户端执行 `schema/task_tables.sql` 文件中的 SQL 语句。

## 运行模式

系统支持两种运行模式：

1. **普通爬虫模式**（crawler）：传统方式，从配置文件或命令行参数读取配置并直接执行爬取任务
2. **调度器模式**（scheduler）：从数据库中读取待执行的任务并按优先级执行

## 使用调度器模式

启动调度器模式的命令：

```bash
python main.py --run_mode scheduler --save_data_option db
```

参数说明：
- `--run_mode scheduler`：指定使用调度器模式
- `--save_data_option db`：必须指定为数据库存储模式

调度器会定期（默认每60秒）检查数据库中是否有待执行的任务，并按优先级顺序执行它们。

## 任务管理命令行工具

系统提供了命令行工具用于管理数据库中的任务：

### 1. 列出任务

```bash
# 列出所有任务
python task_manager/cli.py list

# 按平台过滤
python task_manager/cli.py list --platform xhs

# 按状态过滤
python task_manager/cli.py list --status pending

# 按类型过滤
python task_manager/cli.py list --type search

# 限制返回数量
python task_manager/cli.py list --limit 10
```

### 2. 添加任务

```bash
# 添加搜索任务
python task_manager/cli.py add --platform xhs --type search --keywords "编程,副业"

# 添加创作者爬取任务
python task_manager/cli.py add --platform dy --type creator --ids "MS4wLjABAAAA5ZrIWYg...,MS4wLjABAAAAeS7..."

# 添加帖子详情爬取任务
python task_manager/cli.py add --platform xhs --type detail --ids "64820a69000000002303ccbe,648b06c1000000001d01b6ed"

# 设置优先级（范围1-10，默认为5）
python task_manager/cli.py add --platform xhs --type search --keywords "编程" --priority 8

# 设置计划执行时间
python task_manager/cli.py add --platform xhs --type search --keywords "编程" --schedule "1d12h30m"
```

计划时间格式：
- `1d`：1天后
- `12h`：12小时后
- `30m`：30分钟后
- `1d12h30m`：1天12小时30分钟后

### 3. 查看任务详情

```bash
python task_manager/cli.py show --id 1
```

### 4. 更新任务状态

```bash
python task_manager/cli.py update --id 1 --status pending
```

可用状态：
- `pending`：待处理
- `running`：执行中
- `completed`：已完成
- `failed`：已失败

### 5. 删除任务

```bash
python task_manager/cli.py delete --id 1
```

## 编程方式添加任务

您也可以通过编程方式添加任务，示例代码见 `examples/add_task_example.py`：

```python
from task_manager.db_task import TaskDB
from task_manager.models import SearchTaskModel, CreatorTaskModel, DetailTaskModel

# 添加一个搜索任务
search_task = SearchTaskModel(
    platform="xhs",
    keywords=["编程副业", "Python学习"],
    priority=8,
)
task_id = await TaskDB.add_task(search_task)
```

## 任务状态流程

任务状态会自动在以下几种状态间转换：

1. **pending**：新创建的任务默认为待处理状态
2. **running**：调度器选中任务并开始执行时状态变为运行中
3. **completed**：任务成功完成后状态变为已完成
4. **failed**：任务执行过程中发生错误时状态变为失败

## 任务优先级

任务优先级范围从1到10，数字越大优先级越高。调度器会优先执行高优先级的任务。

## 任务调度逻辑

调度器的工作流程：

1. 定期（默认60秒）检查数据库中的待执行任务
2. 优先选择状态为pending、已到计划执行时间且优先级最高的任务
3. 更新任务状态为running并开始执行
4. 执行完成后更新任务状态为completed或failed
5. 记录任务执行的详细日志

## 注意事项

1. 数据库配置必须正确设置在 `config/db_config.py` 文件中
2. 调度器模式需要持续运行才能检查和执行新任务
3. 计划任务的时间精度为分钟级别
4. 任务执行失败会记录错误信息，可通过 `show` 命令查看
