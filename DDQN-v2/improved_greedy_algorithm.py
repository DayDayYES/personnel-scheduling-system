# -*- coding: utf-8 -*-
"""
改进的贪婪算法模块 - 专门针对多工作点并行调度优化
"""

import time
from scheduling_environment import FactoryEnvironment
from visualization import visualize_schedule
from config import get_result_path, FILE_PATHS
from global_best_tracker import global_best_tracker
import matplotlib.pyplot as plt


class ImprovedGreedyScheduler:
    """改进的贪婪调度算法 - 支持多工作点并行调度"""
    
    def __init__(self, env):
        self.env = env
        
    def schedule(self):
        """
        改进的贪婪调度算法实现
        核心策略：充分利用多工作点并行执行能力
        """
        print("🔍 开始改进的贪婪算法调度...")
        
        # 重置环境
        self.env.reset()
        
        step_count = 0
        max_steps = 1000
        
        while step_count < max_steps:
            # 获取有效动作
            valid_actions = self.env.get_valid_actions()
            
            if not valid_actions:
                break
            
            # 改进的贪婪策略：优先考虑并行执行
            best_action = self._select_parallel_greedy_action(valid_actions)
            
            if best_action is None:
                break
                
            # 执行动作
            _, _, done = self.env.step(best_action)
            
            if done:
                break
                
            step_count += 1
        
        # 获取调度结果
        schedule = self.env.get_schedule()
        makespan = self.env.get_makespan()
        
        print(f"🔍 改进贪婪算法完成: {step_count} 步, 完工时间: {makespan:.2f}")
        
        return schedule, makespan
    
    def _select_parallel_greedy_action(self, valid_actions):
        """
        并行贪婪策略选择动作
        核心思想：让不同工作点尽可能同时执行不同阶段的工序
        """
        if not valid_actions:
            return None
        
        # 分离推进时间动作和工序动作
        advance_actions = []
        step_actions = []
        
        for action in valid_actions:
            if action[0] == "advance_time":
                advance_actions.append(action)
            else:
                step_actions.append(action)
        
        # 优先执行工序动作，实现并行调度
        if step_actions:
            return self._select_best_parallel_step(step_actions)
        
        # 如果没有可执行的工序，推进时间
        if advance_actions:
            return advance_actions[0]
        
        return None
    
    def _select_best_parallel_step(self, step_actions):
        """
        选择最适合并行执行的工序
        """
        # 获取当前各工作点的状态
        workpoint_status = self._analyze_workpoint_status()
        
        # 按工作点分组可执行的工序
        workpoint_actions = {}
        for action in step_actions:
            step_id, workers = action
            step = self.env._get_step_by_id(step_id)
            
            if step is None:
                continue
            
            workpoint_id = step.get('workpoint_id', 'unknown')
            if workpoint_id not in workpoint_actions:
                workpoint_actions[workpoint_id] = []
            
            workpoint_actions[workpoint_id].append((action, step))
        
        # 选择最优的并行执行策略
        best_action = None
        best_score = float('-inf')
        
        for workpoint_id, actions_steps in workpoint_actions.items():
            for action, step in actions_steps:
                score = self._calculate_parallel_score(step, action[1], workpoint_status)
                
                if score > best_score:
                    best_score = score
                    best_action = action
        
        return best_action
    
    def _analyze_workpoint_status(self):
        """
        分析各工作点的当前状态
        返回每个工作点的进度信息
        """
        workpoint_status = {}
        
        # 遍历所有工序实例
        for step in self.env.work_steps:
            workpoint_id = step.get('workpoint_id', 'unknown')
            
            if workpoint_id not in workpoint_status:
                workpoint_status[workpoint_id] = {
                    'completed_orders': set(),
                    'available_orders': set(),
                    'running_orders': set(),
                    'min_available_order': float('inf'),
                    'max_completed_order': 0
                }
            
            status = workpoint_status[workpoint_id]
            order = step['order']
            step_id = step['id']
            
            # 检查工序状态
            step_status = self.env.step_status.get(step_id, 0)
            
            if step_status == 2:  # 已完成
                status['completed_orders'].add(order)
                status['max_completed_order'] = max(status['max_completed_order'], order)
            elif step_status == 1:  # 进行中
                status['running_orders'].add(order)
            elif step_status == 0:  # 未开始，检查是否可用
                # 检查前置工序是否完成
                if self._is_step_available(step):
                    status['available_orders'].add(order)
                    status['min_available_order'] = min(status['min_available_order'], order)
        
        return workpoint_status
    
    def _is_step_available(self, step):
        """
        检查工序是否可以开始执行
        """
        workpoint_id = step['workpoint_id']
        current_order = step['order']
        
        # 检查同一工作点的前置工序是否都已完成
        for other_step in self.env.work_steps:
            if (other_step['workpoint_id'] == workpoint_id and 
                other_step['order'] < current_order):
                other_step_id = other_step['id']
                if self.env.step_status.get(other_step_id, 0) != 2:  # 未完成
                    return False
        
        return True
    
    def _calculate_parallel_score(self, step, workers, workpoint_status):
        """
        计算并行调度评分
        重点考虑：
        1. 工序优先级（order）
        2. 并行执行机会
        3. 工作点负载均衡
        4. 资源利用效率
        """
        workpoint_id = step.get('workpoint_id', 'unknown')
        step_order = step['order']
        
        # 1. 基础优先级评分（order越小越优先）
        priority_score = 1000 / (step_order + 1)
        
        # 2. 并行执行评分
        parallel_score = self._get_parallel_execution_score(step, workpoint_status)
        
        # 3. 工作点负载均衡评分
        balance_score = self._get_workpoint_balance_score(workpoint_id, workpoint_status)
        
        # 4. 资源利用效率评分
        team_size = step["team_size"]
        efficiency_score = (workers / team_size) * 100
        
        # 5. 专用团队优先评分
        dedicated_bonus = 200 if step.get("dedicated", False) else 0
        
        # 6. 持续时间评分（短任务优先）
        duration_score = max(0, 100 - step["duration"] * 5)
        
        total_score = (priority_score + parallel_score + balance_score + 
                      efficiency_score + dedicated_bonus + duration_score)
        
        return total_score
    
    def _get_parallel_execution_score(self, step, workpoint_status):
        """
        计算并行执行评分
        鼓励不同工作点执行不同order的工序
        """
        step_order = step['order']
        workpoint_id = step.get('workpoint_id', 'unknown')
        
        # 检查其他工作点正在执行的order
        other_running_orders = set()
        for wp_id, status in workpoint_status.items():
            if wp_id != workpoint_id:
                other_running_orders.update(status['running_orders'])
        
        # 如果当前order没有在其他工作点执行，给予高分（真正的并行）
        if step_order not in other_running_orders:
            parallel_score = 800
        else:
            # 即使相同order，不同工作点也可以并行，给予中等分数
            parallel_score = 400
        
        # 如果是该工作点当前可执行的最小order，额外加分
        if workpoint_id in workpoint_status:
            min_order = workpoint_status[workpoint_id]['min_available_order']
            if step_order == min_order:
                parallel_score += 300
        
        return parallel_score
    
    def _get_workpoint_balance_score(self, workpoint_id, workpoint_status):
        """
        计算工作点负载均衡评分
        优先选择进度相对落后的工作点
        """
        if workpoint_id not in workpoint_status:
            return 0
        
        current_status = workpoint_status[workpoint_id]
        current_progress = len(current_status['completed_orders'])
        
        # 计算所有工作点的平均进度
        total_progress = 0
        workpoint_count = 0
        
        for wp_id, status in workpoint_status.items():
            total_progress += len(status['completed_orders'])
            workpoint_count += 1
        
        if workpoint_count == 0:
            return 0
        
        avg_progress = total_progress / workpoint_count
        
        # 进度越落后，评分越高（鼓励均衡发展）
        balance_score = max(0, (avg_progress - current_progress) * 50 + 100)
        
        return balance_score


