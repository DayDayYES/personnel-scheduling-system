# 工序数据库工作流程说明

## 概述

本系统现在支持将工序数据存储到MySQL数据库，并在运行调度算法时从数据库读取工序数据，实现数据持久化和复用。

## 工作流程

### 流程图

```
[创建工序数据] → [保存到数据库] → [从数据库读取] → [运行调度算法]
       ↓                ↓                  ↓                ↓
  create_sample    save_all_         load_all_         RUN()
  _workpoints      workpoints_       workpoints_
  _data()          processes()       processes()
```

### 详细步骤

#### 1. 初次使用：保存工序到数据库

**方式一：使用main.py（推荐）**

```bash
cd DDQN-v3
python main.py
```

首次运行时，如果数据库中没有工序表，系统会：
1. 尝试从数据库加载工序
2. 如果失败，使用示例数据
3. 自动将示例数据保存到数据库
4. 运行调度算法

**方式二：使用独立初始化脚本**

```bash
cd DDQN-v3
python init_process_db.py
```

这会创建工序表并插入示例数据，但不运行调度算法。

#### 2. 后续使用：从数据库读取工序

再次运行`main.py`时：

```bash
python main.py
```

系统会：
1. ✅ 自动从数据库读取工序数据
2. ✅ 使用读取的数据运行调度算法
3. ✅ 不再重复创建工序数据

## 核心功能说明

### 1. 保存工序到数据库

**函数：** `db_connector.save_all_workpoints_processes(workpoints_data, clear_existing=True)`

**功能：**
- 为每个工作点创建独立的工序表（表名：`process_工作点ID`）
- 插入工序数据
- 可选择是否清空已有数据

**示例代码：**

```python
from db_connector import DatabaseConnector
from scheduling_environment import create_sample_workpoints_data

# 创建数据库连接
db = DatabaseConnector(
    host="localhost",
    user="root",
    password="123456",
    database="secret"
)

# 连接数据库
if db.connect():
    # 获取工序数据
    workpoints_data = create_sample_workpoints_data()
    
    # 保存到数据库
    db.save_all_workpoints_processes(workpoints_data, clear_existing=True)
    
    # 关闭连接
    db.close()
```

### 2. 从数据库读取工序

**函数：** `db_connector.load_all_workpoints_processes()`

**功能：**
- 自动查找所有`process_`开头的表
- 读取每个表的工序数据
- 返回与`create_sample_workpoints_data()`相同格式的数据

**示例代码：**

```python
from db_connector import DatabaseConnector

# 创建数据库连接
db = DatabaseConnector(
    host="localhost",
    user="root",
    password="123456",
    database="secret"
)

# 连接并读取
if db.connect():
    workpoints_data = db.load_all_workpoints_processes()
    db.close()
    
    # 使用读取的数据
    if workpoints_data:
        print(f"成功读取 {len(workpoints_data)} 个工作点")
```

### 3. 在main.py中使用

**函数：** `load_workpoints_from_database()`

**功能：**
- 封装了数据库连接和读取逻辑
- 自动处理错误

**示例代码：**

```python
from main import load_workpoints_from_database, RUN

# 从数据库加载工序
workpoints_data = load_workpoints_from_database()

if workpoints_data:
    # 运行调度算法（不再重复保存工序）
    result = RUN(workpoints_data, save_processes_to_db=False)
```

## 数据库表结构

### 表命名规则

- `process_workpoint_1` - 工作点1的工序表
- `process_workpoint_2` - 工作点2的工序表
- `process_workpoint_3` - 工作点3的工序表

### 表字段

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| id | INT | 自增主键 | 1 |
| process_name | VARCHAR(100) | 工序名称 | 搭架子 |
| process_order | INT | 工序顺序/阶段 | 1 |
| team_name | VARCHAR(50) | 负责团队 | team1 |
| is_dedicated | TINYINT(1) | 是否专用团队 | 1 |
| team_size | INT | 团队规模 | 5 |
| duration | DECIMAL(10,2) | 工序持续时间 | 10.00 |
| is_parallel | TINYINT(1) | 是否可并行 | 0 |
| created_at | TIMESTAMP | 创建时间 | 2025-01-01 12:00:00 |
| updated_at | TIMESTAMP | 更新时间 | 2025-01-01 12:00:00 |

## 测试流程

### 测试1：查看数据库表

```bash
cd DDQN-v3
python test_db_tables.py
```

