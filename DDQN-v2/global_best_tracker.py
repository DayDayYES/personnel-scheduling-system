# -*- coding: utf-8 -*-
"""
全局最优结果跟踪器 - 跨算法保存最佳调度方案
"""

import pickle
import os
from config import get_result_path


class GlobalBestTracker:
    """全局最优结果跟踪器"""
    
    def __init__(self):
        self.best_makespan = float('inf')
        self.best_schedule = None
        self.best_algorithm = None
        self.best_episode = -1
        self.best_model_path = None
        self.global_best_file = "global_best_result.pkl"
        
        # 尝试加载已存在的全局最优结果
        self.load_global_best()
    
    def update_best_result(self, schedule, makespan, algorithm_name, episode=None, model_path=None):
        """
        更新全局最优结果
        
        Args:
            schedule: 调度方案
            makespan: 完工时间
            algorithm_name: 算法名称 ('ddqn', 'enhanced_ddqn', 'greedy')
            episode: 训练轮次 (可选)
            model_path: 模型文件路径 (可选)
        
        Returns:
            bool: 是否更新了最优结果
        """
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
                'model_path': self.best_model_path
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
        else:
            print("暂无有效的最优结果")
        
        print("="*60)


# 全局实例
global_best_tracker = GlobalBestTracker()
