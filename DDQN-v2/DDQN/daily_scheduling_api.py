"""
每日调度系统的Web API接口
适用于：每天调用一次，系统自动调用，员工查看结果的场景
"""

from flask import Flask, request, jsonify, render_template_string
from gevent import pywsgi
import json
import logging
from datetime import datetime, timedelta
from daily_scheduling_ab_test import DailySchedulingService, DailySchedulingABTest
import pandas as pd

# 初始化Flask应用
app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化服务
scheduling_service = DailySchedulingService()
ab_test_manager = DailySchedulingABTest()


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "daily_scheduling_system",
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route('/api/daily-scheduling/run', methods=['POST'])
def run_daily_scheduling():
    """
    执行每日调度
    系统每天自动调用此接口
    """
    try:
        data = request.get_json()
        
        # 验证输入参数
        if not data or 'params' not in data:
            return jsonify({"error": "缺少必需的params参数"}), 400
        
        if len(data['params']) != 15:
            return jsonify({"error": "params必须包含15个数值"}), 400
        
        # 获取日期（可选参数，默认为今天）
        date = data.get('date', datetime.now().strftime("%Y-%m-%d"))
        
        # 执行调度
        result = scheduling_service.run_daily_scheduling(data['params'], date)
        
        logger.info(f"每日调度完成: {date}, 状态: {result['status']}")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"每日调度失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/daily-scheduling/results', methods=['GET'])
