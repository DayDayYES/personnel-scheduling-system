# -*- coding: utf-8 -*-
"""
配置模块 - 包含所有配置参数和常量
"""

import os
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免Qt错误
import matplotlib.pyplot as plt

# 环境变量设置
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Matplotlib 中文显示配置
plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示问题
plt.rcParams['axes.unicode_minus'] = False

# 人员分配参数
ALLOCATION_CONFIG = {
    "min_worker_ratio": 0.2,        # 共用团队最小人员分配比例（相对于团队规模）
    "min_worker_absolute": 2,       # 共用团队最小人员分配绝对数量
    "allocation_strategies": [      # 人员分配策略比例
        1.0,    # 100% 可用人员
        0.75,   # 75% 可用人员
        0.5,    # 50% 可用人员
        0.33,   # 33% 可用人员（适合3个并行工序）
        "min"   # 最小人员数量
    ]
}

# 团队配置
TEAMS_CONFIG = {
    "team1": {"size": 5, "dedicated": True, "available": 5},   # 专人队伍1: 5人
    "team2": {"size": 10, "dedicated": False, "available": 10}, # 人员共用队伍2: 10人
    "team3": {"size": 10, "dedicated": False, "available": 10}, # 人员共用队伍3: 10人
    "team4": {"size": 5, "dedicated": True, "available": 5},   # 专人队伍4: 5人
    "team5": {"size": 15, "dedicated": False, "available": 15}, # 人员共用队伍5: 15人
    "team6": {"size": 5, "dedicated": True, "available": 5}    # 专人队伍6: 5人
}

# 团队颜色配置
TEAM_COLORS = {
    "team1": "#FF6B6B", "team2": "#4ECDC4", "team3": "#45B7D1", 
    "team4": "#96CEB4", "team5": "#FFEAA7", "team6": "#DDA0DD"
}

# 团队中文名称
TEAM_NAMES = {
    "team1": "团队1", "team2": "团队2", "team3": "团队3",
    "team4": "团队4", "team5": "团队5", "team6": "团队6"
}

# 标准工序模板
STANDARD_STEP_TEMPLATES = [
    {"name": "搭架子", "order": 1, "team": "team1", "dedicated": True, "team_size": 5},
    {"name": "拆保温", "order": 2, "team": "team2", "dedicated": False, "team_size": 10},
    {"name": "打磨", "order": 3, "team": "team2", "dedicated": False, "team_size": 10},
    {"name": "宏观检验", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "parallel": True},
    {"name": "壁厚测定", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "parallel": True},
    {"name": "射线检测", "order": 4, "team": "team4", "dedicated": True, "team_size": 5, "parallel": True},
    {"name": "表面检测", "order": 4, "team": "team5", "dedicated": False, "team_size": 15, "parallel": True},
    {"name": "超声检测", "order": 4, "team": "team5", "dedicated": False, "team_size": 15, "parallel": True},
    {"name": "其他无损检测", "order": 4, "team": "team5", "dedicated": False, "team_size": 15, "parallel": True},
    {"name": "铁素体检测", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "parallel": True},
    {"name": "硬度检测", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "parallel": True},
    {"name": "金相检验", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "parallel": True},
    {"name": "检验结果评定", "order": 5, "team": "team3", "dedicated": False, "team_size": 10},
    {"name": "返修", "order": 6, "team": "team6", "dedicated": True, "team_size": 5},
    {"name": "合格报告出具", "order": 7, "team": "team3", "dedicated": False, "team_size": 10},
]

# DDQN 算法参数
DDQN_CONFIG = {
    "gamma": 0.99,          # 折扣因子
    "epsilon": 1.0,         # 探索率
    "epsilon_min": 0.01,    # 最小探索率
    "epsilon_decay": 0.995, # 探索率衰减
    "batch_size": 128,      # 批次大小
    "update_freq": 5,       # 目标网络更新频率
    "learning_rate": 0.001, # 学习率
    "memory_size": 10000,   # 经验回放缓冲区大小
    "episodes": 50,         # 训练轮数
    "max_steps": 200,      # 每轮最大步数
    "action_size": 100      # 动作空间大小
}

# 可视化参数
VISUALIZATION_CONFIG = {
    "figure_size": (16, 10),    # 图表尺寸
    "dpi": 300,                 # 图片分辨率
    "bbox_inches": 'tight',     # 边界框设置
    "alpha": 0.8,               # 透明度
    "fontsize_title": 16,       # 标题字体大小
    "fontsize_label": 14,       # 标签字体大小
    "fontsize_legend": 12,      # 图例字体大小
    "fontsize_text": 10,        # 文本字体大小
    "grid_alpha": 0.3,          # 网格透明度
    "label_threshold": 0.05,    # 标签显示阈值（相对于makespan）
    "label_position_threshold": 0.85,  # 标签位置判断阈值
    "xlim_padding": 1.1         # x轴范围填充比例
}

# 文件路径配置
RESULT_DIR = "result"  # 结果保存目录

FILE_PATHS = {
    "best_schedule_pkl": "best_schedule.pkl",
    "best_model": "best_model.pth",
    "enhanced_model": "enhanced_best_model.pth",
    "process_gantt": "1_process_gantt.png",
    "workpoint_gantt": "2_workpoint_gantt.png", 
    "team_gantt": "3_team_gantt.png",
    "traditional_gantt": "best_schedule.png",
    "greedy_result": "greedy_best_schedule.png",
    "improved_greedy_result": "improved_greedy_best_schedule.png",
    "global_best_tracker": "global_best_tracker.png"
}

# 随机种子（用于结果复现）42
RANDOM_SEED = 42

def ensure_result_dir():
    """确保结果目录存在"""
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(current_dir, RESULT_DIR)
    if not os.path.exists(result_path):
        os.makedirs(result_path)
        print(f"✅ 创建结果目录: {result_path}")
    return result_path

def get_result_path(filename):
    """获取结果文件的完整路径"""
    import os
    result_dir = ensure_result_dir()
    return os.path.join(result_dir, filename)
