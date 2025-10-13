"""
增强的Flask服务，集成模型版本管理和A/B测试
"""

from flask import Flask, request, jsonify, g
from gevent import pywsgi
import numpy as np
import logging
import time
import uuid
from typing import Dict, Any, Union, List
import base64
import torch
from model_manager import ModelVersionManager, ABTestManager
from RUN import RUN, DDQNAgent, FactoryEnvironment

# 初始化 Flask 应用
app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化管理器
model_manager = ModelVersionManager()
ab_manager = ABTestManager()

# 模型缓存
model_cache = {}


class ModelService:
    """模型服务类"""
    
    def __init__(self):
        self.current_models = {}
        self.load_active_models()
    
    def load_active_models(self):
        """加载激活的模型"""
        # 获取最佳模型作为默认模型
        best_model = model_manager.get_best_model("DDQN", "makespan")
        if best_model:
            ab_manager.config["default_model"] = f"{best_model.model_id}_v{best_model.version}"
            ab_manager.save_config()
    
    def get_model(self, model_key: str):
        """获取模型实例"""
        if model_key in model_cache:
            return model_cache[model_key]
        
        # 加载模型
        metadata = model_manager.get_model_info(model_key)
        if not metadata:
            logger.error(f"模型不存在: {model_key}")
            return None
        
        try:
            # 这里简化处理，实际应该根据模型路径加载
            # 由于您的DDQN模型比较复杂，这里提供一个框架
            logger.info(f"加载模型: {model_key}")
            model_cache[model_key] = metadata  # 简化存储元数据
            return metadata
        except Exception as e:
            logger.error(f"模型加载失败 {model_key}: {str(e)}")
            return None
    
    def run_algorithm_with_model(self, model_key: str, input_data: List[float]) -> Dict[str, Any]:
        """使用指定模型运行算法"""
        model = self.get_model(model_key)
        if not model:
            raise RuntimeError(f"无法加载模型: {model_key}")
        
        # 记录模型使用
        logger.info(f"使用模型 {model_key} 执行算法")
        
        # 执行算法 - 这里调用您原有的RUN函数
        # 实际应用中，您需要修改RUN函数以支持加载特定模型
        result, img = RUN(input_data)
        
        return {
            "schedule_details": result,
            "plot_image": base64.b64encode(img.getvalue()).decode('utf-8'),
            "model_info": {
                "model_key": model_key,
                "version": model.version,
                "algorithm": model.algorithm_name
            }
        }


model_service = ModelService()


@app.before_request
def before_request():
    """请求前处理"""
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()
    logger.info(f"请求开始 [{g.request_id}]: {request.method} {request.path}")


@app.after_request
def after_request(response):
    """请求后处理"""
    duration = time.time() - g.start_time
    logger.info(f"请求完成 [{g.request_id}]: {response.status_code}, 耗时: {duration:.2f}s")
    
    # 添加CORS头
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST, GET')
    return response


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "models_loaded": len(model_cache)
    }), 200


