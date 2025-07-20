from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timedelta
import asyncpg
import os
from .models import LogEntry, LogFilter, LogResponse
from .auth import get_current_user

router = APIRouter(prefix="/api/logs", tags=["logs"])

async def get_db_connection():
    """获取数据库连接"""
    return await asyncpg.connect(os.getenv("SUPABASE_DB_URL"))

@router.get("/", response_model=LogResponse)
async def get_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    level: Optional[str] = Query(None, description="日志级别: INFO, WARNING, ERROR"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取系统日志
    - 支持分页、筛选、搜索
    - 按时间倒序返回
    """
    try:
        conn = await get_db_connection()
        
        # 构建查询条件
        conditions = ["1=1"]
        params = []
        param_count = 0
        
        if level:
            param_count += 1
            conditions.append(f"log_level = ${param_count}")
            params.append(level.upper())
        
        if start_date:
            param_count += 1
            conditions.append(f"created_at >= ${param_count}")
            params.append(start_date)
        
        if end_date:
            param_count += 1
            conditions.append(f"created_at <= ${param_count}")
            params.append(end_date)
        
        if search:
            param_count += 1
            conditions.append(f"(message ILIKE ${param_count} OR operation ILIKE ${param_count})")
            params.extend([f"%{search}%", f"%{search}%"])
            param_count += 1
        
        where_clause = " AND ".join(conditions)
        
        # 获取总数
        count_query = f"""
            SELECT COUNT(*) FROM system_logs 
            WHERE {where_clause}
        """
        total = await conn.fetchval(count_query, *params)
        
        # 获取日志数据
        offset = (page - 1) * limit
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count
        
        logs_query = f"""
            SELECT log_id, log_level, operation, message, user_account, 
                   platform, ip_address, user_agent, created_at
            FROM system_logs 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${limit_param} OFFSET ${offset_param}
        """
        params.extend([limit, offset])
        
        rows = await conn.fetch(logs_query, *params)
        
        logs = []
        for row in rows:
            logs.append(LogEntry(
                log_id=row['log_id'],
                level=row['log_level'],
                operation=row['operation'],
                message=row['message'],
                user_account=row['user_account'],
                platform=row['platform'],
                ip_address=row['ip_address'],
                user_agent=row['user_agent'],
                timestamp=row['created_at']
            ))
        
        await conn.close()
        
        return LogResponse(
            logs=logs,
            total=total,
            page=page,
            limit=limit,
            has_next=page * limit < total
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")

@router.get("/stats")
async def get_log_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    """
    获取日志统计信息
    - 按级别统计数量
    - 按日期统计趋势
    """
    try:
        conn = await get_db_connection()
        
        start_date = datetime.now() - timedelta(days=days)
        
        # 按级别统计
        level_stats_query = """
            SELECT log_level, COUNT(*) as count
            FROM system_logs 
            WHERE created_at >= $1
            GROUP BY log_level
            ORDER BY count DESC
        """
        level_stats = await conn.fetch(level_stats_query, start_date)
        
        # 按日期统计
        daily_stats_query = """
            SELECT DATE(created_at) as date, 
                   COUNT(*) as total,
                   COUNT(*) FILTER (WHERE log_level = 'ERROR') as errors,
                   COUNT(*) FILTER (WHERE log_level = 'WARNING') as warnings
            FROM system_logs 
            WHERE created_at >= $1
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """
        daily_stats = await conn.fetch(daily_stats_query, start_date)
        
        # 最近活跃用户
        user_stats_query = """
            SELECT user_account, COUNT(*) as operations
            FROM system_logs 
            WHERE created_at >= $1 AND user_account IS NOT NULL
            GROUP BY user_account
            ORDER BY operations DESC
            LIMIT 10
        """
        user_stats = await conn.fetch(user_stats_query, start_date)
        
        await conn.close()
        
        return {
            "period_days": days,
            "level_stats": [dict(row) for row in level_stats],
            "daily_stats": [dict(row) for row in daily_stats],
            "active_users": [dict(row) for row in user_stats]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")

@router.delete("/cleanup")
async def cleanup_logs(
    days: int = Query(30, ge=1),
    current_user: dict = Depends(get_current_user)
):
    """
    清理旧日志
    - 删除指定天数之前的日志
    - 需要管理员权限
    """
    # 检查管理员权限
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    try:
        conn = await get_db_connection()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        delete_query = """
            DELETE FROM system_logs 
            WHERE created_at < $1
        """
        
        result = await conn.execute(delete_query, cutoff_date)
        deleted_count = int(result.split()[-1])
        
        await conn.close()
        
        # 记录清理操作
        await log_operation(
            level="INFO",
            operation="日志清理",
            message=f"清理了 {deleted_count} 条 {days} 天前的日志",
            user_account=current_user["account"]
        )
        
        return {
            "message": f"成功清理 {deleted_count} 条日志",
            "cutoff_date": cutoff_date,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理日志失败: {str(e)}")

async def log_operation(
    level: str,
    operation: str, 
    message: str,
    user_account: Optional[str] = None,
    platform: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """
    记录系统操作日志
    """
    try:
        conn = await get_db_connection()
        
        insert_query = """
            INSERT INTO system_logs 
            (log_level, operation, message, user_account, platform, ip_address, user_agent)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        await conn.execute(
            insert_query,
            level.upper(),
            operation,
            message,
            user_account,
            platform,
            ip_address,
            user_agent
        )
        
        await conn.close()
        
    except Exception as e:
        # 日志记录失败不应该影响主业务
        print(f"日志记录失败: {str(e)}")