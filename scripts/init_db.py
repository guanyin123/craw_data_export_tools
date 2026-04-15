#!/usr/bin/env python3
"""
数据库初始化脚本

用法:
    python scripts/init_db.py           # 初始化数据库
    python scripts/init_db.py --drop    # 删除所有表后重新创建
    python scripts/init_db.py --check   # 检查数据库连接
    python scripts/init_db.py --version # 显示版本信息
"""
import sys
from pathlib import Path

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from models.database import init_db, engine, Base, check_connection
    from models.models import Item, Keyword, Trend, KeywordItem
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("请确保在项目根目录运行此脚本，且已安装所有依赖:")
    print("  pip install sqlalchemy fastapi uvicorn")
    sys.exit(1)


# 数据库 schema 版本
SCHEMA_VERSION = "1.0.0"


def drop_all_tables():
    """删除所有表（慎用）"""
    confirm = input("⚠️  确认删除所有表？这将清空所有数据！(yes/no): ")
    if confirm.lower() == "yes":
        try:
            with engine.begin() as conn:
                Base.metadata.drop_all(bind=conn)
            print("✅ 所有表已删除")
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            raise
    else:
        print("❌ 取消操作")


def check_db_connection():
    """检查数据库连接状态"""
    print("检查数据库连接...")
    if check_connection():
        print("✅ 数据库连接正常")
        return True
    else:
        print("❌ 数据库连接失败")
        return False


def show_version():
    """显示版本信息"""
    print(f"数据库 Schema 版本: {SCHEMA_VERSION}")
    print(f"数据库路径: {engine.url}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="数据库初始化脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/init_db.py           # 初始化数据库
  python scripts/init_db.py --drop    # 删除所有表后重新创建
  python scripts/init_db.py --check   # 检查数据库连接
  python scripts/init_db.py --version # 显示版本信息
        """
    )
    parser.add_argument("--drop", action="store_true", help="删除所有表后重新创建")
    parser.add_argument("--check", action="store_true", help="检查数据库连接")
    parser.add_argument("--version", action="store_true", help="显示版本信息")
    args = parser.parse_args()

    # 显示版本
    if args.version:
        show_version()
        return

    # 检查连接
    if args.check:
        check_db_connection()
        return

    # 删除表
    if args.drop:
        drop_all_tables()
        print()

    # 检查连接后再初始化
    if not check_db_connection():
        print("❌ 数据库连接失败，无法初始化")
        sys.exit(1)

    # 初始化数据库
    try:
        init_db()

        # 显示创建的表
        print("\n📊 已创建的表:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")

        print(f"\n💾 数据库文件: {engine.url.database}")
        print(f"📋 Schema 版本: {SCHEMA_VERSION}")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