**输出示例：**
```
✅ 成功连接到数据库: secret

📋 数据库中的表 (共 5 个):
============================================================

🔧 工序表:
  - process_workpoint_1: 8 条工序记录
  - process_workpoint_2: 8 条工序记录
  - process_workpoint_3: 15 条工序记录
```

### 测试2：完整工作流程测试

```bash
cd DDQN-v3
python test_db_workflow.py
```

**测试内容：**
1. ✅ 保存示例工序到数据库
2. ✅ 从数据库读取工序
3. ✅ 验证数据一致性
4. ✅ 显示数据摘要

### 测试3：运行调度算法

```bash
cd DDQN-v3
python main.py
```

**预期行为：**
1. 📖 从数据库加载工作点数据
2. 📚 开始训练DDQN代理
3. 📊 生成甘特图
4. 💾 保存调度结果到数据库

## 常见SQL查询

### 查看所有工序表

```sql
SHOW TABLES LIKE 'process_%';
```

### 查看工作点1的所有工序

```sql
SELECT * FROM process_workpoint_1 ORDER BY process_order, id;
```

### 统计各工作点的工序数量

```sql
SELECT 
    'workpoint_1' as 工作点, COUNT(*) as 工序数量 
FROM process_workpoint_1
UNION ALL
SELECT 
    'workpoint_2' as 工作点, COUNT(*) as 工序数量 
FROM process_workpoint_2
UNION ALL
SELECT 
    'workpoint_3' as 工作点, COUNT(*) as 工序数量 
FROM process_workpoint_3;
```

### 按阶段统计工序（以工作点1为例）

```sql
SELECT 
    process_order as 阶段,
    COUNT(*) as 工序数量,
    GROUP_CONCAT(process_name ORDER BY id SEPARATOR ', ') as 工序列表
FROM process_workpoint_1
GROUP BY process_order
ORDER BY process_order;
```

### 查看可并行执行的工序

```sql
SELECT 
    workpoint_id,
    process_order,
    process_name,
    team_name
FROM (
    SELECT 'workpoint_1' as workpoint_id, process_order, process_name, team_name FROM process_workpoint_1 WHERE is_parallel = 1
    UNION ALL
    SELECT 'workpoint_2' as workpoint_id, process_order, process_name, team_name FROM process_workpoint_2 WHERE is_parallel = 1
    UNION ALL
    SELECT 'workpoint_3' as workpoint_id, process_order, process_name, team_name FROM process_workpoint_3 WHERE is_parallel = 1
) AS parallel_processes
ORDER BY workpoint_id, process_order;
```

## 配置说明

### 数据库连接配置

在代码中修改数据库连接信息：

```python
db = DatabaseConnector(
    host="localhost",      # MySQL服务器地址
    user="root",           # 数据库用户名
    password="123456",     # 数据库密码（请修改为您的密码）
    database="secret"      # 数据库名称
)
```

### main.py参数

```python
# 使用数据库数据（默认）
main(use_database=True)

# 使用示例数据
main(use_database=False)
```

### RUN函数参数

```python
# 运行时保存工序到数据库
RUN(workpoints_data, save_processes_to_db=True)

# 运行时不保存工序（避免重复保存）
RUN(workpoints_data, save_processes_to_db=False)
```

## 故障排查

### 问题1：数据库连接失败

**症状：** `❌ 数据库连接失败`

**解决方案：**
1. 检查MySQL服务是否启动
2. 确认用户名和密码是否正确
3. 确认数据库`secret`是否存在

### 问题2：表不存在

**症状：** `⚠️  表 process_workpoint_1 不存在`

**解决方案：**
```bash
python init_process_db.py
# 或
python main.py  # 会自动创建表
```

### 问题3：读取的工序数量为0

**症状：** 表存在但没有数据

**解决方案：**
```bash
# 重新初始化数据
python init_process_db.py
```

### 问题4：数据不一致

**症状：** 读取的数据与预期不符

**解决方案：**
```bash
# 运行测试验证
python test_db_workflow.py

# 如果需要，清空并重新初始化
python init_process_db.py
```

## 优势

1. **数据持久化** - 工序数据保存在数据库中，不会丢失
2. **数据复用** - 多次运行无需重复创建工序
3. **数据管理** - 可以通过SQL直接查询和修改工序
4. **团队协作** - 多人可以共享同一套工序数据
5. **版本控制** - 通过时间戳字段记录数据变更历史

## 下一步扩展

1. **工序管理界面** - 开发前端界面来增删改查工序
2. **工序版本管理** - 支持多个工序方案版本
3. **工序模板库** - 创建不同行业的工序模板
4. **导入导出功能** - 支持Excel导入导出工序数据

