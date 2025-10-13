# -*- coding: utf-8 -*-
"""
独立运行贪婪算法 - 用于快速测试和对比
"""

import time
import random
import numpy as np
from scheduling_environment import create_sample_workpoints_data
from greedy_algorithm import run_greedy_algorithm, save_greedy_result
from config import RANDOM_SEED


def main():
    """只运行贪婪算法的主函数"""
    print("=" * 60)
    print("贪婪算法独立测试")
    print("=" * 60)
    
    # 设置随机种子
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    
    # 创建示例数据
    sample_data = create_sample_workpoints_data()
    print("工作点数据:")
    for wp_id, wp_data in sample_data.items():
        wp_name = wp_data.get("name", wp_id)
        step_count = len(wp_data.get("steps", []))
        print(f"  {wp_name}: {step_count} 个工序" + ("（使用标准模板）" if step_count == 0 else ""))
    
    # 运行贪婪算法
    schedule, makespan, execution_time = run_greedy_algorithm(sample_data)
    
    # 保存结果
    record = save_greedy_result(schedule, makespan)
    
    # 输出详细结果
    print("\n" + "=" * 60)
    print("🔍 贪婪算法最终结果")
    print("=" * 60)
    print(f"完工时间: {makespan:.2f} 时间单位")
    print(f"执行时间: {execution_time:.2f} 秒")
    print(f"任务总数: {len(schedule)}")
    
    # 统计团队使用情况
    teams_used = set(task["team"] for task in schedule)
    print(f"使用团队: {len(teams_used)} 个 ({', '.join(sorted(teams_used))})")
    
    # 输出调度详情
    print(f"\n📋 调度详情:")
    print(record)
    
    print("\n" + "=" * 60)
    print("贪婪算法测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
