# 工序变化检测机制说明

## 概述

系统通过计算工序配置的**MD5哈希值**来检测工序是否发生变化。当工序配置变化时，会自动重置全局最优结果，确保使用新配置重新进行优化。

## 检测原理

### 1. 哈希值计算

系统会提取每个工序的以下关键字段，计算整体配置的MD5哈希值：

```python
def calculate_workpoints_hash(self, workpoints_data):
    """计算工序配置的哈希值"""
    config_data = {}
    
    for wp_id, wp_info in sorted(workpoints_data.items()):
        steps_info = []
        for step in wp_info.get("steps", []):
            # 提取关键字段
            step_key = (
                step.get("name"),           # 工序名称
                step.get("order"),          # 工序顺序（阶段）
                step.get("team"),           # 负责团队
                step.get("dedicated"),      # 是否专用团队
                step.get("team_size"),      # 团队规模
                step.get("duration"),       # 工序持续时间
                step.get("parallel", False) # 是否可并行
            )
            steps_info.append(step_key)
        
        config_data[wp_id] = steps_info
    
    # 转换为JSON字符串并计算哈希
    config_str = json.dumps(config_data, sort_keys=True)
    hash_value = hashlib.md5(config_str.encode('utf-8')).hexdigest()
    
    return hash_value
```

### 2. 变化检测流程

```
┌─────────────────────────────────────────────────────────────┐
│                    开始训练/优化                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          计算当前工序配置的哈希值 (current_hash)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              加载已保存的哈希值 (saved_hash)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  比较两个哈希值
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
   哈希值相同                        哈希值不同
         │                               │
         ▼                               ▼
 使用已有的最优结果            ⚠️ 重置全局最优结果
 (如果存在且更好)              删除旧的最优方案
         │                      从头开始优化
         │                               │
         └───────────────┬───────────────┘
                         │
                         ▼
              继续训练并更新最优结果
```

## 可以检测到的工序变化

### ✅ **能检测到的变化**

| 变化类型 | 说明 | 示例 |
|---------|------|------|
| **工序名称变化** | 工序的名字改变 | "搭架子" → "搭建脚手架" |
| **工序顺序变化** | order值改变 | order=3 → order=4 |
| **团队分配变化** | 负责团队改变 | team="team1" → team="team2" |
| **专用/共享切换** | dedicated字段改变 | dedicated=True → dedicated=False |
| **团队规模变化** | team_size改变 | team_size=5 → team_size=10 |
| **工序时长变化** | duration改变 | duration=10 → duration=12 |
| **并行标识变化** | parallel字段改变 | parallel=False → parallel=True |
| **工序增加** | 新增工序 | 原8个工序 → 现9个工序 |
| **工序删除** | 删除工序 | 原8个工序 → 现7个工序 |
| **工作点增加** | 新增工作点 | 原3个工作点 → 现4个工作点 |
| **工作点删除** | 删除工作点 | 原3个工作点 → 现2个工作点 |

### ❌ **不会检测到的变化**（非关键字段）

以下字段的变化**不会**触发重置，因为它们不影响调度结果：

- 工作点名称的显示文字（如"工作点1" → "一号工作点"）
- 数据库记录的创建时间 (`created_at`)
- 数据库记录的更新时间 (`updated_at`)
- 数据库记录的ID值

## 实际应用示例

### 示例 1：修改工序时长

**场景**：发现"搭架子"工序实际需要12小时而不是10小时

**操作步骤**：
```sql
-- 在数据库中修改工序时长
UPDATE process_workpoint_1 
SET duration = 12 
WHERE process_name = '搭架子';
```

**系统行为**：
```
🚀 开始多工作点调度算法...

💾 第一步：保存工序数据到数据库...
（跳过，因为已存在）

📂 第二步：检查已有的全局最优结果...
📊 发现已有全局最优结果:
   算法: 原版DDQN
   完工时间: 65.50

⚠️  检测到工序配置变化，重置全局最优结果
   旧配置哈希: 5f3a8b21...
   新配置哈希: 7d4c9e12...
🗑️  已删除全局最优结果文件

📚 第三步：开始训练DDQN代理...
（从头开始训练）
```

