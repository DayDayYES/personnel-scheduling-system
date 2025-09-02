import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import namedtuple, deque
import matplotlib.pyplot as plt
import time
from io import BytesIO

t1 = time.time()
plt.rcParams['font.sans-serif'] = ['SimHei']  # 解决中文显示问题
plt.rcParams['axes.unicode_minus'] = False


# Define the factory environment for the scheduling problem
class FactoryEnvironment:
    def __init__(self, input_data):
        # Define work steps based on the table
        # dedicated: True = 专人队伍, False = 人员共用队伍
        self.work_steps = [
            {"name": "搭架子", "order": 1, "team": "team1", "dedicated": True, "team_size": 5, "duration": input_data[0]},
            {"name": "拆保温", "order": 2, "team": "team2", "dedicated": False, "team_size": 10, "duration": input_data[1]},
            {"name": "打磨", "order": 3, "team": "team2", "dedicated": False, "team_size": 10, "duration": input_data[2]},
            {"name": "宏观检验", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "duration": input_data[3],
             "parallel": True},
            {"name": "壁厚测定", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "duration": input_data[4],
             "parallel": True},
            {"name": "射线检测", "order": 4, "team": "team4", "dedicated": True, "team_size": 5, "duration": input_data[5],
             "parallel": True},
            {"name": "表面检测", "order": 4, "team": "team5", "dedicated": False, "team_size": 15, "duration": input_data[6],
             "parallel": True},
            {"name": "超声检测", "order": 4, "team": "team5", "dedicated": False, "team_size": 15, "duration": input_data[7],
             "parallel": True},
            {"name": "其他无损检测", "order": 4, "team": "team5", "dedicated": False, "team_size": 15, "duration": input_data[8],
             "parallel": True},
            {"name": "铁素体检测", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "duration": input_data[9],
             "parallel": True},
            {"name": "硬度检测", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "duration": input_data[10],
             "parallel": True},
            {"name": "金相检验", "order": 4, "team": "team3", "dedicated": False, "team_size": 10, "duration": input_data[11],
             "parallel": True},
            {"name": "检验结果评定", "order": 5, "team": "team3", "dedicated": True, "team_size": 10, "duration": input_data[12]},
            {"name": "返修", "order": 6, "team": "team6", "dedicated": True, "team_size": 5, "duration": input_data[13]},
            {"name": "合格报告出具", "order": 7, "team": "team3", "dedicated": True, "team_size": 10, "duration": input_data[14]},
        ]

        # Define teams
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
        self.step_status = {step["name"]: 0 for step in self.work_steps}
        self.step_allocations = {step["name"]: 0 for step in self.work_steps}
        self.step_max_allocations = {step["name"]: 0 for step in self.work_steps}  # 记录最大分配的工人数
        self.step_start_times = {step["name"]: 0 for step in self.work_steps}
        self.step_end_times = {step["name"]: 0 for step in self.work_steps}

        self.current_time = 0
        self.events = []  # (step_name, completion_time)

    def reset(self):
        # Reset the environment to initial state
        for team in self.teams:
            self.teams[team]["available"] = self.teams[team]["size"]
            self.team_allocations[team] = {}

        self.step_status = {step["name"]: 0 for step in self.work_steps}
        self.step_allocations = {step["name"]: 0 for step in self.work_steps}
        self.step_max_allocations = {step["name"]: 0 for step in self.work_steps}
        self.step_start_times = {step["name"]: 0 for step in self.work_steps}
        self.step_end_times = {step["name"]: 0 for step in self.work_steps}

        self.current_time = 0
        self.events = []

        return self._get_state()

    def _get_state(self):
        """Convert the current environment state to a vector for the neural network."""
        state = []

        # Step statuses and allocations (3 values per step)
        for step in self.work_steps:
            state.append(self.step_status[step["name"]])
            state.append(self.step_allocations[step["name"]])
            state.append(1.0 if step["dedicated"] else 0.0)  # Is the team dedicated?

        # Team availability (normalized percentage)
        for team in self.teams:
            state.append(self.teams[team]["available"] / self.teams[team]["size"])

        # Current time (normalized)
        state.append(min(1.0, self.current_time / 1000))  # Assuming 1000 is max time

        return np.array(state, dtype=np.float32)

    def get_team_used_workers(self, team_name):
        """获取团队当前已分配的总人数"""
        if team_name not in self.team_allocations:
            return 0

        return sum(self.team_allocations[team_name].values())

    def get_available_steps(self):
        """获取当前可以开始的工序。"""
        available_steps = []

        for step in self.work_steps:
            if self.step_status[step["name"]] != 0:
                continue  # 已经在进行或已完成

            # 检查前序约束
            can_start = True
            current_order = step["order"]

            for other_step in self.work_steps:
                # 如果有更低顺序号的工序未完成，不能开始
                if other_step["order"] < current_order and self.step_status[other_step["name"]] != 2:
                    can_start = False
                    break

                # 对于并行步骤（顺序4），需要检查是否来自同一专用团队
                if step.get("parallel") and other_step.get("parallel") and step["team"] == other_step["team"]:
                    if step["dedicated"] and self.step_status[other_step["name"]] == 1:
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
                        available_steps.append(step["name"])
                elif team["available"] == team["size"]:  # 专用团队必须全部可用
                    available_steps.append(step["name"])

        return available_steps

    def get_valid_actions(self):
        """获取当前状态下的所有有效动作。"""
        valid_actions = []
        available_steps = self.get_available_steps()

        # 按团队分组可用工序，用于优化并行处理
        team_steps = {}
        for step_name in available_steps:
            step = next(s for s in self.work_steps if s["name"] == step_name)
            team_name = step["team"]
            if team_name not in team_steps:
                team_steps[team_name] = []
            team_steps[team_name].append(step_name)

        for step_name in available_steps:
            step = next(s for s in self.work_steps if s["name"] == step_name)
            team_name = step["team"]
            team = self.teams[team_name]

            if step["dedicated"]:
                # 专用团队总是使用全部人力
                if team["available"] == team["size"]:
                    valid_actions.append((step_name, team["size"]))
            else:
                # 对于共用团队
                used_workers = self.get_team_used_workers(team_name)
                available_workers = team["size"] - used_workers
                same_team_steps = team_steps.get(team_name, [])

                # 如果是同一团队的唯一可用工序，优先考虑全部人力
                if len(same_team_steps) == 1 and available_workers > 0:
                    valid_actions.append((step_name, available_workers))

                # 如果是同一团队有多个可用工序，提供多种分配选项
                elif len(same_team_steps) > 1 and available_workers > 0:
                    # 可能的工人分配方案：全部、3/4、1/2、1/4、最少1人
                    possible_allocations = [
                        available_workers,
                        max(1, int(available_workers * 0.75)),
                        max(1, int(available_workers * 0.5)),
                        max(1, int(available_workers * 0.25)),
                        1
                    ]

                    # 移除重复值并排序
                    possible_allocations = sorted(list(set(possible_allocations)), reverse=True)

                    for workers in possible_allocations:
                        valid_actions.append((step_name, workers))

                # 如果没有可用工人，跳过
                else:
                    continue

        # 如果有正在进行的工序，添加推进时间的动作
        if self.events:
            valid_actions.append(("advance_time", 0))

        return valid_actions

    def step(self, action):
        """Take an action in the environment."""
        step_name, workers = action

        if step_name == "advance_time":
            # Advance time to the next event
            return self._advance_time()

        # Find the step
        step = next(s for s in self.work_steps if s["name"] == step_name)
        team_name = step["team"]

        # Record start time
        self.step_start_times[step_name] = self.current_time

        # Allocate workers
        if step["dedicated"]:
            # 专用团队
            self.teams[team_name]["available"] = 0  # 将团队设为不可用
        else:
            # 共用团队 - 更新团队分配记录
            if team_name not in self.team_allocations:
                self.team_allocations[team_name] = {}
            self.team_allocations[team_name][step_name] = workers

        self.step_allocations[step_name] = workers
        self.step_max_allocations[step_name] = workers  # 记录分配的工人数
        self.step_status[step_name] = 1  # In progress

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
        # 获取任务的基本信息
        # base_duration = step["duration"]  # 任务的原始预计持续时间
        # team_size = step["team_size"]  # 这个任务的理想团队大小
        #
        # # 简单的线性计算 - 人数翻倍，时间减半
        # adjusted_duration = base_duration * (team_size / workers)
        #
        # # 计算最终完成时间
        # completion_time = self.current_time + adjusted_duration
        # Record expected end time
        self.step_end_times[step_name] = completion_time

        # Add to events
        self.events.append((step_name, completion_time))

        # Sort events by completion time
        self.events.sort(key=lambda x: x[1])

        # Return state, reward, done
        done = all(self.step_status[step["name"]] == 2 for step in self.work_steps)
        next_state = self._get_state()

        # Reward is negative time delta to incentivize faster completion
        reward = -1  # Penalty for each action

        return next_state, reward, done

    def _advance_time(self):
        """推进时间到下一个事件并处理完成情况。"""
        if not self.events:
            # 没有事件要处理
            return self._get_state(), 0, False

        # 获取下一个事件
        step_name, completion_time = self.events.pop(0)

        # 推进时间（不再取整）
        time_delta = completion_time - self.current_time
        self.current_time = completion_time

        # 找到工序
        step = next(s for s in self.work_steps if s["name"] == step_name)
        team_name = step["team"]

        # 完成工序
        self.step_status[step_name] = 2  # 标记为已完成

        # 释放工人
        if step["dedicated"]:
            # 专用团队
            self.teams[team_name]["available"] = self.teams[team_name]["size"]
        else:
            # 共用团队 - 从团队分配记录中移除
            if team_name in self.team_allocations and step_name in self.team_allocations[team_name]:
                del self.team_allocations[team_name][step_name]

        self.step_allocations[step_name] = 0  # 清零当前分配

        # 检查是否所有工序都已完成
        done = all(self.step_status[step["name"]] == 2 for step in self.work_steps)

        # 奖励是负时间增量，以激励更快完成
        reward = -time_delta

        return self._get_state(), reward, done

    def get_makespan(self):
        """返回当前调度的完工时间（总时间）"""
        if all(self.step_status[step["name"]] == 2 for step in self.work_steps):
            return self.current_time  # 不再取整，直接返回小数时间
        else:
            return float('inf')

    def get_schedule(self):
        """Return the schedule information for visualization."""
        schedule = []
        for step in self.work_steps:
            name = step["name"]
            team = step["team"]
            if self.step_status[name] == 2:  # Only include completed steps
                schedule.append({
                    "name": name,
                    "team": team,
                    "start": self.step_start_times[name],
                    "end": self.step_end_times[name],
                    "workers": self.step_max_allocations[name]  # 使用记录的工人数
                })
        return schedule


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
def train(input_data):
    # Import tqdm at the top of your function or file
    from tqdm import tqdm

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    # print(f"Using device: {device}")

    env = FactoryEnvironment(input_data)
    state_size = len(env.reset())
    max_steps = 1000
    action_size = 100

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


