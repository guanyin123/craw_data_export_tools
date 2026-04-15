"""
数据库连接管理模块
"""
from pathlib import Path
import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool

# 配置日志
logger = logging.getLogger(__name__)

# 数据库文件路径
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "opportunity.db"

# 确保数据目录存在
DB_DIR.mkdir(parents=True, exist_ok=True)

# 数据库连接 URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 创建引擎 - SQLite 使用 NullPool 避免文件锁定问题
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 需要
    echo=False,  # 生产环境设为 False，调试时可设为 True
    poolclass=NullPool,  # SQLite 不需要连接池
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _connection_record):
    """
    设置 SQLite 优化参数
    - WAL 模式: 提高并发性能
    - NORMAL 同步: 在性能和安全之间平衡
    """
    cursor = dbapi_conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
    except Exception as e:
        logger.warning(f"设置 SQLite PRAGMA 失败: {e}")


# 创建 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


def get_db():
    """
    获取数据库会话的依赖注入函数
    用于 FastAPI 依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        raise
    finally:
        db.close()


def check_connection() -> bool:
    """
    检查数据库连接状态

    Returns:
        bool: 连接是否正常
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False


def init_db():
    """
    初始化数据库，创建所有表
    """
    from .models import Item, Keyword, Trend, KeywordItem

    Base.metadata.create_all(bind=engine)
    print(f"数据库初始化完成: {DB_PATH}")
