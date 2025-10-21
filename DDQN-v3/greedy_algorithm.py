# -*- coding: utf-8 -*-
"""
贪婪算法模块 - 作为DDQN算法的对比基准
"""

import time
from scheduling_environment import FactoryEnvironment
from visualization import visualize_schedule
from config import get_result_path, FILE_PATHS
import matplotlib.pyplot as plt


class GreedyScheduler:
    """贪婪调度算法"""
    
    def __init__(self, env):
        self.env = env
        
    def schedule(self):
        """
        贪婪调度算法实现
        策略：优先选择最早可以开始的工序，分配最多可用的工人
        """
        print("🔍 开始贪婪算法调度...")
        
        # 重置环境
        self.env.reset()
        
        step_count = 0
        max_steps = 1000
        
        while step_count < max_steps:
            # 获取有效动作
            valid_actions = self.env.get_valid_actions()
            
            if not valid_actions:
                break
            
            # 贪婪策略：选择最优动作
            best_action = self._select_greedy_action(valid_actions)
            
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
        
        print(f"🔍 贪婪算法完成: {step_count} 步, 完工时间: {makespan:.2f}")
        
        return schedule, makespan
    
    def _select_greedy_action(self, valid_actions):
        """
        改进的贪婪策略选择动作
        优先级：
        1. 推进时间动作（如果有正在进行的工序且没有可开始的工序）
        2. 优先选择能立即开始的工序（多工作点并行）
        3. 按工序优先级和工作点负载均衡选择
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
        
        # 如果有可开始的工序，优先执行工序而不是推进时间
        if step_actions:
            return self._select_best_step_action(step_actions)
        
        # 如果只有推进时间动作，执行它
        if advance_actions:
            return advance_actions[0]
        
        return None
    
    def _select_best_step_action(self, step_actions):
        """
        从可执行的工序动作中选择最优的
        考虑多工作点并行和负载均衡
        """
        best_action = None
        best_score = float('-inf')
        
        # 获取当前各工作点的进度情况
        workpoint_progress = self._get_workpoint_progress()
        
        for action in step_actions:
            step_id, workers = action
            step = self.env._get_step_by_id(step_id)
            
            if step is None:
                continue
            
            # 计算综合评分
            score = self._calculate_improved_greedy_score(step, workers, workpoint_progress)
            
            if score > best_score:
                best_score = score
                best_action = action
        
        return best_action
    
    def _get_workpoint_progress(self):
        """获取各工作点的当前进度"""
        workpoint_progress = {}
        
        # 遍历所有工序，统计各工作点的进度
        for step_id, step in self.env.steps.items():
            workpoint_id = step.get('workpoint_id', 'unknown')
            
            if workpoint_id not in workpoint_progress:
                workpoint_progress[workpoint_id] = {
                    'completed': 0,
                    'total': 0,
                    'current_order': 0
                }
            
            workpoint_progress[workpoint_id]['total'] += 1
            
            if step['status'] == 'completed':
                workpoint_progress[workpoint_id]['completed'] += 1
            elif step['status'] == 'available':
                # 记录当前可执行的最小order
                current_order = workpoint_progress[workpoint_id]['current_order']
                if current_order == 0 or step['order'] < current_order:
                    workpoint_progress[workpoint_id]['current_order'] = step['order']
        
        return workpoint_progress
    
    def _calculate_greedy_score(self, step, workers):
        """
        计算贪婪评分
        考虑因素：
        1. 工序优先级（order越小越优先）
        2. 工人数量（越多越好）
        3. 工序持续时间（越短越好）
        4. 团队效率
        """
        # 基础评分：工序优先级（order越小分数越高）
        priority_score = 100 / (step["order"] + 1)
        
        # 工人数量评分（归一化到0-50）
        team_size = step["team_size"]
        worker_score = (workers / team_size) * 50
        
        # 持续时间评分（越短越好，归一化到0-30）
        duration = step["duration"]
        duration_score = max(0, 30 - duration)
        
        # 专用团队加分
        dedicated_bonus = 20 if step["dedicated"] else 0
        
        # 总评分
        total_score = priority_score + worker_score + duration_score + dedicated_bonus
        
        return total_score


def run_greedy_algorithm(workpoints_data):
    """
    运行贪婪算法
    
    Args:
        workpoints_data: 工作点数据字典
        
    Returns:
        tuple: (schedule, makespan, execution_time)
    """
    print("🔍 启动贪婪算法对比测试...")
    start_time = time.time()
    
    # 创建环境
    env = FactoryEnvironment(workpoints_data)
    
    # 创建贪婪调度器
    scheduler = GreedyScheduler(env)
    
    # 执行调度
    schedule, makespan = scheduler.schedule()
    
    execution_time = time.time() - start_time
    
    # 获取工作点摘要
    workpoint_summary = env.get_workpoint_summary()
    print("\n🔍 贪婪算法 - 各工作点完成情况:")
    for wp_id, wp_info in workpoint_summary.items():
        print(f"  {wp_info['name']}: {wp_info['completed_steps']}/{wp_info['total_steps']} 工序完成, "
              f"进度: {wp_info['progress']:.1%}, 完工时间: {wp_info['makespan']:.2f}")
    
    print(f"\n🔍 贪婪算法执行时间: {execution_time:.2f} 秒")
    
    return schedule, makespan, execution_time


def save_greedy_result(schedule, makespan):
    """
    保存贪婪算法结果图表
    只生成一张best_schedule.png图
    """
    print("🔍 生成贪婪算法结果图表...")
    
    # 生成传统甘特图
    record, img = visualize_schedule(schedule, makespan)
    
    # 修改标题以区分是贪婪算法结果
    # plt.suptitle(f'贪婪算法调度方案 (总完工时间: {makespan:.2f} 时间单位)', 
    #             fontsize=16, fontweight='bold', y=0.98)
    
    # 保存到result目录
    greedy_result_path = get_result_path(FILE_PATHS["greedy_result"])
    plt.savefig(greedy_result_path, dpi=300, bbox_inches='tight')
    print(f"✅ 贪婪算法结果图已保存为: {greedy_result_path}")
    
    # 关闭图形
    plt.close()
    
    return record


def compare_algorithms(workpoints_data, ddqn_makespan=None):
    """
    对比DDQN和贪婪算法
    
    Args:
        workpoints_data: 工作点数据
        ddqn_makespan: DDQN算法的完工时间（可选）
    """
    print("=" * 60)
    print("算法对比测试 - DDQN vs 贪婪算法")
    print("=" * 60)
    
    # 运行贪婪算法
    greedy_schedule, greedy_makespan, greedy_time = run_greedy_algorithm(workpoints_data)
    
    # 保存贪婪算法结果
    greedy_record = save_greedy_result(greedy_schedule, greedy_makespan)
    
    # 输出对比结果
    print("\n" + "=" * 60)
    print("📊 算法性能对比")
    print("=" * 60)
    
    print(f"🔍 贪婪算法:")
    print(f"  - 完工时间: {greedy_makespan:.2f} 时间单位")
    print(f"  - 执行时间: {greedy_time:.2f} 秒")
    print(f"  - 任务数量: {len(greedy_schedule)}")
    
    if ddqn_makespan is not None:
        print(f"\n🤖 DDQN算法:")
        print(f"  - 完工时间: {ddqn_makespan:.2f} 时间单位")
        
        # 计算性能差异
        improvement = ((greedy_makespan - ddqn_makespan) / greedy_makespan) * 100
        if improvement > 0:
            print(f"\n🏆 DDQN算法优于贪婪算法:")
            print(f"  - 完工时间减少: {greedy_makespan - ddqn_makespan:.2f} 时间单位")
            print(f"  - 性能提升: {improvement:.2f}%")
        elif improvement < 0:
            print(f"\n📈 贪婪算法优于DDQN算法:")
            print(f"  - 完工时间减少: {ddqn_makespan - greedy_makespan:.2f} 时间单位")
            print(f"  - 性能提升: {-improvement:.2f}%")
        else:
            print(f"\n⚖️  两种算法性能相当")
    
    print("\n" + "=" * 60)
    
    return greedy_schedule, greedy_makespan, greedy_time


if __name__ == "__main__":
    # 测试贪婪算法
    from scheduling_environment import create_sample_workpoints_data
    
    sample_data = create_sample_workpoints_data()
    compare_algorithms(sample_data)
