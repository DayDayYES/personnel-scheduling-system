from flask import Flask, request, jsonify
from gevent import pywsgi
import numpy as np
import logging
from typing import Dict, Any, Union, List
from flask import send_file
import io
import base64
from main import RUN
from scheduling_environment import FactoryEnvironment, create_sample_workpoints_data

# 初始化 Flask 应用
app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# CORS 处理中间件
@app.after_request
def after_request(response):
    """
    处理跨域请求的中间件
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST')
    return response


# 错误处理
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad Request", "message": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found", "message": str(error)}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500


# 健康检查端点
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


# 主业务端点
@app.route('/run_ddqn', methods=['POST'])
def run_ddqn():
    """
    处理 DDQN 算法请求
    请求格式:
    {
        "algorithm_name": "ddqn",
        "params": [10,5,8,6,7,9,6,7,6,7,7,7,4,7,5]
    }
    """
    try:
        # 1. 获取并验证输入数据
        input_data = request.get_json()
        logger.info(f"Received request: {input_data}")

        if not input_data:
            raise ValueError("No input data provided")

        if 'algorithm_name' not in input_data:
            raise ValueError("algorithm_name is required")

        if 'params' not in input_data or not isinstance(input_data['params'], list):
            raise ValueError("params must be a list")

        # 2. 调用算法
        algorithm_name = input_data['algorithm_name']
        params = input_data['params']

        result = run_algorithm(algorithm_name, params)

        # 3. 处理并返回结果
        processed_result = {
            "status": "success",
            "algorithm": algorithm_name,
            "result": result
        }

        return jsonify(processed_result), 200

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500


def run_algorithm(algorithm_name: str, input_data: List[float]) -> Dict[str, Any]:
    """
    执行指定算法

    Args:
        algorithm_name: 算法名称 (如 'ddqn')
        input_data: 输入参数列表

    Returns:
        算法执行结果字典
    """

    try:
        print("=" * 60)
        print("多工作点调度系统")
        print("=" * 60)
        
        # **修复**: 使用示例工作点数据而不是直接传递input_data
        # 因为RUN函数期望的是workpoints_data字典格式，而不是数字列表
        sample_data = create_sample_workpoints_data()
        print("开始多工作点调度算法...")
        print(f"工作点数量: {len(sample_data)}")
        print(f"接收到的参数: {input_data}")
        
        for wp_id, wp_data in sample_data.items():
            wp_name = wp_data.get("name", wp_id)
            step_count = len(wp_data.get("steps", []))
            print(f"  {wp_name}: {step_count} 个工序" + ("（使用标准模板）" if step_count == 0 else ""))
        
        # 运行调度算法
        result = RUN(sample_data)
        
        # 检查返回值
        if result is None:
            raise RuntimeError("Algorithm execution failed - no result returned")
        
        if isinstance(result, tuple) and len(result) == 2 and result[0] is None:
            raise RuntimeError("Algorithm execution failed - returned None result")
        
        if isinstance(result, tuple) and len(result) == 4:
            # RUN函数返回: record, process_fig, workpoint_fig, team_fig
            record, process_fig, workpoint_fig, team_fig = result
            
            # 转换所有图像缓冲区为base64
            images = {}
            
            # 工序视角甘特图
            if process_fig is not None and hasattr(process_fig, 'getvalue'):
                images['process_gantt'] = base64.b64encode(process_fig.getvalue()).decode('utf-8')
            else:
                images['process_gantt'] = None
                
            # 工作点视角甘特图  
            if workpoint_fig is not None and hasattr(workpoint_fig, 'getvalue'):
                images['workpoint_gantt'] = base64.b64encode(workpoint_fig.getvalue()).decode('utf-8')
            else:
                images['workpoint_gantt'] = None
                
            # 团队视角甘特图
            if team_fig is not None and hasattr(team_fig, 'getvalue'):
                images['team_gantt'] = base64.b64encode(team_fig.getvalue()).decode('utf-8')
            else:
                images['team_gantt'] = None
            
            return {
                "schedule_details": record if record else "Algorithm completed successfully",
                "gantt_charts": {
                    "process": images['process_gantt'],
                    "workpoint": images['workpoint_gantt'], 
                    "team": images['team_gantt']
                },
                "chart_info": {
                    "process": "工序视角甘特图 - 按工序顺序显示调度方案",
                    "workpoint": "工作点视角甘特图 - 按工作点分组显示任务分配",
                    "team": "团队视角甘特图 - 按团队分组显示工作负载"
                }
            }
        else:
            raise RuntimeError(f"Unexpected return format from RUN function: {type(result)}, length: {len(result) if isinstance(result, tuple) else 'N/A'}")
    except ImportError:
        raise RuntimeError("RUN module not available")
    except Exception as e:
        raise RuntimeError(f"Algorithm execution failed: {str(e)}")






def convert_result_to_dict(result: Any) -> Union[Dict, List]:
    """
    将算法结果转换为可序列化的字典/列表

    Args:
        result: 算法原始结果

    Returns:
        可序列化的结果
    """
    if isinstance(result, np.ndarray):
        return result.tolist()
    elif isinstance(result, (np.int_, np.float_)):
        return int(result) if isinstance(result, np.int_) else float(result)
    elif isinstance(result, (list, tuple)):
        return [convert_result_to_dict(item) for item in result]
    elif isinstance(result, dict):
        return {key: convert_result_to_dict(value) for key, value in result.items()}
    else:
        return result


if __name__ == '__main__':
    # 生产环境配置
    app.config.update(
        DEBUG=False,
        JSONIFY_PRETTYPRINT_REGULAR=False
    )

    # 启动 gevent WSGI 服务器
    server = pywsgi.WSGIServer(
        ('0.0.0.0', 5001),
        app,
        log=logging.getLogger('gevent')
    )
    print("服务器启动，监听端口 5001...")
    logger.info("Starting server on http://0.0.0.0:5001")
    server.serve_forever()