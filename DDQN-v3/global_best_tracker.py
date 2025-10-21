# -*- coding: utf-8 -*-
"""
全局最优结果跟踪器 - 跨算法保存最佳调度方案
"""

import pickle
import os
import hashlib
import json
from config import get_result_path


class GlobalBestTracker:
    """全局最优结果跟踪器"""
    
    def __init__(self):
        self.best_makespan = float('inf')
        self.best_schedule = None
        self.best_algorithm = None
        self.best_episode = -1
        self.best_model_path = None
        self.workpoints_hash = None  # 工序配置的哈希值
        self.global_best_file = "global_best_result.pkl"
        
        # 尝试加载已存在的全局最优结果
        self.load_global_best()
    
    def calculate_workpoints_hash(self, workpoints_data):
        """
        计算工序配置的哈希值，用于识别工序是否发生变化
        
        Args:
            workpoints_data: 工作点数据字典
        
        Returns:
            str: 工序配置的MD5哈希值
        """
        # 提取关键信息用于生成哈希
        config_data = {}
        
        for wp_id, wp_info in sorted(workpoints_data.items()):
            steps_info = []
            for step in wp_info.get("steps", []):
                # 只包含影响调度的关键字段
                step_key = (
                    step.get("name"),
                    step.get("order"),
                    step.get("team"),
                    step.get("dedicated"),
                    step.get("team_size"),
                    step.get("duration"),
                    step.get("parallel", False)
                )
                steps_info.append(step_key)
            
            config_data[wp_id] = steps_info
        
        # 转换为JSON字符串并计算哈希
        config_str = json.dumps(config_data, sort_keys=True)
        hash_value = hashlib.md5(config_str.encode('utf-8')).hexdigest()
        
        return hash_value
    
    def update_best_result(self, schedule, makespan, algorithm_name, workpoints_data, episode=None, model_path=None):
        """
        更新全局最优结果
        
        Args:
            schedule: 调度方案
            makespan: 完工时间
            algorithm_name: 算法名称 ('ddqn', 'enhanced_ddqn', 'greedy')
            workpoints_data: 工作点数据字典（用于计算哈希）
            episode: 训练轮次 (可选)
            model_path: 模型文件路径 (可选)
        
        Returns:
            bool: 是否更新了最优结果
        """
        # 计算当前工序配置的哈希值
        current_hash = self.calculate_workpoints_hash(workpoints_data)
        
        # 如果工序配置发生变化，重置最优结果
        if self.workpoints_hash is not None and self.workpoints_hash != current_hash:
            print(f"\n⚠️  检测到工序配置变化，重置全局最优结果")
            print(f"   旧配置哈希: {self.workpoints_hash[:8]}...")
            print(f"   新配置哈希: {current_hash[:8]}...")
            self.reset()
        
        # 更新哈希值
        self.workpoints_hash = current_hash
        
        if makespan < self.best_makespan:
            self.best_makespan = makespan
            self.best_schedule = schedule
            self.best_algorithm = algorithm_name
            self.best_episode = episode
            self.best_model_path = model_path
            
            # 立即保存到文件
            self.save_global_best()
            
            print(f"🏆 发现新的全局最优结果!")
            print(f"   算法: {algorithm_name}")
            print(f"   完工时间: {makespan:.2f}")
            if episode is not None:
                print(f"   训练轮次: Episode {episode}")
            print(f"   工序配置: {current_hash[:8]}...")
            
            return True
        
        return False
    
    def save_global_best(self):
        """保存全局最优结果到文件"""
        try:
            global_best_path = get_result_path(self.global_best_file)
            
            data = {
                'makespan': self.best_makespan,
                'schedule': self.best_schedule,
                'algorithm': self.best_algorithm,
                'episode': self.best_episode,
                'model_path': self.best_model_path,
                'workpoints_hash': self.workpoints_hash  # 保存工序配置哈希
            }
            
            with open(global_best_path, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"✅ 全局最优结果已保存: {global_best_path}")
            
        except Exception as e:
            print(f"⚠️  保存全局最优结果失败: {e}")
    
    def load_global_best(self):
        """从文件加载全局最优结果"""
        try:
            global_best_path = get_result_path(self.global_best_file)
            
            if os.path.exists(global_best_path):
                with open(global_best_path, 'rb') as f:
                    data = pickle.load(f)
                
                self.best_makespan = data.get('makespan', float('inf'))
                self.best_schedule = data.get('schedule', None)
                self.best_algorithm = data.get('algorithm', None)
                self.best_episode = data.get('episode', -1)
                self.best_model_path = data.get('model_path', None)
                self.workpoints_hash = data.get('workpoints_hash', None)  # 加载工序配置哈希

                
                # print(f"📂 加载已存在的全局最优结果:")
                # print(f"   算法: {self.best_algorithm}")
                # print(f"   完工时间: {self.best_makespan:.2f}")
                # if self.best_episode >= 0:
                #     print(f"   训练轮次: Episode {self.best_episode}")
            
        except Exception as e:
            print(f"⚠️  加载全局最优结果失败: {e}")
            # 重置为默认值
            self.best_makespan = float('inf')
            self.best_schedule = None
            self.best_algorithm = None
            self.best_episode = -1
            self.best_model_path = None
            self.workpoints_hash = None
    
    def get_best_result(self):
        """获取当前全局最优结果"""
        return {
            'makespan': self.best_makespan,
            'schedule': self.best_schedule,
            'algorithm': self.best_algorithm,
            'episode': self.best_episode,
            'model_path': self.best_model_path
        }
    
    def reset(self):
        """重置全局最优结果"""
        self.best_makespan = float('inf')
        self.best_schedule = None
        self.best_algorithm = None
        self.best_episode = -1
        self.best_model_path = None
        self.workpoints_hash = None

        # 删除保存的文件
        try:
            global_best_path = get_result_path(self.global_best_file)
            if os.path.exists(global_best_path):
                os.remove(global_best_path)
                print(f"🗑️  已删除全局最优结果文件")
        except Exception as e:
            print(f"⚠️  删除全局最优结果文件失败: {e}")
    
    def print_summary(self):
        """打印全局最优结果摘要"""
        print(f"\n" + "="*60)
        print("🏆 全局最优结果摘要")
        print("="*60)
        
        if self.best_makespan != float('inf'):
            print(f"最佳算法: {self.best_algorithm}")
            print(f"最佳完工时间: {self.best_makespan:.2f} 时间单位")
            print(f"任务数量: {len(self.best_schedule) if self.best_schedule else 0}")
            
            if self.best_episode >= 0:
                print(f"训练轮次: Episode {self.best_episode}")
            
            if self.best_model_path:
                print(f"模型路径: {self.best_model_path}")
            if self.workpoints_hash:
                print(f"工序配置: {self.workpoints_hash[:16]}...")
        else:
            print("暂无有效的最优结果")
        
        print("="*60)


# 全局实例
global_best_tracker = GlobalBestTracker()