def run_improved_greedy_algorithm(workpoints_data):
    """
    运行改进的贪婪算法
    
    Args:
        workpoints_data: 工作点数据字典
        
    Returns:
        tuple: (schedule, makespan, execution_time)
    """
    print("🔍 启动改进的贪婪算法对比测试...")
    start_time = time.time()
    
    # 创建环境
    env = FactoryEnvironment(workpoints_data)
    
    # 创建改进的贪婪调度器
    scheduler = ImprovedGreedyScheduler(env)
    
    # 执行调度
    schedule, makespan = scheduler.schedule()
    
    execution_time = time.time() - start_time
    
    # 获取工作点摘要
    workpoint_summary = env.get_workpoint_summary()
    print("\n🔍 改进贪婪算法 - 各工作点完成情况:")
    for wp_id, wp_info in workpoint_summary.items():
        print(f"  {wp_info['name']}: {wp_info['completed_steps']}/{wp_info['total_steps']} 工序完成, "
              f"进度: {wp_info['progress']:.1%}, 完工时间: {wp_info['makespan']:.2f}")
    
    print(f"\n🔍 改进贪婪算法执行时间: {execution_time:.2f} 秒")
    
    # 更新全局最优结果
    global_best_tracker.update_best_result(
        schedule=schedule,
        makespan=makespan,
        algorithm_name="改进贪婪算法",
        episode=None,
        model_path=None
    )
    
    return schedule, makespan, execution_time


