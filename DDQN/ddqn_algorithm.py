# -*- coding: utf-8 -*-
"""
DDQN算法模块 - 包含神经网络和强化学习算法
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import namedtuple, deque
from tqdm import tqdm
from config import DDQN_CONFIG, get_result_path, FILE_PATHS
from global_best_tracker import global_best_tracker


# 定义经验回放的数据结构
Experience = namedtuple('Experience', ('state', 'action_idx', 'next_state', 'reward', 'done'))


class DDQNNetwork(nn.Module):
    """DDQN神经网络"""
    
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


class ReplayBuffer:
    """经验回放缓冲区"""
    
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, *args):
        self.buffer.append(Experience(*args))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)


class DDQNAgent:
    """DDQN智能体"""
    
    def __init__(self, state_size, action_size, device='cpu'):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = ReplayBuffer(DDQN_CONFIG["memory_size"])
        self.device = device

        # 从配置加载参数
        self.gamma = DDQN_CONFIG["gamma"]
        self.epsilon = DDQN_CONFIG["epsilon"]
        self.epsilon_min = DDQN_CONFIG["epsilon_min"]
        self.epsilon_decay = DDQN_CONFIG["epsilon_decay"]
        self.batch_size = DDQN_CONFIG["batch_size"]
        self.update_freq = DDQN_CONFIG["update_freq"]

        # 创建策略网络和目标网络
        self.policy_net = DDQNNetwork(state_size, action_size).to(device)
        self.target_net = DDQNNetwork(state_size, action_size).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()  # 设置目标网络为评估模式

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=DDQN_CONFIG["learning_rate"])
        self.criterion = nn.MSELoss()

    def remember(self, state, action_idx, next_state, reward, done):
        """存储经验到回放缓冲区"""
        self.memory.push(state, action_idx, next_state, reward, done)

    def act(self, state, valid_actions):
        """选择动作（epsilon-贪婪策略）"""
        if np.random.rand() <= self.epsilon:
            return np.random.randint(0, len(valid_actions))

        # 获取状态的Q值
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.policy_net(state_tensor).cpu().numpy()[0]

        # 为有效动作过滤Q值
        valid_q_values = [(i, q_values[i % len(q_values)]) for i in range(len(valid_actions))]

        # 返回具有最高Q值的动作
        return max(valid_q_values, key=lambda x: x[1])[0]

    def replay(self):
        """经验回放学习"""
        if len(self.memory) < self.batch_size:
            return

        # 采样批次
        batch = self.memory.sample(self.batch_size)
        states = torch.FloatTensor([exp.state for exp in batch]).to(self.device)
        action_idxs = torch.LongTensor([exp.action_idx for exp in batch]).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor([exp.reward for exp in batch]).to(self.device)
        next_states = torch.FloatTensor([exp.next_state for exp in batch]).to(self.device)
        dones = torch.FloatTensor([exp.done for exp in batch]).to(self.device)

        # 获取当前Q值
        current_q = self.policy_net(states).gather(1, action_idxs).squeeze(1)

        # DDQN更新：使用策略网络选择动作，目标网络评估
        with torch.no_grad():
            next_actions = self.policy_net(next_states).max(1)[1].unsqueeze(1)
            max_next_q = self.target_net(next_states).gather(1, next_actions).squeeze(1)

            # 计算目标Q值
            target_q = rewards + (self.gamma * max_next_q * (1 - dones))

        # 更新策略网络
        loss = self.criterion(current_q, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        # 应用梯度裁剪
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()

        # 衰减epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def update_target_network(self):
        """更新目标网络"""
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def save(self, filename=None):
        """保存模型到result文件夹"""
        if filename is None:
            filename = FILE_PATHS["best_model"]
        
        model_path = get_result_path(filename)
        torch.save({
            'policy_model': self.policy_net.state_dict(),
            'target_model': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, model_path)
        print(f"✅ 模型已保存到: {model_path}")

    def load(self, filename=None):
        """从result文件夹加载模型"""
        if filename is None:
            filename = FILE_PATHS["best_model"]
        
        model_path = get_result_path(filename)
        try:
            checkpoint = torch.load(model_path)
            self.policy_net.load_state_dict(checkpoint['policy_model'])
            self.target_net.load_state_dict(checkpoint['target_model'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            self.epsilon = checkpoint['epsilon']
            print(f"✅ 模型已从 {model_path} 加载")
        except Exception as e:
            print(f"⚠️  模型加载失败: {e}")


def train_ddqn_agent(env, workpoints_data=None):
    """
    训练DDQN智能体
    
    Args:
        env: 调度环境
        workpoints_data: 工作点数据字典（用于全局最优跟踪）
    """
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    state_size = len(env.reset())
    action_size = DDQN_CONFIG["action_size"]
    episodes = DDQN_CONFIG["episodes"]
    max_steps = DDQN_CONFIG["max_steps"]

    print(f"状态空间维度: {state_size}")
    print(f"总工序数量: {len(env.work_steps)}")
    print(f"使用设备: {device}")

    agent = DDQNAgent(state_size, action_size, device)

    episode_rewards = []
    episode_makespans = []
    best_makespan = float('inf')
    best_schedule = None

    # 训练循环
    for episode in tqdm(range(episodes), desc="Training Progress", ncols=100):
        state = env.reset()
        total_reward = 0
        done = False
        step_counter = 0

        # 单个episode内的步骤循环
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
        
        # 更新最佳结果
        if makespan < best_makespan:
            best_makespan = makespan
            best_schedule = env.get_schedule()
            print(f"Episode {episode}: 新的最佳完工时间 {best_makespan:.2f}")
            
            # 更新全局最优结果
            model_path = get_result_path(FILE_PATHS["best_model"])
            if workpoints_data is not None:
                global_best_tracker.update_best_result(
                    schedule=best_schedule,
                    makespan=best_makespan,
                    algorithm_name="原版DDQN",
                    workpoints_data=workpoints_data,
                    episode=episode,
                    model_path=model_path
                )

        # 更新目标网络
        if episode % agent.update_freq == 0:
            agent.update_target_network()

        episode_rewards.append(total_reward)
        episode_makespans.append(makespan)

    # 训练完成后保存模型
    print("训练完成，保存模型...")
    agent.save()

    return agent, env, best_schedule, episode_rewards, episode_makespans


def run_best_schedule(env, agent_file=None):
    """运行训练好的代理以获取最佳调度方案"""
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    env.reset()

    # 创建代理
    state_size = len(env.reset())
    action_size = DDQN_CONFIG["action_size"]
    agent = DDQNAgent(state_size, action_size, device)
    
    # 如果提供了模型文件，加载它
    if agent_file:
        try:
            agent.load(agent_file)
        except:
            print(f"无法加载模型文件 {agent_file}，使用随机初始化的代理")
    
    agent.epsilon = 0.0  # 不再探索，只利用已学到的知识

    state = env.reset()
    done = False
    step_counter = 0

    while not done and step_counter < DDQN_CONFIG["max_steps"]:
        valid_actions = env.get_valid_actions()

        if not valid_actions:
            break

        action_idx = agent.act(state, valid_actions)
        action = valid_actions[action_idx]

        next_state, _, done = env.step(action)
        state = next_state
        step_counter += 1

    # 获取调度方案
    schedule = env.get_schedule()
    makespan = env.get_makespan()
    return schedule, makespan
