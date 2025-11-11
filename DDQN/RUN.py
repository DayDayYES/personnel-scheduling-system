import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import namedtuple, deque
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免Qt错误
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import time
from io import BytesIO
# import seaborn as sns
from datetime import datetime, timedelta
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

t1 = time.time()
plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示问题
plt.rcParams['axes.unicode_minus'] = False


# Define the factory environment for the scheduling problem
class FactoryEnvironment:
    def __init__(self, workpoints_data):
        """
        初始化多工作点工厂环境
        
        Args:
            workpoints_data: 字典格式，包含多个工作点的工序信息
            格式示例:
            {
                "workpoint_1": {
                    "name": "工作点1",
                    "steps": [
                        {"name": "搭架子", "order": 1, "team": "team1", "dedicated": True, "team_size": 5, "duration": 10},
                        {"name": "拆保温", "order": 2, "team": "team2", "dedicated": False, "team_size": 10, "duration": 5},
                        # ... 更多工序
                    ]
                },
                "workpoint_2": {
                    "name": "工作点2", 
                    "steps": [
                        # 可能包含不同的工序组合
                    ]
                }
            }
        """
        
        # 存储工作点信息
        self.workpoints = workpoints_data
        self.workpoint_ids = list(workpoints_data.keys())
        
        # 标准工序模板（用于生成默认工序）
        self.standard_step_templates = [
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
            {"name": "检验结果评定", "order": 5, "team": "team3", "dedicated": True, "team_size": 10},
            {"name": "返修", "order": 6, "team": "team6", "dedicated": True, "team_size": 5},
            {"name": "合格报告出具", "order": 7, "team": "team3", "dedicated": True, "team_size": 10},
        ]
        
        # 生成所有工作点的工序实例
        self.work_steps = self._generate_workpoint_steps()
        
        print(f"初始化完成: {len(self.workpoint_ids)}个工作点, 共{len(self.work_steps)}个工序实例")

        # Define teams (保持不变，所有工作点共享人员团队)
        self.teams = {
            "team1": {"size": 5, "dedicated": True, "available": 5},  # 专人队伍1: 5人
            "team2": {"size": 10, "dedicated": False, "available": 10},  # 人员共用队伍2: 10人
            "team3": {"size": 10, "dedicated": False, "available": 10},  # 人员共用队伍3: 10人
            "team4": {"size": 5, "dedicated": True, "available": 5},  # 专人队伍4: 5人
            "team5": {"size": 15, "dedicated": False, "available": 15},  # 人员共用队伍5: 15人
            "team6": {"size": 5, "dedicated": True, "available": 5}  # 专人队伍6: 5人
        }

        # 记录每个队伍目前在各工序上分配的人数
        self.team_allocations = {team: {} for team in self.teams}

        # Step status: 0 = not started, 1 = in progress, 2 = completed
        # 使用工序ID作为键，而不是工序名称
        self.step_status = {step["id"]: 0 for step in self.work_steps}
        self.step_allocations = {step["id"]: 0 for step in self.work_steps}
        self.step_max_allocations = {step["id"]: 0 for step in self.work_steps}  # 记录最大分配的工人数
        self.step_start_times = {step["id"]: 0 for step in self.work_steps}
        self.step_end_times = {step["id"]: 0 for step in self.work_steps}

        self.current_time = 0
        self.events = []  # (step_id, completion_time)

    def _generate_workpoint_steps(self):
        """
        根据工作点数据生成所有工序实例
        每个工序实例都有唯一的ID，格式为: workpoint_id + "_" + step_name
        """
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
                
                # # 更新显示名称以包含工作点信息
                # step_instance["display_name"] = f"{workpoint_name}-{step_template['name']}"
                # 更新显示名称以包含工作点信息（简化显示）
                # 提取工作点编号（如从"工作点1"提取"1"）
                wp_number = workpoint_name.replace("工作点", "").strip()
                if not wp_number:  # 如果没有数字，使用工作点ID的最后部分
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
        # Reset the environment to initial state
        for team in self.teams:
            self.teams[team]["available"] = self.teams[team]["size"]
            self.team_allocations[team] = {}

        # 使用工序ID重置状态
        self.step_status = {step["id"]: 0 for step in self.work_steps}
        self.step_allocations = {step["id"]: 0 for step in self.work_steps}
        self.step_max_allocations = {step["id"]: 0 for step in self.work_steps}
        self.step_start_times = {step["id"]: 0 for step in self.work_steps}
        self.step_end_times = {step["id"]: 0 for step in self.work_steps}

        self.current_time = 0
        self.events = []

        return self._get_state()

    def _get_state(self):
        """
        将多工作点环境状态转换为神经网络输入向量
        状态向量维度: N工序×4 + 6团队×1 + M工作点×2 + 1时间
        其中N为总工序数，M为工作点数
        """
        state = []

        # 每个工序的状态信息 (4个值/工序)
        for step in self.work_steps:
            step_id = step["id"]
            state.append(self.step_status[step_id])         # 工序状态: 0未开始,1进行中,2已完成
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

    def get_team_used_workers(self, team_name):
        """获取团队当前已分配的总人数"""
        if team_name not in self.team_allocations:
            return 0

        return sum(self.team_allocations[team_name].values())
    
    def get_team_concurrent_workers(self, team_name, current_time):
        """
        获取指定团队在指定时间点的并发工作人数
        检查时间重叠的工序，确保不超过团队总人数
        """
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
        """
        检查团队容量约束：确保在整个工序执行期间，团队总分配人数不超过团队规模
        
        Args:
            team_name: 团队名称
            new_workers: 新工序需要的人数
            start_time: 新工序开始时间
            end_time: 新工序结束时间
            
        Returns:
            bool: True表示满足约束，False表示违反约束
        """
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
        """
        获取当前可以开始的工序
        多工作点版本：需要检查同一工作点内的工序依赖关系
        """
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
        """
        获取当前状态下的所有有效动作
        多工作点版本：动作格式为 (step_id, workers)
        增加了人员时间冲突检查
        """
        valid_actions = []
        available_steps = self.get_available_steps()

        # 按团队分组可用工序，用于优化并行处理
        team_steps = {}
        for step_id in available_steps:
            step = self._get_step_by_id(step_id)
            team_name = step["team"]
            if team_name not in team_steps:
                team_steps[team_name] = []
            team_steps[team_name].append(step_id)

        for step_id in available_steps:
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
                used_workers = self.get_team_used_workers(team_name)
                available_workers = team["size"] - used_workers
                same_team_steps = team_steps.get(team_name, [])

                # 生成可能的工人分配方案
                possible_allocations = []
                
                if len(same_team_steps) == 1 and available_workers > 0:
                    possible_allocations = [available_workers]
                elif len(same_team_steps) > 1 and available_workers > 0:
                    possible_allocations = [
                        available_workers,
                        max(1, int(available_workers * 0.75)),
                        max(1, int(available_workers * 0.5)),
                        max(1, int(available_workers * 0.25)),
                        1
                    ]
                    # 移除重复值并排序
                    possible_allocations = sorted(list(set(possible_allocations)), reverse=True)

                # 检查每个分配方案是否满足时间约束
                for workers in possible_allocations:
                    # 计算预期完成时间
                    efficiency = 0.6 + 0.4 * (workers / team_size)
                    collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5
                    adjusted_duration = base_duration * (team_size / workers) * efficiency * collaboration_bonus
                    predicted_end_time = predicted_start_time + adjusted_duration
                    
                    # 检查团队容量约束
                    if self.check_team_capacity_constraint(team_name, workers, 
                                                         predicted_start_time, predicted_end_time):
                        valid_actions.append((step_id, workers))
                    else:
                        # 如果当前分配方案不满足约束，后续更大的分配方案也不会满足
                        break

        # 如果有正在进行的工序，添加推进时间的动作
        if self.events:
            valid_actions.append(("advance_time", 0))

        return valid_actions

    def step(self, action):
        """
        在多工作点环境中执行动作
        action格式: (step_id, workers) 或 ("advance_time", 0)
        """
        step_id, workers = action

        if step_id == "advance_time":
            # Advance time to the next event
            return self._advance_time()

        # 根据工序ID找到工序
        step = self._get_step_by_id(step_id)
        if step is None:
            raise ValueError(f"工序ID {step_id} 不存在")
            
        team_name = step["team"]

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

        # More workers = faster completion (with enhanced team efficiency)
        # 新的效率计算方式，更强调团队协作效应
        efficiency = 0.6 + 0.4 * (workers / team_size)  # 扩大效率因子范围: 0.6-1.0
        # 使用非线性函数使多人协作效果更明显
        collaboration_bonus = 1.0 - 0.2 * (workers / team_size) ** 0.5  # 协作加速因子
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

    def _advance_time(self):
        """
        推进时间到下一个事件并处理完成情况
        多工作点版本：使用工序ID而不是工序名称
        """
        if not self.events:
            # 没有事件要处理
            return self._get_state(), 0, False

        # 获取下一个事件
        step_id, completion_time = self.events.pop(0)

        # 推进时间（不再取整）
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
            return self.current_time  # 不再取整，直接返回小数时间
        else:
            return float('inf')

    def get_schedule(self):
        """
        返回多工作点调度信息用于可视化
        增加工作点信息以便更好地显示结果
        """
        schedule = []
        for step in self.work_steps:
            step_id = step["id"]
            if self.step_status[step_id] == 2:  # Only include completed steps
                schedule.append({
                    "id": step_id,
                    "name": step["display_name"],  # 使用包含工作点信息的显示名称
                    "original_name": step["original_name"],
                    "workpoint_id": step["workpoint_id"],
                    "workpoint_name": step["workpoint_name"],
                    "team": step["team"],
                    "start": self.step_start_times[step_id],
                    "end": self.step_end_times[step_id],
                    "workers": self.step_max_allocations[step_id],  # 使用记录的工人数
                    "order": step["order"]
                })
        return schedule

    def get_workpoint_summary(self):
        """
        获取各工作点的完成情况摘要
        """
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

    def get_visualization_data(self):
        """
        生成用于多工作点可视化的完整数据结构
        包含时间线、资源利用率、冲突检测等信息
        """
        # 基础调度数据
        schedule = self.get_schedule()
        workpoint_summary = self.get_workpoint_summary()
        
        # 生成时间线数据
        timeline_data = self._generate_timeline_data(schedule)
        
        # 生成资源利用率数据
        resource_data = self._generate_resource_utilization_data()
        
        # 检测资源冲突
        conflicts = self._detect_resource_conflicts()
        
        # 生成关键路径分析
        critical_path = self._analyze_critical_path()
        
        # 生成团队负载分析
        team_workload = self._analyze_team_workload()
        
        return {
            "timeline": timeline_data,
            "resources": resource_data,
            "conflicts": conflicts,
            "critical_path": critical_path,
            "team_workload": team_workload,
            "workpoint_summary": workpoint_summary,
            "total_makespan": self.get_makespan(),
            "current_time": self.current_time
        }
    
    def _generate_timeline_data(self, schedule):
        """生成时间线数据，按工作点分组"""
        timeline_data = {"workpoints": []}
        
        # 按工作点分组
        workpoint_tasks = {}
        for task in schedule:
            wp_id = task["workpoint_id"]
            if wp_id not in workpoint_tasks:
                workpoint_tasks[wp_id] = {
                    "id": wp_id,
                    "name": task["workpoint_name"],
                    "tasks": []
                }
            
            workpoint_tasks[wp_id]["tasks"].append({
                "id": task["id"],
                "name": task["original_name"],
                "display_name": task["name"],
                "start": task["start"],
                "end": task["end"],
                "duration": task["end"] - task["start"],
                "team": task["team"],
                "workers": task["workers"],
                "order": task["order"],
                "status": "completed"
            })
        
        # 按工作点ID排序并添加到结果中
        for wp_id in sorted(workpoint_tasks.keys()):
            wp_data = workpoint_tasks[wp_id]
            # 按开始时间排序任务
            wp_data["tasks"].sort(key=lambda x: x["start"])
            timeline_data["workpoints"].append(wp_data)
        
        return timeline_data
    
    def _generate_resource_utilization_data(self):
        """生成资源利用率数据"""
        resource_data = {"teams": []}
        
        # 计算时间范围
        if not self.events and self.current_time == 0:
            time_range = (0, 100)  # 默认范围
        else:
            max_time = max(self.current_time, 
                          max([end_time for end_time in self.step_end_times.values()] + [0]))
            time_range = (0, max(max_time, 1))  # 确保至少有1个时间单位
        
        # 为每个团队生成利用率时间序列
        for team_name, team_info in self.teams.items():
            team_capacity = team_info["size"]
            utilization_timeline = []
            
            # 生成时间点（每个时间单位采样一次）
            time_points = np.arange(time_range[0], time_range[1] + 1, 1)
            
            for time_point in time_points:
                used_workers = self.get_team_concurrent_workers(team_name, time_point)
                
                # 确保数值有效性
                if used_workers < 0:
                    used_workers = 0
                elif used_workers > team_capacity:
                    used_workers = team_capacity
                
                utilization_rate = used_workers / team_capacity if team_capacity > 0 else 0
                
                # 找出此时间点该团队在哪些工作点工作
                active_workpoints = []
                if team_name in self.team_allocations:
                    for step_id, workers in self.team_allocations[team_name].items():
                        if (step_id in self.step_start_times and step_id in self.step_end_times and
                            self.step_start_times[step_id] <= time_point <= self.step_end_times[step_id]):
                            step = self._get_step_by_id(step_id)
                            if step:
                                active_workpoints.append({
                                    "workpoint": step["workpoint_name"],
                                    "task": step["original_name"],
                                    "workers": workers
                                })
                
                utilization_timeline.append({
                    "time": float(time_point),
                    "used": used_workers,
                    "capacity": team_capacity,
                    "utilization_rate": utilization_rate,
                    "active_workpoints": active_workpoints
                })
            
            # 计算平均利用率，处理空数据
            if utilization_timeline:
                avg_util = np.mean([u["utilization_rate"] for u in utilization_timeline])
                # 确保平均利用率是有效数值
                if np.isnan(avg_util) or np.isinf(avg_util):
                    avg_util = 0.0
            else:
                avg_util = 0.0
            
            resource_data["teams"].append({
                "name": team_name,
                "capacity": team_capacity,
                "dedicated": team_info["dedicated"],
                "utilization_timeline": utilization_timeline,
                "average_utilization": avg_util
            })
        
        return resource_data
    
    def _detect_resource_conflicts(self):
        """检测资源分配冲突"""
        conflicts = []
        
        # 检查每个团队在每个时间点的资源分配
        for team_name, team_info in self.teams.items():
            team_capacity = team_info["size"]
            
            # 收集所有相关时间点
            time_points = set()
            if team_name in self.team_allocations:
                for step_id in self.team_allocations[team_name]:
                    if step_id in self.step_start_times and step_id in self.step_end_times:
                        start_time = self.step_start_times[step_id]
                        end_time = self.step_end_times[step_id]
                        # 添加关键时间点
                        time_points.update([start_time, end_time])
                        # 添加中间时间点用于检测
                        for t in np.arange(start_time, end_time + 0.1, 0.5):
                            time_points.add(t)
            
            # 检查每个时间点
            for time_point in sorted(time_points):
                concurrent_workers = self.get_team_concurrent_workers(team_name, time_point)
                
                if concurrent_workers > team_capacity:
                    # 找出冲突的工序
                    conflicting_tasks = []
                    if team_name in self.team_allocations:
                        for step_id, workers in self.team_allocations[team_name].items():
                            if (step_id in self.step_start_times and step_id in self.step_end_times and
                                self.step_start_times[step_id] <= time_point <= self.step_end_times[step_id]):
                                step = self._get_step_by_id(step_id)
                                if step:
                                    conflicting_tasks.append({
                                        "step_id": step_id,
                                        "workpoint": step["workpoint_name"],
                                        "task": step["original_name"],
                                        "workers": workers
                                    })
                    
                    conflicts.append({
                        "time": float(time_point),
                        "team": team_name,
                        "required": concurrent_workers,
                        "available": team_capacity,
                        "overflow": concurrent_workers - team_capacity,
                        "conflicting_tasks": conflicting_tasks,
                        "severity": "high" if concurrent_workers > team_capacity * 1.5 else "medium"
                    })
        
        return conflicts
    
    def _analyze_critical_path(self):
        """分析关键路径"""
        # 简化版关键路径分析
        bottleneck_teams = []
        
        # 找出利用率最高的团队
        for team_name, team_info in self.teams.items():
            total_work_time = 0
            total_time = self.get_makespan()
            
            if team_name in self.team_allocations:
                for step_id, workers in self.team_allocations[team_name].items():
                    if step_id in self.step_start_times and step_id in self.step_end_times:
                        duration = self.step_end_times[step_id] - self.step_start_times[step_id]
                        total_work_time += duration * workers
            
            utilization = (total_work_time / (team_info["size"] * total_time)) if total_time > 0 else 0
            
            if utilization > 0.8:  # 高利用率团队
                bottleneck_teams.append({
                    "team": team_name,
                    "utilization": utilization,
                    "capacity": team_info["size"]
                })
        
        # 计算延期风险
        risk_level = "低"
        if any(team["utilization"] > 0.95 for team in bottleneck_teams):
            risk_level = "高"
        elif any(team["utilization"] > 0.85 for team in bottleneck_teams):
            risk_level = "中"
        
        return {
            "bottleneck_teams": bottleneck_teams,
            "delay_risk": risk_level,
            "estimated_completion": self.get_makespan()
        }
    
    def _analyze_team_workload(self):
        """分析团队工作负载分布"""
        team_workload = []
        
        for team_name, team_info in self.teams.items():
            workload_by_workpoint = {}
            total_workload = 0
            
            if team_name in self.team_allocations:
                for step_id, workers in self.team_allocations[team_name].items():
                    step = self._get_step_by_id(step_id)
                    if step and step_id in self.step_start_times and step_id in self.step_end_times:
                        duration = self.step_end_times[step_id] - self.step_start_times[step_id]
                        workload = duration * workers
                        total_workload += workload
                        
                        wp_name = step["workpoint_name"]
                        if wp_name not in workload_by_workpoint:
                            workload_by_workpoint[wp_name] = 0
                        workload_by_workpoint[wp_name] += workload
            
            team_workload.append({
                "team": team_name,
                "capacity": team_info["size"],
                "total_workload": total_workload,
                "workload_by_workpoint": workload_by_workpoint,
                "efficiency": total_workload / (team_info["size"] * self.get_makespan()) if self.get_makespan() > 0 else 0
            })
        
        return team_workload


