import pymysql
from config import settings
import logging
from typing import Optional, Generator
from dbutils.pooled_db import PooledDB
from pymysql import connections
from contextlib import contextmanager

logger = logging.getLogger(__name__)  # 日志记录器：有则返回已有实例，无则新建

_pool: Optional[PooledDB] = None


def init_db_pool() -> None:
    """初始化数据库连接池（在应用启动时调用）"""
    global _pool
    if _pool is not None:
        return

    try:
        _pool = PooledDB(
            # 连接池多出来的设置
            creator=pymysql,  # 使用pymysql创建连接,
            maxconnections=settings.POOL_MAX_SIZE,
            mincached=settings.POOL_MIN_SIZE,
            maxcached=settings.POOL_MAX_SIZE,
            maxshared=0,  # 不共享连接
            blocking=True,  # True：当达到最大连接数后，阻塞等待，False：直接抛出异常TooManyConnections
            maxusage=None,  # 无限复用
            setsession=[f"SET NAMES {settings.MYSQL_CHARSET}"],
            ping=1,  # 每次获取连接时检查可用性
            autocommit=False,  # 手动控制事务
            connect_timeout=settings.POOL_CONN_TIMEOUT,
            cursorclass=pymysql.cursors.DictCursor,  # 返回字典而非元组，便于前端读取
            # conn本有的设置
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset="utf8mb4",  # 支持emoji完整utf8
        )
        logger.info("MySQL 连接池初始化成功")
    except Exception as e:
        logger.error(f"MySQL 连接池初始化失败：{e}")
        raise


def get_connection() -> connections.Connection:
    """从连接池获取一个连接（调用者需负责关闭连接）"""
    if _pool is None:
        init_db_pool()
    return _pool.connection()


@contextmanager
def get_db_cursor(commit: bool = True) -> Generator[connections.Connection, None, None]:
    """
    Generator解析：
    语法格式：Generator[YieldType, SendType, ReturnType]
    YieldType：函数里yield xxx抛出去的数据类型；
    SendType：是否需要用.send()向生成器内部传值，如果又generator.send(xxx)的需求，这里就填写对应类型；
    ReturnType：生成器函数结束时return携带的值的类型，函数中没有写return xxx，函数结束无返回值，填None。

    上下文管理器，自动提交/回滚事务并释放连接。
    用法：
        with get_db_cursor() as conn:
            cursor=conn.cursor()
            cursor.execute("select * from users")
            result=cursor.fetchall()
            # 如果commit = True，退出时自动提交
    """
    conn = get_connection()
    try:
        yield conn  # 函数暂停在此处，将连接返回给调用者，等调用者的内容全部执行完毕，返回继续往下执行
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

# 快捷方式：提供get_db()用于FastAPI依赖注入
def get_db() -> Generator[connections.Connection, None, None]:
    """FastAPI依赖注入函数，在每个请求中提供数据库连接"""
    with get_db_cursor() as conn:
        yield conn

# 测试连接
def test_connection()->bool:
    try:
         with get_db_cursor() as conn:
            cursor=conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"数据库测试失败：{e}")
        return False