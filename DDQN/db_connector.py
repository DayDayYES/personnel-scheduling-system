# -*- coding: utf-8 -*-
"""
数据库连接模块 - 用于将调度结果和工序数据存储到MySQL数据库
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
        """
        保存工序调度明细（旧方法，保留用于文本格式解析）
        已废弃，请使用 save_schedule_result() 方法
        """
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
    
    def save_schedule_result(self, schedule_data):
        """
        保存调度结果到数据库（新方法，推荐使用）
        
        Args:
            schedule_data: 调度结果列表，格式来自 env.get_schedule()
                [
                    {
                        'id': 1,
                        'name': '任务名称',
                        'workpoint_id': 'workpoint_1',
                        'workpoint_name': '设备1',
                        'team': 'team1',
                        'start': 0.0,
                        'end': 10.5,
                        'workers': 5,
                        'order': 1
                    },
                    ...
                ]
            makespan: 完工时间（可选）
            algorithm_name: 算法名称（可选，如 'DDQN', 'Greedy'）
        
        Returns:
            str: 表名，如果成功；None 如果失败
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor()
            
            # 生成表名
            cursor.execute("SELECT DATE_FORMAT(NOW(), '%Y%m%d_%H%i%s')")
            time_suffix = cursor.fetchone()[0]
            table_name = f"schedule_result_{time_suffix}"
            
            # 构建表注释
            comment_parts = []
            # if algorithm_name:
            #     comment_parts.append(f"算法:{algorithm_name}")
            # if makespan is not None:
            #     comment_parts.append(f"完工时间:{makespan:.2f}")
            table_comment = ''.join(comment_parts) if comment_parts else '调度结果'
            
            # 检查表是否存在，如果存在则删除
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{self.connection_config['database']}' 
                AND table_name = '{table_name}'
            """)
            
            if cursor.fetchone()[0] > 0:
                print(f"ℹ️  表 {table_name} 已存在，删除旧表...")
                cursor.execute(f"DROP TABLE `{table_name}`")
            
            # 创建新表（简化字段，优化显示格式）
            create_table_sql = f"""
            CREATE TABLE `{table_name}` (
                `task_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务序号',
                `task_name` VARCHAR(100) NOT NULL COMMENT '任务名称',
                `workpoint_id` INT NOT NULL COMMENT '设备ID（1,2,3...）',
                `workpoint_name` VARCHAR(50) NOT NULL COMMENT '设备名称',
                `team_id` INT NOT NULL COMMENT '团队ID（1,2,3...）',
                `team_name` VARCHAR(50) NOT NULL COMMENT '团队名称（团队1,团队2...）',
                `start_time` DECIMAL(10,2) NOT NULL COMMENT '开始时间',
                `end_time` DECIMAL(10,2) NOT NULL COMMENT '结束时间',
                `duration` DECIMAL(10,2) NOT NULL COMMENT '持续时间',
                `workers` INT NOT NULL COMMENT '分配工人数',
                `process_order` INT COMMENT '工序顺序',
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                INDEX `idx_workpoint` (`workpoint_id`),
                INDEX `idx_team` (`team_id`),
                INDEX `idx_start_time` (`start_time`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
            COMMENT='{table_comment}';
            """
            cursor.execute(create_table_sql)
            
            # 插入数据
            insert_query = f"""
            INSERT INTO `{table_name}` 
            (task_name, workpoint_id, workpoint_name, team_id, team_name,
             start_time, end_time, duration, workers, process_order)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            insert_count = 0
            for task in schedule_data:
                # 计算持续时间
                duration = task['end'] - task['start']
                
                # 提取workpoint数字ID: 'workpoint_1' -> 1
                workpoint_id_str = task['workpoint_id']
                workpoint_id_num = int(workpoint_id_str.replace('workpoint_', ''))
                
                # 提取team数字ID和名称: 'team1' -> 1, '团队1'
                team_id_str = task['team']
                team_id_num = int(team_id_str.replace('team', ''))
                team_name = f'团队{team_id_num}'
                
                values = (
                    task['name'],
                    workpoint_id_num,  # 数字ID
                    task['workpoint_name'],
                    team_id_num,  # 数字ID
                    team_name,  # 团队名称
                    task['start'],
                    task['end'],
                    duration,
                    task['workers'],
                    task.get('order', None)
                )
                cursor.execute(insert_query, values)
                insert_count += 1
            
            self.connection.commit()
            print(f"✅ 成功保存 {insert_count} 条调度结果到表 {table_name}")

            
            cursor.close()
            return table_name
            
        except Error as e:
            print(f"❌ 保存调度结果失败: {e}")
            import traceback
            traceback.print_exc()
            self.connection.rollback()
            return None
    
    def load_schedule_result(self, table_name=None):
        """
        从数据库读取调度结果
        
        Args:
            table_name: 表名，如果为None则读取最新的 schedule_result_ 表
        
        Returns:
            dict: {
                'schedule_data': [...],  # 调度任务列表
                'makespan': float,       # 完工时间
                'algorithm': str,        # 算法名称（从表注释提取）
                'table_name': str,       # 表名
                'task_count': int        # 任务数量
            }
            如果失败返回 None
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor()
            
            # 如果未指定表名，查找最新的
            if not table_name:
                cursor.execute(f"""
                    SELECT table_name, table_comment
                    FROM information_schema.tables
                    WHERE table_schema = '{self.connection_config['database']}'
                    AND table_name LIKE 'schedule_result_%'
                    ORDER BY table_name DESC
                    LIMIT 1
                """)
                result = cursor.fetchone()
                if not result:
                    print("⚠️  未找到调度结果表")
                    cursor.close()
                    return None
                table_name, table_comment = result
                print(f"📖 读取最新调度结果表: {table_name}")
            else:
                # 获取表注释
                cursor.execute(f"""
                    SELECT table_comment
                    FROM information_schema.tables
                    WHERE table_schema = '{self.connection_config['database']}'
                    AND table_name = '{table_name}'
                """)
                result = cursor.fetchone()
                table_comment = result[0] if result else None
            
            # 从表注释提取算法名称
            algorithm_name = None
            if table_comment:
                import re
                match = re.search(r'算法:(\w+)', table_comment)
                if match:
                    algorithm_name = match.group(1)
            
            # 读取数据（兼容新旧表结构）
            # 先检查表结构，确定是否有team_id字段（新表结构）
            cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = '{self.connection_config['database']}' 
                AND TABLE_NAME = '{table_name}' 
                AND COLUMN_NAME = 'team_id'
            """)
            is_new_structure = cursor.fetchone() is not None
            
            if is_new_structure:
                # 新表结构（优化后）
                query = f"""
                SELECT task_id, task_name, workpoint_id, workpoint_name, 
                       team_id, team_name, start_time, end_time, duration, workers, process_order
                FROM `{table_name}`
                ORDER BY start_time, task_id
                """
            else:
                # 旧表结构（兼容）
                query = f"""
                SELECT task_id, task_name, workpoint_id, workpoint_name, 
                       team, start_time, end_time, duration, workers, process_order
                FROM `{table_name}`
                ORDER BY start_time, task_id
                """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                print(f"⚠️  表 {table_name} 中没有数据")
                cursor.close()
                return None
            
            # 转换为标准格式
            schedule_data = []
            for row in rows:
                if is_new_structure:
                    # 新表结构：重新构造原始格式
                    task_id = row[0]
                    workpoint_id_num = row[2]
                    team_id_num = row[4]
                    
                    schedule_data.append({
                        'id': task_id,
                        'name': row[1],
                        'workpoint_id': f'workpoint_{workpoint_id_num}',  # 转回原格式
                        'workpoint_name': row[3],
                        'team': f'team{team_id_num}',  # 转回原格式
                        'start': float(row[6]),
                        'end': float(row[7]),
                        'duration': float(row[8]),
                        'workers': row[9],
                        'order': row[10] if row[10] is not None else 0
                    })
                else:
                    # 旧表结构
                    schedule_data.append({
                        'id': row[0],
                        'name': row[1],
                        'workpoint_id': row[2],
                        'workpoint_name': row[3],
                        'team': row[4],
                        'start': float(row[5]),
                        'end': float(row[6]),
                        'duration': float(row[7]),
                        'workers': row[8],
                        'order': row[9] if row[9] is not None else 0
                    })
            
            # 计算makespan（从数据中获取最大结束时间）
            makespan = max([task['end'] for task in schedule_data]) if schedule_data else 0
            
            result = {
                'schedule_data': schedule_data,
                'makespan': makespan,
                'algorithm': algorithm_name or '未知',
                'table_name': table_name,
                'task_count': len(schedule_data)
            }
            
            print(f"✅ 成功从表 {table_name} 读取 {len(schedule_data)} 条调度结果")
            print(f"   完工时间: {makespan:.2f}")
            if algorithm_name:
                print(f"   算法名称: {algorithm_name}")
            
            cursor.close()
            return result
            
        except Error as e:
            print(f"❌ 读取调度结果失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def list_schedule_results(self, limit=10):
        """
        列出数据库中的所有调度结果表
        
        Args:
            limit: 返回的最大数量，默认10
        
        Returns:
            list: [
                {
                    'table_name': 'schedule_result_20241027_153045',
                    'comment': '算法:DDQN - 完工时间:75.50',
                    'created_at': '2024-10-27 15:30:45',
                    'task_count': 24
                },
                ...
            ]
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor()
            
            # 查找所有 schedule_result_ 表
            cursor.execute(f"""
                SELECT table_name, table_comment, create_time
                FROM information_schema.tables
                WHERE table_schema = '{self.connection_config['database']}'
                AND table_name LIKE 'schedule_result_%'
                ORDER BY table_name DESC
                LIMIT {limit}
            """)
            
            tables = cursor.fetchall()
            
            if not tables:
                print("ℹ️  数据库中没有调度结果表")
                cursor.close()
                return []
            
            results = []
            for table_name, table_comment, create_time in tables:
                # 查询任务数量
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                task_count = cursor.fetchone()[0]
                
                results.append({
                    'table_name': table_name,
                    'comment': table_comment or '',
                    'created_at': str(create_time) if create_time else None,
                    'task_count': task_count
                })
            
            print(f"📋 找到 {len(results)} 个调度结果表")
            cursor.close()
            return results
            
        except Error as e:
            print(f"❌ 列出调度结果表失败: {e}")
            return None
    
    def create_process_table(self, workpoint_id, workpoint_name):
        """
        为每个工作点创建工序表
        
        Args:
            workpoint_id: 工作点ID（如 workpoint_1）
            workpoint_name: 工作点名称（如 工作点1）
        
        Returns:
            bool: 是否创建成功
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            
            # 表名使用工作点ID
            table_name = f"process_{workpoint_id}"
            
            # 创建表的SQL语句
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
                `process_name` VARCHAR(100) NOT NULL COMMENT '工序名称',
                `process_order` INT NOT NULL COMMENT '工序顺序（阶段）',
                `team_name` VARCHAR(50) NOT NULL COMMENT '团队名称',
                `is_dedicated` TINYINT(1) DEFAULT 0 COMMENT '是否专用团队（1=是，0=否）',
                `team_size` INT NOT NULL COMMENT '团队规模（人数）',
                `duration` DECIMAL(10, 2) NOT NULL COMMENT '工序持续时间',
                `is_parallel` TINYINT(1) DEFAULT 0 COMMENT '是否可并行执行（1=是，0=否）',
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX `idx_order` (`process_order`),
                INDEX `idx_team` (`team_name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
            COMMENT='工作点【{workpoint_name}】工序信息表';
            """
            
            cursor.execute(create_table_query)
            self.connection.commit()
            print(f"✅ 成功创建表: {table_name} ({workpoint_name})")
            
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ 创建表 process_{workpoint_id} 失败: {e}")
            return False
    
    def clear_process_table(self, workpoint_id):
        """
        清空指定工作点的表数据（保留表结构）
        
        Args:
            workpoint_id: 工作点ID
        
        Returns:
            bool: 是否清空成功
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            table_name = f"process_{workpoint_id}"
            
            # 检查表是否存在
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{self.connection_config['database']}' 
                AND table_name = '{table_name}'
            """)
            
            if cursor.fetchone()[0] == 0:
                print(f"ℹ️  表 {table_name} 不存在，跳过清空操作")
                cursor.close()
                return True
            
            # 清空表数据
            cursor.execute(f"TRUNCATE TABLE `{table_name}`")
            self.connection.commit()
            print(f"✅ 成功清空表 {table_name}")
            
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ 清空表 process_{workpoint_id} 失败: {e}")
            return False
    
    def save_processes(self, workpoint_id, workpoint_name, steps_data):
        """
        保存工序数据到对应的工作点表
        
        Args:
            workpoint_id: 工作点ID
            workpoint_name: 工作点名称
            steps_data: 工序数据列表
        
        Returns:
            bool: 是否保存成功
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return False
        
        try:
            cursor = self.connection.cursor()
            table_name = f"process_{workpoint_id}"
            
            # 插入SQL语句
            insert_query = f"""
            INSERT INTO `{table_name}` 
            (process_name, process_order, team_name, is_dedicated, team_size, duration, is_parallel)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            # 准备数据
            insert_count = 0
            for step in steps_data:
                process_name = step.get("name")
                process_order = step.get("order")
                team_name = step.get("team")
                is_dedicated = 1 if step.get("dedicated", False) else 0
                team_size = step.get("team_size")
                duration = step.get("duration")
                is_parallel = 1 if step.get("parallel", False) else 0
                
                values = (process_name, process_order, team_name, is_dedicated, 
                         team_size, duration, is_parallel)
                
                cursor.execute(insert_query, values)
                insert_count += 1
            
            self.connection.commit()
            print(f"✅ 成功向表 {table_name} 插入 {insert_count} 条工序数据")
            
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ 插入数据到表 process_{workpoint_id} 失败: {e}")
            self.connection.rollback()
            return False
    
    def save_all_workpoints_processes(self, workpoints_data, clear_existing=True):
        """
        保存所有工作点的工序数据
        
        Args:
            workpoints_data: 工作点数据字典
            clear_existing: 是否清空已有数据（默认True）
        
        Returns:
            bool: 是否全部保存成功
        """
        from config import STANDARD_STEP_TEMPLATES
        
        print("\n" + "=" * 60)
        print("💾 开始保存工作点工序数据到数据库")
        print("=" * 60)
        
        success_count = 0
        total_count = len(workpoints_data)
        
        for workpoint_id, workpoint_info in workpoints_data.items():
            workpoint_name = workpoint_info.get("name", workpoint_id)
            steps_data = workpoint_info.get("steps", [])
            
            # 如果没有指定工序，使用标准模板
            if not steps_data:
                print(f"\n⚠️  {workpoint_name} 未指定工序，使用标准模板")
                steps_data = STANDARD_STEP_TEMPLATES.copy()
                # 为标准模板添加默认持续时间
                default_durations = [10, 5, 8, 6, 7, 9, 6, 7, 6, 7, 7, 7, 4, 7, 5]
                for i, step in enumerate(steps_data):
                    if "duration" not in step and i < len(default_durations):
                        step["duration"] = default_durations[i]
            
            print(f"\n📋 处理 {workpoint_name} ({workpoint_id})")
            print(f"   工序数量: {len(steps_data)}")
            
            # 创建表
            if not self.create_process_table(workpoint_id, workpoint_name):
                print(f"❌ {workpoint_name} 表创建失败，跳过")
                continue
            
            # 清空旧数据（如果需要）
            if clear_existing:
                if not self.clear_process_table(workpoint_id):
                    print(f"⚠️  {workpoint_name} 清空数据失败，继续插入")
            
            # 插入新数据
            if self.save_processes(workpoint_id, workpoint_name, steps_data):
                success_count += 1
        
        print("\n" + "=" * 60)
        print(f"✅ 工序数据保存完成: {success_count}/{total_count} 个工作点成功")
        print("=" * 60)
        
        return success_count == total_count
    
    def load_processes_from_table(self, workpoint_id):
        """
        从数据库表中读取指定工作点的工序数据
        
        Args:
            workpoint_id: 工作点ID（如 workpoint_1）
        
        Returns:
            list: 工序数据列表，如果失败返回None
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor()
            table_name = f"process_{workpoint_id}"
            
            # 检查表是否存在
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = '{self.connection_config['database']}' 
                AND table_name = '{table_name}'
            """)
            
            if cursor.fetchone()[0] == 0:
                print(f"⚠️  表 {table_name} 不存在")
                cursor.close()
                return None
            
            # 读取工序数据，按order排序
            query = f"""
            SELECT process_name, process_order, team_name, is_dedicated, 
                   team_size, duration, is_parallel
            FROM `{table_name}`
            ORDER BY process_order, id
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # 转换为标准格式
            steps_data = []
            for row in rows:
                step = {
                    "name": row[0],
                    "order": row[1],
                    "team": row[2],
                    "dedicated": bool(row[3]),
                    "team_size": row[4],
                    "duration": float(row[5]),
                    "parallel": bool(row[6])
                }
                steps_data.append(step)
            
            print(f"✅ 成功从表 {table_name} 读取 {len(steps_data)} 条工序数据")
            cursor.close()
            return steps_data
            
        except Error as e:
            print(f"❌ 从表 process_{workpoint_id} 读取数据失败: {e}")
            return None
    
    def load_all_workpoints_processes(self):
        """
        从数据库读取所有工作点的工序数据
        
        Returns:
            dict: 工作点数据字典，格式与create_sample_workpoints_data相同
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return None
        
        try:
            cursor = self.connection.cursor()
            
            # 查找所有 process_ 开头的表
            cursor.execute(f"""
                SELECT table_name, table_comment
                FROM information_schema.tables 
                WHERE table_schema = '{self.connection_config['database']}' 
                AND table_name LIKE 'process_%'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            cursor.close()
            
            if not tables:
                print("⚠️  数据库中未找到工序表")
                return None
            
            print("\n" + "=" * 60)
            print(f"📖 开始从数据库读取设备工序数据")
            print(f"   找到 {len(tables)} 个工序表")
            print("=" * 60)
            
            workpoints_data = {}
            
            for table_name, table_comment in tables:
                # 从表名提取工作点ID: process_workpoint_1 -> workpoint_1
                workpoint_id = table_name.replace('process_', '')
                
                # 从表注释提取工作点名称
                workpoint_name = workpoint_id  # 默认使用ID
                if table_comment:
                    import re
                    # 优先尝试提取【】中的内容: '工作点【工作点1】工序信息表' -> '工作点1'
                    match = re.search(r'【(.+?)】', table_comment)
                    if match:
                        workpoint_name = match.group(1)
                    else:
                        # 如果没有【】，则清理后缀并使用整个注释
                        # '设备1' -> '设备1'
                        # '设备1工序信息表' -> '设备1'
                        workpoint_name = table_comment.replace('工序信息表', '')\
                                                     .replace('工序表', '')\
                                                     .replace('信息表', '')\
                                                     .strip()
                        # 如果处理后为空，使用ID
                        if not workpoint_name:
                            workpoint_name = workpoint_id
                
                print(f"\n📋 读取 {workpoint_name} ({workpoint_id})")
                
                # 读取工序数据
                steps_data = self.load_processes_from_table(workpoint_id)
                
                if steps_data:
                    workpoints_data[workpoint_id] = {
                        "name": workpoint_name,
                        "steps": steps_data
                    }
                    print(f"   工序数量: {len(steps_data)}")
                else:
                    print(f"   ⚠️  读取失败，跳过")
            
            print("\n" + "=" * 60)
            print(f"✅ 工序数据读取完成: {len(workpoints_data)}/{len(tables)} 个工作点成功")
            print("=" * 60)
            
            return workpoints_data if workpoints_data else None
            
        except Error as e:
            print(f"❌ 读取工作点工序数据失败: {e}")
            return None