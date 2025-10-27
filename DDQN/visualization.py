# -*- coding: utf-8 -*-
"""
可视化模块 - 包含所有图表生成功能
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from io import BytesIO
import os
from config import TEAM_COLORS, TEAM_NAMES, VISUALIZATION_CONFIG, get_result_path, FILE_PATHS


def _set_time_axis(ax, makespan):
    """
    设置横坐标为天数格式（上午/下午），每10个时间单位为一个半天
    并添加时间分隔虚线
    
    Args:
        ax: matplotlib轴对象
        makespan: 完工时间
    """
    # 计算需要多少个时间段（每10个单位为一个半天）
    interval = 10  # 每个半天的时间单位
    max_time = int(np.ceil(makespan / interval)) * interval + interval
    
    # 生成时间刻度位置（每10个单位）
    time_ticks = np.arange(0, max_time + 1, interval)
    
    # 生成时间标签
    time_labels = []
    for i, tick in enumerate(time_ticks):
        day = i // 2 + 1  # 每两个时间段为一天
        period = "上午" if i % 2 == 0 else "下午"
        time_labels.append(f"第{day}天\n{period}")
    
    # 设置刻度和标签
    ax.set_xticks(time_ticks)
    ax.set_xticklabels(time_labels, fontsize=9, rotation=0)
    
    # 添加垂直虚线分隔
    for tick in time_ticks[1:]:  # 跳过第一条线（起点）
        ax.axvline(x=tick, color='gray', linestyle='--', alpha=0.4, linewidth=1)


def create_traditional_gantt_chart(schedule, makespan):
    """创建传统工序视角甘特图"""
    print(f"📊 创建工序视角甘特图，完工时间: {makespan:.2f}")
    
    fig, ax = plt.subplots(figsize=VISUALIZATION_CONFIG["figure_size"])
    
    # 按开始时间排序
    sorted_schedule = sorted(schedule, key=lambda x: x["start"])
    
    print(f"    工序甘特图: {len(sorted_schedule)} 个任务")
    
    # 绘制每个工序
    for i, step in enumerate(sorted_schedule):
        team = step["team"]
        duration = step["end"] - step["start"]
        
        # 绘制条形
        color = TEAM_COLORS.get(team, '#CCCCCC')
        rect = Rectangle((step["start"], i - 0.4), duration, 0.8,
                        facecolor=color, alpha=VISUALIZATION_CONFIG["alpha"], 
                        edgecolor='black', linewidth=1)
        ax.add_patch(rect)
        
        # 添加标签
        label_text = f"{step['name']} ({step['workers']}人)"
        if duration > makespan * VISUALIZATION_CONFIG["label_threshold"]:
            ax.text(step["start"] + duration/2, i, label_text,
                   ha='center', va='center', fontsize=VISUALIZATION_CONFIG["fontsize_text"], 
                   fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
        else:
            ax.text(step["end"] + makespan * 0.01, i, label_text,
                   ha='left', va='center', fontsize=9)
    
    # 设置坐标轴
    ax.set_ylim(-0.5, len(sorted_schedule) - 0.5)
    ax.set_xlim(0, makespan * VISUALIZATION_CONFIG["xlim_padding"])
    ax.set_yticks(range(len(sorted_schedule)))
    ax.set_yticklabels([step["name"] for step in sorted_schedule], 
                       fontsize=VISUALIZATION_CONFIG["fontsize_text"])
    ax.set_xlabel("时间", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_ylabel("工序", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_title(f'工序视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=VISUALIZATION_CONFIG["fontsize_title"], fontweight='bold', pad=20)
    
    # 自定义横坐标为天数格式（上午/下午）
    _set_time_axis(ax, makespan)
    ax.grid(axis='x', alpha=VISUALIZATION_CONFIG["grid_alpha"], linestyle='--')
    
    # 添加图例
    legend_elements = []
    used_teams = set()
    for step in sorted_schedule:
        team = step["team"]
        if team not in used_teams:
            legend_elements.append(plt.Rectangle((0,0),1,1, 
                                               facecolor=TEAM_COLORS.get(team, '#CCCCCC'), 
                                               alpha=VISUALIZATION_CONFIG["alpha"], 
                                               label=TEAM_NAMES.get(team, team)))
            used_teams.add(team)
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1),
             fontsize=VISUALIZATION_CONFIG["fontsize_legend"], frameon=True)
    
    return fig


def detect_parallel_tasks(tasks):
    """
    检测并行任务并分配层级
    
    Args:
        tasks: 任务列表，每个任务包含start和end时间
    
    Returns:
        list: 每个任务的层级信息 (layer_index, total_layers)
    """
    if not tasks:
        return []
    
    # 按开始时间排序任务
    sorted_tasks = sorted(enumerate(tasks), key=lambda x: x[1]["start"])
    
    # 分配层级
    layers = []  # 每一层的任务结束时间
    task_layers = [0] * len(tasks)  # 每个任务的层级
    
    for original_index, task in sorted_tasks:
        start_time = task["start"]
        end_time = task.get("end", task["start"] + task.get("duration", 0))
        
        # 找到第一个可用的层级（该层级的最后任务已结束）
        assigned_layer = 0
        for layer_idx, layer_end_time in enumerate(layers):
            if start_time >= layer_end_time:  # 可以放在这一层
                assigned_layer = layer_idx
                layers[layer_idx] = end_time
                break
        else:
            # 需要新的层级
            assigned_layer = len(layers)
            layers.append(end_time)
        
        task_layers[original_index] = assigned_layer
    
    # 返回每个任务的层级信息
    total_layers = len(layers)
    return [(layer, total_layers) for layer in task_layers]


def create_layered_workpoint_gantt_chart(schedule, makespan, env=None):
    """创建分层的多设备视角甘特图（解决并行任务重叠问题）"""
    print(f"📊 创建分层多设备视角甘特图，完工时间: {makespan:.2f}")
    
    fig, ax = plt.subplots(figsize=(VISUALIZATION_CONFIG["figure_size"][0], 
                                   VISUALIZATION_CONFIG["figure_size"][1] * 1.2))  # 增加高度
    
    # 直接从schedule推断设备信息
    workpoints = _infer_workpoints_from_schedule(schedule)
    
    if not workpoints:
        ax.text(0.5, 0.5, "无多设备数据", ha='center', va='center', 
                transform=ax.transAxes, fontsize=VISUALIZATION_CONFIG["fontsize_label"])
        ax.set_title(f'设备视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                    fontsize=VISUALIZATION_CONFIG["fontsize_title"], fontweight='bold', pad=20)
        return fig
    
    y_pos = 0
    y_labels = []
    y_positions = []
    
    # 固定的行高和任务条参数
    row_height = 1.0  # 每个工作点占用的固定行高
    max_task_height = 0.7  # 单个任务条的最大高度
    layer_gap = 0.05  # 层之间的间隙
    
    # print(f"    分层多工作点甘特图: {len(workpoints)} 个工作点")
    
    for wp in workpoints:
        wp_name = wp["name"]
        tasks = wp["tasks"]
        
        if not tasks:
            continue
        
        # 检测并行任务并分配层级
        task_layers = detect_parallel_tasks(tasks)
        max_layers = max(layer[1] for layer in task_layers) if task_layers else 1
        
        # 工作点标签位置（行的中心）
        y_labels.append(wp_name)
        y_positions.append(y_pos)
        
        # print(f"    工作点 {wp_name}: {len(tasks)} 个任务, {max_layers} 层")
        
        # 计算每层任务条的高度（确保所有层能够适应固定的行高）
        if max_layers == 1:
            task_height = max_task_height
        else:
            # 根据层数动态调整任务条高度，保证总高度不超过row_height
            available_height = row_height - (max_layers - 1) * layer_gap
            task_height = min(max_task_height, available_height / max_layers)
        
        # 绘制该工作点的所有任务（分层显示）
        for i, (task, (layer_index, total_layers)) in enumerate(zip(tasks, task_layers)):
            start = task["start"]
            duration = task["duration"]
            team = task["team"]
            workers = task["workers"]
            task_name = task["name"]
            
            # 计算当前任务的y位置（在固定行高内分层）
            if total_layers == 1:
                # 单层时，任务条居中
                task_y_pos = y_pos
            else:
                # 多层时，从行的顶部开始分层排列
                layer_offset = (layer_index * (task_height + layer_gap)) - (row_height / 2) + (task_height / 2)
                task_y_pos = y_pos + layer_offset
            
            # print(f"      任务: {task_name}, 层级: {layer_index+1}/{total_layers}, Y位置: {task_y_pos:.2f}, 高度: {task_height:.2f}")
            
            # 绘制任务条
            color = TEAM_COLORS.get(team, '#CCCCCC')
            rect = Rectangle((start, task_y_pos - task_height/2), duration, task_height,
                           facecolor=color, alpha=VISUALIZATION_CONFIG["alpha"], 
                           edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 添加任务标签（根据任务条高度调整字体大小）
            font_size = max(6, min(9, int(task_height * 12)))  # 根据任务条高度调整字体大小
            label_text = f"{task_name}\n{workers}人"
            
            ax.text(start + duration/2, task_y_pos, label_text,
                    ha='center', va='center', fontsize=font_size, fontweight='bold')
        
        # 绘制工作点分隔线（固定间距）
        if y_pos > 0:
            separation_y = y_pos - row_height / 2 - 0.1
            ax.axhline(y=separation_y, color='gray', linestyle='-', alpha=0.3, linewidth=1)
        
        y_pos += row_height + 0.2  # 固定的行间距
    
    # 设置坐标轴
    ax.set_ylim(-0.5, y_pos - 0.5)
    ax.set_xlim(0, makespan * VISUALIZATION_CONFIG["xlim_padding"])
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=VISUALIZATION_CONFIG["fontsize_legend"])
    ax.set_xlabel("时间", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_ylabel("设备", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_title(f'分层多设备视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=VISUALIZATION_CONFIG["fontsize_title"], fontweight='bold', pad=20)
    
    # 自定义横坐标为天数格式（上午/下午）
    _set_time_axis(ax, makespan)
    ax.grid(axis='x', alpha=VISUALIZATION_CONFIG["grid_alpha"], linestyle='--')
    
    # 添加图例
    legend_elements = []
    for team, color in TEAM_COLORS.items():
        legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color, 
                                           alpha=VISUALIZATION_CONFIG["alpha"], label=team))
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1),
             fontsize=VISUALIZATION_CONFIG["fontsize_legend"], frameon=True)
    
    return fig


def create_layered_team_gantt_chart(schedule, makespan):
    """创建分层的团队视角甘特图（解决并行任务重叠问题）"""
    print(f"📊 创建分层团队视角甘特图，完工时间: {makespan:.2f}")
    
    fig, ax = plt.subplots(figsize=(VISUALIZATION_CONFIG["figure_size"][0], 
                                   VISUALIZATION_CONFIG["figure_size"][1] * 1.2))  # 增加高度
    
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
    
    # print(f"    分层团队甘特图: {len(team_tasks)} 个团队")
    
    y_pos = 0
    y_labels = []
    y_positions = []
    
    # 固定的行高和任务条参数
    row_height = 1.0  # 每个团队占用的固定行高
    max_task_height = 0.7  # 单个任务条的最大高度
    layer_gap = 0.05  # 层之间的间隙
    
    for team, tasks in team_tasks.items():
        team_name = TEAM_NAMES.get(team, team)
        
        # 检测并行任务并分配层级
        task_layers = detect_parallel_tasks(tasks)
        max_layers = max(layer[1] for layer in task_layers) if task_layers else 1
        
        # 团队标签位置（行的中心）
        y_labels.append(team_name)
        y_positions.append(y_pos)
        
        # print(f"    团队 {team_name}: {len(tasks)} 个任务, {max_layers} 层")
        
        # 计算每层任务条的高度（确保所有层能够适应固定的行高）
        if max_layers == 1:
            task_height = max_task_height
        else:
            # 根据层数动态调整任务条高度，保证总高度不超过row_height
            available_height = row_height - (max_layers - 1) * layer_gap
            task_height = min(max_task_height, available_height / max_layers)
        
        # 绘制该团队的所有任务（分层显示）
        for i, (task, (layer_index, total_layers)) in enumerate(zip(tasks, task_layers)):
            start = task["start"]
            duration = task["end"] - task["start"]
            workers = task["workers"]
            task_name = task["name"]
            
            # 计算当前任务的y位置（在固定行高内分层）
            if total_layers == 1:
                # 单层时，任务条居中
                task_y_pos = y_pos
            else:
                # 多层时，从行的顶部开始分层排列
                layer_offset = (layer_index * (task_height + layer_gap)) - (row_height / 2) + (task_height / 2)
                task_y_pos = y_pos + layer_offset
            
            # print(f"      任务: {task_name}, 层级: {layer_index+1}/{total_layers}, Y位置: {task_y_pos:.2f}, 高度: {task_height:.2f}")
            
            # 绘制任务条
            color = TEAM_COLORS.get(team, '#CCCCCC')
            rect = Rectangle((start, task_y_pos - task_height/2), duration, task_height,
                           facecolor=color, alpha=VISUALIZATION_CONFIG["alpha"], 
                           edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 添加任务标签（根据任务条高度调整字体大小）
            font_size = max(6, min(9, int(task_height * 12)))  # 根据任务条高度调整字体大小
            label_text = f"{task_name}\n{workers}人"
            
            # if duration > makespan * VISUALIZATION_CONFIG["label_threshold"]:
            #     ax.text(start + duration/2, task_y_pos, label_text,
            #            ha='center', va='center', fontsize=font_size, fontweight='bold',
            #            bbox=dict(boxstyle="round,pad=0.1", facecolor='white', alpha=0.9))
            # else:
            #     ax.text(start + duration + makespan * 0.01, task_y_pos, label_text,
            #            ha='left', va='center', fontsize=font_size,
            #            bbox=dict(boxstyle="round,pad=0.1", facecolor='white', alpha=0.9))

            ax.text(start + duration/2, task_y_pos, label_text,
                       ha='center', va='center', fontsize=font_size, fontweight='bold')
        
        # 绘制团队分隔线（固定间距）
        if y_pos > 0:
            separation_y = y_pos - row_height / 2 - 0.1
            ax.axhline(y=separation_y, color='gray', linestyle='-', alpha=0.3, linewidth=1)
        
        y_pos += row_height + 0.2  # 固定的行间距
    
    # 设置坐标轴
    ax.set_ylim(-0.5, y_pos - 0.5)
    ax.set_xlim(0, makespan * VISUALIZATION_CONFIG["xlim_padding"])
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=VISUALIZATION_CONFIG["fontsize_legend"])
    ax.set_xlabel("时间", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_ylabel("团队", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_title(f'团队视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=VISUALIZATION_CONFIG["fontsize_title"], fontweight='bold', pad=20)
    
    # 自定义横坐标为天数格式（上午/下午）
    _set_time_axis(ax, makespan)
    ax.grid(axis='x', alpha=VISUALIZATION_CONFIG["grid_alpha"], linestyle='--')
    
    # 添加工作量统计（调整位置以适应固定行高显示）
    team_workload = {}
    for team, tasks in team_tasks.items():
        total_duration = sum(task["end"] - task["start"] for task in tasks)
        team_workload[team] = total_duration
    
    # 在右侧添加工作量信息
    workload_text = "团队工作量:\n"
    for team, workload in team_workload.items():
        team_name = TEAM_NAMES.get(team, team)
        workload_text += f"{team_name}: {workload:.1f}\n"
    
    ax.text(1.02, 0.5, workload_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='center', bbox=dict(boxstyle="round,pad=0.3", 
                                               facecolor='lightgray', alpha=0.8))
    
    return fig


def create_workpoint_gantt_chart(schedule, makespan, env=None):
    """创建多工作点视角甘特图"""
    print(f"📊 创建多工作点视角甘特图，完工时间: {makespan:.2f}")
    
    fig, ax = plt.subplots(figsize=VISUALIZATION_CONFIG["figure_size"])
    
    # 直接从schedule推断工作点信息，不使用env数据（避免数据不一致）
    workpoints = _infer_workpoints_from_schedule(schedule)
    
    if not workpoints:
        ax.text(0.5, 0.5, "无多工作点数据", ha='center', va='center', 
                transform=ax.transAxes, fontsize=VISUALIZATION_CONFIG["fontsize_label"])
        ax.set_title(f'多工作点视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                    fontsize=VISUALIZATION_CONFIG["fontsize_title"], fontweight='bold', pad=20)
        return fig
    
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
            color = TEAM_COLORS.get(team, '#CCCCCC')
            rect = Rectangle((start, y_pos - 0.4), duration, 0.8,
                           facecolor=color, alpha=VISUALIZATION_CONFIG["alpha"], 
                           edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 修复标签位置逻辑 - 基于makespan而不是actual_max_time
            label_text = f"{task_name}\n{workers}人"
            
            if duration > makespan * VISUALIZATION_CONFIG["label_threshold"]:  # 任务足够长，在内部显示
                ax.text(start + duration/2, y_pos, label_text,
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
            elif start + duration < makespan * VISUALIZATION_CONFIG["label_position_threshold"]:  # 任务在左侧，右侧显示
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
    ax.set_xlim(0, makespan * VISUALIZATION_CONFIG["xlim_padding"])
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=VISUALIZATION_CONFIG["fontsize_legend"])
    ax.set_xlabel("时间", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_ylabel("工作点", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_title(f'多工作点视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=VISUALIZATION_CONFIG["fontsize_title"], fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=VISUALIZATION_CONFIG["grid_alpha"], linestyle='--')
    
    # 添加图例
    legend_elements = []
    for team, color in TEAM_COLORS.items():
        legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color, 
                                           alpha=VISUALIZATION_CONFIG["alpha"], label=team))
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1),
             fontsize=VISUALIZATION_CONFIG["fontsize_legend"], frameon=True)
    
    return fig


def create_team_gantt_chart(schedule, makespan):
    """创建团队视角甘特图"""
    print(f"📊 创建团队视角甘特图，完工时间: {makespan:.2f}")
    
    fig, ax = plt.subplots(figsize=VISUALIZATION_CONFIG["figure_size"])
    
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
        team_name = TEAM_NAMES.get(team, team)
        y_labels.append(team_name)
        y_positions.append(y_pos)
        
        # 绘制该团队的所有任务
        for task in tasks:
            start = task["start"]
            duration = task["end"] - task["start"]
            workers = task["workers"]
            task_name = task["name"]
            
            # 绘制任务条
            color = TEAM_COLORS.get(team, '#CCCCCC')
            rect = Rectangle((start, y_pos - 0.4), duration, 0.8,
                           facecolor=color, alpha=VISUALIZATION_CONFIG["alpha"], 
                           edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 添加任务标签
            label_text = f"{task_name}\n{workers}人"
            if duration > makespan * VISUALIZATION_CONFIG["label_threshold"]:
                ax.text(start + duration/2, y_pos, label_text,
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
            else:
                ax.text(start + duration + makespan * 0.01, y_pos, label_text,
                       ha='left', va='center', fontsize=8)
        
        y_pos += 1
    
    # 设置坐标轴
    ax.set_ylim(-0.5, len(team_tasks) - 0.5)
    ax.set_xlim(0, makespan * VISUALIZATION_CONFIG["xlim_padding"])
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=VISUALIZATION_CONFIG["fontsize_legend"])
    ax.set_xlabel("时间", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_ylabel("团队", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_title(f'团队视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=VISUALIZATION_CONFIG["fontsize_title"], fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=VISUALIZATION_CONFIG["grid_alpha"], linestyle='--')
    
    # 添加工作量统计
    team_workload = {}
    for team, tasks in team_tasks.items():
        total_duration = sum(task["end"] - task["start"] for task in tasks)
        team_workload[team] = total_duration
    
    # 在右侧添加工作量信息
    workload_text = "团队工作量:\n"
    for team, workload in team_workload.items():
        team_name = TEAM_NAMES.get(team, team)
        workload_text += f"{team_name}: {workload:.1f}h\n"
    
    ax.text(1.02, 0.5, workload_text, transform=ax.transAxes, fontsize=9,
           verticalalignment='center', bbox=dict(boxstyle="round,pad=0.3", 
                                               facecolor='lightgray', alpha=0.8))
    
    return fig
    
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
            color = TEAM_COLORS.get(team, '#CCCCCC')
            rect = Rectangle((start, y_pos - 0.4), duration, 0.8,
                           facecolor=color, alpha=VISUALIZATION_CONFIG["alpha"], 
                           edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 修复标签位置逻辑 - 基于makespan而不是actual_max_time
            label_text = f"{task_name}\n{workers}人"
            
            if duration > makespan * VISUALIZATION_CONFIG["label_threshold"]:  # 任务足够长，在内部显示
                ax.text(start + duration/2, y_pos, label_text,
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
            elif start + duration < makespan * VISUALIZATION_CONFIG["label_position_threshold"]:  # 任务在左侧，右侧显示
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
    ax.set_xlim(0, makespan * VISUALIZATION_CONFIG["xlim_padding"])
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=VISUALIZATION_CONFIG["fontsize_legend"])
    ax.set_xlabel("时间", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_ylabel("工作点", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_title(f'多工作点视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=VISUALIZATION_CONFIG["fontsize_title"], fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=VISUALIZATION_CONFIG["grid_alpha"], linestyle='--')
    
    # 添加图例
    legend_elements = []
    for team, color in TEAM_COLORS.items():
        legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color, 
                                           alpha=VISUALIZATION_CONFIG["alpha"], label=team))
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1),
             fontsize=VISUALIZATION_CONFIG["fontsize_legend"], frameon=True)
    
    return fig


def create_team_gantt_chart(schedule, makespan):
    """创建团队视角甘特图"""
    print(f"📊 创建团队视角甘特图，完工时间: {makespan:.2f}")
    
    fig, ax = plt.subplots(figsize=VISUALIZATION_CONFIG["figure_size"])
    
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
        team_name = TEAM_NAMES.get(team, team)
        y_labels.append(team_name)
        y_positions.append(y_pos)
        
        # 绘制该团队的所有任务
        for task in tasks:
            start = task["start"]
            duration = task["end"] - task["start"]
            workers = task["workers"]
            task_name = task["name"]
            
            # 绘制任务条
            color = TEAM_COLORS.get(team, '#CCCCCC')
            rect = Rectangle((start, y_pos - 0.4), duration, 0.8,
                           facecolor=color, alpha=VISUALIZATION_CONFIG["alpha"], 
                           edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 添加任务标签
            label_text = f"{task_name}\n{workers}人"
            if duration > makespan * VISUALIZATION_CONFIG["label_threshold"]:
                ax.text(start + duration/2, y_pos, label_text,
                       ha='center', va='center', fontsize=9, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', alpha=0.8))
            else:
                ax.text(start + duration + makespan * 0.01, y_pos, label_text,
                       ha='left', va='center', fontsize=8)
        
        y_pos += 1
    
    # 设置坐标轴
    ax.set_ylim(-0.5, len(team_tasks) - 0.5)
    ax.set_xlim(0, makespan * VISUALIZATION_CONFIG["xlim_padding"])
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=VISUALIZATION_CONFIG["fontsize_legend"])
    ax.set_xlabel("时间", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_ylabel("团队", fontsize=VISUALIZATION_CONFIG["fontsize_label"])
    ax.set_title(f'团队视角甘特图 (完工时间: {makespan:.2f} 时间单位)', 
                fontsize=VISUALIZATION_CONFIG["fontsize_title"], fontweight='bold', pad=20)
    ax.grid(axis='x', alpha=VISUALIZATION_CONFIG["grid_alpha"], linestyle='--')
    
    # 添加工作量统计
    team_workload = {}
    for team, tasks in team_tasks.items():
        total_duration = sum(task["end"] - task["start"] for task in tasks)
        team_workload[team] = total_duration
    
    # 在右侧添加工作量信息
    workload_text = "团队工作量:\n"
    for team, workload in team_workload.items():
        team_name = TEAM_NAMES.get(team, team)
        workload_text += f"{team_name}: {workload:.1f}h\n"
    
    ax.text(1.02, 0.5, workload_text, transform=ax.transAxes,
           fontsize=VISUALIZATION_CONFIG["fontsize_text"], verticalalignment='center',
           bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
    
    return fig


def visualize_schedule(schedule, makespan):
    """创建传统甘特图可视化调度方案，并打印详细信息"""
    # 按开始时间排序
    schedule.sort(key=lambda x: x["start"])

    # 按团队统计工作量
    team_workload = {team: 0 for team in TEAM_NAMES}
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
        result_output += f"{step['name']:<20} {TEAM_NAMES[team]:<20} {step['start']:<10.2f} {step['end']:<10.2f} {duration:<10.2f} {step['workers']:<10}\n"

    # 创建图表
    fig, ax = plt.subplots(figsize=(9, 6))

    # 绘制每个工序为一个条形
    for i, step in enumerate(schedule):
        team = step["team"]
        # 使用中文团队名称作为图例标签
        ax.barh(i, step["end"] - step["start"], left=step["start"],
                color=TEAM_COLORS[team],
                edgecolor='black',
                label=TEAM_NAMES[team] if team not in [s["team"] for s in schedule[:i]] else "")

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
    ax.set_title(f'工序视角甘特图 (总完工时间: {makespan:.2f} 时间单位)', fontsize=14, fontweight='bold')
    ax.set_xlabel('时间', fontsize=12)
    ax.set_ylabel('工序', fontsize=12)

    # 自定义横坐标为天数格式（上午/下午）
    _set_time_axis(ax, makespan)
    
    # 设置网格线
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    # 完善图例
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels,
              loc='upper center', bbox_to_anchor=(0.5, -0.1),
              ncol=3, fontsize=10)

    # 创建图片缓冲区
    buffer = BytesIO()
    buffer.seek(0)
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    plt.show()
    return result_output, buffer


def _infer_workpoints_from_schedule(schedule):
    """从调度结果推断工作点信息"""
    workpoints = []
    
    # 按工作点分组任务（基于任务名称格式：如"1-搭架子"、"2-拆保温"）
    workpoint_tasks = {}
    
    for task in schedule:
        task_name = task["name"]
        
        # 解析新的任务名称格式："1-搭架子" -> 设备1
        if "-" in task_name:
            parts = task_name.split("-", 1)  # 只分割第一个"-"
            if len(parts) == 2 and parts[0].isdigit():
                wp_number = parts[0]
                wp_id = f"设备{wp_number}"
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


def save_gantt_charts(schedule, makespan, env=None):
    """保存所有甘特图到result文件夹"""
    from io import BytesIO
    
    saved_files = []
    
    # 初始化返回变量
    record = None
    process_fig = None
    workpoint_fig = None
    team_fig = None
    
    try:
        # 1. 工序视角甘特图

        # 生成工序甘特图作为对比
        print("1/3 生成工序视角甘特图...")
        record, process_fig = visualize_schedule(schedule, makespan)
        process_path = get_result_path(FILE_PATHS["process_gantt"])
        plt.savefig(process_path, dpi=VISUALIZATION_CONFIG["dpi"], 
                bbox_inches=VISUALIZATION_CONFIG["bbox_inches"])
        print(f"✅ 工序视角甘特图已保存为: {process_path}")
        saved_files.append(FILE_PATHS["process_gantt"])
        plt.close()

        # print("1/3 生成工序视角甘特图...")
        # process_fig = create_traditional_gantt_chart(schedule, makespan)
        # process_path = get_result_path(FILE_PATHS["process_gantt"])
        # process_fig.savefig(process_path, dpi=VISUALIZATION_CONFIG["dpi"], 
        #                    bbox_inches=VISUALIZATION_CONFIG["bbox_inches"])
        # print(f"✅ 工序视角甘特图已保存为: {process_path}")
        # saved_files.append(FILE_PATHS["process_gantt"])
        # plt.close(process_fig)
        
    except Exception as e:
        print(f"❌ 工序视角甘特图生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # 2. 分层多设备视角甘特图（解决并行任务重叠问题）
        print("2/3 生成分层多设备视角甘特图...")
        workpoint_fig_obj = create_layered_workpoint_gantt_chart(schedule, makespan, env)
        workpoint_path = get_result_path(FILE_PATHS["workpoint_gantt"])
        workpoint_fig_obj.savefig(workpoint_path, dpi=VISUALIZATION_CONFIG["dpi"], 
                                 bbox_inches=VISUALIZATION_CONFIG["bbox_inches"])
        
        # 转换为BytesIO对象供Flask使用
        workpoint_fig = BytesIO()
        workpoint_fig_obj.savefig(workpoint_fig, format='png', dpi=VISUALIZATION_CONFIG["dpi"], 
                                 bbox_inches=VISUALIZATION_CONFIG["bbox_inches"])
        workpoint_fig.seek(0)
        
        print(f"✅ 分层多工作点视角甘特图已保存为: {workpoint_path}")
        saved_files.append(FILE_PATHS["workpoint_gantt"])
        plt.close(workpoint_fig_obj)
        
    except Exception as e:
        print(f"❌ 多设备视角甘特图生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # 3. 分层团队视角甘特图（解决并行任务重叠问题）
        print("3/3 生成分层团队视角甘特图...")
        team_fig_obj = create_layered_team_gantt_chart(schedule, makespan)
        team_path = get_result_path(FILE_PATHS["team_gantt"])
        team_fig_obj.savefig(team_path, dpi=VISUALIZATION_CONFIG["dpi"], 
                            bbox_inches=VISUALIZATION_CONFIG["bbox_inches"])
        
        # 转换为BytesIO对象供Flask使用
        team_fig = BytesIO()
        team_fig_obj.savefig(team_fig, format='png', dpi=VISUALIZATION_CONFIG["dpi"], 
                            bbox_inches=VISUALIZATION_CONFIG["bbox_inches"])
        team_fig.seek(0)
        
        print(f"✅ 分层团队视角甘特图已保存为: {team_path}")
        saved_files.append(FILE_PATHS["team_gantt"])
        plt.close(team_fig_obj)
        
    except Exception as e:
        print(f"❌ 团队视角甘特图生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    if saved_files:
        print(f"\n📊 三张图表统计:")
        print(f"  - 统一完工时间: {makespan:.2f} 时间单位")
        print(f"  - 任务总数: {len(schedule)}")
        
        # 统计团队参与情况
        teams_used = set(task["team"] for task in schedule)
        print(f"  - 参与团队: {len(teams_used)} 个 ({', '.join(sorted(teams_used))})")
        print(f"  - 成功保存: {len(saved_files)}/3 张图片")
    else:
        print("❌ 所有甘特图生成都失败了")
    
    
    # 获取result目录路径用于显示
    from config import ensure_result_dir
    result_dir = ensure_result_dir()
    
    print(f"\n🎉 所有图表生成完成！")
    print(f"📁 生成的文件 (保存在 {result_dir}):")
    print(f"  • {FILE_PATHS['process_gantt']} - 工序视角甘特图")
    print(f"  • {FILE_PATHS['workpoint_gantt']} - 多工作点视角甘特图")
    print(f"  • {FILE_PATHS['team_gantt']} - 团队视角甘特图")
    
    return record, process_fig, workpoint_fig, team_fig
