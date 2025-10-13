# -*- coding: utf-8 -*-
"""
主运行模块 - 使用全局最优结果的版本
"""

import time
import random
import numpy as np
import torch
from scheduling_environment import FactoryEnvironment, create_sample_workpoints_data
from ddqn_algorithm import train_ddqn_agent, run_best_schedule
from enhanced_ddqn_algorithm import train_enhanced_ddqn_agent, run_enhanced_best_schedule
from improved_greedy_algorithm import run_improved_greedy_algorithm
from visualization import save_gantt_charts, visualize_schedule
from global_best_tracker import global_best_tracker
from config import RANDOM_SEED, get_result_path, FILE_PATHS


def run_all_algorithms_and_find_best(workpoints_data):
    """
    运行所有算法并找到全局最优结果
    
    Args:
        workpoints_data: 工作点数据字典
        
    Returns:
        dict: 包含所有算法结果的字典
    """
    print("=" * 80)
    print("🚀 多算法训练 - 寻找全局最优调度方案")
    print("=" * 80)
    
    # 设置随机种子
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    torch.manual_seed(RANDOM_SEED)
    
    # 重置全局最优跟踪器
    global_best_tracker.reset()
    
    results = {}
    
    # 1. 运行改进贪婪算法
    print(f"\n🔍 第1步: 运行改进贪婪算法...")
    start_time = time.time()
    try:
        greedy_schedule, greedy_makespan, greedy_exec_time = run_improved_greedy_algorithm(workpoints_data)
        results['greedy'] = {
            'makespan': greedy_makespan,
            'execution_time': greedy_exec_time,
            'schedule': greedy_schedule,
            'status': 'success'
        }
        print(f"✅ 贪婪算法完成: {greedy_makespan:.2f} 时间单位")
    except Exception as e:
        print(f"❌ 贪婪算法失败: {e}")
        results['greedy'] = {'status': 'failed', 'error': str(e)}
    
    # 2. 运行原版DDQN算法
    print(f"\n🤖 第2步: 运行原版DDQN算法...")
    start_time = time.time()
    try:
        env = FactoryEnvironment(workpoints_data)
        agent, env, best_schedule, rewards, makespans = train_ddqn_agent(env)
        
        # 多次运行取最佳结果
        best_ddqn_makespan = float('inf')
        best_ddqn_schedule = None
        
        for i in range(3):
            schedule, makespan = run_best_schedule(env)
            if makespan < best_ddqn_makespan:
                best_ddqn_makespan = makespan
                best_ddqn_schedule = schedule
        
        ddqn_exec_time = time.time() - start_time
        results['ddqn'] = {
            'makespan': best_ddqn_makespan,
            'execution_time': ddqn_exec_time,
            'schedule': best_ddqn_schedule,
            'training_makespans': makespans,
            'status': 'success'
        }
        print(f"✅ 原版DDQN完成: {best_ddqn_makespan:.2f} 时间单位")
        
    except Exception as e:
        print(f"❌ 原版DDQN失败: {e}")
        results['ddqn'] = {'status': 'failed', 'error': str(e)}
    
    # 3. 运行增强版DDQN算法
    print(f"\n🚀 第3步: 运行增强版DDQN算法...")
    start_time = time.time()
    try:
        env = FactoryEnvironment(workpoints_data)
        enhanced_agent, env, best_schedule, enhanced_rewards, enhanced_makespans = train_enhanced_ddqn_agent(env)
        
        # 多次运行取最佳结果
        best_enhanced_makespan = float('inf')
        best_enhanced_schedule = None
        
        for i in range(3):
            schedule, makespan = run_enhanced_best_schedule(env)
            if makespan < best_enhanced_makespan:
                best_enhanced_makespan = makespan
                best_enhanced_schedule = schedule
        
        enhanced_exec_time = time.time() - start_time
        results['enhanced_ddqn'] = {
            'makespan': best_enhanced_makespan,
            'execution_time': enhanced_exec_time,
            'schedule': best_enhanced_schedule,
            'training_makespans': enhanced_makespans,
            'status': 'success'
        }
        print(f"✅ 增强版DDQN完成: {best_enhanced_makespan:.2f} 时间单位")
        
    except Exception as e:
        print(f"❌ 增强版DDQN失败: {e}")
        results['enhanced_ddqn'] = {'status': 'failed', 'error': str(e)}
    
    return results