### 示例 2：增加新工序

**场景**：在工作点2增加一个"复检"工序

**操作步骤**：
```sql
-- 在数据库中插入新工序
INSERT INTO process_workpoint_2 
(process_name, process_order, team_name, is_dedicated, team_size, duration, is_parallel)
VALUES ('复检', 6, 'team3', 1, 10, 3, 0);
```

**系统行为**：
```
📂 第二步：检查已有的全局最优结果...
⚠️  检测到工序配置变化，重置全局最优结果
   旧配置哈希: 5f3a8b21...
   新配置哈希: 8e5f1a34...
🗑️  已删除全局最优结果文件
```

### 示例 3：只修改显示名称（不触发重置）

**场景**：修改工作点的显示名称

**操作步骤**：
```sql
-- 修改表注释（显示名称）
ALTER TABLE process_workpoint_1 
COMMENT '工作点【一号工作点】工序信息表';
```

**系统行为**：
```
📂 第二步：检查已有的全局最优结果...
📊 发现已有全局最优结果:
   算法: 原版DDQN
   完工时间: 65.50
   
（不会触发重置，继续使用已有最优结果）
```

## 技术细节

### 哈希值示例

对于以下工序配置：
```python
{
    "workpoint_1": {
        "name": "工作点1",
        "steps": [
            {"name": "搭架子", "order": 1, "team": "team1", 
             "dedicated": True, "team_size": 5, "duration": 10},
            {"name": "拆保温", "order": 2, "team": "team2", 
             "dedicated": False, "team_size": 10, "duration": 5}
        ]
    }
}
```

生成的哈希值可能是：`5f3a8b2147c9d6e8f1a34b67c2d5e8f9`

只要任何一个关键字段改变，哈希值就会完全不同：
- 修改 `duration: 10 → 12`：新哈希 = `7d4c9e12a8f5b3c6e1d8a7f4b9c2e5d1`
- 修改 `team_size: 5 → 6`：新哈希 = `3e7a1f5c9d2b8e4f6a3c7d1e5b8f2a9c`

### 存储位置

哈希值保存在以下位置：
- **文件**：`DDQN-v3/result/global_best_result.pkl`
- **内存**：`global_best_tracker.workpoints_hash`

数据结构：
```python
{
    'makespan': 65.50,
    'schedule': [...],
    'algorithm': '原版DDQN',
    'episode': 42,
    'model_path': 'result/best_model.pth',
    'workpoints_hash': '5f3a8b2147c9d6e8f1a34b67c2d5e8f9'
}
```

## 手动重置最优结果

如果需要手动强制重置全局最优结果（无论工序是否变化），可以使用以下方法：

### 方法 1：删除保存文件
```bash
cd DDQN-v3/result
rm global_best_result.pkl
```

### 方法 2：使用Python代码
```python
from global_best_tracker import global_best_tracker

# 重置全局最优结果
global_best_tracker.reset()
print("全局最优结果已重置")
```

### 方法 3：创建重置脚本
```python
# reset_best.py
from global_best_tracker import global_best_tracker

if __name__ == '__main__':
    print("确认要重置全局最优结果吗？(y/n)")
    choice = input().strip().lower()
    
    if choice == 'y':
        global_best_tracker.reset()
        print("✅ 全局最优结果已重置")
    else:
        print("❌ 操作已取消")
```

## 查看当前哈希值

可以使用以下脚本查看当前工序配置的哈希值：

