"""
同步 SQLite checkpoint 和 MySQL 记录
删除 MySQL 中不存在的 checkpoint
"""
import sqlite3
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from backend.config import SessionLocal
from backend.models import InterviewRecord, ConsultantRecord

# SQLite 数据库路径
CHECKPOINT_DB = Path("checkpoints-sqlite/checkpoints.sqlite")

if not CHECKPOINT_DB.exists():
    print(f"❌ 数据库文件不存在: {CHECKPOINT_DB}")
    exit(1)

# 连接数据库
sqlite_conn = sqlite3.connect(str(CHECKPOINT_DB))
sqlite_cursor = sqlite_conn.cursor()
mysql_db = SessionLocal()

print("=" * 80)
print("🔄 同步 SQLite Checkpoint 和 MySQL 记录")
print("=" * 80)

try:
    # 1. 获取 SQLite 中的所有 thread_id
    sqlite_cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
    sqlite_thread_ids = set(row[0] for row in sqlite_cursor.fetchall())
    print(f"\n📊 SQLite 中有 {len(sqlite_thread_ids)} 个 thread_id")
    
    # 2. 获取 MySQL 中的所有 thread_id
    interview_ids = set(record.thread_id for record in mysql_db.query(InterviewRecord).all())
    consultant_ids = set(record.thread_id for record in mysql_db.query(ConsultantRecord).all())
    mysql_thread_ids = interview_ids | consultant_ids
    print(f"📊 MySQL 中有 {len(mysql_thread_ids)} 个 thread_id")
    print(f"   - 面试记录: {len(interview_ids)} 个")
    print(f"   - 顾问记录: {len(consultant_ids)} 个")
    
    # 3. 找出孤儿 checkpoint（在 SQLite 但不在 MySQL）
    orphan_thread_ids = sqlite_thread_ids - mysql_thread_ids
    
    if not orphan_thread_ids:
        print("\n✅ 没有孤儿 checkpoint，数据已同步")
    else:
        print(f"\n⚠️  发现 {len(orphan_thread_ids)} 个孤儿 checkpoint:")
        for thread_id in orphan_thread_ids:
            # 统计该 thread_id 的 checkpoint 数量
            sqlite_cursor.execute("SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?", (thread_id,))
            count = sqlite_cursor.fetchone()[0]
            print(f"   - {thread_id}: {count} 个 checkpoint")
        
        # 4. 询问是否删除
        confirm = input("\n是否删除这些孤儿 checkpoint? (y/n): ").strip().lower()
        
        if confirm == 'y':
            deleted_checkpoints = 0
            deleted_writes = 0
            
            for thread_id in orphan_thread_ids:
                # 删除 checkpoints
                sqlite_cursor.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
                deleted_checkpoints += sqlite_cursor.rowcount
                
                # 删除 writes
                sqlite_cursor.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
                deleted_writes += sqlite_cursor.rowcount
            
            sqlite_conn.commit()
            print(f"\n✅ 已删除:")
            print(f"   - {deleted_checkpoints} 条 checkpoint 记录")
            print(f"   - {deleted_writes} 条 writes 记录")
        else:
            print("\n❌ 已取消删除")
    
    # 5. 显示最终状态
    sqlite_cursor.execute("SELECT COUNT(*) FROM checkpoints")
    final_count = sqlite_cursor.fetchone()[0]
    print(f"\n📊 当前 SQLite 中有 {final_count} 条 checkpoint 记录")
    
    # 6. 显示剩余的 thread_id 列表
    sqlite_cursor.execute("""
        SELECT thread_id, COUNT(*) as count 
        FROM checkpoints 
        GROUP BY thread_id 
        ORDER BY count DESC
    """)
    remaining_threads = sqlite_cursor.fetchall()
    
    print(f"\n📋 剩余的 Thread ID 列表 (共 {len(remaining_threads)} 个):")
    print(f"{'Thread ID':<50} {'Checkpoint 数量':<20} {'类型':<20}")
    print("-" * 90)
    
    for thread_id, count in remaining_threads:
        # 判断类型
        if thread_id in interview_ids:
            record_type = "面试记录 ✅"
        elif thread_id in consultant_ids:
            record_type = "顾问记录 ✅"
        else:
            record_type = "⚠️  未找到记录"
        
        print(f"{thread_id:<50} {count:<20} {record_type:<20}")

except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    sqlite_conn.close()
    mysql_db.close()

print("\n" + "=" * 80)
print("✅ 完成")
print("=" * 80)
