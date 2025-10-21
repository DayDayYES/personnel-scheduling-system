# -*- coding: utf-8 -*-
"""
测试脚本 - 查看数据库中的表
"""

import mysql.connector
from mysql.connector import Error

def list_database_tables():
    """列出数据库中的所有表"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="123456",
            database="secret"
        )
        
        if connection.is_connected():
            print("✅ 成功连接到数据库: secret\n")
            
            cursor = connection.cursor()
            
            # 查询所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"📋 数据库中的表 (共 {len(tables)} 个):")
            print("=" * 60)
            
            process_tables = []
            schedule_tables = []
            other_tables = []
            
            for table in tables:
                table_name = table[0]
                if table_name.startswith('process_'):
                    process_tables.append(table_name)
                elif table_name.startswith('task_schedule_'):
                    schedule_tables.append(table_name)
                else:
                    other_tables.append(table_name)
            
            # 显示工序表
            if process_tables:
                print("\n🔧 工序表:")
                for table_name in sorted(process_tables):
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    count = cursor.fetchone()[0]
                    print(f"  - {table_name}: {count} 条工序记录")
            
            # 显示调度结果表
            if schedule_tables:
                print("\n📅 调度结果表:")
                for table_name in sorted(schedule_tables)[-5:]:  # 只显示最近5个
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    count = cursor.fetchone()[0]
                    print(f"  - {table_name}: {count} 条记录")
                if len(schedule_tables) > 5:
                    print(f"  ... 还有 {len(schedule_tables) - 5} 个调度表")
            
            # 显示其他表
            if other_tables:
                print("\n📦 其他表:")
                for table_name in sorted(other_tables):
                    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                    count = cursor.fetchone()[0]
                    print(f"  - {table_name}: {count} 条记录")
            
            print("\n" + "=" * 60)
            
            # 如果有工序表，显示详细信息
            if process_tables:
                print("\n🔍 工序表详细信息:")
                for table_name in sorted(process_tables):
                    print(f"\n表: {table_name}")
                    cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 3")
                    rows = cursor.fetchall()
                    if rows:
                        print(f"  前3条记录:")
                        for row in rows:
                            print(f"    ID={row[0]}, 工序={row[1]}, 阶段={row[2]}, 团队={row[3]}, 人数={row[5]}, 时长={row[6]}")
            
            cursor.close()
            connection.close()
            print("\n✅ 数据库连接已关闭")
            
    except Error as e:
        print(f"❌ 数据库操作失败: {e}")

if __name__ == '__main__':
    list_database_tables()

