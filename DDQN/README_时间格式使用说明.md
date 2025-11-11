# 甘特图时间格式使用说明

## 📋 功能说明

visualization.py 已支持两种时间格式的横轴显示：
1. **天数格式** (`time_format='day'`) - 显示"第X天上午/下午"
2. **数字格式** (`time_format='numeric'`) - 显示具体的时间数值

## 🎯 使用方法

### 方法1：使用 `visualize_schedule` 函数

```python
from visualization import visualize_schedule

# 天数格式（默认）
record, img = visualize_schedule(schedule, makespan, time_format='day')

# 数字格式
record, img = visualize_schedule(schedule, makespan, time_format='numeric')
```

### 方法2：使用 `create_traditional_gantt_chart` 函数

```python
from visualization import create_traditional_gantt_chart

# 天数格式（默认）
fig = create_traditional_gantt_chart(schedule, makespan, time_format='day')

# 数字格式
fig = create_traditional_gantt_chart(schedule, makespan, time_format='numeric')
```

### 方法3：直接在其他甘特图函数中使用

所有主要的甘特图函数都支持 `time_format` 参数：
- `create_layered_workpoint_gantt_chart(schedule, makespan, env, time_format='day')`
- `create_layered_team_gantt_chart(schedule, makespan, time_format='day')`
- 等等...

## 📊 两种格式对比

### 1️⃣ 天数格式 (`time_format='day'`)

**特点**：
- 横轴显示："第1天上午"、"第1天下午"、"第2天上午"...
- 每10个时间单位为一个半天
- 虚线分隔每个时间段

**适用场景**：
- ✅ 项目管理（按天规划）
- ✅ 工程施工（工期计算）
- ✅ 管道检修（现场作业）
- ✅ 需要直观理解"第几天"的场景

**示例**：
```
横轴标签: 第1天上午 | 第1天下午 | 第2天上午 | 第2天下午 | 第3天上午
刻度位置:    0      |    10     |    20     |    30     |    40
```

**优点**：
- 更符合人的时间认知习惯
- 便于现场管理人员理解
- 直观展示工期天数

**缺点**：
- 不便于精确时间比较
- 学术论文中可能不够正式

---

### 2️⃣ 数字格式 (`time_format='numeric'`)

**特点**：
- 横轴显示：0, 5, 10, 15, 20, 25...
- 刻度间隔自动调整（根据makespan大小）
- 虚线分隔每个刻度

**刻度间隔规则**：
| Makespan范围 | 刻度间隔 | 示例 |
|-------------|---------|------|
| ≤ 50 | 5 | 0, 5, 10, 15, 20... |
| 50 ~ 100 | 10 | 0, 10, 20, 30... |
| 100 ~ 200 | 20 | 0, 20, 40, 60... |
| > 200 | 50 | 0, 50, 100, 150... |

**适用场景**：
- ✅ 学术研究（论文、期刊）
- ✅ 算法性能对比
- ✅ 需要精确时间数据的分析
- ✅ 数据统计和量化分析

**示例**（makespan=74.40）：
```
横轴标签:  0  |  10  |  20  |  30  |  40  |  50  |  60  |  70  |  80
```

**优点**：
- 精确显示时间数值
- 便于算法性能对比
- 学术规范，适合论文
- 便于读取具体时间点

**缺点**：
- 不够直观
- 现场人员理解成本高

---

## 🚀 快速演示

运行示例脚本，生成两种格式的对比图：

```bash
cd DDQN
python example_time_formats.py
```

这会生成：
- `result42/甘特图_天数格式.png`
- `result42/甘特图_数字格式.png`

## 📝 完整示例代码

```python
# 示例：生成贪婪算法的甘特图（数字格式）

from visualization import visualize_schedule
from scheduling_environment import FactoryEnvironment, create_sample_workpoints_data
from greedy_algorithm import GreedyScheduler
import matplotlib.pyplot as plt

# 1. 执行调度
workpoints_data = create_sample_workpoints_data()
env = FactoryEnvironment(workpoints_data)
scheduler = GreedyScheduler(env)
schedule, makespan = scheduler.schedule()

# 2. 生成数字格式甘特图
record, img = visualize_schedule(schedule, makespan, time_format='numeric')

# 3. 保存图片
plt.savefig('贪婪算法_数字格式.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"完工时间: {makespan:.2f}")
print(f"任务数量: {len(schedule)}")
```

## ❓ 常见问题

### Q1: 如何修改天数格式的时间间隔？

**答**: 在 `_set_day_time_axis` 函数中修改 `interval` 变量：
```python
interval = 10  # 默认每10个时间单位为一个半天
# 修改为其他值，如 interval = 8
```

### Q2: 如何修改数字格式的刻度间隔规则？

**答**: 在 `_set_numeric_time_axis` 函数中修改间隔判断逻辑：
```python
if makespan <= 50:
    interval = 5  # 修改这里
elif makespan <= 100:
    interval = 10  # 修改这里
# ...
```

### Q3: 可以添加第三种时间格式吗？

**答**: 可以！步骤如下：
1. 在 `visualization.py` 中添加新的函数，如 `_set_hour_time_axis(ax, makespan)`
2. 在 `_set_time_axis` 中添加新的条件分支：
```python
def _set_time_axis(ax, makespan, time_format='day'):
    if time_format == 'day':
        _set_day_time_axis(ax, makespan)
    elif time_format == 'numeric':
        _set_numeric_time_axis(ax, makespan)
    elif time_format == 'hour':  # 新增
        _set_hour_time_axis(ax, makespan)
    else:
        raise ValueError(...)
```

### Q4: 论文中应该使用哪种格式？

**答**: 
- **推荐使用数字格式 (`time_format='numeric'`)**
- 原因：
  1. 学术规范，便于数据对比
  2. 精确显示时间数值
  3. 便于其他研究者复现实验
  4. 国际期刊通常要求数字格式

- **天数格式适合：**
  1. 实际应用场景演示
  2. 项目汇报和现场管理
  3. 面向非技术人员的展示

### Q5: 如何在同一个图中显示两种格式？

**答**: 不建议在同一个图中混用，但可以使用双x轴：
```python
ax2 = ax.twiny()  # 创建第二个x轴
_set_day_time_axis(ax, makespan)     # 下方x轴：天数格式
_set_numeric_time_axis(ax2, makespan) # 上方x轴：数字格式
```

## 📚 相关文件

- `visualization.py` - 主要实现文件
- `example_time_formats.py` - 演示示例
- `config.py` - 可视化配置参数

## 🔄 版本历史

- **v1.1** (2025-01-XX) - 新增数字格式支持，添加 `time_format` 参数
- **v1.0** (2025-01-XX) - 初始版本，仅支持天数格式

## 📧 技术支持

如有问题或建议，请：
1. 查看 `visualization.py` 源代码
2. 运行 `example_time_formats.py` 查看效果
3. 根据需求修改参数和函数

---

**提示**: 默认使用天数格式 (`time_format='day'`)，如需切换为数字格式，只需在调用函数时添加 `time_format='numeric'` 参数即可。