def get_scheduling_results():
    """
    获取调度结果
    员工和管理者查看调度结果
    """
    try:
        # 获取查询参数
        date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
        days = int(request.args.get('days', 7))  # 默认查看最近7天
        
        # 获取数据
        df = ab_test_manager.get_experiment_data(days)
        
        if df.empty:
            return jsonify({
                "status": "success",
                "message": "暂无调度数据",
                "results": []
            }), 200
        
        # 转换为前端友好的格式
        results = []
        for _, row in df.iterrows():
            schedule_details = json.loads(row['schedule_details']) if row['schedule_details'] else []
            
            results.append({
                "date": row['date'],
                "model_version": row['model_version'],
                "experiment_group": row['experiment_group'],
                "performance": {
                    "makespan": row['makespan'],
                    "resource_utilization": row['resource_utilization'],
                    "total_workers": row['total_workers'],
                    "execution_time": row['execution_time'],
                    "delayed_tasks": row['delayed_tasks'],
                    "overtime_hours": row['overtime_hours']
                },
                "schedule_details": schedule_details,
                "success": bool(row['success']),
                "employee_satisfaction": row['employee_satisfaction'] if row['employee_satisfaction'] > 0 else None
            })
        
        return jsonify({
            "status": "success",
            "results": results,
            "total": len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"获取调度结果失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/daily-scheduling/analysis', methods=['GET'])
def get_analysis():
    """
    获取A/B测试分析结果
    管理者查看实验效果
    """
    try:
        days = int(request.args.get('days', 30))
        
        # 获取分析结果
        analysis = ab_test_manager.analyze_experiment_results(days)
        
        return jsonify({
            "status": "success",
            "analysis": analysis,
            "period_days": days
        }), 200
        
    except Exception as e:
        logger.error(f"获取分析结果失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/daily-scheduling/report', methods=['GET'])
def get_daily_report():
    """
    获取每日报告
    包含今日结果和趋势分析
    """
    try:
        report = ab_test_manager.generate_daily_report()
        
        return jsonify({
            "status": "success",
            "report": report
        }), 200
        
    except Exception as e:
        logger.error(f"获取每日报告失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/daily-scheduling/feedback', methods=['POST'])
def submit_employee_feedback():
    """
    员工提交满意度反馈
    """
    try:
        data = request.get_json()
        
        if not data or 'date' not in data or 'satisfaction_score' not in data:
            return jsonify({"error": "缺少必需参数"}), 400
        
        date = data['date']
        satisfaction_score = float(data['satisfaction_score'])
        
        # 验证满意度评分范围
        if not (0 <= satisfaction_score <= 5):
            return jsonify({"error": "满意度评分必须在0-5之间"}), 400
        
        # 更新反馈
        ab_test_manager.update_employee_feedback(date, satisfaction_score)
        
        return jsonify({
            "status": "success",
            "message": "反馈提交成功"
        }), 200
        
    except Exception as e:
        logger.error(f"提交反馈失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ab-test/config', methods=['GET'])
def get_ab_test_config():
    """获取A/B测试配置"""
    try:
        return jsonify({
            "status": "success",
            "config": ab_test_manager.config
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/ab-test/config', methods=['POST'])
def update_ab_test_config():
    """更新A/B测试配置"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "缺少配置数据"}), 400
        
        # 更新配置
        ab_test_manager.config.update(data)
        ab_test_manager.save_config()
        
        logger.info("A/B测试配置已更新")
        
        return jsonify({
            "status": "success",
            "message": "配置更新成功"
        }), 200
        
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/dashboard')
def dashboard():
    """
    简单的仪表板页面
    员工和管理者查看调度结果
    """
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>每日调度系统 - 仪表板</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; 
                   box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .metric { display: inline-block; margin: 10px 20px; text-align: center; }
            .metric-value { font-size: 24px; font-weight: bold; color: #333; }
            .metric-label { font-size: 14px; color: #666; }
            .status-success { color: #28a745; }
            .status-warning { color: #ffc107; }
            .status-error { color: #dc3545; }
            .btn { padding: 10px 20px; background: #007bff; color: white; border: none; 
                  border-radius: 5px; cursor: pointer; margin: 5px; }
            .btn:hover { background: #0056b3; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f8f9fa; }
            .loading { text-align: center; padding: 20px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏭 每日调度系统仪表板</h1>
                <p>智能人员调度管理系统 - A/B测试版本</p>
            </div>
            
            <div class="card">
                <h2>📊 今日调度概览</h2>
                <div id="today-overview" class="loading">加载中...</div>
            </div>
            
            <div class="card">
                <h2>📈 最近7天趋势</h2>
                <div id="recent-trends" class="loading">加载中...</div>
            </div>
            
            <div class="card">
                <h2>🧪 A/B测试分析</h2>
                <div id="ab-analysis" class="loading">加载中...</div>
            </div>
            
            <div class="card">
                <h2>💬 满意度反馈</h2>
                <div>
                    <label>对今日调度方案的满意度 (1-5分):</label>
                    <input type="number" id="satisfaction" min="1" max="5" step="0.1" value="3">
                    <button class="btn" onclick="submitFeedback()">提交反馈</button>
                </div>
                <div id="feedback-message"></div>
            </div>
        </div>
        
        <script>
            // 加载今日概览
            async function loadTodayOverview() {
                try {
                    const response = await fetch('/api/daily-scheduling/report');
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        const report = data.report;
                        let html = `
                            <div class="metric">
                                <div class="metric-value">${report.date}</div>
                                <div class="metric-label">调度日期</div>
                            </div>
                        `;
                        
                        if (report.today_result) {
                            const result = report.today_result;
                            html += `
                                <div class="metric">
                                    <div class="metric-value ${result.success ? 'status-success' : 'status-error'}">
                                        ${result.makespan ? result.makespan.toFixed(1) : 'N/A'}
                                    </div>
                                    <div class="metric-label">完工时间</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-value">${(result.resource_utilization * 100).toFixed(1)}%</div>
                                    <div class="metric-label">资源利用率</div>
                                </div>
                                <div class="metric">
                                    <div class="metric-value">${result.model_used}</div>
                                    <div class="metric-label">使用模型</div>
                                </div>
                            `;
                        }
                        
                        document.getElementById('today-overview').innerHTML = html;
                    }
                } catch (error) {
                    document.getElementById('today-overview').innerHTML = '加载失败: ' + error.message;
                }
            }
            
            // 加载最近趋势
            async function loadRecentTrends() {
                try {
                    const response = await fetch('/api/daily-scheduling/results?days=7');
                    const data = await response.json();
                    
                    if (data.status === 'success' && data.results.length > 0) {
                        let html = '<table><tr><th>日期</th><th>模型版本</th><th>完工时间</th><th>资源利用率</th><th>状态</th></tr>';
                        
                        data.results.forEach(result => {
                            html += `
                                <tr>
                                    <td>${result.date}</td>
                                    <td>${result.model_version}</td>
                                    <td>${result.performance.makespan.toFixed(1)}</td>
                                    <td>${(result.performance.resource_utilization * 100).toFixed(1)}%</td>
                                    <td class="${result.success ? 'status-success' : 'status-error'}">
                                        ${result.success ? '成功' : '失败'}
                                    </td>
                                </tr>
                            `;
                        });
                        
                        html += '</table>';
                        document.getElementById('recent-trends').innerHTML = html;
                    } else {
                        document.getElementById('recent-trends').innerHTML = '暂无数据';
                    }
                } catch (error) {
                    document.getElementById('recent-trends').innerHTML = '加载失败: ' + error.message;
                }
            }
            
            // 加载A/B测试分析
            async function loadABAnalysis() {
                try {
                    const response = await fetch('/api/daily-scheduling/analysis?days=30');
                    const data = await response.json();
                    
                    if (data.status === 'success' && data.analysis) {
                        const analysis = data.analysis;
                        let html = '';
                        
                        // 显示各组表现
                        Object.keys(analysis).forEach(key => {
                            if (key !== 'comparison' && key !== 'statistical_test') {
                                const group = analysis[key];
                                html += `
                                    <div style="margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                                        <h4>${key} 组表现</h4>
                                        <p>样本数量: ${group.sample_size}</p>
                                        <p>平均完工时间: ${group.avg_makespan ? group.avg_makespan.toFixed(2) : 'N/A'}</p>
                                        <p>资源利用率: ${group.avg_resource_utilization ? (group.avg_resource_utilization * 100).toFixed(1) + '%' : 'N/A'}</p>
                                        <p>成功率: ${(group.success_rate * 100).toFixed(1)}%</p>
                                    </div>
                                `;
                            }
                        });
                        
                        // 显示对比结果
                        if (analysis.comparison) {
                            const comp = analysis.comparison;
                            html += `
                                <div style="background-color: #e7f3ff; padding: 10px; border-radius: 5px;">
                                    <h4>对比结果</h4>
                                    <p>性能改进: ${comp.improvement_percentage.toFixed(1)}%</p>
                                    <p>更优组: ${comp.better_group}</p>
                                    <p>样本充足: ${comp.sample_sufficient ? '是' : '否'}</p>
                                </div>
                            `;
                        }
                        
                        document.getElementById('ab-analysis').innerHTML = html;
                    } else {
                        document.getElementById('ab-analysis').innerHTML = '暂无分析数据';
                    }
                } catch (error) {
                    document.getElementById('ab-analysis').innerHTML = '加载失败: ' + error.message;
                }
            }
            
            // 提交满意度反馈
            async function submitFeedback() {
                try {
                    const satisfaction = document.getElementById('satisfaction').value;
                    const today = new Date().toISOString().split('T')[0];
                    
                    const response = await fetch('/api/daily-scheduling/feedback', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            date: today,
                            satisfaction_score: parseFloat(satisfaction)
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        document.getElementById('feedback-message').innerHTML = 
                            '<p style="color: green;">反馈提交成功！感谢您的评价。</p>';
                    } else {
                        document.getElementById('feedback-message').innerHTML = 
                            '<p style="color: red;">提交失败: ' + data.error + '</p>';
                    }
                } catch (error) {
                    document.getElementById('feedback-message').innerHTML = 
                        '<p style="color: red;">提交失败: ' + error.message + '</p>';
                }
            }
            
            // 页面加载时执行
            document.addEventListener('DOMContentLoaded', function() {
                loadTodayOverview();
                loadRecentTrends();
                loadABAnalysis();
            });
            
            // 每5分钟刷新一次数据
            setInterval(() => {
                loadTodayOverview();
                loadRecentTrends();
                loadABAnalysis();
            }, 300000);
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html_template)


if __name__ == '__main__':
    print("启动每日调度系统API服务...")
    print("功能包括:")
    print("- 每日自动调度 (POST /api/daily-scheduling/run)")
    print("- 调度结果查看 (GET /api/daily-scheduling/results)")
    print("- A/B测试分析 (GET /api/daily-scheduling/analysis)")
    print("- 员工反馈收集 (POST /api/daily-scheduling/feedback)")
    print("- 仪表板页面 (GET /dashboard)")
    print("- 服务运行在 http://localhost:5002")
    
    # 启动服务器
    server = pywsgi.WSGIServer(
        ('0.0.0.0', 5002),
        app,
        log=logging.getLogger('gevent')
    )
    
    server.serve_forever()


