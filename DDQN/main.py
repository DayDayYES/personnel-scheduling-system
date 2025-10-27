# -*- coding: utf-8 -*-
"""
主运行模块 - 整合所有模块的主要执行逻辑
"""

# 设置matplotlib非交互式后端
import matplotlib
matplotlib.use('Agg')

import random
import numpy as np
import torch
import time
import pickle
import os
from config import RANDOM_SEED, FILE_PATHS, get_result_path
from scheduling_environment import FactoryEnvironment, create_sample_workpoints_data
from ddqn_algorithm import train_ddqn_agent, run_best_schedule
from visualization import save_gantt_charts
from global_best_tracker import global_best_tracker
# 导入数据库连接器
from db_connector import DatabaseConnector


def set_random_seeds():
    """设置随机种子以确保结果可复现"""
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    torch.manual_seed(RANDOM_SEED)


def load_workpoints_from_database():
    """
    从数据库加载工作点工序数据
    
    Returns:
        dict: 工作点数据字典，如果失败返回None
    """
    db = DatabaseConnector(
        host="localhost",
        user="root",
        password="123456",
        database="secret"
    )
    
    if db.connect():
        workpoints_data = db.load_all_workpoints_processes()
        db.close()
        return workpoints_data
    else:
        print("❌ 无法连接数据库")
        return None


def load_best_schedule():
    """加载最佳调度方案"""
    try:
        pkl_path = get_result_path(FILE_PATHS["best_schedule_pkl"])
        with open(pkl_path, 'rb') as f:
            final_schedule, final_makespan = pickle.load(f)
        print(f"成功加载最佳调度方案! 完工时间: {final_makespan:.2f}")
        return final_schedule, final_makespan
    except Exception as e:
        print(f"加载保存的最佳方案失败: {e}")
        return None, None


def save_best_schedule(schedule, makespan):
    """保存最佳调度方案"""
    try:
        pkl_path = get_result_path(FILE_PATHS["best_schedule_pkl"])
        with open(pkl_path, 'wb') as f:
            pickle.dump((schedule, makespan), f)
        print(f"✅ 最优调度方案已保存到: {pkl_path}")
        print(f"   完工时间: {makespan:.2f}")
    except Exception as e:
        print(f"⚠️  保存最优方案失败: {e}")


def find_best_schedule_from_runs(env, num_runs=10):
    """通过多次运行找到最佳调度方案"""
    best_final_makespan = float('inf')
    best_final_schedule = None
    best_run_index = -1
    
    print("运行最佳模型以获取最优调度方案...")
    
    for i in range(num_runs):
        schedule, makespan = run_best_schedule(env)
        print(f"运行 {i + 1}/{num_runs}: 完工时间 = {makespan:.2f}")
        
        if makespan < best_final_makespan:
            best_final_makespan = makespan
            best_final_schedule = schedule
            best_run_index = i + 1
            print(f"  发现更优方案! 新的最佳完工时间: {best_final_makespan:.2f}")
    
    print(f"\n🏆 最终采用的最优方案:")
    print(f"  - 完工时间: {best_final_makespan:.2f} 时间单位")
    print(f"  - 任务数量: {len(best_final_schedule)}")
    print(f"  - 来源: 最佳模型第{best_run_index}次运行")
    
    return best_final_schedule, best_final_makespan


