# -*- coding: utf-8 -*-
"""
数据库连接模块 - 用于将调度结果存储到MySQL数据库
"""

import mysql.connector
from mysql.connector import Error

class DatabaseConnector:
    """数据库连接器，用于存储调度结果"""
    
    def __init__(self, host="localhost", user="root", password="123456", database="scheduling_system"):
        """初始化数据库连接"""
        self.connection_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database
        }
        self.connection = None
        
    def connect(self):
        """建立数据库连接"""
        try:
            self.connection = mysql.connector.connect(**self.connection_config)
            print("✅ 数据库连接成功")
            return True
        except Error as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
            
    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ 数据库连接已关闭")
            
    def save_task_schedule(self, record):
        """保存工序调度明细"""
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
                
        try:
            cursor = self.connection.cursor()
            
            # 获取当前时间作为表名后缀
            cursor.execute("SELECT DATE_FORMAT(NOW(), '%Y%m%d_%H%i%s')")
            time_suffix = cursor.fetchone()[0]
            table_name = f"task_schedule_{time_suffix}"
            
            # 创建新表
            create_table_sql = f"""
            CREATE TABLE {table_name} (
                task_id INT,
                task_name VARCHAR(100),
                team VARCHAR(50),
                start_time FLOAT,
                end_time FLOAT,
                duration FLOAT,
                workers INT,
                PRIMARY KEY (task_id)
            )
            """
            cursor.execute(create_table_sql)
            
            # 解析调度记录
            lines = record.split('\n')
            schedule_data = []
            
            for line in lines:
                # 跳过标题行、分隔线和空行
                if not line or line.startswith('工序') or line.startswith('---'):
                    continue
                    
                # 分割每行数据，确保正确处理中文和空格
                parts = line.split()
                if len(parts) >= 6:
                    task_name = parts[0]
                    team = parts[1]
                    start_time = float(parts[2])
                    end_time = float(parts[3])
                    duration = float(parts[4])
                    workers = int(parts[5])
                    
                    schedule_data.append((task_name, team, start_time, end_time, duration, workers))
            
            # 按开始时间排序
            schedule_data.sort(key=lambda x: x[2])
            
            # 插入数据
            query = f"""
            INSERT INTO {table_name} 
            (task_id, task_name, team, start_time, end_time, duration, workers) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            for i, task in enumerate(schedule_data, 1):
                values = (i,) + task
                cursor.execute(query, values)
            
            self.connection.commit()
            print(f"✅ 已保存 {len(schedule_data)} 条调度记录到表 {table_name}")
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ 保存调度记录失败: {e}")
            self.connection.rollback()
            return False