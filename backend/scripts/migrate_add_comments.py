"""添加评论相关字段到 items 表"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from models.database import engine

def migrate():
    """执行迁移"""
    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("PRAGMA table_info(items)"))
        columns = [row[1] for row in result]

        if "comment_summary" in columns:
            print("字段已存在，跳过迁移")
            return

        # 添加新字段
        conn.execute(text(
            "ALTER TABLE items ADD COLUMN comment_summary TEXT"
        ))
        conn.execute(text(
            "ALTER TABLE items ADD COLUMN top_comment_score INTEGER"
        ))
        conn.commit()
        print("迁移完成: 添加 comment_summary, top_comment_score 字段")

if __name__ == "__main__":
    migrate()