def RUN(workpoints_data, save_processes_to_db=True):
    """
    多工作点调度算法主函数 - 集成全局最优跟踪
    
    Args:
        workpoints_data: 工作点数据字典
        save_processes_to_db: 是否将工序数据保存到数据库（默认True）
    """
    print("🚀 开始多工作点调度算法...")
    start_time = time.time()
    
    # 1. 保存工序数据到数据库（如果需要）
    if save_processes_to_db:
        print("\n💾 第一步：保存工序数据到数据库...")
        db = DatabaseConnector(
            host="localhost",
            user="root",
            password="123456",
            database="secret"
        )
        
        if db.connect():
            # 保存所有工作点的工序数据
            db.save_all_workpoints_processes(workpoints_data, clear_existing=True)
            db.close()
        else:
            print("⚠️  数据库连接失败，跳过工序数据保存")
    
    # 设置随机种子
    set_random_seeds()
    
    # 2. 加载已有的全局最优结果（如果存在）
    print("\n📂 第二步：检查已有的全局最优结果...")
    global_best_tracker.load_global_best()
    initial_best = global_best_tracker.get_best_result()
    
    if initial_best['makespan'] != float('inf'):
        print(f"📊 发现已有全局最优结果:")
        print(f"   算法: {initial_best['algorithm']}")
        print(f"   完工时间: {initial_best['makespan']:.2f}")
        if initial_best['episode'] is not None:
            print(f"   训练轮次: Episode {initial_best['episode']}")
    else:
        print("📊 未发现已有全局最优结果，将从头开始")
    
    # 3. 训练DDQN代理
    print("\n📚 第三步：开始训练DDQN代理...")
    env = FactoryEnvironment(workpoints_data)
    agent, env, best_schedule, rewards, makespans = train_ddqn_agent(env, workpoints_data)
    
    # 打印训练结果
    valid_makespans = [m for m in makespans if m is not None and m != float('inf')]
    if valid_makespans:
        training_best = min(valid_makespans)
        training_avg = np.mean(valid_makespans)
        print(f"✅ DDQN训练完成:")
        print(f"   训练最佳: {training_best:.2f}")
        print(f"   训练平均: {training_avg:.2f}")
        print(f"   训练轮数: {len(makespans)}")
    else:
        print("⚠️  DDQN训练未产生有效结果")
    
    # 获取工作点摘要
    workpoint_summary = env.get_workpoint_summary()
    print("\n📋 各工作点完成情况:")
    for wp_id, wp_info in workpoint_summary.items():
        print(f"  {wp_info['name']}: {wp_info['completed_steps']}/{wp_info['total_steps']} 工序完成, "
              f"进度: {wp_info['progress']:.1%}, 完工时间: {wp_info['makespan']:.2f}")
    
    # 运行改进贪婪算法对比
    # print(f"\n🔍 运行改进贪婪算法对比...")
    # compare_with_improved_greedy(workpoints_data, None)  # 不传入DDQN结果，让贪婪算法自己更新全局最优
    
    # 获取当前全局最优结果
    current_best = global_best_tracker.get_best_result()
    
    if current_best['makespan'] == float('inf'):
        print("❌ 未找到任何有效的调度结果")
        return None, None
    
    # 使用全局最优结果
    final_schedule = current_best['schedule']
    final_makespan = current_best['makespan']
    best_algorithm = current_best['algorithm']
    
    print(f"\n🏆 使用全局最优结果进行可视化:")
    print(f"   最佳算法: {best_algorithm}")
    print(f"   最佳完工时间: {final_makespan:.2f}")
    print(f"   任务数量: {len(final_schedule)}")
    if current_best['episode'] is not None:
        print(f"   训练轮次: Episode {current_best['episode']}")
    
    print(f'\n⏱️  总运行时间: {time.time() - start_time:.2f} 秒')
    
    # 生成可视化图表
    print(f"\n🎨 生成可视化图表...")
    
    try:
        # 生成三张独立的甘特图
        record, process_fig, workpoint_fig, team_fig = save_gantt_charts(final_schedule, final_makespan, env)
    
        
        # 打印调度详情
        print(f"\n📋 最优调度详情:")
        print(record)

        # 注意：数据库保存已移到Flask.py中统一处理，避免重复保存
        
        # 打印全局最优摘要
        # global_best_tracker.print_summary()
        
        # 返回: schedule数据, makespan, 以及三个图表
        return final_schedule, final_makespan, process_fig, workpoint_fig, team_fig
        
    except Exception as e:
        print(f"❌ 可视化生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def main(use_database=True):
    """
    主函数 - 程序入口点
    
    Args:
        use_database: 是否从数据库加载工序数据（默认True），否则使用示例数据
    """
    print("=" * 60)
    print("多工作点调度系统")
    print("=" * 60)
    
    # 获取工作点数据
    if use_database:
        print("\n📖 从数据库加载工作点数据...")
        workpoints_data = load_workpoints_from_database()
        
        if workpoints_data is None:
            print("⚠️  数据库加载失败，改用示例数据")
            workpoints_data = create_sample_workpoints_data()
            # 如果使用示例数据，需要先保存到数据库
            print("\n💾 将示例数据保存到数据库...")
            db = DatabaseConnector(
                host="localhost",
                user="root",
                password="123456",
                database="secret"
            )
    else:
        print("\n📝 使用示例工作点数据...")
        workpoints_data = create_sample_workpoints_data()
    
    print("\n开始多工作点调度算法...")
    print(f"工作点数量: {len(workpoints_data)}")
    
    for wp_id, wp_data in workpoints_data.items():
        wp_name = wp_data.get("name", wp_id)
        step_count = len(wp_data.get("steps", []))
        print(f"  {wp_name}: {step_count} 个工序" + ("（使用标准模板）" if step_count == 0 else ""))
    
    # 运行调度算法（不再重复保存工序到数据库）
    final_schedule, final_makespan, process_fig, workpoint_fig, team_fig = RUN(workpoints_data, save_processes_to_db=False)
    if db.connect():
        # 使用新的 save_schedule_result 方法保存
        table_name = db.save_schedule_result(
            schedule_data=final_schedule,
        )
        
        if table_name:
            print(f"✅ 调度结果已保存到表: {table_name}")
        else:
            print("⚠️  调度结果保存失败")
        
        # 关闭数据库连接
        db.close()
    
    print("\n" + "=" * 60)
    print("调度算法执行完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