# Define DDQN model
class DDQNNetwork(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DDQNNetwork, self).__init__()
        self.fc1 = nn.Linear(input_dim, 128)
        self.fc2 = nn.Linear(128, 256)
        self.fc3 = nn.Linear(256, 128)
        self.fc4 = nn.Linear(128, output_dim)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        return self.fc4(x)


# Define replay buffer
Experience = namedtuple('Experience', ('state', 'action_idx', 'next_state', 'reward', 'done'))


class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, *args):
        self.buffer.append(Experience(*args))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)


# DDQN Agent
class DDQNAgent:
    def __init__(self, state_size, action_size, device='cpu'):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = ReplayBuffer(10000)
        self.device = device

        self.gamma = 0.99  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 64
        self.update_freq = 5  # Update target network every 5 episodes

        self.policy_net = DDQNNetwork(state_size, action_size).to(device)
        self.target_net = DDQNNetwork(state_size, action_size).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # Set target network to evaluation mode

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()

    def remember(self, state, action_idx, next_state, reward, done):
        self.memory.push(state, action_idx, next_state, reward, done)

    def act(self, state, valid_actions):
        if np.random.rand() <= self.epsilon:
            return np.random.randint(0, len(valid_actions))

        # Get Q values for the state
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.policy_net(state_tensor).cpu().numpy()[0]

        # Filter Q values for valid actions
        valid_q_values = [(i, q_values[i % len(q_values)]) for i in range(len(valid_actions))]

        # Return the action with highest Q value
        return max(valid_q_values, key=lambda x: x[1])[0]

    def replay(self):
        if len(self.memory) < self.batch_size:
            return

        # Sample batch
        batch = self.memory.sample(self.batch_size)
        states = torch.FloatTensor([exp.state for exp in batch]).to(self.device)
        action_idxs = torch.LongTensor([exp.action_idx for exp in batch]).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor([exp.reward for exp in batch]).to(self.device)
        next_states = torch.FloatTensor([exp.next_state for exp in batch]).to(self.device)
        dones = torch.FloatTensor([exp.done for exp in batch]).to(self.device)

        # Get current Q values
        current_q = self.policy_net(states).gather(1, action_idxs).squeeze(1)

        # DDQN update: use policy net to select actions, target net to evaluate
        with torch.no_grad():
            next_actions = self.policy_net(next_states).max(1)[1].unsqueeze(1)
            max_next_q = self.target_net(next_states).gather(1, next_actions).squeeze(1)

            # Calculate target Q values
            target_q = rewards + (self.gamma * max_next_q * (1 - dones))

        # Update policy network
        loss = self.criterion(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        # Apply gradient clipping
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def update_target_network(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def save(self, filename):
        torch.save({
            'policy_model': self.policy_net.state_dict(),
            'target_model': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, filename)

    def load(self, filename):
        checkpoint = torch.load(filename)
        self.policy_net.load_state_dict(checkpoint['policy_model'])
        self.target_net.load_state_dict(checkpoint['target_model'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']


# 训练参数调整
def train(workpoints_data):
    """
    多工作点调度算法训练函数
    
    Args:
        workpoints_data: 工作点数据字典
    """
    # Import tqdm at the top of your function or file
    from tqdm import tqdm

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    # print(f"Using device: {device}")

    env = FactoryEnvironment(workpoints_data)
    state_size = len(env.reset())
    max_steps = 1000
    action_size = 100  # 可能需要根据实际工序数量调整

    print(f"状态空间维度: {state_size}")
    print(f"总工序数量: {len(env.work_steps)}")

    agent = DDQNAgent(state_size, action_size, device)

    # 调整学习参数
    agent.gamma = 0.99
    agent.epsilon = 1.0
    agent.epsilon_min = 0.01
    agent.epsilon_decay = 0.995
    agent.batch_size = 128

    episode_rewards = []
    episode_makespans = []
    best_makespan = float('inf')
    best_schedule = None
    episodes = 70

    import pickle

    # Wrap your episode loop with tqdm
    for episode in tqdm(range(episodes), desc="Training Progress", ncols=100):
        state = env.reset()
        total_reward = 0
        done = False
        step_counter = 0

        # Inner loop for steps within an episode
        while not done and step_counter < max_steps:
            valid_actions = env.get_valid_actions()

            if not valid_actions:
                break

            action_idx = agent.act(state, valid_actions)
            action = valid_actions[action_idx]

            next_state, reward, done = env.step(action)

            agent.remember(state, action_idx, next_state, reward, done)
            agent.replay()

            state = next_state
            total_reward += reward
            step_counter += 1

        makespan = env.get_makespan()

        # if makespan < best_makespan:
        #     best_makespan = makespan
        #     best_schedule = env.get_schedule()
        #
        #     with open('best_schedule.pkl', 'wb') as f:
        #         pickle.dump((best_schedule, best_makespan), f)
        #
        #     with open('best_schedule_info.txt', 'w') as f:
        #         f.write(f"Best makespan: {best_makespan}\n")
        #         f.write(f"Found in episode: {episode}\n")
        #         f.write(f"Detailed schedule:\n")
        #         for step in best_schedule:
        #             f.write(
        #                 f"  {step['name']}: start={step['start']:.2f}, end={step['end']:.2f}, workers={step['workers']}\n")
        #
        #     agent.save('best_model.pth')

        if episode % agent.update_freq == 0:
            agent.update_target_network()

        episode_rewards.append(total_reward)
        episode_makespans.append(makespan)

        # Update the progress bar description with current metrics
        # if episode % 10 == 0:
        #     tqdm.write(
        #         f"Episode {episode}: Steps = {step_counter}, Total Reward = {total_reward:.2f}, Makespan = {makespan:.2f}, Best Makespan = {best_makespan:.2f}")
        #
        # if episode > 100 and all(m >= best_makespan for m in episode_makespans[-50:]):
        #     tqdm.write("Early stopping due to no improvement")
        #     break

    return agent, env, best_schedule, episode_rewards, episode_makespans


# Function to run the best schedule for visualization
def run_best_schedule(env, agent_file='best_model.pth'):
    """运行训练好的代理以获取最佳调度方案。"""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    env.reset()

    # 加载训练好的代理
    state_size = len(env.reset())
    action_size = 100
    agent = DDQNAgent(state_size, action_size, device)
    #agent.load(agent_file)
    agent.epsilon = 0.0  # 不再探索，只利用已学到的知识

    state = env.reset()
    done = False
    step_counter = 0

    while not done and step_counter < 1000:
        valid_actions = env.get_valid_actions()

        if not valid_actions:
            break

        action_idx = agent.act(state, valid_actions)
        action = valid_actions[action_idx]

        next_state, _, done = env.step(action)
        state = next_state
        step_counter += 1

    # 获取调度方案（不再取整时间）
    schedule = env.get_schedule()
    makespan = env.get_makespan()
    return schedule, makespan


def create_traditional_gantt_chart(schedule, makespan):
    """创建传统工序视角甘特图"""
    print(f"📊 创建工序视角甘特图，完工时间: {makespan:.2f}")
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    team_colors = {
        "team1": "#FF6B6B", "team2": "#4ECDC4", "team3": "#45B7D1", 
        "team4": "#96CEB4", "team5": "#FFEAA7", "team6": "#DDA0DD"
    }
    
    team_names = {
        "team1": "团队1", "team2": "团队2", "team3": "团队3",
        "team4": "团队4", "team5": "团队5", "team6": "团队6"
    }
    
    # 按开始时间排序
    sorted_schedule = sorted(schedule, key=lambda x: x["start"])
    
    print(f"    工序甘特图: {len(sorted_schedule)} 个任务")
    
    # 绘制每个工序
    for i, step in enumerate(sorted_schedule):
        team = step["team"]
        duration = step["end"] - step["start"]
        
        # 绘制条形
        color = team_colors.get(team, '#CCCCCC')
        rect = Rectangle((step["start"], i - 0.4), duration, 0.8,
                        facecolor=color, alpha=0.8, edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        
        # 添加标签
        label_text = f"{step['name']} ({step['workers']}人)"
        if duration > makespan * 0.03:
            ax.text(step["start"] + duration/2, i, label_text,
                   ha='center', va='center', fontsize=10, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        else:
            ax.text(step["end"] + makespan * 0.01, i, label_text,
                   ha='left', va='center', fontsize=9)
    
    # 设置坐标轴
    ax.set_ylim(-0.5, len(sorted_schedule) - 0.5)
    ax.set_xlim(0, makespan * 1.05)
    ax.set_yticks(range(len(sorted_schedule)))
    ax.set_yticklabels([step["name"] for step in sorted_schedule], fontsize=11)
    ax.set_xlabel("时间", fontsize=14)
    ax.set_ylabel("工序", fontsize=14)
    ax.set_title(f'工序视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    # 添加图例
    legend_elements = []
    used_teams = set()
    for step in sorted_schedule:
        team = step["team"]
        if team not in used_teams:
            legend_elements.append(plt.Rectangle((0,0),1,1, 
                                               facecolor=team_colors.get(team, '#CCCCCC'), 
                                               alpha=0.8, label=team_names.get(team, team)))
            used_teams.add(team)
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1),
             fontsize=12, frameon=True)
    
    return fig


def create_workpoint_gantt_chart(schedule, makespan, env=None):
    """创建多工作点视角甘特图"""
    print(f"📊 创建多工作点视角甘特图，完工时间: {makespan:.2f}")
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # 直接从schedule推断工作点信息，不使用env数据（避免数据不一致）
    workpoints = _infer_workpoints_from_schedule(schedule)
    
    if not workpoints:
        ax.text(0.5, 0.5, "无多工作点数据", ha='center', va='center', 
                transform=ax.transAxes, fontsize=14)
        ax.set_title(f'多工作点视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                    fontsize=16, fontweight='bold', pad=20)
        return fig
    
    team_colors = {
        'team1': '#FF6B6B', 'team2': '#4ECDC4', 'team3': '#45B7D1', 
        'team4': '#96CEB4', 'team5': '#FFEAA7', 'team6': '#DDA0DD'
    }
    
    y_pos = 0
    y_labels = []
    y_positions = []
    
    print(f"    多工作点甘特图: {len(workpoints)} 个工作点")
    
    # 计算实际的最大时间，确保数据一致性
    actual_max_time = max(task["start"] + task["duration"] for wp in workpoints for task in wp["tasks"]) if workpoints else makespan
    print(f"    实际最大时间: {actual_max_time:.2f}, 传入完工时间: {makespan:.2f}")
    
    for wp in workpoints:
        wp_name = wp["name"]
        tasks = wp["tasks"]
        
        if not tasks:
            continue
            
        y_labels.append(wp_name)
        y_positions.append(y_pos)
        
        print(f"    工作点 {wp_name}: {len(tasks)} 个任务")
        
        # 绘制该工作点的所有任务
        for task in tasks:
            start = task["start"]
            duration = task["duration"]
            team = task["team"]
            workers = task["workers"]
            task_name = task["name"]
            
            print(f"      任务: {task_name}, 开始: {start:.1f}, 结束: {start+duration:.1f}, 团队: {team}")
            
            # 绘制任务条
            color = team_colors.get(team, '#CCCCCC')
            rect = Rectangle((start, y_pos - 0.4), duration, 0.8,
                           facecolor=color, alpha=0.8, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 修复标签位置逻辑 - 基于makespan而不是actual_max_time
            label_text = f"{task_name}\n{workers}人"
            
            if duration > makespan * 0.05:  # 任务足够长，在内部显示
                ax.text(start + duration/2, y_pos, label_text,
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
            elif start + duration < makespan * 0.85:  # 任务在左侧，右侧显示
                ax.text(start + duration + makespan * 0.02, y_pos, label_text,
                       ha='left', va='center', fontsize=8,
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
            else:  # 任务在右侧，左侧显示
                ax.text(start - makespan * 0.02, y_pos, label_text,
                       ha='right', va='center', fontsize=8,
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        
        y_pos += 1
    
    # 设置坐标轴 - 基于makespan设置合理的x轴范围
    ax.set_ylim(-0.5, len(workpoints) - 0.5)
    ax.set_xlim(0, makespan * 1.1)  # 减少右侧空白，只增加10%
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=12)
    ax.set_xlabel("时间", fontsize=14)
    ax.set_ylabel("工作点", fontsize=14)
    ax.set_title(f'多工作点视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    # 添加图例
    legend_elements = []
    for team, color in team_colors.items():
        legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.8, label=team))
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1),
             fontsize=12, frameon=True)
    
    return fig


def create_team_gantt_chart(schedule, makespan):
    """创建团队视角甘特图"""
    print(f"📊 创建团队视角甘特图，完工时间: {makespan:.2f}")
    
    fig, ax = plt.subplots(figsize=(16, 10))
    
    team_colors = {
        "team1": "#FF6B6B", "team2": "#4ECDC4", "team3": "#45B7D1", 
        "team4": "#96CEB4", "team5": "#FFEAA7", "team6": "#DDA0DD"
    }
    
    team_names = {
        "team1": "团队1", "team2": "团队2", "team3": "团队3",
        "team4": "团队4", "team5": "团队5", "team6": "团队6"
    }
    
    # 按团队分组任务
    team_tasks = {}
    for step in schedule:
        team = step["team"]
        if team not in team_tasks:
            team_tasks[team] = []
        team_tasks[team].append(step)
    
    # 为每个团队排序任务
    for team in team_tasks:
        team_tasks[team].sort(key=lambda x: x["start"])
    
    print(f"    团队甘特图: {len(team_tasks)} 个团队")
    
    y_pos = 0
    y_labels = []
    y_positions = []
    
    for team, tasks in team_tasks.items():
        team_name = team_names.get(team, team)
        y_labels.append(team_name)
        y_positions.append(y_pos)
        
        # 绘制该团队的所有任务
        for task in tasks:
            start = task["start"]
            duration = task["end"] - task["start"]
            workers = task["workers"]
            task_name = task["name"]
            
            # 绘制任务条
            color = team_colors.get(team, '#CCCCCC')
            rect = Rectangle((start, y_pos - 0.4), duration, 0.8,
                           facecolor=color, alpha=0.8, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 添加任务标签
            label_text = f"{task_name}\n{workers}人"
            if duration > makespan * 0.03:
                ax.text(start + duration/2, y_pos, label_text,
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
            else:
                ax.text(start + duration + makespan * 0.01, y_pos, label_text,
                       ha='left', va='center', fontsize=8)
        
        y_pos += 1
    
    # 设置坐标轴
    ax.set_ylim(-0.5, len(team_tasks) - 0.5)
    ax.set_xlim(0, makespan * 1.05)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=12)
    ax.set_xlabel("时间", fontsize=14)
    ax.set_ylabel("团队", fontsize=14)
    ax.set_title(f'团队视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    
    # 添加工作量统计
    team_workload = {}
    for team, tasks in team_tasks.items():
        total_duration = sum(task["end"] - task["start"] for task in tasks)
        team_workload[team] = total_duration
    
    # 在右侧添加工作量信息
    workload_text = "团队工作量:\n"
    for team, workload in team_workload.items():
        team_name = team_names.get(team, team)
        workload_text += f"{team_name}: {workload:.1f}h\n"
    
    ax.text(1.02, 0.5, workload_text, transform=ax.transAxes,
           fontsize=11, verticalalignment='center',
           bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
    
    return fig


def _infer_workpoints_from_schedule(schedule):
    """从调度结果推断工作点信息"""
    workpoints = []
    
    # 按工作点分组任务（基于任务名称格式：如"1-搭架子"、"2-拆保温"）
    workpoint_tasks = {}
    
    for task in schedule:
        task_name = task["name"]
        
        # 解析新的任务名称格式："1-搭架子" -> 工作点1
        if "-" in task_name:
            parts = task_name.split("-", 1)  # 只分割第一个"-"
            if len(parts) == 2 and parts[0].isdigit():
                wp_number = parts[0]
                wp_id = f"工作点{wp_number}"
                task_display_name = parts[1]
                
                if wp_id not in workpoint_tasks:
                    workpoint_tasks[wp_id] = []
                
                workpoint_tasks[wp_id].append({
                    "name": task_display_name,  # 去掉工作点前缀的任务名
                    "start": task["start"],
                    "duration": task["end"] - task["start"],
                    "team": task["team"],
                    "workers": task["workers"]
                })
                continue
        
        # 兼容旧格式：workpoint_1_搭架子
        if "_" in task_name and "workpoint" in task_name.lower():
            parts = task_name.split("_")
            if len(parts) >= 2:
                wp_id = f"{parts[0]}_{parts[1]}"  # workpoint_1
                task_display_name = "_".join(parts[2:]) if len(parts) > 2 else task_name
                
                if wp_id not in workpoint_tasks:
                    workpoint_tasks[wp_id] = []
                
                workpoint_tasks[wp_id].append({
                    "name": task_display_name,
                    "start": task["start"],
                    "duration": task["end"] - task["start"],
                    "team": task["team"],
                    "workers": task["workers"]
                })
                continue
        
        # 如果都不匹配，放入默认工作点
        if "default_workpoint" not in workpoint_tasks:
            workpoint_tasks["default_workpoint"] = []
        
        workpoint_tasks["default_workpoint"].append({
            "name": task_name,
            "start": task["start"],
            "duration": task["end"] - task["start"],
            "team": task["team"],
            "workers": task["workers"]
        })
    
    # 转换为工作点格式，并按工作点编号排序
    for wp_id in sorted(workpoint_tasks.keys(), key=lambda x: (x != "default_workpoint", x)):
        tasks = workpoint_tasks[wp_id]
        # 按开始时间排序任务
        tasks.sort(key=lambda x: x["start"])
        
        workpoints.append({
            "name": wp_id,
            "tasks": tasks
        })
    
    return workpoints

def _create_basic_viz_data(schedule, makespan):
    """为没有环境对象的情况创建基础可视化数据"""
    # 简化版数据结构
    workpoint_tasks = {}
    for task in schedule:
        wp_id = task.get("workpoint_id", "unknown")
        wp_name = task.get("workpoint_name", f"工作点{wp_id}")
        
        if wp_id not in workpoint_tasks:
            workpoint_tasks[wp_id] = {
                "id": wp_id,
                "name": wp_name,
                "tasks": []
            }
        
        workpoint_tasks[wp_id]["tasks"].append({
            "id": task.get("id", task["name"]),
            "name": task.get("original_name", task["name"]),
            "display_name": task["name"],
            "start": task["start"],
            "end": task["end"],
            "duration": task["end"] - task["start"],
            "team": task["team"],
            "workers": task["workers"],
            "status": "completed"
        })
    
    return {
        "timeline": {"workpoints": list(workpoint_tasks.values())},
        "total_makespan": makespan,
        "conflicts": [],
        "critical_path": {"bottleneck_teams": [], "delay_risk": "低"},
        "resources": {"teams": []},
        "workpoint_summary": {}
    }

def _plot_workpoint_overview(ax, viz_data):
    """绘制工作点总览"""
    ax.set_title("工作点完成情况", fontsize=14, fontweight='bold')
    
    workpoints = viz_data["timeline"]["workpoints"]
    if not workpoints:
        ax.text(0.5, 0.5, "无数据", ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return
    
    print(f"    工作点总览: {len(workpoints)} 个工作点")
    
    # 计算每个工作点的完成度
    wp_names = []
    progress_values = []
    task_counts = []
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#8E44AD']
    
    for i, wp in enumerate(workpoints):
        wp_name = wp["name"]
        tasks = wp.get("tasks", [])
        
        # 计算完成度（这里假设所有任务都已完成）
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("status", "completed") == "completed"])
        progress = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        wp_names.append(wp_name)
        progress_values.append(progress)
        task_counts.append(total_tasks)
        
        print(f"      {wp_name}: {completed_tasks}/{total_tasks} 任务完成 ({progress:.1%})")
    
    # 绘制水平条形图
    bars = ax.barh(wp_names, progress_values, color=colors[:len(wp_names)])
    
    # 添加百分比和任务数量标签
    for i, (bar, progress, count) in enumerate(zip(bars, progress_values, task_counts)):
        width = bar.get_width()
        # 在条形图内部显示百分比
        ax.text(width/2, bar.get_y() + bar.get_height()/2, 
                f'{progress:.1%}', ha='center', va='center', 
                fontsize=11, fontweight='bold', color='white')
        # 在右侧显示任务数量
        ax.text(width + 0.02, bar.get_y() + bar.get_height()/2, 
                f'({count}个任务)', ha='left', va='center', fontsize=10)
    
    ax.set_xlim(0, 1.2)
    ax.set_xlabel("完成进度", fontsize=12)
    ax.grid(axis='x', alpha=0.3)
    
    # 设置y轴标签字体大小
    ax.tick_params(axis='y', labelsize=11)
    ax.tick_params(axis='x', labelsize=10)

def _plot_resource_overview(ax, viz_data):
    """绘制资源利用率总览"""
    ax.set_title("团队资源利用率", fontsize=12, fontweight='bold')
    
    teams = viz_data["resources"].get("teams", [])
    if not teams:
        ax.text(0.5, 0.5, "无数据", ha='center', va='center', transform=ax.transAxes)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return
    
    # 提取团队数据，处理 NaN 和无效值
    team_names = []
    utilizations = []
    
    for team in teams:
        team_name = team["name"]
        util = team.get("average_utilization", 0)
        
        # 处理 NaN 和无效值
        if util is None or np.isnan(util) or np.isinf(util) or util < 0:
            util = 0.0
        elif util > 1.0:
            util = 1.0
            
        team_names.append(team_name)
        utilizations.append(util)
    
    # 如果所有利用率都是0，显示提示信息
    if all(u == 0 for u in utilizations):
        ax.text(0.5, 0.5, "暂无资源利用率数据", ha='center', va='center', 
                transform=ax.transAxes, fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return
    
    # 根据利用率设置颜色
    colors = []
    for util in utilizations:
        if util > 0.9:
            colors.append('#C73E1D')  # 红色 - 过载
        elif util > 0.7:
            colors.append('#F18F01')  # 橙色 - 高负载
        elif util > 0.5:
            colors.append('#6A994E')  # 绿色 - 正常
        else:
            colors.append('#2E86AB')  # 蓝色 - 低负载
    
    # 绘制饼图
    try:
        wedges, texts, autotexts = ax.pie(utilizations, labels=team_names, colors=colors,
                                         autopct='%1.1f%%', startangle=90)
        
        # 调整文字大小
        for text in texts:
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_fontsize(8)
            autotext.set_color('white')
            autotext.set_weight('bold')
            
    except Exception as e:
        print(f"绘制饼图时出错: {e}")
        # fallback: 绘制条形图
        ax.clear()
        ax.set_title("团队资源利用率", fontsize=12, fontweight='bold')
        bars = ax.barh(team_names, utilizations, color=colors)
        ax.set_xlim(0, 1)
        ax.set_xlabel("利用率")
        
        # 添加百分比标签
        for i, (bar, util) in enumerate(zip(bars, utilizations)):
            width = bar.get_width()
            ax.text(width + 0.01, bar.get_y() + bar.get_height()/2, 
                    f'{util:.1%}', ha='left', va='center', fontsize=10)

def _plot_critical_path_analysis(ax, viz_data):
    """绘制关键路径分析"""
    ax.set_title("关键路径分析", fontsize=14, fontweight='bold')
    
    critical_path = viz_data.get("critical_path", {})
    bottleneck_teams = critical_path.get("bottleneck_teams", [])
    delay_risk = critical_path.get("delay_risk", "低")
    completion_time = viz_data.get("total_makespan", 0)
    
    print(f"    关键路径: 瓶颈团队 {len(bottleneck_teams)} 个, 风险等级: {delay_risk}")
    
    # 显示关键信息
    info_lines = []
    
    if bottleneck_teams:
        info_lines.append("🔴 瓶颈团队:")
        for i, team in enumerate(bottleneck_teams[:3]):  # 只显示前3个
            info_lines.append(f"  • {team['team']}: {team['utilization']:.1%}")
        if len(bottleneck_teams) > 3:
            info_lines.append(f"  ... 还有 {len(bottleneck_teams)-3} 个")
    else:
        info_lines.append("✅ 瓶颈团队: 无")
    
    info_lines.append("")
    info_lines.append(f"⚠️  延期风险: {delay_risk}")
    info_lines.append(f"🎯 预计完工: {completion_time:.1f}")
    
    # 添加风险等级说明
    risk_desc = {
        "低": "资源充足，按时完成",
        "中": "资源紧张，需要关注", 
        "高": "资源不足，延期风险大"
    }
    info_lines.append(f"📋 {risk_desc.get(delay_risk, '未知风险')}")
    
    # 绘制文本信息
    info_text = '\n'.join(info_lines)
    ax.text(0.05, 0.95, info_text, transform=ax.transAxes, 
            fontsize=11, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.8))
    
    # 根据风险等级设置背景色
    risk_colors = {"低": '#E8F5E8', "中": '#FFF3CD', "高": '#F8D7DA'}
    ax.set_facecolor(risk_colors.get(delay_risk, '#FFFFFF'))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

def _plot_conflict_alerts(ax, viz_data):
    """绘制冲突告警"""
    ax.set_title("资源冲突告警", fontsize=14, fontweight='bold')
    
    conflicts = viz_data.get("conflicts", [])
    
    print(f"    冲突告警: {len(conflicts)} 个冲突")
    
    if not conflicts:
        ax.text(0.5, 0.5, "✅ 无冲突\n\n调度方案合理\n资源分配正常", 
                ha='center', va='center', transform=ax.transAxes, 
                fontsize=16, color='green', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgreen', alpha=0.3))
        ax.set_facecolor('#E8F5E8')
    else:
        # 显示冲突信息
        high_conflicts = len([c for c in conflicts if c.get("severity") == "high"])
        medium_conflicts = len([c for c in conflicts if c.get("severity") == "medium"])
        
        conflict_lines = [
            "⚠️ 发现冲突",
            "",
            f"🔴 高危: {high_conflicts}",
            f"🟡 中危: {medium_conflicts}",
            f"📊 总计: {len(conflicts)}",
            "",
            "需要调整资源分配"
        ]
        
        conflict_text = '\n'.join(conflict_lines)
        ax.text(0.5, 0.5, conflict_text, ha='center', va='center',
                transform=ax.transAxes, fontsize=14, color='red', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.5", facecolor='white', alpha=0.8))
        ax.set_facecolor('#F8D7DA')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

def _plot_multi_workpoint_gantt(ax, viz_data):
    """绘制多工作点甘特图"""
    ax.set_title("多工作点时间线甘特图", fontsize=16, fontweight='bold', pad=20)
    
    workpoints = viz_data["timeline"]["workpoints"]
    if not workpoints:
        ax.text(0.5, 0.5, "无调度数据", ha='center', va='center', transform=ax.transAxes, fontsize=14)
        return
    
    # 团队颜色映射
    team_colors = {
        'team1': '#FF6B6B', 'team2': '#4ECDC4', 'team3': '#45B7D1', 
        'team4': '#96CEB4', 'team5': '#FFEAA7', 'team6': '#DDA0DD'
    }
    
    y_pos = 0
    y_labels = []
    y_positions = []
    
    max_time = viz_data.get("total_makespan", 100)
    if max_time <= 0:
        max_time = 100
    
    print(f"    甘特图数据: {len(workpoints)} 个工作点, 最大时间: {max_time:.2f}")
    
    for wp_idx, wp in enumerate(workpoints):
        wp_name = wp["name"]
        tasks = wp["tasks"]
        
        print(f"    工作点 {wp_name}: {len(tasks)} 个任务")
        
        if not tasks:
            continue
            
        # 为每个工作点创建一行
        y_labels.append(wp_name)
        y_positions.append(y_pos)
        
        # 绘制该工作点的所有任务
        for task_idx, task in enumerate(tasks):
            start = task["start"]
            duration = task["duration"]
            team = task["team"]
            workers = task["workers"]
            task_name = task["name"]
            
            print(f"      任务: {task_name}, 开始: {start:.1f}, 持续: {duration:.1f}, 团队: {team}")
            
            # 绘制任务条
            color = team_colors.get(team, '#CCCCCC')
            rect = Rectangle((start, y_pos - 0.4), duration, 0.8, 
                           facecolor=color, alpha=0.8, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 添加任务标签 - 改进标签显示逻辑
            label_text = f"{task_name}\n{workers}人"
            
            # 根据任务长度决定是否显示标签
            min_duration_for_label = max_time * 0.03  # 降低阈值
            if duration > min_duration_for_label:
                ax.text(start + duration/2, y_pos, label_text, 
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
            else:
                # 对于短任务，在右侧显示标签
                ax.text(start + duration + max_time * 0.01, y_pos, label_text, 
                       ha='left', va='center', fontsize=8,
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        
        y_pos += 1
    
    # 设置坐标轴
    ax.set_ylim(-0.5, len(workpoints) - 0.5)
    ax.set_xlim(0, max_time * 1.1)
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=12)
    ax.set_xlabel("时间", fontsize=14)
    
    # 添加网格
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.grid(axis='y', alpha=0.2, linestyle=':')
    
    # 添加图例 - 改进图例位置和样式
    legend_elements = []
    for team, color in team_colors.items():
        legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color, alpha=0.8, label=team))
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1),
             fontsize=10, frameon=True, fancybox=True, shadow=True)
    
    # 添加时间刻度
    time_ticks = np.arange(0, max_time * 1.1, max(1, max_time / 10))
    ax.set_xticks(time_ticks)
    ax.set_xticklabels([f"{t:.0f}" for t in time_ticks], fontsize=11)

def _plot_resource_heatmap(ax, viz_data):
    """绘制资源分配热力图"""
    ax.set_title("团队资源利用率热力图", fontsize=12, fontweight='bold')
    
    teams_data = viz_data["resources"].get("teams", [])
    if not teams_data:
        ax.text(0.5, 0.5, "无资源数据", ha='center', va='center', transform=ax.transAxes)
        return
    
    # 准备热力图数据
    team_names = [team["name"] for team in teams_data]
    max_time = viz_data.get("total_makespan", 100)
    
    # 如果没有有效的完工时间，使用默认值
    if max_time is None or np.isnan(max_time) or max_time <= 0:
        max_time = 100
    
    # 创建时间网格
    time_bins = np.arange(0, max_time + 5, 5)  # 每5个时间单位一个bin
    utilization_matrix = []
    
    for team in teams_data:
        team_utilization = []
        timeline = team.get("utilization_timeline", [])
        
        for i in range(len(time_bins) - 1):
            bin_start = time_bins[i]
            bin_end = time_bins[i + 1]
            
            # 计算该时间段的平均利用率
            bin_utils = []
            for u in timeline:
                if bin_start <= u.get("time", 0) < bin_end:
                    util_rate = u.get("utilization_rate", 0)
                    # 处理无效值
                    if util_rate is not None and not np.isnan(util_rate) and not np.isinf(util_rate):
                        bin_utils.append(max(0, min(1, util_rate)))  # 限制在0-1范围内
            
            avg_util = np.mean(bin_utils) if bin_utils else 0
            team_utilization.append(avg_util)
        
        utilization_matrix.append(team_utilization)
    
    # 绘制热力图
    if utilization_matrix and len(utilization_matrix) > 0 and len(utilization_matrix[0]) > 0:
        try:
            utilization_matrix = np.array(utilization_matrix)
            
            # 检查矩阵是否包含有效数据
            if np.all(np.isnan(utilization_matrix)) or np.all(utilization_matrix == 0):
                ax.text(0.5, 0.5, "暂无利用率数据", ha='center', va='center', transform=ax.transAxes)
                return
            
            # 处理 NaN 值
            utilization_matrix = np.nan_to_num(utilization_matrix, nan=0.0, posinf=1.0, neginf=0.0)
            
            im = ax.imshow(utilization_matrix, cmap='RdYlGn_r', aspect='auto', 
                          vmin=0, vmax=1, interpolation='nearest')
            
            # 设置坐标轴
            ax.set_yticks(range(len(team_names)))
            ax.set_yticklabels(team_names)
            
            # 设置x轴标签，避免过于密集
            x_step = max(1, len(time_bins)//10)
            x_indices = range(0, len(time_bins)-1, x_step)
            ax.set_xticks(x_indices)
            ax.set_xticklabels([f"{time_bins[i]:.0f}" for i in x_indices])
            ax.set_xlabel("时间段")
            
            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax, shrink=0.8)
            cbar.set_label('利用率', rotation=270, labelpad=15)
            
            # 添加数值标签（只在数据点不太多时显示）
            if len(team_names) <= 6 and len(time_bins) <= 20:
                for i in range(len(team_names)):
                    for j in range(len(time_bins)-1):
                        if j % 2 == 0:  # 只在偶数列显示数值，避免过于拥挤
                            value = utilization_matrix[i, j]
                            if not np.isnan(value):
                                text = ax.text(j, i, f'{value:.2f}',
                                             ha="center", va="center", color="black", fontsize=8)
                                
        except Exception as e:
            print(f"绘制热力图时出错: {e}")
            ax.text(0.5, 0.5, f"热力图绘制失败: {str(e)}", ha='center', va='center', 
                   transform=ax.transAxes, fontsize=10)
    else:
        ax.text(0.5, 0.5, "无利用率数据", ha='center', va='center', transform=ax.transAxes)


# Visualize the final schedule
def visualize_schedule(schedule, makespan):
    """创建甘特图可视化调度方案，并打印详细信息。"""
    team_colors = {
        "team1": "tab:blue",
        "team2": "tab:orange",
        "team3": "tab:green",
        "team4": "tab:red",
        "team5": "tab:purple",
        "team6": "tab:brown"
    }

    team_names = {
        "team1": "团队1 ",
        "team2": "团队2 ",
        "team3": "团队3 ",
        "team4": "团队4 ",
        "team5": "团队5 ",
        "team6": "团队6 "
    }

    # 按开始时间排序（不再取整）
    schedule.sort(key=lambda x: x["start"])

    # 按团队统计工作量
    team_workload = {team: 0 for team in team_names}
    for step in schedule:
        team = step["team"]
        duration = step["end"] - step["start"]
        team_workload[team] += duration

    # 创建一个字符串变量来保存输出信息
    result_output = "\n===== 调度结果详细信息 =====\n"
    result_output += f"总完工时间: {makespan:.2f} 时间单位\n"
    result_output += "\n工序调度明细:\n"
    result_output += f"{'工序名称':<20} {'团队':<20} {'开始时间':<10} {'结束时间':<10} {'持续时间':<10} {'工人数':<10}\n"
    result_output += "-" * 85 + "\n"

    # 添加工序详细信息
    for step in schedule:
        duration = step["end"] - step["start"]
        team = step["team"]
        # 使用中文团队名称而不是英文代码
        result_output += f"{step['name']:<20} {team_names[team]:<20} {step['start']:<10.2f} {step['end']:<10.2f} {duration:<10.2f} {step['workers']:<10}\n"

    # 创建图表
    fig, ax = plt.subplots(figsize=(9, 6))

    # 绘制每个工序为一个条形
    for i, step in enumerate(schedule):
        team = step["team"]
        # 使用中文团队名称作为图例标签
        ax.barh(i, step["end"] - step["start"], left=step["start"],
                color=team_colors[team],
                edgecolor='black',
                label=team_names[team] if team not in [s["team"] for s in schedule[:i]] else "")

        # 在条形中添加工序名称和工人数
        duration = step["end"] - step["start"]
        bar_width = duration
        if bar_width > 5:  # 只有当条形宽度足够时才添加文本
            ax.text(step["start"] + duration / 2, i,
                    f"{step['name']} ({step['workers']}人)",
                    ha='center', va='center', color='black', fontweight='bold')
        else:
            # 如果条形太窄，将文本放在外面
            ax.text(step["end"] + 1, i,
                    f"{step['name']} ({step['workers']}人)",
                    ha='left', va='center', color='black')

    # 设置y轴刻度为工序名称
    ax.set_yticks(range(len(schedule)))
    ax.set_yticklabels([step["name"] for step in schedule])

    # x轴刻度不再强制为整数
    ax.set_title(f'工厂调度方案 (总完工时间: {makespan:.2f} 时间单位)', fontsize=14, fontweight='bold')
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('工序', fontsize=12)

    # 设置网格线
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    # 完善图例
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels,
              loc='upper center', bbox_to_anchor=(0.5, -0.1),
              ncol=3, fontsize=10)

    # 创建图片缓冲区
    buffer = BytesIO()
    #plt.figure(figsize=(10, 6))
    #plt.close()
    buffer.seek(0)
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    plt.show()
    return result_output, buffer


# 创建一个函数，直接使用最佳动作序列重现最佳调度方案
def replay_best_schedule(env, best_actions_file='best_schedule_info.txt'):
    """使用保存的最佳动作序列重现最佳调度方案。"""
    try:
        # 尝试从文件读取最佳动作序列
        with open(best_actions_file, 'r') as f:
            lines = f.readlines()
            best_makespan_line = lines[0].strip()
            best_makespan = float(best_makespan_line.split(': ')[1])
            actions_line = lines[2].strip()
            # 解析动作字符串为实际动作列表
            actions_str = actions_line[actions_line.find('['):].replace('(', '').replace(')', '').replace('[',
                                                                                                          '').replace(
                ']', '')
            action_pairs = []

            # 解析每个动作对
            parts = actions_str.split(',')
            i = 0
            while i < len(parts):
                if i + 1 < len(parts):
                    step_name = parts[i].strip().strip("'")
                    if i + 1 < len(parts):
                        try:
                            workers = int(parts[i + 1].strip())
                            action_pairs.append((step_name, workers))
                        except ValueError:
                            # 如果不是整数，可能是特殊情况，如'advance_time'
                            if 'advance_time' in step_name:
                                action_pairs.append(('advance_time', 0))
                                i -= 1  # 调整索引，因为我们没有使用下一部分
                    i += 2
                else:
                    i += 1

            print(f"从文件加载了 {len(action_pairs)} 个动作序列")

            # 使用这些动作重现最佳调度方案
            env.reset()
            for action in action_pairs:
                _, _, done = env.step(action)
                if done:
                    break

            return env.get_schedule(), env.get_makespan()
    except Exception as e:
        print(f"加载最佳调度方案失败: {e}")
        return None, float('inf')


# Main execution
def RUN(workpoints_data):
    """
    多工作点调度算法主函数
    
    Args:
        workpoints_data: 工作点数据，格式如下：
        {
            "workpoint_1": {
                "name": "工作点1",
                "steps": [
                    {"name": "搭架子", "order": 1, "team": "team1", "dedicated": True, "team_size": 5, "duration": 10},
                    {"name": "拆保温", "order": 2, "team": "team2", "dedicated": False, "team_size": 10, "duration": 5},
                    # ... 更多工序
                ]
            },
            # ... 更多工作点
        }
    """
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    # 增加训练轮数以找到更优解
    agent, env, best_schedule, rewards, makespans = train(workpoints_data)

    # 打印最佳结果（不再取整）
    best_makespan = min([m for m in makespans if m is not None])
    print(f"训练完成. 最佳完工时间: {best_makespan:.2f}")

    # 获取工作点摘要
    workpoint_summary = env.get_workpoint_summary()
    print("\n各工作点完成情况:")
    for wp_id, wp_info in workpoint_summary.items():
        print(f"{wp_info['name']}: {wp_info['completed_steps']}/{wp_info['total_steps']} 工序完成, "
              f"进度: {wp_info['progress']:.1%}, 完工时间: {wp_info['makespan']:.2f}")

    # 直接从保存的文件加载最佳调度方案
    import pickle

    try:
        pkl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'best_schedule.pkl')
        with open(pkl_path, 'rb') as f:
            final_schedule, final_makespan = pickle.load(f)
        print(f"成功加载最佳调度方案! 完工时间: {final_makespan:.2f}")
    except Exception as e:
        print(f"加载保存的最佳方案失败: {e}")
        print("将尝试使用最佳模型...")

        # 备选方案：运行最佳模型
        best_final_makespan = float('inf')
        best_final_schedule = None

        print("运行最佳模型以获取最优调度方案...")
        best_run_index = -1
        for i in range(10):  # 运行10次，取最好的结果
            schedule, makespan = run_best_schedule(env)
            print(f"运行 {i + 1}/10: 完工时间 = {makespan:.2f}")
            if makespan < best_final_makespan:
                best_final_makespan = makespan
                best_final_schedule = schedule
                best_run_index = i + 1
                print(f"  发现更优方案! 新的最佳完工时间: {best_final_makespan:.2f}")

        final_schedule = best_final_schedule
        final_makespan = best_final_makespan
        
        # 保存最优结果到文件，供下次使用
        try:
            with open('best_schedule.pkl', 'wb') as f:
                pickle.dump((final_schedule, final_makespan), f)
            print(f"✅ 最优调度方案已保存! 完工时间: {final_makespan:.2f}")
        except Exception as e:
            print(f"⚠️  保存最优方案失败: {e}")
        
        print(f"\n🏆 最终采用的最优方案:")
        print(f"  - 完工时间: {final_makespan:.2f} 时间单位")
        print(f"  - 任务数量: {len(final_schedule)}")
        print(f"  - 来源: 最佳模型第{best_run_index}次运行")
    # plot_training_progress(rewards, makespans)

    print('Running time: ', time.time() - t1)
    
    # 创建三张独立的甘特图（统一数据源和完工时间）
    print("生成三张独立的甘特图...")
    print(f"使用最优方案数据: 完工时间={final_makespan:.2f}, 任务数={len(final_schedule)}")
    
    # 确保保存在当前目录（DDQN-v2文件夹）
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    saved_files = []
    
    try:
        # 1. 工序视角甘特图
        print("1/3 生成工序视角甘特图...")
        process_fig = create_traditional_gantt_chart(final_schedule, final_makespan)
        process_path = os.path.join(current_dir, '1_process_gantt.png')
        process_fig.savefig(process_path, dpi=300, bbox_inches='tight')
        print(f"✅ 工序视角甘特图已保存为: {process_path}")
        saved_files.append('1_process_gantt.png')
        plt.close(process_fig)
        
    except Exception as e:
        print(f"❌ 工序视角甘特图生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # 2. 多工作点视角甘特图
        print("2/3 生成多工作点视角甘特图...")
        workpoint_fig = create_workpoint_gantt_chart(final_schedule, final_makespan, env)
        workpoint_path = os.path.join(current_dir, '2_workpoint_gantt.png')
        workpoint_fig.savefig(workpoint_path, dpi=300, bbox_inches='tight')
        print(f"✅ 多工作点视角甘特图已保存为: {workpoint_path}")
        saved_files.append('2_workpoint_gantt.png')
        plt.close(workpoint_fig)
        
    except Exception as e:
        print(f"❌ 多工作点视角甘特图生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # 3. 团队视角甘特图
        print("3/3 生成团队视角甘特图...")
        team_fig = create_team_gantt_chart(final_schedule, final_makespan)
        team_path = os.path.join(current_dir, '3_team_gantt.png')
        team_fig.savefig(team_path, dpi=300, bbox_inches='tight')
        print(f"✅ 团队视角甘特图已保存为: {team_path}")
        saved_files.append('3_team_gantt.png')
        plt.close(team_fig)
        
    except Exception as e:
        print(f"❌ 团队视角甘特图生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    if saved_files:
        print(f"\n📊 三张图表统计:")
        print(f"  - 统一完工时间: {final_makespan:.2f} 时间单位")
        print(f"  - 任务总数: {len(final_schedule)}")
        
        # 统计团队参与情况
        teams_used = set(task["team"] for task in final_schedule)
        print(f"  - 参与团队: {len(teams_used)} 个 ({', '.join(sorted(teams_used))})")
        print(f"  - 成功保存: {len(saved_files)}/3 张图片")
        print(f"  - 保存位置: {current_dir}")
    else:
        print("❌ 所有甘特图生成都失败了")
    
    # 生成传统甘特图作为对比（保持原有功能）
    print("生成传统甘特图...")
    record, img = visualize_schedule(final_schedule, final_makespan)
    print(record)
    
    # 保存传统甘特图到DDQN-v2目录
    traditional_path = os.path.join(current_dir, 'best_schedule.png')
    plt.savefig(traditional_path, dpi=300, bbox_inches='tight')
    print(f"✅ 传统甘特图已保存为: {traditional_path}")
    
    # 关闭当前图形以释放内存
    plt.close()
    
    print(f"\n🎉 所有图表生成完成！")
    print(f"📁 生成的文件 (保存在 {current_dir}):")
    print(f"  • 1_process_gantt.png - 工序视角甘特图")
    print(f"  • 2_workpoint_gantt.png - 多工作点视角甘特图")
    print(f"  • 3_team_gantt.png - 团队视角甘特图")
    print(f"  • best_schedule.png - 传统甘特图 (对比)")
    
    return record, img


def create_sample_workpoints_data():
    """
    创建示例工作点数据
    演示如何定义多个工作点的工序
    """
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

if __name__ == '__main__':
    # 使用示例工作点数据进行测试
    sample_data = create_sample_workpoints_data()
    print("开始多工作点调度算法测试...")
    print(f"工作点数量: {len(sample_data)}")
    for wp_id, wp_data in sample_data.items():
        wp_name = wp_data.get("name", wp_id)
        step_count = len(wp_data.get("steps", []))
        print(f"  {wp_name}: {step_count} 个工序" + ("（使用标准模板）" if step_count == 0 else ""))
    
    t1 = time.time()
    RUN(sample_data)