def save_improved_greedy_result(schedule, makespan):
    """
    保存改进贪婪算法结果图表
    """
    print("🔍 生成改进贪婪算法结果图表...")
    
    # 生成传统甘特图
    record, img = visualize_schedule(schedule, makespan)
    
    # 修改标题以区分是改进贪婪算法结果
    # plt.suptitle(f'改进贪婪算法调度方案 (总完工时间: {makespan:.2f} 时间单位)', 
    #             fontsize=16, fontweight='bold', y=0.98)
    
    # 保存到result目录
    improved_greedy_path = get_result_path("improved_greedy_best_schedule.png")
    plt.savefig(improved_greedy_path, dpi=300, bbox_inches='tight')
    print(f"✅ 改进贪婪算法结果图已保存为: {improved_greedy_path}")
    
    # 关闭图形
    plt.close()
    
    return record


def compare_with_improved_greedy(workpoints_data, ddqn_makespan=None):
    """
    使用改进的贪婪算法进行对比
    """
    print("=" * 60)
    print("算法对比测试 - DDQN vs 改进贪婪算法")
    print("=" * 60)
    
    # 运行改进的贪婪算法
    schedule, makespan, exec_time = run_improved_greedy_algorithm(workpoints_data)
    
    # 保存结果
    record = save_improved_greedy_result(schedule, makespan)
    
    # 输出对比结果
    print("\n" + "=" * 60)
    print("📊 算法性能对比")
    print("=" * 60)
    
    print(f"🔍 改进贪婪算法:")
    print(f"  - 完工时间: {makespan:.2f} 时间单位")
    print(f"  - 执行时间: {exec_time:.2f} 秒")
    print(f"  - 任务数量: {len(schedule)}")
    
    if ddqn_makespan is not None:
        print(f"\n🤖 DDQN算法:")
        print(f"  - 完工时间: {ddqn_makespan:.2f} 时间单位")
        
        # 计算性能差异
        improvement = ((makespan - ddqn_makespan) / makespan) * 100
        if improvement > 0:
            print(f"\n🏆 DDQN算法优于改进贪婪算法:")
            print(f"  - 完工时间减少: {makespan - ddqn_makespan:.2f} 时间单位")
            print(f"  - 性能提升: {improvement:.2f}%")
        elif improvement < 0:
            print(f"\n📈 改进贪婪算法优于DDQN算法:")
            print(f"  - 完工时间减少: {ddqn_makespan - makespan:.2f} 时间单位")
            print(f"  - 性能提升: {-improvement:.2f}%")
        else:
            print(f"\n⚖️  两种算法性能相当")
    
    print(f"\n💡 改进贪婪算法特点:")
    print(f"  - 支持多工作点真正并行调度")
    print(f"  - 优先级驱动的工序选择")
    print(f"  - 工作点负载均衡")
    print(f"  - 资源利用效率优化")
    
    print("\n" + "=" * 60)
    
    return schedule, makespan, exec_time


if __name__ == "__main__":
    # 测试改进的贪婪算法
    from scheduling_environment import create_sample_workpoints_data
    
    sample_data = create_sample_workpoints_data()
    compare_with_improved_greedy(sample_data)
