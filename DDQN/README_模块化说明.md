# 多工作点调度系统 - 模块化重构说明

## 📁 模块结构

```
DDQN-v2/
├── config.py                    # 配置模块 - 所有配置参数和常量
├── scheduling_environment.py    # 调度环境模块 - 工厂环境和调度逻辑
├── ddqn_algorithm.py           # DDQN算法模块 - 神经网络和强化学习算法
├── visualization.py            # 可视化模块 - 所有图表生成功能
├── main.py                     # 主运行模块 - 整合所有模块的执行逻辑
├── RUN.py                      # 原始文件（保留作为备份）
└── README_模块化说明.md        # 本说明文档
```

## 🔧 各模块功能详解

### 1. config.py - 配置模块
**功能**: 集中管理所有配置参数和常量
**包含内容**:
- 团队配置 (`TEAMS_CONFIG`)
- 团队颜色映射 (`TEAM_COLORS`)
- 团队中文名称 (`TEAM_NAMES`)
- 标准工序模板 (`STANDARD_STEP_TEMPLATES`)
- DDQN算法参数 (`DDQN_CONFIG`)
- 可视化参数 (`VISUALIZATION_CONFIG`)
- 文件路径配置 (`FILE_PATHS`)
- 随机种子 (`RANDOM_SEED`)

**优势**:
- 统一管理配置，便于调整参数
- 避免硬编码，提高代码可维护性
- 支持不同环境的配置切换

### 2. scheduling_environment.py - 调度环境模块
**功能**: 实现工厂调度环境和相关逻辑
**主要类**:
- `FactoryEnvironment`: 多工作点工厂调度环境
- `create_sample_workpoints_data()`: 创建示例数据

**核心方法**:
- `reset()`: 重置环境状态
- `step()`: 执行调度动作
- `get_valid_actions()`: 获取有效动作
- `get_schedule()`: 获取调度结果
- `get_makespan()`: 计算完工时间

**特点**:
- 支持多工作点调度
- 实现团队资源约束检查
- 处理并行和串行工序依赖

### 3. ddqn_algorithm.py - DDQN算法模块
**功能**: 实现深度强化学习算法
**主要类**:
- `DDQNNetwork`: 深度Q网络
- `ReplayBuffer`: 经验回放缓冲区
- `DDQNAgent`: DDQN智能体

**核心函数**:
- `train_ddqn_agent()`: 训练DDQN代理
- `run_best_schedule()`: 运行最佳调度方案

**特点**:
- 使用Double DQN算法
- 支持经验回放和目标网络
- 可配置的超参数

### 4. visualization.py - 可视化模块
**功能**: 生成各种调度结果图表
**主要函数**:
- `create_traditional_gantt_chart()`: 工序视角甘特图
- `create_workpoint_gantt_chart()`: 多工作点视角甘特图
- `create_team_gantt_chart()`: 团队视角甘特图
- `visualize_schedule()`: 传统甘特图
- `save_gantt_charts()`: 保存所有图表

**特点**:
- 智能标签定位，避免重叠
- 统一的颜色和样式配置
- 支持多种视角的可视化

### 5. main.py - 主运行模块
**功能**: 整合所有模块，提供统一的执行入口
**主要函数**:
- `RUN()`: 主要调度执行函数
- `main()`: 程序入口点
- `load_best_schedule()`: 加载最佳方案
- `save_best_schedule()`: 保存最佳方案
- `find_best_schedule_from_runs()`: 多次运行寻优

**特点**:
- 模块化的执行流程
- 完整的错误处理
- 结果持久化存储

## 🚀 使用方法

### 基本使用
```python
# 导入主模块
from main import RUN
from scheduling_environment import create_sample_workpoints_data

# 创建工作点数据
workpoints_data = create_sample_workpoints_data()

# 运行调度算法
record, img = RUN(workpoints_data)
```

### 自定义配置
```python
# 修改配置参数
from config import DDQN_CONFIG, VISUALIZATION_CONFIG

# 调整训练参数
DDQN_CONFIG["episodes"] = 100
DDQN_CONFIG["learning_rate"] = 0.0005

# 调整可视化参数
VISUALIZATION_CONFIG["figure_size"] = (20, 12)
VISUALIZATION_CONFIG["dpi"] = 600
```

### 单独使用模块
```python
# 只使用调度环境
from scheduling_environment import FactoryEnvironment
env = FactoryEnvironment(workpoints_data)

# 只使用可视化功能
from visualization import create_traditional_gantt_chart
fig = create_traditional_gantt_chart(schedule, makespan)

# 只使用DDQN算法
from ddqn_algorithm import train_ddqn_agent
agent, env, _, _, _ = train_ddqn_agent(env)
```

## 🔄 与原版本的对比

### 原版本 (RUN.py)
- ❌ 单一大文件，2300+ 行代码
- ❌ 功能耦合度高，难以维护
- ❌ 配置参数分散，难以管理
- ❌ 代码复用性差

### 模块化版本
- ✅ 5个专门模块，职责清晰
- ✅ 低耦合高内聚，易于维护
- ✅ 集中配置管理，参数调整方便
- ✅ 高度模块化，便于扩展和测试

## 📈 模块化优势

### 1. 可维护性
- 每个模块职责单一，便于理解和修改
- 模块间接口清晰，降低修改风险
- 配置集中管理，参数调整更方便

### 2. 可扩展性
- 新增功能只需修改相关模块
- 支持插件式的功能扩展
- 便于添加新的算法或可视化方式

### 3. 可测试性
- 每个模块可以独立测试
- 便于编写单元测试和集成测试
- 问题定位更加精确

### 4. 可复用性
- 模块可以在其他项目中复用
- 支持不同的组合使用方式
- 便于构建更大的系统

## 🔧 开发建议

### 添加新功能
1. 确定功能归属的模块
2. 在对应模块中添加实现
3. 在config.py中添加相关配置
4. 更新main.py中的调用逻辑

### 性能优化
1. 在ddqn_algorithm.py中优化算法
2. 在scheduling_environment.py中优化环境逻辑
3. 在visualization.py中优化图表生成

### 配置调整
1. 修改config.py中的相关参数
2. 无需修改其他模块代码
3. 支持运行时动态配置

## 📝 注意事项

1. **导入顺序**: 确保config.py最先导入
2. **路径问题**: 所有模块应在同一目录下
3. **依赖管理**: 确保所需的Python包已安装
4. **文件权限**: 确保有写入权限以保存图表和数据

## 🎯 未来扩展方向

1. **算法扩展**: 添加其他优化算法（遗传算法、粒子群等）
2. **可视化增强**: 添加交互式图表、3D可视化
3. **数据接口**: 支持数据库、API等数据源
4. **Web界面**: 开发Web版本的用户界面
5. **性能监控**: 添加性能分析和监控功能
