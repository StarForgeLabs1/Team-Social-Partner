from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum

# 枚举类型定义
class PlatformType(str, Enum):
    """支持的社交平台类型"""
    WEIBO = "weibo"
    WECHAT = "wechat"
    DOUYIN = "douyin"
    XIAOHONGSHU = "xiaohongshu"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"

class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ContentType(str, Enum):
    """内容类型"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    MIXED = "mixed"

# 用户相关模型
class User(BaseModel):
    """用户基础模型"""
    account: str = Field(..., description="用户账号", min_length=1, max_length=100)
    platform: PlatformType = Field(..., description="所属平台")
    password_hash: Optional[str] = Field(None, description="密码哈希")
    is_active: bool = Field(True, description="是否激活")
    is_admin: bool = Field(False, description="是否管理员")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class UserResponse(BaseModel):
    """用户响应模型"""
    account: str
    platform: PlatformType
    is_active: bool
    is_admin: bool
    created_at: Optional[datetime]
    last_login: Optional[datetime]

class UserCreate(BaseModel):
    """用户创建模型"""
    account: str = Field(..., min_length=1, max_length=100)
    platform: PlatformType
    password: str = Field(..., min_length=6, max_length=128)
    is_admin: bool = Field(False)

class UserUpdate(BaseModel):
    """用户更新模型"""
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

# 认证相关模型
class LoginRequest(BaseModel):
    """登录请求模型"""
    account: str = Field(..., description="用户账号")
    platform: PlatformType = Field(..., description="平台类型")
    password: str = Field(..., description="密码")

class RegisterRequest(BaseModel):
    """注册请求模型"""
    account: str = Field(..., min_length=1, max_length=100)
    platform: PlatformType
    password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('密码不匹配')
        return v

class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    user: UserResponse

# API密钥相关模型
class APIKey(BaseModel):
    """API密钥模型"""
    key_id: Optional[int] = Field(None, description="密钥ID")
    key_name: str = Field(..., description="密钥名称", max_length=100)
    key_value: str = Field(..., description="密钥值", max_length=500)
    platform: PlatformType = Field(..., description="关联平台")
    user_account: str = Field(..., description="所属用户")
    is_active: bool = Field(True, description="是否激活")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class APIKeyCreate(BaseModel):
    """API密钥创建模型"""
    key_name: str = Field(..., max_length=100)
    key_value: str = Field(..., max_length=500)
    platform: PlatformType

class APIKeyUpdate(BaseModel):
    """API密钥更新模型"""
    key_name: Optional[str] = Field(None, max_length=100)
    key_value: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class APIKeyResponse(BaseModel):
    """API密钥响应模型"""
    key_id: int
    key_name: str
    platform: PlatformType
    is_active: bool
    created_at: datetime
    # 注意：响应中不包含实际密钥值以保证安全

# 内容相关模型
class Content(BaseModel):
    """内容模型"""
    content_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=200)
    text_content: Optional[str] = Field(None, max_length=5000)
    media_urls: Optional[List[str]] = Field(default_factory=list)
    content_type: ContentType = ContentType.TEXT
    platforms: List[PlatformType] = Field(..., min_items=1)
    user_account: str
    is_published: bool = Field(False)
    scheduled_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ContentCreate(BaseModel):
    """内容创建模型"""
    title: Optional[str] = Field(None, max_length=200)
    text_content: Optional[str] = Field(None, max_length=5000)
    media_urls: Optional[List[str]] = Field(default_factory=list)
    content_type: ContentType = ContentType.TEXT
    platforms: List[PlatformType] = Field(..., min_items=1)
    scheduled_time: Optional[datetime] = None
    
    @validator('text_content', 'media_urls')
    def content_required(cls, v, values, **kwargs):
        """至少需要文本内容或媒体文件"""
        text_content = values.get('text_content')
        media_urls = v if 'media_urls' in kwargs.get('field', {}).name else values.get('media_urls', [])
        
        if not text_content and not media_urls:
            raise ValueError('至少需要提供文本内容或媒体文件')
        return v

class ContentUpdate(BaseModel):
    """内容更新模型"""
    title: Optional[str] = Field(None, max_length=200)
    text_content: Optional[str] = Field(None, max_length=5000)
    media_urls: Optional[List[str]] = None
    content_type: Optional[ContentType] = None
    platforms: Optional[List[PlatformType]] = None
    scheduled_time: Optional[datetime] = None

class ContentResponse(BaseModel):
    """内容响应模型"""
    content_id: int
    title: Optional[str]
    text_content: Optional[str]
    media_urls: List[str]
    content_type: ContentType
    platforms: List[PlatformType]
    user_account: str
    is_published: bool
    scheduled_time: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

# 自动化任务相关模型
class AutomationTask(BaseModel):
    """自动化任务模型"""
    task_id: Optional[int] = None
    task_name: str = Field(..., max_length=200)
    task_type: str = Field(..., max_length=50)  # 如: "scheduled_post", "auto_reply", "data_sync"
    platform: PlatformType
    user_account: str
    config: Dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    is_active: bool = Field(True)
    cron_expression: Optional[str] = Field(None, description="定时任务表达式")
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    run_count: int = Field(0, description="执行次数")
    success_count: int = Field(0, description="成功次数")
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AutomationTaskCreate(BaseModel):
    """自动化任务创建模型"""
    task_name: str = Field(..., max_length=200)
    task_type: str = Field(..., max_length=50)
    platform: PlatformType
    config: Dict[str, Any] = Field(default_factory=dict)
    cron_expression: Optional[str] = None
    
    @validator('cron_expression')
    def validate_cron(cls, v):
        """验证cron表达式格式"""
        if v and len(v.split()) != 5:
            raise ValueError('无效的cron表达式格式')
        return v

class AutomationTaskUpdate(BaseModel):
    """自动化任务更新模型"""
    task_name: Optional[str] = Field(None, max_length=200)
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    cron_expression: Optional[str] = None

class AutomationTaskResponse(BaseModel):
    """自动化任务响应模型"""
    task_id: int
    task_name: str
    task_type: str
    platform: PlatformType
    user_account: str
    config: Dict[str, Any]
    status: TaskStatus
    is_active: bool
    cron_expression: Optional[str]
    next_run_time: Optional[datetime]
    last_run_time: Optional[datetime]
    run_count: int
    success_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

# 日志相关模型
class LogEntry(BaseModel):
    """日志条目模型"""
    log_id: Optional[int] = None
    level: LogLevel
    operation: str = Field(..., max_length=100)
    message: str = Field(..., max_length=1000)
    user_account: Optional[str] = None
    platform: Optional[PlatformType] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: Optional[datetime] = None
    
class LogFilter(BaseModel):
    """日志过滤模型"""
    level: Optional[LogLevel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_account: Optional[str] = None
    platform: Optional[PlatformType] = None
    search: Optional[str] = None

class LogResponse(BaseModel):
    """日志响应模型"""
    logs: List[LogEntry]
    total: int
    page: int
    limit: int
    has_next: bool

# 统计相关模型
class PlatformStats(BaseModel):
    """平台统计模型"""
    platform: PlatformType
    user_count: int = 0
    content_count: int = 0
    task_count: int = 0
    active_tasks: int = 0
    last_activity: Optional[datetime] = None

class UserStats(BaseModel):
    """用户统计模型"""
    account: str
    platform: PlatformType
    content_count: int = 0
    task_count: int = 0
    login_count: int = 0
    last_login: Optional[datetime] = None
    created_at: datetime

class SystemStats(BaseModel):
    """系统统计模型"""
    total_users: int = 0
    total_content: int = 0
    total_tasks: int = 0
    active_tasks: int = 0
    platform_stats: List[PlatformStats] = Field(default_factory=list)
    recent_activities: List[LogEntry] = Field(default_factory=list)

# 响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# 文件上传相关模型
class FileUpload(BaseModel):
    """文件上传模型"""
    file_id: Optional[int] = None
    filename: str
    original_name: str
    file_type: str
    file_size: int
    file_path: str
    user_account: str
    platform: Optional[PlatformType] = None
    is_public: bool = Field(False)
    upload_time: Optional[datetime] = None

class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: int
    filename: str
    file_url: str
    file_type: str
    file_size: int
    upload_time: datetime

# 配置相关模型
class SystemConfig(BaseModel):
    """系统配置模型"""
    config_key: str = Field(..., max_length=100)
    config_value: str = Field(..., max_length=1000)
    config_type: str = Field("string", max_length=20)  # string, integer, boolean, json
    description: Optional[str] = Field(None, max_length=500)
    is_public: bool = Field(False, description="是否为公开配置")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SystemConfigUpdate(BaseModel):
    """系统配置更新模型"""
    config_value: str = Field(..., max_length=1000)
    description: Optional[str] = Field(None, max_length=500)

# 通知相关模型
class Notification(BaseModel):
    """通知模型"""
    notification_id: Optional[int] = None
    title: str = Field(..., max_length=200)
    content: str = Field(..., max_length=1000)
    notification_type: str = Field(..., max_length=50)  # info, warning, error, success
    user_account: Optional[str] = None  # None表示系统广播
    is_read: bool = Field(False)
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

class NotificationCreate(BaseModel):
    """通知创建模型"""
    title: str = Field(..., max_length=200)
    content: str = Field(..., max_length=1000)
    notification_type: str = Field("info", max_length=50)
    user_account: Optional[str] = None

class NotificationResponse(BaseModel):
    """通知响应模型"""
    notification_id: int
    title: str
    content: str
    notification_type: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]

# 导出所有模型
__all__ = [
    # 枚举
    "PlatformType", "LogLevel", "TaskStatus", "ContentType",
    # 用户相关
    "User", "UserResponse", "UserCreate", "UserUpdate",
    # 认证相关
    "LoginRequest", "RegisterRequest", "TokenResponse",
    # API密钥相关
    "APIKey", "APIKeyCreate", "APIKeyUpdate", "APIKeyResponse",
    # 内容相关
    "Content", "ContentCreate", "ContentUpdate", "ContentResponse",
    # 自动化任务相关
    "AutomationTask", "AutomationTaskCreate", "AutomationTaskUpdate", "AutomationTaskResponse",
    # 日志相关
    "LogEntry", "LogFilter", "LogResponse",
    # 统计相关
    "PlatformStats", "UserStats", "SystemStats",
    # 响应相关
    "BaseResponse", "PaginatedResponse", "ErrorResponse",
    # 文件相关
    "FileUpload", "FileUploadResponse",
    # 配置相关
    "SystemConfig", "SystemConfigUpdate",
    # 通知相关
    "Notification", "NotificationCreate", "NotificationResponse",
]