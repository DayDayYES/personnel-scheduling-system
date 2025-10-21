# -*- coding: utf-8 -*-
"""
工序数据库初始化模块 - 创建工作点工序表并插入数据
"""

import mysql.connector
from mysql.connector import Error
from scheduling_environment import create_sample_workpoints_data
from config import STANDARD_STEP_TEMPLATES


class ProcessDatabaseInitializer:
    """工序数据库初始化器"""
    
    def __init__(self, host="localhost", user="root", password="123456", database="secret"):
        """
        初始化数据库连接配置
        
        Args:
            host: MySQL服务器地址
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
        """
        self.connection_config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        self.connection = None
    
    def connect(self):
        """连接到数据库"""
        try:
            self.connection = mysql.connector.connect(**self.connection_config)
            if self.connection.is_connected():
                print(f"✅ 成功连接到MySQL数据库: {self.connection_config['database']}")
                return True
        except Error as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ 数据库连接已关闭")
    
    def create_workpoint_table(self, workpoint_id, workpoint_name):
        """
        为每个工作点创建工序表
        
        Args:
            workpoint_id: 工作点ID（如 workpoint_1）
            workpoint_name: 工作点名称（如 工作点1）
        """
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
            print(f"❌ 创建表 {table_name} 失败: {e}")
            return False
    
    def insert_processes(self, workpoint_id, workpoint_name, steps_data):
        """
        插入工序数据到对应的工作点表
        
        Args:
            workpoint_id: 工作点ID
            workpoint_name: 工作点名称
            steps_data: 工序数据列表
        """
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
            print(f"❌ 插入数据到表 {table_name} 失败: {e}")
            self.connection.rollback()
            return False
    
    def clear_table(self, workpoint_id):
        """
        清空指定工作点的表数据（保留表结构）
        
        Args:
            workpoint_id: 工作点ID
        """
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
                print(f"⚠️  表 {table_name} 不存在，跳过清空操作")
                cursor.close()
                return True
            
            # 清空表数据
            cursor.execute(f"TRUNCATE TABLE `{table_name}`")
            self.connection.commit()
            print(f"✅ 成功清空表 {table_name}")
            
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ 清空表 {table_name} 失败: {e}")
            return False
    
    def initialize_all_workpoints(self, clear_existing=True):
        """
        初始化所有工作点的工序数据
        
        Args:
            clear_existing: 是否清空已有数据（默认True）
        """
        print("\n" + "=" * 60)
        print("开始初始化工作点工序数据库")
        print("=" * 60)
        
        # 获取示例工作点数据
        workpoints_data = create_sample_workpoints_data()
        
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
            if not self.create_workpoint_table(workpoint_id, workpoint_name):
                print(f"❌ {workpoint_name} 表创建失败，跳过")
                continue
            
            # 清空旧数据（如果需要）
            if clear_existing:
                if not self.clear_table(workpoint_id):
                    print(f"⚠️  {workpoint_name} 清空数据失败，继续插入")
            
            # 插入新数据
            if self.insert_processes(workpoint_id, workpoint_name, steps_data):
                success_count += 1
        
        print("\n" + "=" * 60)
        print(f"初始化完成: {success_count}/{total_count} 个工作点成功")
        print("=" * 60)
        
        return success_count == total_count


def main():
    """主函数 - 执行数据库初始化"""
    # 创建初始化器实例
    initializer = ProcessDatabaseInitializer(
        host="localhost",
        user="root",
        password="123456",  # 请修改为您的MySQL密码
        database="secret"
    )
    
    # 连接数据库
    if not initializer.connect():
        print("❌ 无法连接到数据库，退出")
        return
    
    try:
        # 初始化所有工作点
        initializer.initialize_all_workpoints(clear_existing=True)
        
    except Exception as e:
        print(f"❌ 初始化过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭数据库连接
        initializer.close()


if __name__ == '__main__':
    main()