def plot_training_progress(episode_rewards, episode_makespans):
    """
    绘制训练过程中的奖励和完工时间变化图。

    Args:
        episode_rewards: 每个episode的总奖励列表
        episode_makespans: 每个episode的完工时间列表
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

    # 绘制奖励曲线
    episodes = range(1, len(episode_rewards) + 1)
    ax1.plot(episodes, episode_rewards, 'b-', label='总奖励')

    # 添加平滑奖励曲线（移动平均）
    window_size = min(20, len(episode_rewards) // 5 + 1)  # 自适应窗口大小
    if window_size > 1:
        smoothed_rewards = np.convolve(episode_rewards, np.ones(window_size) / window_size, mode='valid')
        smoothed_episodes = range(window_size, len(episode_rewards) + 1)
        ax1.plot(smoothed_episodes, smoothed_rewards, 'r-', linewidth=2, label=f'移动平均 ({window_size}回合)')

    ax1.set_ylabel('总奖励', fontsize=12)
    ax1.set_title('训练进度：奖励和完工时间', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, linestyle='--', alpha=0.7)

    # 绘制完工时间曲线（过滤掉无限值）
    valid_makespans = [(i + 1, m) for i, m in enumerate(episode_makespans) if m != float('inf') and m is not None]
    if valid_makespans:
        makespan_episodes, makespan_values = zip(*valid_makespans)
        ax2.plot(makespan_episodes, makespan_values, 'g-', label='完工时间')

        # 添加平滑的完工时间曲线
        if len(valid_makespans) > window_size:
            smoothed_makespans = np.convolve(makespan_values, np.ones(window_size) / window_size, mode='valid')
            smoothed_makespan_episodes = makespan_episodes[window_size - 1:]
            ax2.plot(smoothed_makespan_episodes, smoothed_makespans, 'orange', linewidth=2,
                     label=f'移动平均 ({window_size}回合)')

        # 突出显示最佳完工时间
        best_makespan = min(makespan_values)
        best_episode = makespan_episodes[makespan_values.index(best_makespan)]
        ax2.scatter(best_episode, best_makespan, color='red', s=100, zorder=5,
                    label=f'最佳值: {best_makespan:.2f} (第{best_episode}回合)')

    ax2.set_xlabel('训练回合', fontsize=12)
    ax2.set_ylabel('完工时间', fontsize=12)
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.savefig('training_progress.png')
    plt.show()


# Main execution
def RUN(input_data):
    # Set random seed for reproducibility
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    # 增加训练轮数以找到更优解
    agent, env, best_schedule, rewards, makespans = train(input_data)

    # 打印最佳结果（不再取整）
    best_makespan = min([m for m in makespans if m is not None])
    print(f"训练完成. 最佳完工时间: {best_makespan:.2f}")

    # 直接从保存的文件加载最佳调度方案
    import pickle

    try:
        with open('best_schedule.pkl', 'rb') as f:
            final_schedule, final_makespan = pickle.load(f)
        print(f"成功加载最佳调度方案! 完工时间: {final_makespan:.2f}")
    except Exception as e:
        print(f"加载保存的最佳方案失败: {e}")
        print("将尝试使用最佳模型...")

        # 备选方案：运行最佳模型
        best_final_makespan = float('inf')
        best_final_schedule = None

        print("运行最佳模型以获取最优调度方案...")
        for i in range(10):  # 运行10次，取最好的结果
            schedule, makespan = run_best_schedule(env)
            print(f"运行 {i + 1}/10: 完工时间 = {makespan:.2f}")
            if makespan < best_final_makespan:
                best_final_makespan = makespan
                best_final_schedule = schedule
                print(f"  发现更优方案! 新的最佳完工时间: {best_final_makespan:.2f}")

        final_schedule = best_final_schedule
        final_makespan = best_final_makespan
    # plot_training_progress(rewards, makespans)

    print('Running time: ', time.time() - t1)
    # 可视化最终最优方案
    record, img = visualize_schedule(final_schedule, final_makespan)
    print(record)
    plt.savefig('best_schedule.png')
    #plt.show()
    return record, img

if __name__ == '__main__':

    t1 = time.time()
    RUN([10, 5, 8, 6, 7, 9, 6, 7, 6, 7, 7, 7, 4, 7, 5])
    # train(episodes=1000)
    # run_best_schedule()