def generate_global_best_visualization():
    """使用全局最优结果生成可视化"""
    print(f"\n" + "🎨" * 20)
    print("生成全局最优结果可视化")
    print("🎨" * 20)
    
    # 获取全局最优结果
    best_result = global_best_tracker.get_best_result()
    
    if best_result['makespan'] == float('inf'):
        print("❌ 没有有效的全局最优结果可用于可视化")
        return None
    
    print(f"📊 使用全局最优结果:")
    print(f"   算法: {best_result['algorithm']}")
    print(f"   完工时间: {best_result['makespan']:.2f}")
    if best_result['episode'] is not None:
        print(f"   训练轮次: Episode {best_result['episode']}")
    
    schedule = best_result['schedule']
    makespan = best_result['makespan']
    
    # 生成三张独立的甘特图
    print(f"\n📈 生成甘特图可视化...")
    try:
        # 创建一个临时环境用于可视化
        sample_data = create_sample_workpoints_data()
        env = FactoryEnvironment(sample_data)
        
        saved_files = save_gantt_charts(schedule, makespan, env)
        
        if saved_files:
            print(f"✅ 成功生成 {len(saved_files)} 张甘特图")
        else:
            print(f"⚠️  甘特图生成失败")
        
        # 生成传统甘特图
        print(f"📊 生成传统甘特图...")
        record, img = visualize_schedule(schedule, makespan)
        
        # 保存传统甘特图，文件名包含算法信息
        algorithm_name = best_result['algorithm'].replace(" ", "_")
        traditional_path = get_result_path(f"global_best_{algorithm_name}_schedule.png")
        
        import matplotlib.pyplot as plt
        plt.suptitle(f'全局最优调度方案 - {best_result["algorithm"]} (完工时间: {makespan:.2f})', 
                    fontsize=16, fontweight='bold', y=0.98)
        plt.savefig(traditional_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ 全局最优传统甘特图已保存: {traditional_path}")
        print(f"\n📋 调度详情:")
        print(record)
        
        return {
            'schedule': schedule,
            'makespan': makespan,
            'algorithm': best_result['algorithm'],
            'visualization_files': saved_files,
            'traditional_chart': traditional_path
        }
        
    except Exception as e:
        print(f"❌ 可视化生成失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_final_summary(results):
    """打印最终总结"""
    print(f"\n" + "=" * 80)
    print("📊 算法对比与全局最优结果总结")
    print("=" * 80)
    
    # 打印各算法结果
    successful_results = []
    
    for algo_name, result in results.items():
        if result.get('status') == 'success':
            makespan = result['makespan']
            exec_time = result['execution_time']
            
            algo_display = {
                'greedy': '改进贪婪算法',
                'ddqn': '原版DDQN',
                'enhanced_ddqn': '增强版DDQN'
            }.get(algo_name, algo_name)
            
            successful_results.append((algo_display, makespan, exec_time))
            print(f"✅ {algo_display}: {makespan:.2f} 时间单位 (执行时间: {exec_time:.1f}s)")
        else:
            algo_display = {
                'greedy': '改进贪婪算法',
                'ddqn': '原版DDQN',
                'enhanced_ddqn': '增强版DDQN'
            }.get(algo_name, algo_name)
            print(f"❌ {algo_display}: 执行失败")
    
    # 排序并显示排名
    if successful_results:
        successful_results.sort(key=lambda x: x[1])  # 按makespan排序
        
        print(f"\n🏆 算法性能排名:")
        for rank, (algo, makespan, exec_time) in enumerate(successful_results, 1):
            print(f"  {rank}. {algo}: {makespan:.2f} 时间单位")
    
    # 显示全局最优结果
    global_best_tracker.print_summary()
    
    # 训练过程分析
    print(f"\n📈 训练过程分析:")
    for algo_name in ['ddqn', 'enhanced_ddqn']:
        if algo_name in results and 'training_makespans' in results[algo_name]:
            makespans = results[algo_name]['training_makespans']
            valid_makespans = [m for m in makespans if m != float('inf')]
            
            if valid_makespans:
                best_training = min(valid_makespans)
                avg_training = np.mean(valid_makespans)
                final_training = valid_makespans[-1] if valid_makespans else float('inf')
                
                algo_display = {'ddqn': '原版DDQN', 'enhanced_ddqn': '增强版DDQN'}.get(algo_name)
                print(f"  {algo_display}:")
                print(f"    训练最佳: {best_training:.2f}")
                print(f"    训练平均: {avg_training:.2f}")
                print(f"    最终结果: {final_training:.2f}")


def main():
    """主函数"""
    print("🎯 全局最优调度算法对比系统")
    print("=" * 80)
    
    # 创建测试数据
    sample_data = create_sample_workpoints_data()
    print("📋 测试数据:")
    for wp_id, wp_data in sample_data.items():
        wp_name = wp_data.get("name", wp_id)
        step_count = len(wp_data.get("steps", []))
        print(f"  {wp_name}: {step_count} 个工序" + ("（使用标准模板）" if step_count == 0 else ""))
    
    # 运行所有算法
    results = run_all_algorithms_and_find_best(sample_data)
    
    # 生成全局最优可视化
    visualization_result = generate_global_best_visualization()
    
    # 打印最终总结
    print_final_summary(results)
    
    print(f"\n" + "=" * 80)
    print("🎉 全局最优调度算法对比完成!")
    print("=" * 80)
    
    return results, visualization_result


if __name__ == "__main__":
    main()
