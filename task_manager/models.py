# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。 

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskModel:
    """任务基础模型"""
    def __init__(
        self,
        id: Optional[int] = None,
        platform: str = "",
        task_type: str = "",
        status: TaskStatus = TaskStatus.PENDING,
        priority: int = 5,
        created_at: Optional[datetime] = None,
        scheduled_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ):
        self.id = id
        self.platform = platform
        self.task_type = task_type
        self.status = status
        self.priority = priority
        self.created_at = created_at or datetime.now()
        self.scheduled_at = scheduled_at
        self.completed_at = completed_at
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "platform": self.platform,
            "task_type": self.task_type,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "scheduled_at": self.scheduled_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskModel':
        """从字典创建任务模型"""
        status = data.get("status")
        if isinstance(status, str):
            status = TaskStatus(status)
        
        return cls(
            id=data.get("id"),
            platform=data.get("platform", ""),
            task_type=data.get("task_type", ""),
            status=status,
            priority=data.get("priority", 5),
            created_at=data.get("created_at"),
            scheduled_at=data.get("scheduled_at"),
            completed_at=data.get("completed_at"),
            error_message=data.get("error_message")
        )


class SearchTaskModel(TaskModel):
    """搜索任务模型"""
    def __init__(
        self,
        keywords: List[str] = None,
        **kwargs
    ):
        super().__init__(task_type="search", **kwargs)
        self.keywords = keywords or []


class CreatorTaskModel(TaskModel):
    """创作者爬取任务模型"""
    def __init__(
        self,
        creator_ids: List[str] = None,
        **kwargs
    ):
        super().__init__(task_type="creator", **kwargs)
        self.creator_ids = creator_ids or []


class DetailTaskModel(TaskModel):
    """帖子详情爬取任务模型"""
    def __init__(
        self,
        post_ids: List[str] = None,
        **kwargs
    ):
        super().__init__(task_type="detail", **kwargs)
        self.post_ids = post_ids or []


class TaskExecutionLog:
    """任务执行日志"""
    def __init__(
        self,
        id: Optional[int] = None,
        task_id: int = 0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: str = "running",
        items_processed: int = 0,
        log_message: Optional[str] = None
    ):
        self.id = id
        self.task_id = task_id
        self.start_time = start_time or datetime.now()
        self.end_time = end_time
        self.status = status
        self.items_processed = items_processed
        self.log_message = log_message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "items_processed": self.items_processed,
            "log_message": self.log_message
        }
