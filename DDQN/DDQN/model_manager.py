"""
模型版本管理系统
支持模型注册、版本控制、性能跟踪和自动部署
"""

import os
import json
import pickle
import hashlib
import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """模型元数据"""
    model_id: str
    version: str
    algorithm_name: str
    training_params: Dict[str, Any]
    performance_metrics: Dict[str, float]
    training_time: str
    model_size: int
    description: str
    status: str  # 'training', 'validated', 'deployed', 'retired'
    created_by: str
    created_at: str
    model_path: str
    config_hash: str


class ModelVersionManager:
    """模型版本管理器"""
    
    def __init__(self, base_path: str = "./models"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # 创建目录结构
        self.models_dir = self.base_path / "models"
        self.metadata_dir = self.base_path / "metadata"
        self.configs_dir = self.base_path / "configs"
        
        for dir_path in [self.models_dir, self.metadata_dir, self.configs_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def register_model(self, 
                      model_path: str,
                      algorithm_name: str,
                      training_params: Dict[str, Any],
                      performance_metrics: Dict[str, float],
                      description: str = "",
                      created_by: str = "system") -> str:
        """注册新模型版本"""
        
        # 生成模型ID和版本
        config_hash = self._calculate_config_hash(training_params)
        model_id = f"{algorithm_name}_{config_hash[:8]}"
        version = self._generate_version(model_id)
        
        # 复制模型文件
        model_filename = f"{model_id}_v{version}.pth"
        target_path = self.models_dir / model_filename
        shutil.copy2(model_path, target_path)
        
        # 创建元数据
        metadata = ModelMetadata(
            model_id=model_id,
            version=version,
            algorithm_name=algorithm_name,
            training_params=training_params,
            performance_metrics=performance_metrics,
            training_time=str(training_params.get('training_episodes', 'unknown')),
            model_size=os.path.getsize(target_path),
            description=description,
            status='validated',
            created_by=created_by,
            created_at=datetime.datetime.now().isoformat(),
            model_path=str(target_path),
            config_hash=config_hash
        )
        
        # 保存元数据
        metadata_path = self.metadata_dir / f"{model_id}_v{version}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)
        
        logger.info(f"模型注册成功: {model_id} v{version}")
        return f"{model_id}_v{version}"
    
    def get_model_info(self, model_key: str) -> Optional[ModelMetadata]:
        """获取模型信息"""
        metadata_path = self.metadata_dir / f"{model_key}.json"
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return ModelMetadata(**data)
    
    def list_models(self, algorithm_name: Optional[str] = None) -> List[ModelMetadata]:
        """列出所有模型"""
        models = []
        for metadata_file in self.metadata_dir.glob("*.json"):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metadata = ModelMetadata(**data)
                
                if algorithm_name is None or metadata.algorithm_name == algorithm_name:
                    models.append(metadata)
        
        # 按创建时间排序
        models.sort(key=lambda x: x.created_at, reverse=True)
        return models
    
    def get_best_model(self, algorithm_name: str, metric: str = 'makespan') -> Optional[ModelMetadata]:
        """获取性能最佳的模型"""
        models = self.list_models(algorithm_name)
        if not models:
            return None
        
        # 根据指标排序（makespan越小越好）
        if metric == 'makespan':
            best_model = min(models, key=lambda x: x.performance_metrics.get(metric, float('inf')))
        else:
            best_model = max(models, key=lambda x: x.performance_metrics.get(metric, 0))
        
        return best_model
    
    def promote_model(self, model_key: str, status: str) -> bool:
        """提升模型状态"""
        metadata = self.get_model_info(model_key)
        if not metadata:
            return False
        
        metadata.status = status
        metadata_path = self.metadata_dir / f"{model_key}.json"
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, indent=2, ensure_ascii=False)
        
        logger.info(f"模型状态更新: {model_key} -> {status}")
        return True
    
    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """计算配置哈希值"""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _generate_version(self, model_id: str) -> str:
        """生成版本号"""
        existing_versions = []
        for metadata_file in self.metadata_dir.glob(f"{model_id}_v*.json"):
            version = metadata_file.stem.split('_v')[-1]
            existing_versions.append(int(version))
        
        if not existing_versions:
            return "1.0"
        
        latest_version = max(existing_versions)
        return f"{latest_version + 1}.0"


class ABTestManager:
    """A/B测试管理器"""
    
    def __init__(self, config_path: str = "./ab_test_config.json"):
        self.config_path = config_path
        self.load_config()
    
    def load_config(self):
        """加载A/B测试配置"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "experiments": {},
                "default_model": None
            }
    
    def save_config(self):
        """保存A/B测试配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def create_experiment(self, 
                         experiment_name: str,
                         model_a: str,
                         model_b: str,
                         traffic_split: Dict[str, float],
                         success_metric: str = "makespan",
                         duration_days: int = 7) -> str:
        """创建A/B测试实验"""
        
        experiment_config = {
            "name": experiment_name,
            "model_a": model_a,
            "model_b": model_b,
            "traffic_split": traffic_split,
            "success_metric": success_metric,
            "start_time": datetime.datetime.now().isoformat(),
            "duration_days": duration_days,
            "status": "active",
            "results": {
                "model_a": {"requests": 0, "metrics": {}},
                "model_b": {"requests": 0, "metrics": {}}
            }
        }
        
        self.config["experiments"][experiment_name] = experiment_config
        self.save_config()
        
        logger.info(f"A/B测试实验创建: {experiment_name}")
        return experiment_name
    
    def get_model_for_request(self, experiment_name: str, user_id: str = None) -> str:
        """根据A/B测试配置返回模型"""
        if experiment_name not in self.config["experiments"]:
            return self.config.get("default_model", "default")
        
        experiment = self.config["experiments"][experiment_name]
        if experiment["status"] != "active":
            return self.config.get("default_model", "default")
        
        # 基于用户ID的哈希值进行流量分配
        if user_id:
            hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            split_point = experiment["traffic_split"]["model_a"]
            
            if (hash_value % 100) < (split_point * 100):
                return experiment["model_a"]
            else:
                return experiment["model_b"]
        else:
            # 随机分配
            import random
            if random.random() < experiment["traffic_split"]["model_a"]:
                return experiment["model_a"]
            else:
                return experiment["model_b"]
    
    def record_result(self, 
                     experiment_name: str, 
                     model_key: str, 
                     metrics: Dict[str, float]):
        """记录实验结果"""
        if experiment_name not in self.config["experiments"]:
            return
        
        experiment = self.config["experiments"][experiment_name]
        model_group = "model_a" if model_key == experiment["model_a"] else "model_b"
        
        # 更新请求计数
        experiment["results"][model_group]["requests"] += 1
        
        # 更新指标
        for metric, value in metrics.items():
            if metric not in experiment["results"][model_group]["metrics"]:
                experiment["results"][model_group]["metrics"][metric] = []
            experiment["results"][model_group]["metrics"][metric].append(value)
        
        self.save_config()
    
    def get_experiment_results(self, experiment_name: str) -> Dict[str, Any]:
        """获取实验结果分析"""
        if experiment_name not in self.config["experiments"]:
            return {}
        
        experiment = self.config["experiments"][experiment_name]
        results = experiment["results"]
        
        analysis = {
            "experiment_name": experiment_name,
            "status": experiment["status"],
            "total_requests": {
                "model_a": results["model_a"]["requests"],
                "model_b": results["model_b"]["requests"]
            },
            "average_metrics": {}
        }
        
        # 计算平均指标
        for model_group in ["model_a", "model_b"]:
            analysis["average_metrics"][model_group] = {}
            for metric, values in results[model_group]["metrics"].items():
                if values:
                    analysis["average_metrics"][model_group][metric] = {
                        "mean": sum(values) / len(values),
                        "count": len(values),
                        "min": min(values),
                        "max": max(values)
                    }
        
        # 计算显著性（简单版本）
        success_metric = experiment["success_metric"]
        if (success_metric in analysis["average_metrics"]["model_a"] and 
            success_metric in analysis["average_metrics"]["model_b"]):
            
            mean_a = analysis["average_metrics"]["model_a"][success_metric]["mean"]
            mean_b = analysis["average_metrics"]["model_b"][success_metric]["mean"]
            
            improvement = ((mean_a - mean_b) / mean_b) * 100 if mean_b != 0 else 0
            analysis["improvement_percentage"] = improvement
            
            # 简单的显著性判断
            total_requests = (analysis["total_requests"]["model_a"] + 
                            analysis["total_requests"]["model_b"])
            analysis["is_significant"] = total_requests > 100 and abs(improvement) > 5
        
        return analysis


# 使用示例
if __name__ == "__main__":
    # 初始化管理器
    model_manager = ModelVersionManager()
    ab_manager = ABTestManager()
    
    # 注册模型示例
    training_params = {
        "episodes": 1000,
        "learning_rate": 0.001,
        "batch_size": 32,
        "epsilon_decay": 0.995
    }
    
    performance_metrics = {
        "makespan": 45.2,
        "resource_utilization": 0.85,
        "convergence_episode": 800
    }
    
    # model_key = model_manager.register_model(
    #     model_path="./best_model.pth",
    #     algorithm_name="DDQN",
    #     training_params=training_params,
    #     performance_metrics=performance_metrics,
    #     description="优化的DDQN模型，改进了奖励函数"
    # )
    
    # 创建A/B测试
    # ab_manager.create_experiment(
    #     experiment_name="ddqn_v1_vs_v2",
    #     model_a="DDQN_v1.0",
    #     model_b="DDQN_v2.0", 
    #     traffic_split={"model_a": 0.7, "model_b": 0.3},
    #     success_metric="makespan"
    # )
    
    print("模型版本管理系统初始化完成")