@app.route('/run_algorithm', methods=['POST'])
def run_algorithm():
    """运行算法 - 支持A/B测试"""
    try:
        # 获取请求数据
        input_data = request.get_json()
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400
        
        # 验证参数
        if 'params' not in input_data or not isinstance(input_data['params'], list):
            return jsonify({"error": "params must be a list"}), 400
        
        if len(input_data['params']) != 15:
            return jsonify({"error": "params must contain exactly 15 values"}), 400
        
        # 获取实验配置和用户ID
        experiment_name = input_data.get('experiment', 'default')
        user_id = input_data.get('user_id', g.request_id)
        
        # A/B测试模型选择
        model_key = ab_manager.get_model_for_request(experiment_name, user_id)
        logger.info(f"A/B测试选择模型: {model_key} for experiment: {experiment_name}")
        
        # 执行算法
        start_time = time.time()
        result = model_service.run_algorithm_with_model(model_key, input_data['params'])
        execution_time = time.time() - start_time
        
        # 提取性能指标
        makespan = extract_makespan_from_result(result)
        
        # 记录A/B测试结果
        if experiment_name != 'default':
            ab_manager.record_result(
                experiment_name=experiment_name,
                model_key=model_key,
                metrics={
                    "makespan": makespan,
                    "execution_time": execution_time
                }
            )
        
        # 返回结果
        response_data = {
            "status": "success",
            "result": result,
            "performance": {
                "makespan": makespan,
                "execution_time": execution_time
            },
            "experiment_info": {
                "experiment": experiment_name,
                "model_used": model_key,
                "user_id": user_id
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"算法执行失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/models', methods=['GET'])
def list_models():
    """列出所有模型"""
    try:
        algorithm = request.args.get('algorithm', 'DDQN')
        models = model_manager.list_models(algorithm)
        
        model_list = []
        for model in models:
            model_list.append({
                "model_key": f"{model.model_id}_v{model.version}",
                "algorithm": model.algorithm_name,
                "version": model.version,
                "status": model.status,
                "performance": model.performance_metrics,
                "created_at": model.created_at,
                "description": model.description
            })
        
        return jsonify({
            "status": "success",
            "models": model_list,
            "total": len(model_list)
        }), 200
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/models/register', methods=['POST'])
def register_model():
    """注册新模型"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        required_fields = ['model_path', 'algorithm_name', 'training_params', 'performance_metrics']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # 注册模型
        model_key = model_manager.register_model(
            model_path=data['model_path'],
            algorithm_name=data['algorithm_name'],
            training_params=data['training_params'],
            performance_metrics=data['performance_metrics'],
            description=data.get('description', ''),
            created_by=data.get('created_by', 'api')
        )
        
        return jsonify({
            "status": "success",
            "model_key": model_key,
            "message": "模型注册成功"
        }), 200
        
    except Exception as e:
        logger.error(f"模型注册失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/experiments', methods=['POST'])
def create_experiment():
    """创建A/B测试实验"""
    try:
        data = request.get_json()
        
        # 验证参数
        required_fields = ['experiment_name', 'model_a', 'model_b', 'traffic_split']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # 创建实验
        experiment_name = ab_manager.create_experiment(
            experiment_name=data['experiment_name'],
            model_a=data['model_a'],
            model_b=data['model_b'],
            traffic_split=data['traffic_split'],
            success_metric=data.get('success_metric', 'makespan'),
            duration_days=data.get('duration_days', 7)
        )
        
        return jsonify({
            "status": "success",
            "experiment_name": experiment_name,
            "message": "A/B测试实验创建成功"
        }), 200
        
    except Exception as e:
        logger.error(f"创建实验失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/experiments/<experiment_name>/results', methods=['GET'])
def get_experiment_results(experiment_name):
    """获取实验结果"""
    try:
        results = ab_manager.get_experiment_results(experiment_name)
        
        if not results:
            return jsonify({"error": "Experiment not found"}), 404
        
        return jsonify({
            "status": "success",
            "results": results
        }), 200
        
    except Exception as e:
        logger.error(f"获取实验结果失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/experiments', methods=['GET'])
def list_experiments():
    """列出所有实验"""
    try:
        experiments = []
        for name, config in ab_manager.config["experiments"].items():
            experiments.append({
                "name": name,
                "status": config["status"],
                "model_a": config["model_a"],
                "model_b": config["model_b"],
                "traffic_split": config["traffic_split"],
                "start_time": config["start_time"],
                "duration_days": config["duration_days"]
            })
        
        return jsonify({
            "status": "success",
            "experiments": experiments,
            "total": len(experiments)
        }), 200
        
    except Exception as e:
        logger.error(f"获取实验列表失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


def extract_makespan_from_result(result: Dict[str, Any]) -> float:
    """从结果中提取makespan"""
    try:
        # 从调度详情中提取makespan
        schedule_details = result.get('schedule_details', [])
        if schedule_details:
            # 假设最后一个任务的结束时间就是makespan
            max_end_time = max([task.get('end', 0) for task in schedule_details])
            return float(max_end_time)
        return 0.0
    except Exception as e:
        logger.warning(f"无法提取makespan: {str(e)}")
        return 0.0


if __name__ == '__main__':
    # 生产环境配置
    app.config.update(
        DEBUG=False,
        JSONIFY_PRETTYPRINT_REGULAR=False
    )
    
    # 启动服务器
    server = pywsgi.WSGIServer(
        ('0.0.0.0', 5001),
        app,
        log=logging.getLogger('gevent')
    )
    
    print("增强的算法服务启动，监听端口 5001...")
    print("功能包括：模型版本管理、A/B测试、性能监控")
    logger.info("Starting enhanced server on http://0.0.0.0:5001")
    server.serve_forever()
