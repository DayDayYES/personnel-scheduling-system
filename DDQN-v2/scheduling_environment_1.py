# -*- coding: utf-8 -*-
"""
调度环境模块 - 包含工厂环境和调度逻辑
"""

import numpy as np
from config import TEAMS_CONFIG, STANDARD_STEP_TEMPLATES


class FactoryEnvironment:
    """多工作点工厂调度环境"""
    
    def __init__(self, workpoints_data):
        """
        初始化多工作点工厂环境
        
        Args:
            workpoints_data: 字典格式，包含多个工作点的工序信息
        """
        # 存储工作点信息
        self.workpoints = workpoints_data
        self.workpoint_ids = list(workpoints_data.keys())
        
        # 标准工序模板（用于生成默认工序）
        self.standard_step_templates = STANDARD_STEP_TEMPLATES.copy()
        
        # 生成所有工作点的工序实例
        self.work_steps = self._generate_workpoint_steps()
        
        print(f"初始化完成: {len(self.workpoint_ids)}个工作点, 共{len(self.work_steps)}个工序实例")

        # 团队配置
        self.teams = TEAMS_CONFIG.copy()

        # 记录每个队伍目前在各工序上分配的人数
        self.team_allocations = {team: {} for team in self.teams}

        # 🔒 新增：专用团队全局状态跟踪
        self.dedicated_team_current_step = {}  # 跟踪每个专用团队当前正在执行的工序

        # 工序状态: 0 = 未开始, 1 = 进行中, 2 = 已完成
        self.step_status = {step["id"]: 0 for step in self.work_steps}
        self.step_allocations = {step["id"]: 0 for step in self.work_steps}
        self.step_max_allocations = {step["id"]: 0 for step in self.work_steps}
        self.step_start_times = {step["id"]: 0 for step in self.work_steps}
        self.step_end_times = {step["id"]: 0 for step in self.work_steps}

        self.current_time = 0
        self.events = []  # (step_id, completion_time)

    def _generate_workpoint_steps(self):
        """根据工作点数据生成所有工序实例"""
        all_steps = []
        
        for workpoint_id, workpoint_data in self.workpoints.items():
            workpoint_name = workpoint_data.get("name", workpoint_id)
            steps_data = workpoint_data.get("steps", [])
            
            # 如果工作点没有指定工序，使用标准模板
            if not steps_data:
                print(f"工作点 {workpoint_name} 未指定工序，使用标准模板")
                steps_data = self.standard_step_templates.copy()
                # 为标准模板添加默认持续时间
                for i, step in enumerate(steps_data):
                    if "duration" not in step:
                        step["duration"] = [10, 5, 8, 6, 7, 9, 6, 7, 6, 7, 7, 7, 4, 7, 5][i]
            
            # 为每个工作点的工序创建实例
            for step_template in steps_data:
                step_instance = step_template.copy()
                
                # 生成唯一的工序ID
                step_instance["id"] = f"{workpoint_id}_{step_template['name']}"
                step_instance["workpoint_id"] = workpoint_id
                step_instance["workpoint_name"] = workpoint_name
                step_instance["original_name"] = step_template["name"]
                
                # 更新显示名称以包含工作点信息（简化显示）
                wp_number = workpoint_name.replace("工作点", "").strip()
                if not wp_number:
                    wp_number = workpoint_id.split("_")[-1] if "_" in workpoint_id else workpoint_id
                step_instance["display_name"] = f"{wp_number}-{step_template['name']}"

                all_steps.append(step_instance)
                
            print(f"工作点 {workpoint_name}: 生成了 {len(steps_data)} 个工序")
        
        return all_steps

    def _get_step_by_id(self, step_id):
        """根据工序ID获取工序实例"""
        for step in self.work_steps:
            if step["id"] == step_id:
                return step
        return None

    def _get_workpoint_steps(self, workpoint_id):
        """获取指定工作点的所有工序"""
        return [step for step in self.work_steps if step["workpoint_id"] == workpoint_id]

    def reset(self):
        """重置环境到初始状态"""
        for team in self.teams:
            self.teams[team]["available"] = self.teams[team]["size"]
            self.team_allocations[team] = {}

        self.step_status = {step["id"]: 0 for step in self.work_steps}
        self.step_allocations = {step["id"]: 0 for step in self.work_steps}
        self.step_max_allocations = {step["id"]: 0 for step in self.work_steps}
        self.step_start_times = {step["id"]: 0 for step in self.work_steps}
        self.step_end_times = {step["id"]: 0 for step in self.work_steps}

        self.current_time = 0
        self.events = []

        return self._get_state()

    def _get_state(self):
        """将多工作点环境状态转换为神经网络输入向量"""
        state = []

        # 每个工序的状态信息 (4个值/工序)
        for step in self.work_steps:
            step_id = step["id"]
            state.append(self.step_status[step_id])         # 工序状态
            state.append(self.step_allocations[step_id])    # 当前分配人数
            state.append(1.0 if step["dedicated"] else 0.0) # 是否专用团队
            state.append(step["order"])                     # 工序顺序号

        # 团队可用性 (标准化百分比)
        for team in self.teams:
            state.append(self.teams[team]["available"] / self.teams[team]["size"])

        # 工作点完成度统计 (2个值/工作点)
        for workpoint_id in self.workpoint_ids:
            workpoint_steps = self._get_workpoint_steps(workpoint_id)
            if workpoint_steps:
                # 工作点完成进度
                completed_steps = sum(1 for step in workpoint_steps if self.step_status[step["id"]] == 2)
                progress = completed_steps / len(workpoint_steps)
                state.append(progress)
                
                # 工作点活跃度 (正在进行的工序数量)
                active_steps = sum(1 for step in workpoint_steps if self.step_status[step["id"]] == 1)
                activity = active_steps / len(workpoint_steps)
                state.append(activity)
            else:
                state.extend([0.0, 0.0])  # 无工序的工作点

        # 当前时间 (标准化)
        state.append(min(1.0, self.current_time / 1000))

        return np.array(state, dtype=np.float32)

    def get_team_used_workers(self, team_name, check_time=None):
        """获取团队在指定时间点使用的工人数量"""
        if check_time is None:
            check_time = self.current_time
            
        used_workers = 0
        if team_name in self.team_allocations:
            for step_id, workers in self.team_allocations[team_name].items():
                if self.step_status[step_id] == 1:  # 正在进行的工序
                    # 检查工序是否在指定时间点正在执行
                    start_time = self.step_start_times.get(step_id, 0)
                    end_time = self.step_end_times.get(step_id, float('inf'))
                    if start_time <= check_time <= end_time:
                        used_workers += workers
        return used_workers
    
    def get_team_concurrent_workers(self, team_name, current_time):
        """获取指定团队在指定时间点的并发工作人数"""
        if team_name not in self.team_allocations:
            return 0
            
        concurrent_workers = 0
        
        # 检查所有正在进行的工序
        for step_id, workers in self.team_allocations[team_name].items():
            step = self._get_step_by_id(step_id)
            if step and self.step_status[step_id] == 1:  # 正在进行中
                start_time = self.step_start_times[step_id]
                end_time = self.step_end_times[step_id]
                
                # 检查时间是否重叠
                if start_time <= current_time <= end_time:
                    concurrent_workers += workers
                    
        return concurrent_workers
    
    def check_team_capacity_constraint(self, team_name, new_workers, start_time, end_time):
        """检查团队容量约束"""
        team_size = self.teams[team_name]["size"]
        
        # 检查整个时间段内的人员冲突
        time_points = [start_time, end_time]
        
        # 收集所有相关工序的时间点
        if team_name in self.team_allocations:
            for step_id in self.team_allocations[team_name]:
                if self.step_status[step_id] == 1:  # 正在进行的工序
                    time_points.extend([
                        self.step_start_times[step_id],
                        self.step_end_times[step_id]
                    ])
        
        # 去重并排序时间点
        time_points = sorted(list(set(time_points)))
        
        # 检查每个时间段
        for i in range(len(time_points) - 1):
            check_time = (time_points[i] + time_points[i + 1]) / 2  # 时间段中点
            
            # 如果检查时间在新工序时间范围内
            if start_time <= check_time <= end_time:
                concurrent_workers = self.get_team_concurrent_workers(team_name, check_time)
                
                # 加上新工序的人数
                total_workers = concurrent_workers + new_workers
                
                if total_workers > team_size:
                    return False
                    
        return True

    def get_available_steps(self):
        """获取当前可以开始的工序"""
        available_steps = []

        for step in self.work_steps:
            step_id = step["id"]
            
            if self.step_status[step_id] != 0:
                continue  # 已经在进行或已完成

            # 检查同一工作点内的前序约束
            can_start = True
            current_order = step["order"]
            workpoint_id = step["workpoint_id"]

            # 获取同一工作点的所有工序
            workpoint_steps = self._get_workpoint_steps(workpoint_id)
            
            for other_step in workpoint_steps:
                other_step_id = other_step["id"]
                
                # 如果有更低顺序号的工序未完成，不能开始
                if other_step["order"] < current_order and self.step_status[other_step_id] != 2:
                    can_start = False
                    break

                # 对于并行步骤（顺序4），需要检查是否来自同一专用团队
                if (step.get("parallel") and other_step.get("parallel") and 
                    step["team"] == other_step["team"]):
                    if step["dedicated"] and self.step_status[other_step_id] == 1:
                        # 如果同一专用团队的另一个步骤正在进行，不能开始
                        can_start = False
                        break

            if can_start:
                # 检查团队是否有可用人员
                team_name = step["team"]
                team = self.teams[team_name]

                # 对于非专用团队，检查团队总分配人数是否小于团队规模
                if not team["dedicated"]:
                    used_workers = self.get_team_used_workers(team_name)
                    if used_workers < team["size"]:
                        available_steps.append(step_id)
                elif team["available"] == team["size"]:  # 专用团队必须全部可用
                    available_steps.append(step_id)

        return available_steps

    def get_valid_actions(self):
        """获取当前状态下的所有有效动作"""
        valid_actions = []
        available_steps = self.get_available_steps()

        # 按团队分组可用工序
        team_steps = {}
        for step_id in available_steps:
            step = self._get_step_by_id(step_id)
            team_name = step["team"]
            if team_name not in team_steps:
                team_steps[team_name] = []
            team_steps[team_name].append(step_id)

        # 🔒 全局资源分配管理：防止并发分配超出团队容量
        team_allocation_budget = {}  # 跟踪每个团队的剩余分配预算
        
        # 初始化每个团队的可用预算
        for team_name in self.teams:
            current_concurrent = self.get_team_concurrent_workers(team_name, self.current_time)
            available_budget = self.teams[team_name]["size"] - current_concurrent
            team_allocation_budget[team_name] = max(0, available_budget)

        for step_id in available_steps:
            step = self._get_step_by_id(step_id)
            team_name = step["team"]
            team = self.teams[team_name]

            if step["dedicated"]:
                # 🔒 专用团队：使用全局状态跟踪确保互斥性
                # 检查该专用团队是否已经被分配给其他工序
                if team_name in self.dedicated_team_current_step:
                    current_step_id = self.dedicated_team_current_step[team_name]
                    if self.step_status[current_step_id] == 1:  # 仍在进行中
                        # 该专用团队正在执行其他工序，跳过
                        continue
                
                # 检查团队是否可以用于专用工序
                # 🔒 关键修复：区分共用和专用工序的占用情况
                can_use_dedicated = self._can_team_be_used_for_dedicated(team_name, self.current_time)
                
                if can_use_dedicated:
                    workers = team["size"]
                    # 🔒 检查全局预算是否足够
                    if team_allocation_budget[team_name] >= workers:
                        valid_actions.append((step_id, workers))
                        # 更新预算（专用团队用完所有预算）
                        team_allocation_budget[team_name] = 0
                    # 如果预算不足，专用工序无法执行
                # 如果团队部分被占用，专用工序无法执行
            else:
                # 🔒 共用团队处理：所有团队都使用统一的共用团队逻辑
                same_team_steps = team_steps.get(team_name, [])
                
                # 🎯 智能人员分配策略：避免单人分配，优先均匀分配
                possible_allocations = self._generate_smart_worker_allocations(
                    team, step, same_team_steps
                )
                
                # 🔒 关键修复：基于全局预算验证每个分配方案
                validated_allocations = []
                for workers in possible_allocations:
                    if workers <= team_allocation_budget[team_name]:
                        validated_allocations.append(workers)
                
                possible_allocations = validated_allocations
                
                # 严格检查每个分配方案
                for workers in possible_allocations:
                    if workers <= 0:
                        continue
                    
                    # 计算任务的执行时间段
                    base_duration = step["duration"]
                    team_size = step["team_size"]
                    efficiency = 0.6 + 0.4 * (workers / team_size)
                    collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5
                    adjusted_duration = base_duration * (team_size / workers) * efficiency * collaboration_bonus
                    predicted_end_time = self.current_time + adjusted_duration
                    
                    # 🔒 关键修复：检查整个执行期间的并发约束
                    constraint_violated = False
                    
                    # 检查多个时间点
                    check_times = [
                        self.current_time,
                        self.current_time + adjusted_duration * 0.25,
                        self.current_time + adjusted_duration * 0.5,
                        self.current_time + adjusted_duration * 0.75,
                        predicted_end_time - 0.01  # 稍微提前一点避免边界问题
                    ]
                    
                    for check_time in check_times:
                        if check_time < self.current_time:
                            continue
                            
                        # 计算在check_time时刻的并发人数
                        concurrent_at_time = 0
                        if team_name in self.team_allocations:
                            for existing_step_id, existing_workers in self.team_allocations[team_name].items():
                                if self.step_status[existing_step_id] == 1:  # 正在进行
                                    existing_start = self.step_start_times.get(existing_step_id, 0)
                                    existing_end = self.step_end_times.get(existing_step_id, float('inf'))
                                    # 检查现有任务是否在check_time时刻还在执行
                                    if existing_start <= check_time <= existing_end:
                                        concurrent_at_time += existing_workers
                        
                        # 如果新任务在check_time时刻也在执行，加上新任务的人数
                        if self.current_time <= check_time <= predicted_end_time:
                            concurrent_at_time += workers
                        
                        # 检查是否超出团队容量
                        if concurrent_at_time > team["size"]:
                            constraint_violated = True
                            break
                    
                    # 如果没有违反约束，这个分配方案是有效的
                    if not constraint_violated:
                        valid_actions.append((step_id, workers))
                        # 🔒 更新全局预算
                        team_allocation_budget[team_name] -= workers
                        break  # 找到一个有效方案就足够了

        # 如果有正在进行的工序，添加推进时间的动作
        if self.events:
            valid_actions.append(("advance_time", 0))

        return valid_actions

    def step(self, action):
        """在多工作点环境中执行动作"""
        step_id, workers = action

        if step_id == "advance_time":
            # Advance time to the next event
            return self._advance_time()

        # 根据工序ID找到工序
        step = self._get_step_by_id(step_id)
        if step is None:
            raise ValueError(f"工序ID {step_id} 不存在")
            
        team_name = step["team"]
        team = self.teams[team_name]

        # ========== 简化的人员约束检查 ==========
        if step["dedicated"]:
            # 🔒 专用团队全局互斥性检查
            # 检查该专用团队是否已经被分配给其他工序
            if team_name in self.dedicated_team_current_step:
                current_step_id = self.dedicated_team_current_step[team_name]
                if self.step_status[current_step_id] == 1:  # 仍在进行中
                    next_state = self._get_state()
                    reward = -10  # 较大的惩罚
                    done = all(self.step_status[step["id"]] == 2 for step in self.work_steps)
                    print(f"⚠️  专用工序{step_id}无法执行：团队{team_name}正在执行工序{current_step_id}")
                    return next_state, reward, done
            
            # 专用团队检查：使用更智能的可用性判断
            # 🔒 关键修复：区分共用和专用工序的占用情况
            can_use_dedicated = self._can_team_be_used_for_dedicated(team_name, self.current_time)
            
            if not can_use_dedicated:
                # 团队不可用于专用工序
                next_state = self._get_state()
                reward = -10  # 较大的惩罚
                done = all(self.step_status[step["id"]] == 2 for step in self.work_steps)
                
                # 详细的错误信息
                current_concurrent = self.get_team_concurrent_workers(team_name, self.current_time)
                if current_concurrent > 0:
                    print(f"⚠️  专用工序{step_id}无法执行：团队{team_name}当前有{current_concurrent}人被其他工序占用")
                else:
                    print(f"⚠️  专用工序{step_id}无法执行：团队{team_name}状态不满足专用工序要求")
                return next_state, reward, done
                
            # 🔒 更新专用团队全局状态
            self.dedicated_team_current_step[team_name] = step_id
        else:
            # 🔒 简化的共用团队检查：统一使用严格容量约束验证
            is_valid, current_concurrent, team_size = self._validate_team_capacity_constraint(
                team_name, workers, self.current_time
            )
            
            if not is_valid:
                # 容量不足，尝试调整人数
                available_workers = team_size - current_concurrent
                if available_workers > 0:
                    workers = available_workers
                    print(f"⚠️  团队{team_name}容量不足，调整分配人数为{workers}人 (当前使用{current_concurrent}/{team_size})")
                else:
                    # 完全没有可用人员，动作无效
                    next_state = self._get_state()
                    reward = -10
                    done = all(self.step_status[step["id"]] == 2 for step in self.work_steps)
                    print(f"❌ 团队{team_name}容量已满，无法分配人员 (当前使用{current_concurrent}/{team_size})")
                    return next_state, reward, done
        # ========== 检查结束 ==========

        # 继续原有的执行逻辑
        self.step_start_times[step_id] = self.current_time

        # Allocate workers
        if step["dedicated"]:
            # 专用团队
            self.teams[team_name]["available"] = 0  # 将团队设为不可用
        else:
            # 共用团队 - 更新团队分配记录
            if team_name not in self.team_allocations:
                self.team_allocations[team_name] = {}
            self.team_allocations[team_name][step_id] = workers

        self.step_allocations[step_id] = workers
        self.step_max_allocations[step_id] = workers
        self.step_status[step_id] = 1

        # 计算完成时间
        base_duration = step["duration"]
        team_size = step["team_size"]
        efficiency = 0.6 + 0.4 * (workers / team_size)
        collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5
        adjusted_duration = base_duration * (team_size / workers) * efficiency * collaboration_bonus
        completion_time = self.current_time + adjusted_duration

        self.step_end_times[step_id] = completion_time
        self.events.append((step_id, completion_time))
        self.events.sort(key=lambda x: x[1])

        done = all(self.step_status[step["id"]] == 2 for step in self.work_steps)
        next_state = self._get_state()
        reward = -1

        return next_state, reward, done

    def _advance_time(self):
        """推进时间到下一个事件并处理完成情况"""
        if not self.events:
            return self._get_state(), 0, False

        # 获取下一个事件
        step_id, completion_time = self.events.pop(0)

        # 推进时间
        time_delta = completion_time - self.current_time
        self.current_time = completion_time

        # 找到工序
        step = self._get_step_by_id(step_id)
        if step is None:
            raise ValueError(f"工序ID {step_id} 不存在")
            
        team_name = step["team"]

        # 完成工序
        self.step_status[step_id] = 2  # 标记为已完成

        # 释放工人
        if step["dedicated"]:
            # 专用团队
            self.teams[team_name]["available"] = self.teams[team_name]["size"]
            # 🔒 清理专用团队全局状态
            if team_name in self.dedicated_team_current_step:
                if self.dedicated_team_current_step[team_name] == step_id:
                    del self.dedicated_team_current_step[team_name]
        else:
            # 共用团队 - 从团队分配记录中移除
            if team_name in self.team_allocations and step_id in self.team_allocations[team_name]:
                del self.team_allocations[team_name][step_id]

        self.step_allocations[step_id] = 0  # 清零当前分配

        # 检查是否所有工序都已完成
        done = all(self.step_status[step["id"]] == 2 for step in self.work_steps)

        # 奖励是负时间增量，以激励更快完成
        reward = -time_delta

        return self._get_state(), reward, done

    def get_makespan(self):
        """返回当前调度的完工时间（总时间）"""
        if all(self.step_status[step["id"]] == 2 for step in self.work_steps):
            return self.current_time
        else:
            return float('inf')

    def _generate_smart_worker_allocations(self, team, step, same_team_steps):
        """
        智能人员分配策略：避免单人分配，优先均匀分配
        """
        team_size = team["size"]
        step_team_size = step["team_size"]
        team_name = step["team"]
        
        # 获取当前团队的可用人数
        current_concurrent_workers = self.get_team_concurrent_workers(team_name, self.current_time)
        available_workers = team_size - current_concurrent_workers
        
        # 计算理想的分配人数
        max_workers = min(available_workers, step_team_size)
        
        if max_workers <= 0:
            return []
        
        # 🎯 核心策略：避免单人分配，优先合理分配
        possible_allocations = []
        
        if len(same_team_steps) == 1:
            # 只有一个任务时，优先使用更多人员
            if max_workers >= 5:
                # 大团队：提供多种高效选项
                possible_allocations = [max_workers, max_workers * 3 // 4, max_workers // 2]
            elif max_workers >= 3:
                # 中等团队：避免单人，优先3人以上
                possible_allocations = [max_workers, max(3, max_workers * 2 // 3)]
            elif max_workers == 2:
                # 小团队：使用2人
                possible_allocations = [2]
            else:
                # 只有1人可用时，无奈使用（但加入警告）
                possible_allocations = [1]
        else:
            # 多个任务时，均匀分配策略
            num_tasks = len(same_team_steps)
            
            # 计算均匀分配的基础人数
            base_allocation = max(2, available_workers // num_tasks)  # 至少2人
            
            if base_allocation >= available_workers:
                # 可用人数不足以给每个任务分配2人以上
                if available_workers >= 2:
                    possible_allocations = [min(available_workers, step_team_size)]
                else:
                    possible_allocations = [1]  # 无奈的单人分配
            else:
                # 提供均匀分配的多种选项
                optimal_allocation = min(base_allocation + 1, step_team_size)
                balanced_allocation = min(base_allocation, step_team_size)
                
                possible_allocations = [optimal_allocation, balanced_allocation]
                
                # 如果还有余量，可以考虑更多人员
                if optimal_allocation < step_team_size and available_workers > optimal_allocation:
                    extra_allocation = min(optimal_allocation + 2, step_team_size, available_workers)
                    possible_allocations.insert(0, extra_allocation)
        
        # 移除重复值并排序（优先高人数）
        possible_allocations = sorted(list(set(possible_allocations)), reverse=True)
        
        # 🎯 特殊优化：早期阶段优先使用更多人员
        if step["order"] <= 2:  # 早期阶段
            # 为早期阶段增加更多人员选项
            if max_workers >= 4:
                enhanced_allocations = []
                for allocation in possible_allocations:
                    enhanced_allocations.append(allocation)
                    if allocation < max_workers:
                        enhanced_allocation = min(allocation + 1, max_workers, step_team_size)
                        if enhanced_allocation not in enhanced_allocations:
                            enhanced_allocations.append(enhanced_allocation)
                possible_allocations = sorted(list(set(enhanced_allocations)), reverse=True)
        
        # 🚨 最后检查：确保没有不合理的单人分配（除非真的没办法）
        if len(possible_allocations) > 1 and possible_allocations[-1] == 1:
            if available_workers >= 2:
                # 如果有2人以上可用，移除单人选项
                possible_allocations = [a for a in possible_allocations if a >= 2]
        
        return possible_allocations

    def _validate_team_capacity_constraint(self, team_name, additional_workers, current_time):
        """
        严格验证团队容量约束
        检查添加additional_workers是否会违反团队总容量限制
        """
        team_size = self.teams[team_name]["size"]
        current_concurrent = self.get_team_concurrent_workers(team_name, current_time)
        
        # 检查是否会超出容量
        if current_concurrent + additional_workers > team_size:
            return False, current_concurrent, team_size
        
        return True, current_concurrent, team_size

    def _can_team_be_used_for_dedicated(self, team_name, current_time):
        """
        检查团队是否可以用于专用工序
        关键逻辑：专用工序需要整个团队，但需要区分当前占用是共用还是专用
        """
        team_size = self.teams[team_name]["size"]
        
        # 1. 检查是否已经有专用工序在执行
        if team_name in self.dedicated_team_current_step:
            current_step_id = self.dedicated_team_current_step[team_name]
            if self.step_status[current_step_id] == 1:  # 专用工序正在进行
                return False
        
        # 2. 获取当前所有正在进行的工序
        if team_name not in self.team_allocations:
            return True  # 团队完全空闲
        
        current_shared_workers = 0
        current_dedicated_workers = 0
        
        for step_id, workers in self.team_allocations[team_name].items():
            if self.step_status[step_id] == 1:  # 正在进行
                start_time = self.step_start_times.get(step_id, 0)
                end_time = self.step_end_times.get(step_id, float('inf'))
                
                if start_time <= current_time <= end_time:
                    step = self._get_step_by_id(step_id)
                    if step:
                        if step["dedicated"]:
                            current_dedicated_workers += workers
                        else:
                            current_shared_workers += workers
        
        # 3. 专用工序的可用性判断
        if current_dedicated_workers > 0:
            # 已经有专用工序在执行，不能再分配
            return False
        
        if current_shared_workers == 0:
            # 完全空闲，可以分配
            return True
        
        # 4. 🔒 关键判断：有共用工序在执行时的处理
        # 这里需要更智能的策略：
        # - 如果共用工序即将结束（比如剩余时间很短），可以等待
        # - 如果共用工序还有很长时间，专用工序应该等待
        
        # 检查共用工序的剩余时间
        min_remaining_time = float('inf')
        for step_id, workers in self.team_allocations[team_name].items():
            if self.step_status[step_id] == 1:  # 正在进行
                start_time = self.step_start_times.get(step_id, 0)
                end_time = self.step_end_times.get(step_id, float('inf'))
                
                if start_time <= current_time <= end_time:
                    step = self._get_step_by_id(step_id)
                    if step and not step["dedicated"]:  # 共用工序
                        remaining_time = end_time - current_time
                        min_remaining_time = min(min_remaining_time, remaining_time)
        
        # 5. 策略决策
        if min_remaining_time <= 2.0:  # 如果共用工序很快结束（2个时间单位内）
            # 可以考虑让专用工序等待，但这里先返回False，让系统推进时间
            return False
        else:
            # 共用工序还需要较长时间，专用工序需要等待
            return False

    def get_schedule(self):
        """返回多工作点调度信息用于可视化"""
        schedule = []
        for step in self.work_steps:
            step_id = step["id"]
            if self.step_status[step_id] == 2:  # Only include completed steps
                schedule.append({
                    "id": step_id,
                    "name": step["display_name"],
                    "original_name": step["original_name"],
                    "workpoint_id": step["workpoint_id"],
                    "workpoint_name": step["workpoint_name"],
                    "team": step["team"],
                    "start": self.step_start_times[step_id],
                    "end": self.step_end_times[step_id],
                    "workers": self.step_max_allocations[step_id],
                    "order": step["order"]
                })
        return schedule

    def get_workpoint_summary(self):
        """获取各工作点的完成情况摘要"""
        summary = {}
        for workpoint_id in self.workpoint_ids:
            workpoint_steps = self._get_workpoint_steps(workpoint_id)
            if workpoint_steps:
                completed_steps = [step for step in workpoint_steps if self.step_status[step["id"]] == 2]
                workpoint_makespan = 0
                if completed_steps:
                    workpoint_makespan = max(self.step_end_times[step["id"]] for step in completed_steps)
                
                summary[workpoint_id] = {
                    "name": workpoint_steps[0]["workpoint_name"],
                    "total_steps": len(workpoint_steps),
                    "completed_steps": len(completed_steps),
                    "progress": len(completed_steps) / len(workpoint_steps),
                    "makespan": workpoint_makespan,
                    "steps": [{"id": step["id"], "name": step["original_name"], 
                             "status": self.step_status[step["id"]]} for step in workpoint_steps]
                }
        
        return summary


def create_sample_workpoints_data():
    """创建示例工作点数据"""
    return {
        "workpoint_1": {
            "name": "工作点1",
            "steps": [
                {"name": "搭架子", "order": 1, "team": "team1", "dedicated": True, "team_size": 5, "duration": 10},
                {"name": "拆保温", "order": 2, "team": "team2", "dedicated": False, "team_size": 10, "duration": 5},
                {"name": "打磨", "order": 3, "team": "team2", "dedicated": False, "team_size": 10, "duration": 8},
                {"name": "宏观检验", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "duration": 6, "parallel": True},
                {"name": "壁厚测定", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "duration": 7, "parallel": True},
                {"name": "射线检测", "order": 4, "team": "team4", "dedicated": True, "team_size": 5, "duration": 9, "parallel": True},
                {"name": "检验结果评定", "order": 5, "team": "team3", "dedicated": True, "team_size": 10, "duration": 4},
                {"name": "合格报告出具", "order": 7, "team": "team3", "dedicated": True, "team_size": 10, "duration": 5},
            ]
        },
        "workpoint_2": {
            "name": "工作点2", 
            "steps": [
                {"name": "搭架子", "order": 1, "team": "team1", "dedicated": True, "team_size": 5, "duration": 12},
                {"name": "拆保温", "order": 2, "team": "team2", "dedicated": False, "team_size": 10, "duration": 6},
                {"name": "打磨", "order": 3, "team": "team2", "dedicated": False, "team_size": 10, "duration": 7},
                {"name": "表面检测", "order": 4, "team": "team5", "dedicated": False, "team_size": 15, "duration": 8, "parallel": True},
                {"name": "超声检测", "order": 4, "team": "team5", "dedicated": False, "team_size": 15, "duration": 9, "parallel": True},
                {"name": "检验结果评定", "order": 5, "team": "team3", "dedicated": True, "team_size": 10, "duration": 5},
                {"name": "返修", "order": 6, "team": "team6", "dedicated": True, "team_size": 5, "duration": 8},
                {"name": "合格报告出具", "order": 7, "team": "team3", "dedicated": True, "team_size": 10, "duration": 4},
            ]
        },
        "workpoint_3": {
            "name": "工作点3",
            # 不指定steps，将使用标准模板
        }
    }
