# -*- coding: utf-8 -*-
"""
调度环境模块 - 包含工厂环境和调度逻辑
"""

import numpy as np
from config import TEAMS_CONFIG, STANDARD_STEP_TEMPLATES, ALLOCATION_CONFIG


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
                    if start_time <= check_time < end_time:  # 修改为 < 而不是 <=，避免边界重复计数
                        used_workers += workers
        return used_workers
    
    def get_max_concurrent_workers_in_period(self, team_name, start_time, end_time, exclude_steps=None):
        """
        获取团队在指定时间段内的最大并发工作人数
        
        Args:
            team_name: 团队名称
            start_time: 时间段开始
            end_time: 时间段结束
            exclude_steps: 要排除的工序ID列表（用于检查新工序时排除自己）
        
        Returns:
            该时间段内的最大并发人数
        """
        if exclude_steps is None:
            exclude_steps = set()
        else:
            exclude_steps = set(exclude_steps)
        
        # 收集所有相关的时间点
        time_points = set([start_time, end_time])
        
        if team_name in self.team_allocations:
            for step_id, workers in self.team_allocations[team_name].items():
                if step_id in exclude_steps:
                    continue
                    
                if self.step_status[step_id] == 1:  # 正在进行的工序
                    step_start = self.step_start_times.get(step_id, 0)
                    step_end = self.step_end_times.get(step_id, float('inf'))
                    
                    # 只添加与检查时间段有重叠的工序时间点
                    if not (step_end <= start_time or step_start >= end_time):
                        time_points.add(step_start)
                        time_points.add(step_end)
        
        # 排序时间点
        time_points = sorted(list(time_points))
        
        # 检查每个时间段的并发人数
        max_concurrent = 0
        for i in range(len(time_points) - 1):
            # 在时间段的中点检查并发人数
            check_time = (time_points[i] + time_points[i + 1]) / 2
            
            # 只检查在指定范围内的时间点
            if start_time <= check_time < end_time:
                concurrent = 0
                
                if team_name in self.team_allocations:
                    for step_id, workers in self.team_allocations[team_name].items():
                        if step_id in exclude_steps:
                            continue
                            
                        if self.step_status[step_id] == 1:
                            step_start = self.step_start_times.get(step_id, 0)
                            step_end = self.step_end_times.get(step_id, float('inf'))
                            
                            if step_start <= check_time < step_end:
                                concurrent += workers
                
                max_concurrent = max(max_concurrent, concurrent)
        
        return max_concurrent
    
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
    
    def check_team_capacity_constraint(self, team_name, new_workers, start_time, end_time, exclude_steps=None):
        """
        检查团队容量约束（改进版）
        
        Args:
            team_name: 团队名称
            new_workers: 新工序需要的人数
            start_time: 新工序开始时间
            end_time: 新工序结束时间
            exclude_steps: 要排除的工序ID列表（用于批量检查时排除其他批量工序）
        
        Returns:
            True表示满足约束，False表示违反约束
        """
        team_size = self.teams[team_name]["size"]
        team_info = self.teams[team_name]
        
        # 对于专用团队，检查是否完全可用
        if team_info["dedicated"]:
            if team_info["available"] != team_size:
                return False  # 专用团队必须完全可用才能开始新任务
            return True
        
        # 对于共用团队，使用新的方法检查整个时间段内的最大并发人数
        max_concurrent = self.get_max_concurrent_workers_in_period(
            team_name, start_time, end_time, exclude_steps
        )
        
        # 检查加上新工序后是否超过团队容量
        if max_concurrent + new_workers > team_size:
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

                # 对于专用团队，检查是否完全可用
                if step["dedicated"]:
                    if team["available"] == team["size"]:  # 专用团队必须全部可用
                        available_steps.append(step_id)
                else:
                    # 对于共用团队，检查是否有足够的可用人员
                    used_workers = self.get_team_used_workers(team_name)
                    min_required = max(
                        ALLOCATION_CONFIG["min_worker_absolute"], 
                        int(team["size"] * ALLOCATION_CONFIG["min_worker_ratio"])
                    )
                    if used_workers + min_required <= team["size"]:
                        available_steps.append(step_id)

        return available_steps

    def get_parallel_step_groups(self):
        """
        识别可以同时并行执行的工序组（按工作点、团队和order分组）
        只针对共用团队的并行工序
        
        Returns:
            字典格式: {(workpoint_id, team_name, order): [step_ids]}
        """
        available_steps = self.get_available_steps()
        parallel_groups = {}
        
        for step_id in available_steps:
            step = self._get_step_by_id(step_id)
            
            # 只处理共用团队的并行工序
            if step["dedicated"]:
                continue
                
            # 检查是否标记为可并行
            if not step.get("parallel", False):
                continue
            
            # 按工作点、团队和order分组
            group_key = (step["workpoint_id"], step["team"], step["order"])
            
            if group_key not in parallel_groups:
                parallel_groups[group_key] = []
            
            parallel_groups[group_key].append(step_id)
        
        # 过滤掉只有单个工序的组（单个工序不需要批量启动）
        parallel_groups = {k: v for k, v in parallel_groups.items() if len(v) > 1}
        
        return parallel_groups
    
    def generate_batch_allocation(self, step_ids, team_name, team_size):
        """
        为一组并行工序生成均匀分配方案
        
        Args:
            step_ids: 工序ID列表
            team_name: 团队名称
            team_size: 团队总人数
            
        Returns:
            分配方案列表: [[(step_id1, workers1), (step_id2, workers2), ...], ...]
        """
        num_steps = len(step_ids)
        if num_steps == 0:
            return []
        
        # 获取当前时间点团队已使用的人数
        current_used = self.get_team_used_workers(team_name, self.current_time)
        available_workers = team_size - current_used
        
        # 最小分配人数
        min_workers = max(
            ALLOCATION_CONFIG["min_worker_absolute"],
            int(team_size * ALLOCATION_CONFIG["min_worker_ratio"])
        )
        
        # 检查是否有足够的人员进行批量启动
        min_required_total = num_steps * min_workers
        if available_workers < min_required_total:
            return []  # 人员不足，无法批量启动
        
        allocation_schemes = []
        
        # 方案1: 完全均匀分配
        if available_workers >= num_steps * min_workers:
            workers_per_step = available_workers // num_steps
            remainder = available_workers % num_steps
            
            if workers_per_step >= min_workers:
                allocation = []
                for i, step_id in enumerate(step_ids):
                    # 将余数分配给前面的工序
                    workers = workers_per_step + (1 if i < remainder else 0)
                    allocation.append((step_id, workers))
                allocation_schemes.append(allocation)
        
        # 方案2: 优先分配策略（为前面的工序分配更多人员）
        # 这样可以让部分工序更快完成，释放资源
        if available_workers >= num_steps * min_workers:
            allocation = []
            remaining = available_workers
            
            for i, step_id in enumerate(step_ids):
                if i == num_steps - 1:
                    # 最后一个工序获得剩余所有人员
                    workers = remaining
                else:
                    # 计算一个合理的分配比例
                    avg_for_rest = remaining // (num_steps - i)
                    workers = max(min_workers, int(avg_for_rest * 1.2))
                    workers = min(workers, remaining - (num_steps - i - 1) * min_workers)
                
                allocation.append((step_id, workers))
                remaining -= workers
            
            # 确保方案与方案1不同
            if allocation != allocation_schemes[0] if allocation_schemes else True:
                allocation_schemes.append(allocation)
        
        # 方案3: 最小人员分配（所有工序都分配最小人数）
        if available_workers >= num_steps * min_workers:
            allocation = [(step_id, min_workers) for step_id in step_ids]
            if allocation not in allocation_schemes:
                allocation_schemes.append(allocation)
        
        return allocation_schemes
    
    def validate_batch_allocation(self, batch_allocation):
        """
        验证批量分配方案是否满足所有约束
        
        Args:
            batch_allocation: [(step_id, workers), ...]
            
        Returns:
            (is_valid, reason): (是否有效, 失败原因)
        """
        if not batch_allocation:
            return False, "空分配方案"
        
        # 按团队分组检查
        team_allocations = {}
        for step_id, workers in batch_allocation:
            step = self._get_step_by_id(step_id)
            if step is None:
                return False, f"工序{step_id}不存在"
            
            team_name = step["team"]
            if team_name not in team_allocations:
                team_allocations[team_name] = []
            team_allocations[team_name].append((step_id, workers, step))
        
        # 检查每个团队的约束
        for team_name, allocations in team_allocations.items():
            team_size = self.teams[team_name]["size"]
            
            # 计算总分配人数
            total_workers = sum(workers for _, workers, _ in allocations)
            
            # 检查是否超过团队容量
            current_used = self.get_team_used_workers(team_name, self.current_time)
            if current_used + total_workers > team_size:
                return False, f"团队{team_name}容量不足: 当前使用{current_used}, 需要{total_workers}, 总容量{team_size}"
            
            # 检查时间约束（计算每个工序的预计完成时间，确保不会超员）
            step_times = []
            for step_id, workers, step in allocations:
                base_duration = step["duration"]
                team_step_size = step["team_size"]
                
                efficiency = 0.6 + 0.4 * (workers / team_step_size)
                collaboration_bonus = 1.0 - 0.2 * (workers / team_step_size) ** 0.5
                adjusted_duration = base_duration * (team_step_size / workers) * efficiency * collaboration_bonus
                
                start_time = self.current_time
                end_time = start_time + adjusted_duration
                step_times.append((step_id, workers, start_time, end_time))
            
            # 检查批量启动时是否所有工序都能满足容量约束
            # 需要排除批量中的其他工序，只检查与已有工序的冲突
            exclude_step_ids = [step_id for step_id, _, _ in allocations]
            
            for step_id, workers, start_time, end_time in step_times:
                # 排除当前检查的工序和同批次的其他工序
                exclude_for_this = [sid for sid in exclude_step_ids if sid != step_id]
                
                if not self.check_team_capacity_constraint(
                    team_name, workers, start_time, end_time, exclude_steps=exclude_for_this
                ):
                    return False, f"工序{step_id}时间段[{start_time:.2f}, {end_time:.2f}]违反容量约束"
        
        return True, "验证通过"

    def get_valid_actions(self):
        """
        获取当前状态下的所有有效动作（支持批量启动）
        
        Returns:
            valid_actions: 动作列表，包含以下类型：
                - 单个工序启动: (step_id, workers)
                - 批量工序启动: ("batch_start", [(step_id1, w1), (step_id2, w2), ...])
                - 推进时间: ("advance_time", 0)
        """
        valid_actions = []
        available_steps = self.get_available_steps()

        # 1. 识别可以批量启动的并行工序组
        parallel_groups = self.get_parallel_step_groups()
        batch_step_ids = set()  # 已经在批量方案中的工序
        
        # 为每个并行工序组生成批量启动方案
        for (workpoint_id, team_name, order), step_ids in parallel_groups.items():
            team = self.teams[team_name]
            team_size = team["size"]
            
            # 生成均匀分配方案
            allocation_schemes = self.generate_batch_allocation(step_ids, team_name, team_size)
            
            # 验证并添加有效的批量方案
            for allocation in allocation_schemes:
                is_valid, reason = self.validate_batch_allocation(allocation)
                if is_valid:
                    valid_actions.append(("batch_start", tuple(allocation)))
                    # 记录这些工序ID，避免重复生成单个启动动作
                    batch_step_ids.update([step_id for step_id, _ in allocation])
        
        # 2. 为非批量工序和专用团队工序生成单个启动动作
        # 按团队分组可用工序，用于优化并行处理
        team_steps = {}
        for step_id in available_steps:
            # 跳过已经在批量方案中的工序
            if step_id in batch_step_ids:
                continue
                
            step = self._get_step_by_id(step_id)
            team_name = step["team"]
            if team_name not in team_steps:
                team_steps[team_name] = []
            team_steps[team_name].append(step_id)

        # 3. 为非批量工序生成单个启动动作
        for step_id in available_steps:
            # 跳过已经在批量方案中的工序
            if step_id in batch_step_ids:
                continue
                
            step = self._get_step_by_id(step_id)
            team_name = step["team"]
            team = self.teams[team_name]

            # 预计算工序的开始和结束时间
            base_duration = step["duration"]
            team_size = step["team_size"]
            predicted_start_time = self.current_time

            if step["dedicated"]:
                # 专用团队总是使用全部人力
                if team["available"] == team["size"]:
                    workers = team["size"]
                    
                    # 计算预期完成时间
                    efficiency = 0.6 + 0.4 * (workers / team_size)
                    collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5
                    adjusted_duration = base_duration * (team_size / workers) * efficiency * collaboration_bonus
                    predicted_end_time = predicted_start_time + adjusted_duration
                    
                    # 专用团队不需要检查时间冲突（因为他们独占团队）
                    valid_actions.append((step_id, workers))
            else:
                # 对于共用团队，需要检查时间冲突
                used_workers = self.get_team_used_workers(team_name, self.current_time)
                available_workers = team["size"] - used_workers
                same_team_steps = team_steps.get(team_name, [])

                # 生成可能的工人分配方案
                possible_allocations = []
                
                # 设置最小分配人数，避免单人分配效率过低
                min_workers = max(
                    ALLOCATION_CONFIG["min_worker_absolute"], 
                    int(team_size * ALLOCATION_CONFIG["min_worker_ratio"])
                )
                
                if len(same_team_steps) == 1 and available_workers > 0:
                    # 单个工序时，优先分配较多人员
                    if available_workers >= min_workers:
                        possible_allocations = [min(available_workers, team_size)]
                elif len(same_team_steps) > 1 and available_workers > 0:
                    # 多个工序时，考虑均匀分配
                    max_allocation = min(available_workers, team_size)
                    
                    if max_allocation >= min_workers:
                        # 生成均匀分配方案，避免单人分配
                        possible_allocations = [
                            max_allocation,
                            max(min_workers, int(max_allocation * 0.75)),
                            max(min_workers, int(max_allocation * 0.5)),
                            max(min_workers, int(max_allocation * 0.33)),  # 适合3个并行工序
                            min_workers
                        ]
                        # 移除重复值并排序
                        possible_allocations = sorted(list(set(possible_allocations)), reverse=True)

                # 检查每个分配方案是否满足时间约束
                for workers in possible_allocations:
                    if workers <= 0:
                        continue
                        
                    # 计算预期完成时间
                    efficiency = 0.6 + 0.4 * (workers / team_size)
                    collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5
                    adjusted_duration = base_duration * (team_size / workers) * efficiency * collaboration_bonus
                    predicted_end_time = predicted_start_time + adjusted_duration
                    
                    # 使用改进的容量约束检查
                    if self.check_team_capacity_constraint(team_name, workers, 
                                                         predicted_start_time, predicted_end_time):
                        valid_actions.append((step_id, workers))
                    else:
                        # 如果当前分配方案不满足约束，后续更大的分配方案也不会满足
                        break

        # 4. 如果有正在进行的工序，添加推进时间的动作
        if self.events:
            valid_actions.append(("advance_time", 0))

        return valid_actions

    def step(self, action):
        """
        在多工作点环境中执行动作（支持批量启动）
        
        Args:
            action: 动作，可以是：
                - (step_id, workers): 单个工序启动
                - ("batch_start", [(step_id1, w1), (step_id2, w2), ...]): 批量启动
                - ("advance_time", 0): 推进时间
        
        Returns:
            (next_state, reward, done): 下一状态，奖励，是否完成
        """
        action_type, action_data = action

        if action_type == "advance_time":
            # 推进时间到下一个事件
            return self._advance_time()
        
        if action_type == "batch_start":
            # 批量启动多个工序
            return self._step_batch(action_data)
        
        # 单个工序启动（保持向后兼容）
        step_id = action_type
        workers = action_data

        # 根据工序ID找到工序
        step = self._get_step_by_id(step_id)
        if step is None:
            raise ValueError(f"工序ID {step_id} 不存在")
            
        team_name = step["team"]
        team_size = step["team_size"]

        # 🔒 最终安全检查：验证团队容量约束
        base_duration = step["duration"]
        efficiency = 0.6 + 0.4 * (workers / team_size)
        collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5
        adjusted_duration = base_duration * (team_size / workers) * efficiency * collaboration_bonus
        predicted_end_time = self.current_time + adjusted_duration
        
        if step["dedicated"]:
            # 专用团队检查：必须完全可用才能开始
            if self.teams[team_name]["available"] != self.teams[team_name]["size"]:
                reward = -1000  # 严重惩罚
                done = all(self.step_status[step["id"]] == 2 for step in self.work_steps)
                next_state = self._get_state()
                print(f"⚠️  专用团队{team_name}不完全可用：可用{self.teams[team_name]['available']}人，需要{self.teams[team_name]['size']}人")
                return next_state, reward, done
            # 专用团队使用全部人员
            workers = self.teams[team_name]["size"]
        else:
            # 共用团队检查：使用改进的容量约束检查
            # 检查整个执行时间段内是否会违反容量约束
            if not self.check_team_capacity_constraint(team_name, workers, 
                                                     self.current_time, predicted_end_time):
                # 尝试计算可用的最大人数
                max_concurrent = self.get_max_concurrent_workers_in_period(
                    team_name, self.current_time, predicted_end_time
                )
                available_workers = self.teams[team_name]["size"] - max_concurrent
                min_required = max(
                    ALLOCATION_CONFIG["min_worker_absolute"], 
                    int(self.teams[team_name]["size"] * ALLOCATION_CONFIG["min_worker_ratio"])
                )
                
                if available_workers < min_required:
                    # 没有足够可用人员，返回惩罚
                    reward = -1000  # 严重惩罚
                    done = all(self.step_status[step["id"]] == 2 for step in self.work_steps)
                    next_state = self._get_state()
                    print(f"⚠️  团队{team_name}容量约束违反：时间段[{self.current_time:.2f}, {predicted_end_time:.2f}]内最大已用{max_concurrent}人，尝试分配{workers}人，总容量{self.teams[team_name]['size']}人")
                    return next_state, reward, done
                else:
                    # 自动调整为可用人数
                    old_workers = workers
                    workers = available_workers
                    print(f"🔧 自动调整团队{team_name}分配：从{old_workers}人调整为{workers}人")
                    
                    # 重新计算完成时间
                    efficiency = 0.6 + 0.4 * (workers / team_size)
                    collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5
                    adjusted_duration = base_duration * (team_size / workers) * efficiency * collaboration_bonus
                    predicted_end_time = self.current_time + adjusted_duration

        # Record start time
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
        self.step_max_allocations[step_id] = workers  # 记录分配的工人数
        self.step_status[step_id] = 1  # In progress

        # Calculate completion time based on worker allocation
        base_duration = step["duration"]
        team_size = step["team_size"]

        # 效率计算
        efficiency = 0.6 + 0.4 * (workers / team_size)
        collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5
        adjusted_duration = base_duration * (team_size / workers) * efficiency * collaboration_bonus
        completion_time = self.current_time + adjusted_duration

        # Record expected end time
        self.step_end_times[step_id] = completion_time

        # Add to events
        self.events.append((step_id, completion_time))

        # Sort events by completion time
        self.events.sort(key=lambda x: x[1])

        # Return state, reward, done
        done = all(self.step_status[step["id"]] == 2 for step in self.work_steps)
        next_state = self._get_state()

        # Reward is negative time delta to incentivize faster completion
        reward = -1  # Penalty for each action

        return next_state, reward, done

    def _step_batch(self, batch_allocation):
        """
        批量启动多个工序
        
        Args:
            batch_allocation: [(step_id1, workers1), (step_id2, workers2), ...]
            
        Returns:
            (next_state, reward, done): 下一状态，奖励，是否完成
        """
        if not batch_allocation:
            # 空批量，返回惩罚
            return self._get_state(), -100, False
        
        # 最终验证批量分配方案
        is_valid, reason = self.validate_batch_allocation(batch_allocation)
        if not is_valid:
            print(f"⚠️  批量启动验证失败: {reason}")
            return self._get_state(), -1000, False
        
        # 启动所有工序
        total_reward = 0
        num_started = 0
        
        for step_id, workers in batch_allocation:
            step = self._get_step_by_id(step_id)
            if step is None:
                print(f"⚠️  工序ID {step_id} 不存在")
                continue
            
            team_name = step["team"]
            
            # 记录开始时间
            self.step_start_times[step_id] = self.current_time
            
            # 分配工人
            if step["dedicated"]:
                # 专用团队（理论上不应该在批量启动中）
                self.teams[team_name]["available"] = 0
            else:
                # 共用团队 - 更新团队分配记录
                if team_name not in self.team_allocations:
                    self.team_allocations[team_name] = {}
                self.team_allocations[team_name][step_id] = workers
            
            self.step_allocations[step_id] = workers
            self.step_max_allocations[step_id] = workers
            self.step_status[step_id] = 1  # 进行中
            
            # 计算完成时间
            base_duration = step["duration"]
            team_size = step["team_size"]
            
            efficiency = 0.6 + 0.4 * (workers / team_size)
            collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5
            adjusted_duration = base_duration * (team_size / workers) * efficiency * collaboration_bonus
            completion_time = self.current_time + adjusted_duration
            
            # 记录预期结束时间
            self.step_end_times[step_id] = completion_time
            
            # 添加到事件列表
            self.events.append((step_id, completion_time))
            
            num_started += 1
        
        # 排序事件列表
        self.events.sort(key=lambda x: x[1])
        
        # 检查是否完成
        done = all(self.step_status[step["id"]] == 2 for step in self.work_steps)
        next_state = self._get_state()
        
        # 批量启动的奖励：鼓励批量启动（负值较小）
        # 批量启动多个工序只算一次动作惩罚，而不是每个工序都惩罚
        reward = -1  # 单次动作惩罚
        
        # 额外奖励：成功批量启动多个工序
        if num_started > 1:
            reward += (num_started - 1) * 0.5  # 每多启动一个工序，获得0.5的奖励
        
        # print(f"✅ 批量启动成功: {num_started}个工序同时启动")
        # for step_id, workers in batch_allocation:
        #     step = self._get_step_by_id(step_id)
        #     print(f"   - {step['display_name']}: {workers}人")
        
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
