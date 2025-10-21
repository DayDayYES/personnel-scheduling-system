# 工序数据库管理说明

## 概述

本模块用于将工作点的工序信息存储到MySQL数据库中，每个工作点对应一个独立的数据表。

## 数据库表结构

每个工作点对应一个表，表名格式：`process_工作点ID`

例如：
- `process_workpoint_1` - 工作点1的工序表
- `process_workpoint_2` - 工作点2的工序表
- `process_workpoint_3` - 工作点3的工序表

### 字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 自增主键 |
| process_name | VARCHAR(100) | 工序名称（如：搭架子、拆保温） |
| process_order | INT | 工序顺序/阶段（order值） |
| team_name | VARCHAR(50) | 负责团队名称（如：team1, team2） |
| is_dedicated | TINYINT(1) | 是否专用团队（1=是，0=否） |
| team_size | INT | 团队规模（人数） |
| duration | DECIMAL(10, 2) | 工序持续时间 |
| is_parallel | TINYINT(1) | 是否可并行执行（1=是，0=否） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 使用方法

### 1. 初始化工序数据库

运行初始化脚本，会自动创建表并插入数据：

```bash
cd DDQN-v3
python init_process_db.py
```

### 2. 配置数据库连接

在运行脚本前，请确保修改数据库连接信息：

```python
initializer = ProcessDatabaseInitializer(
    host="localhost",       # MySQL服务器地址
    user="root",           # 数据库用户名
    password="123456",     # 数据库密码（请修改为您的密码）
    database="secret"      # 数据库名称
)
```

### 3. 查看初始化结果

初始化成功后，可以在MySQL中查看数据：

```sql
-- 查看所有工序表
SHOW TABLES LIKE 'process_%';

-- 查看工作点1的工序
SELECT * FROM process_workpoint_1;

-- 查看工作点2的工序
SELECT * FROM process_workpoint_2;

-- 查看工作点3的工序
SELECT * FROM process_workpoint_3;
```

### 4. 统计工序信息

```sql
-- 统计各工作点的工序数量
SELECT 
    'workpoint_1' as workpoint, 
    COUNT(*) as process_count 
FROM process_workpoint_1
UNION ALL
SELECT 
    'workpoint_2' as workpoint, 
    COUNT(*) as process_count 
FROM process_workpoint_2
UNION ALL
SELECT 
    'workpoint_3' as workpoint, 
    COUNT(*) as process_count 
FROM process_workpoint_3;

-- 按阶段统计工序数量（以工作点1为例）
SELECT 
    process_order as stage,
    COUNT(*) as process_count,
    GROUP_CONCAT(process_name) as processes
FROM process_workpoint_1
GROUP BY process_order
ORDER BY process_order;
```

## 工序数据来源

### 工作点1和工作点2
使用 `create_sample_workpoints_data()` 函数中定义的自定义工序数据。

### 工作点3
未指定自定义工序，使用 `STANDARD_STEP_TEMPLATES` 中定义的标准模板。

标准模板包含15个工序：
1. 搭架子 (order=1)
2. 拆保温 (order=2)
3. 打磨 (order=3)
4. 宏观检验 (order=4, 可并行)
5. 壁厚测定 (order=4, 可并行)
6. 射线检测 (order=4, 可并行)
7. 磁粉检测 (order=4, 可并行)
8. 渗透检测 (order=4, 可并行)
9. 超声检测 (order=4, 可并行)
10. 涡流检测 (order=4, 可并行)
11. 表面检测 (order=4, 可并行)
12. 检验结果评定 (order=5)
13. 返修 (order=6)
14. 合格报告出具 (order=7)
15. 拆架子 (order=8)

## 注意事项

1. **数据库权限**：确保MySQL用户具有创建表、插入数据的权限
2. **字符编码**：表使用 `utf8mb4` 编码，支持中文和特殊字符
3. **数据清空**：默认情况下，重新初始化会清空旧数据（`clear_existing=True`）
4. **表命名**：表名必须符合MySQL命名规范，避免使用特殊字符

## 扩展使用

### 添加新的工作点

在 `scheduling_environment.py` 的 `create_sample_workpoints_data()` 函数中添加新工作点：

```python
"workpoint_4": {
    "name": "工作点4",
    "steps": [
        {"name": "新工序1", "order": 1, "team": "team1", 
         "dedicated": True, "team_size": 5, "duration": 10},
        # ... 更多工序
    ]
}
```

然后重新运行初始化脚本。

### 自定义表结构

如需修改表结构，编辑 `init_process_db.py` 中的 `create_workpoint_table()` 方法的SQL语句。

## 故障排查

### 连接失败
- 检查MySQL服务是否启动
- 确认用户名和密码是否正确
- 确认数据库 `secret` 是否存在

### 表已存在
- 脚本会自动处理表已存在的情况
- 如需重新创建表，可手动删除后再运行脚本

### 数据插入失败
- 检查数据类型是否匹配
- 确认必填字段都有值
- 查看错误信息中的详细原因