```python
# check_hash.py
from db_connector import DatabaseConnector
from global_best_tracker import global_best_tracker

def check_workpoints_hash():
    """查看当前工序配置的哈希值"""
    print("正在从数据库读取工序数据...")
    
    db = DatabaseConnector(
        host="localhost",
        user="root",
        password="123456",
        database="secret"
    )
    
    if db.connect():
        workpoints_data = db.load_all_workpoints_processes()
        db.close()
        
        if workpoints_data:
            current_hash = global_best_tracker.calculate_workpoints_hash(workpoints_data)
            saved_hash = global_best_tracker.workpoints_hash
            
            print(f"\n当前工序配置哈希: {current_hash}")
            print(f"已保存的配置哈希: {saved_hash if saved_hash else '无'}")
            
            if saved_hash:
                if current_hash == saved_hash:
                    print("✅ 工序配置未变化")
                else:
                    print("⚠️  工序配置已变化，下次运行将重置最优结果")
            else:
                print("ℹ️  尚未保存配置哈希")
        else:
            print("❌ 读取工序数据失败")
    else:
        print("❌ 数据库连接失败")

if __name__ == '__main__':
    check_workpoints_hash()
```

## 最佳实践

### 1. 工序修改流程

```
修改数据库工序
    ↓
运行测试脚本验证
    ↓
运行主程序
    ↓
系统自动检测变化
    ↓
重新开始优化
```

### 2. 版本管理建议

对于重要的工序配置，建议保存配置快照：

```sql
-- 创建工序配置备份表
CREATE TABLE process_config_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_hash VARCHAR(32),
    workpoint_id VARCHAR(50),
    config_json TEXT,
    best_makespan DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_hash (config_hash)
);

-- 保存当前配置
INSERT INTO process_config_history (config_hash, workpoint_id, config_json)
SELECT 
    MD5(CONCAT_WS('|', process_name, process_order, team_name, duration)),
    'workpoint_1',
    JSON_OBJECT(
        'process_name', process_name,
        'process_order', process_order,
        'team_name', team_name,
        'duration', duration
    )
FROM process_workpoint_1;
```

### 3. 监控工序变化

建议定期检查工序变化历史：

```python
def monitor_process_changes():
    """监控工序变化"""
    import time
    
    last_hash = None
    
    while True:
        db = DatabaseConnector(...)
        if db.connect():
            data = db.load_all_workpoints_processes()
            current_hash = calculate_hash(data)
            
            if last_hash and last_hash != current_hash:
                print(f"⚠️  检测到工序变化！")
                print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                # 发送通知或记录日志
            
            last_hash = current_hash
            db.close()
        
        time.sleep(300)  # 每5分钟检查一次
```

## 常见问题

### Q1: 为什么修改了数据库但系统没有检测到变化？

**A**: 请确保：
1. 修改的是关键字段（name, order, team, dedicated, team_size, duration, parallel）
2. 数据已经正确保存到数据库
3. 程序是从数据库读取数据而不是使用示例数据

### Q2: 如何临时禁用变化检测？

**A**: 可以修改 `global_best_tracker.py` 中的 `update_best_result` 方法，注释掉变化检测部分：

```python
# 注释掉这段代码来临时禁用
# if self.workpoints_hash is not None and self.workpoints_hash != current_hash:
#     print(f"\n⚠️  检测到工序配置变化，重置全局最优结果")
#     self.reset()
```

### Q3: 哈希值冲突怎么办？

**A**: MD5哈希冲突的概率极低（约2^-128）。对于工序配置这种数据量，实际上不会发生冲突。如果担心，可以改用SHA256。

### Q4: 能否保留历史最优结果？

**A**: 可以。建议在重置前备份：

```python
import shutil
from datetime import datetime

# 在 reset() 方法中添加备份逻辑
backup_name = f"global_best_result_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
shutil.copy(global_best_path, get_result_path(backup_name))
```

## 总结

工序变化检测机制能够：
- ✅ 自动识别所有影响调度的工序变化
- ✅ 避免使用过时的最优结果
- ✅ 确保每次优化都基于最新配置
- ✅ 提供透明的变化提示信息

这保证了系统在工序配置更新后，总是能产生正确的调度方案。

