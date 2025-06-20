# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。 

from typing import List, Dict, Any, Optional


class TaskConfig:
    """任务配置基类，包含所有任务类型共有的配置"""
    
    def __init__(
        self, 
        platform: str,
        task_type: str,
        login_type: str = "qrcode",
        cookies: str = "",
        save_data_option: str = "json",
        enable_get_comments: bool = True,
        enable_get_sub_comments: bool = False
    ):
        """
        初始化任务配置
        
        Args:
            platform: 平台名称 (xhs, dy, ks, bili, wb, tieba, zhihu)
            task_type: 任务类型 (search, detail, creator)
            login_type: 登录类型 (qrcode, phone, cookie)
            cookies: Cookie字符串，用于cookie登录方式
            save_data_option: 数据保存方式 (csv, db, json)
            enable_get_comments: 是否获取一级评论
            enable_get_sub_comments: 是否获取二级评论
        """
        self.platform = platform
        self.task_type = task_type
        self.login_type = login_type
        self.cookies = cookies
        self.save_data_option = save_data_option
        self.enable_get_comments = enable_get_comments
        self.enable_get_sub_comments = enable_get_sub_comments


class SearchTaskConfig(TaskConfig):
    """搜索任务配置"""
    
    def __init__(
        self,
        platform: str,
        keywords: List[str],
        sort_type: str = "popularity_descending",
        publish_time_type: int = 0,
        start_page: int = 0,
        **kwargs
    ):
        """
        初始化搜索任务配置
        
        Args:
            platform: 平台名称
            keywords: 搜索关键词列表
            sort_type: 排序方式 (popularity_descending 等)
            publish_time_type: 发布时间类型
            start_page: 起始页码
            **kwargs: 传递给基类的其他参数
        """
        super().__init__(platform=platform, task_type="search", **kwargs)
        self.keywords = keywords
        self.keywords_str = ",".join(keywords) if keywords else ""
        self.sort_type = sort_type
        self.publish_time_type = publish_time_type
        self.start_page = start_page


class CreatorTaskConfig(TaskConfig):
    """创作者爬取任务配置"""
    
    def __init__(
        self,
        platform: str,
        creator_ids: List[str],
        **kwargs
    ):
        """
        初始化创作者任务配置
        
        Args:
            platform: 平台名称
            creator_ids: 创作者ID列表
            **kwargs: 传递给基类的其他参数
        """
        super().__init__(platform=platform, task_type="creator", **kwargs)
        self.creator_ids = creator_ids


class DetailTaskConfig(TaskConfig):
    """帖子详情爬取任务配置"""
    
    def __init__(
        self,
        platform: str,
        post_ids: List[str],
        **kwargs
    ):
        """
        初始化帖子详情任务配置
        
        Args:
            platform: 平台名称
            post_ids: 帖子ID列表
            **kwargs: 传递给基类的其他参数
        """
        super().__init__(platform=platform, task_type="detail", **kwargs)
        self.post_ids = post_ids


def create_task_config_from_global_config(config_module) -> TaskConfig:
    """
    从全局配置创建任务配置对象
    
    Args:
        config_module: 全局配置模块
        
    Returns:
        TaskConfig: 对应的任务配置对象
    """
    # 获取共通参数
    common_params = {
        "platform": config_module.PLATFORM,
        "login_type": config_module.LOGIN_TYPE,
        "cookies": config_module.COOKIES,
        "save_data_option": config_module.SAVE_DATA_OPTION,
        "enable_get_comments": config_module.ENABLE_GET_COMMENTS,
        "enable_get_sub_comments": config_module.ENABLE_GET_SUB_COMMENTS,
    }
    
    # 根据爬取类型创建对应的配置对象
    if config_module.CRAWLER_TYPE == "search":
        keywords = config_module.KEYWORDS.split(",") if isinstance(config_module.KEYWORDS, str) else []
        return SearchTaskConfig(
            keywords=keywords,
            sort_type=config_module.SORT_TYPE,
            publish_time_type=config_module.PUBLISH_TIME_TYPE,
            start_page=config_module.START_PAGE,
            **common_params
        )
    
    elif config_module.CRAWLER_TYPE == "creator":
        # 根据平台获取创作者ID列表
        creator_ids = []
        platform = config_module.PLATFORM
        if platform == "xhs":
            creator_ids = config_module.XHS_CREATOR_ID_LIST
        elif platform == "dy":
            creator_ids = config_module.DY_CREATOR_ID_LIST
        elif platform == "bili":
            creator_ids = config_module.BILI_CREATOR_ID_LIST
        elif platform == "ks":
            creator_ids = config_module.KS_CREATOR_ID_LIST
        elif platform == "tieba":
            creator_ids = config_module.TIEBA_CREATOR_URL_LIST
        elif platform == "wb":
            creator_ids = config_module.WB_USER_URL_LIST
        elif platform == "zhihu":
            creator_ids = config_module.ZHIHU_CREATOR_ID_LIST
            
        return CreatorTaskConfig(
            creator_ids=creator_ids,
            **common_params
        )
    
    elif config_module.CRAWLER_TYPE == "detail":
        # 根据平台获取帖子ID列表
        post_ids = []
        platform = config_module.PLATFORM
        if platform == "xhs":
            post_ids = config_module.XHS_SPECIFIED_URL_LIST
        elif platform == "dy":
            post_ids = config_module.DOUYIN_SPECIFIED_URL_LIST
        elif platform == "bili":
            post_ids = config_module.BILI_SPECIFIED_VID_LIST
        elif platform == "ks":
            post_ids = config_module.KUAISHOU_SPECIFIED_URL_LIST
        elif platform == "tieba":
            post_ids = config_module.TIEBA_POST_URL_LIST
        elif platform == "wb":
            post_ids = config_module.WEIBO_SPECIFIED_POST_URL_LIST
        elif platform == "zhihu":
            post_ids = config_module.ZHIHU_SPECIFIED_URL_LIST
            
        return DetailTaskConfig(
            post_ids=post_ids,
            **common_params
        )
    
    # 默认返回基本配置
    return TaskConfig(**common_params, task_type=config_module.CRAWLER_TYPE)
