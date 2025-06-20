-- ----------------------------
-- Table structure for crawl_tasks
-- ----------------------------
DROP TABLE IF EXISTS `crawl_tasks`;
CREATE TABLE `crawl_tasks` (
    `id` int NOT NULL AUTO_INCREMENT COMMENT '任务ID',
    `platform` varchar(10) NOT NULL COMMENT '平台（xhs, dy, bili等）',
    `task_type` varchar(20) NOT NULL COMMENT '任务类型（search, detail, creator）',
    `status` varchar(20) DEFAULT 'pending' COMMENT '任务状态（pending, running, completed, failed）',
    `priority` int DEFAULT 5 COMMENT '优先级（1-10，10为最高）',
    `created_at` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `scheduled_at` timestamp NULL COMMENT '计划执行时间',
    `completed_at` timestamp NULL COMMENT '完成时间',
    `error_message` text DEFAULT NULL COMMENT '错误信息',
    PRIMARY KEY (`id`),
    KEY `idx_tasks_status` (`status`),
    KEY `idx_tasks_platform` (`platform`),
    KEY `idx_tasks_scheduled` (`scheduled_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='爬取任务表';

-- ----------------------------
-- Table structure for search_keyword_tasks
-- ----------------------------
DROP TABLE IF EXISTS `search_keyword_tasks`;
CREATE TABLE `search_keyword_tasks` (
    `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `task_id` int NOT NULL COMMENT '任务ID',
    `keyword` varchar(100) NOT NULL COMMENT '搜索关键词',
    PRIMARY KEY (`id`),
    KEY `idx_search_task_id` (`task_id`),
    CONSTRAINT `fk_search_task` FOREIGN KEY (`task_id`) REFERENCES `crawl_tasks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='搜索关键词任务';

-- ----------------------------
-- Table structure for creator_tasks
-- ----------------------------
DROP TABLE IF EXISTS `creator_tasks`;
CREATE TABLE `creator_tasks` (
    `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `task_id` int NOT NULL COMMENT '任务ID',
    `creator_id` varchar(100) NOT NULL COMMENT '创作者ID',
    PRIMARY KEY (`id`),
    KEY `idx_creator_task_id` (`task_id`),
    CONSTRAINT `fk_creator_task` FOREIGN KEY (`task_id`) REFERENCES `crawl_tasks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='创作者爬取任务';

-- ----------------------------
-- Table structure for post_detail_tasks
-- ----------------------------
DROP TABLE IF EXISTS `post_detail_tasks`;
CREATE TABLE `post_detail_tasks` (
    `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `task_id` int NOT NULL COMMENT '任务ID',
    `post_id` varchar(100) NOT NULL COMMENT '帖子/视频ID',
    PRIMARY KEY (`id`),
    KEY `idx_post_task_id` (`task_id`),
    CONSTRAINT `fk_post_task` FOREIGN KEY (`task_id`) REFERENCES `crawl_tasks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='帖子详情爬取任务';

-- ----------------------------
-- Table structure for task_execution_log
-- ----------------------------
DROP TABLE IF EXISTS `task_execution_log`;
CREATE TABLE `task_execution_log` (
    `id` int NOT NULL AUTO_INCREMENT COMMENT '日志ID',
    `task_id` int NOT NULL COMMENT '任务ID',
    `start_time` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    `end_time` timestamp NULL COMMENT '结束时间',
    `status` varchar(20) DEFAULT 'running' COMMENT '执行状态',
    `items_processed` int DEFAULT 0 COMMENT '处理项目数量',
    `log_message` text DEFAULT NULL COMMENT '日志信息',
    PRIMARY KEY (`id`),
    KEY `idx_log_task_id` (`task_id`),
    CONSTRAINT `fk_log_task` FOREIGN KEY (`task_id`) REFERENCES `crawl_tasks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='任务执行日志';
