from flask import Flask, request, jsonify
from gevent import pywsgi
import numpy as np
import logging
from typing import Dict, Any, Union, List
from flask import send_file
import io
import base64
from RUN import RUN

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
    # 初始化处理时间矩阵
    process_time = initialize_process_time()

    # 用输入数据填充矩阵
    process_time = fill_process_time(process_time, input_data)

    # 调用 RUN 模块 (假设 RUN() 是你实现的算法)
    try:
         # 延迟导入以避免循环依赖
        result, img = RUN(input_data)  # 假设 RUN 可以接受参数
        #print(result)
        # 转换结果为可序列化格式
        return {
            "schedule_details": result,
            "plot_image": base64.b64encode(img.getvalue()).decode('utf-8')
        }
    except ImportError:
        raise RuntimeError("RUN module not available")
    except Exception as e:
        raise RuntimeError(f"Algorithm execution failed: {str(e)}")


def initialize_process_time() -> List[List[List[float]]]:
    """
    初始化处理时间矩阵
    """
    return [
        [
            [10, 999.0, 999.0, 999.0, 999.0, 999.0],
            [999.0, 5, 999.0, 999.0, 999.0, 999.0],
            [999.0, 8, 999.0, 999.0, 999.0, 999.0],
            [999.0, 999.0, 6, 999.0, 999.0, 999.0],
            [999.0, 999.0, 7, 999.0, 999.0, 999.0],
            [999.0, 999.0, 999.0, 9, 999.0, 999.0],
            [999.0, 999.0, 999.0, 999.0, 6, 999.0],
            [999.0, 999.0, 999.0, 999.0, 7, 999.0],
            [999.0, 999.0, 999.0, 999.0, 6, 999.0],
            [999.0, 999.0, 7, 999.0, 999.0, 999.0],
            [999.0, 999.0, 7, 999.0, 999.0, 999.0],
            [999.0, 999.0, 7, 999.0, 999.0, 999.0],
            [999.0, 999.0, 4, 999.0, 999.0, 999.0],
            [999.0, 999.0, 999.0, 999.0, 999.0, 7],
            [999.0, 999.0, 5, 999.0, 999.0, 999.0]
        ]
    ]


def fill_process_time(matrix: List[List[List[float]]], values: List[float]) -> List[List[List[float]]]:
    """
    用输入值填充处理时间矩阵

    Args:
        matrix: 原始矩阵
        values: 输入值列表

    Returns:
        填充后的新矩阵
    """
    value_index = 0
    new_matrix = [row[:] for row in matrix[0]]  # 创建深拷贝

    for i in range(len(new_matrix)):
        for j in range(len(new_matrix[i])):
            if new_matrix[i][j] != 999.0:
                if value_index >= len(values):
                    raise ValueError("Not enough values provided")
                new_matrix[i][j] = values[value_index]
                value_index += 1

    if value_index < len(values):
        raise ValueError("Too many values provided")

    return [new_matrix]


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