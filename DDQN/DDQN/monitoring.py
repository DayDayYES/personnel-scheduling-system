"""
模型性能监控和分析工具
"""

import json
import time
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


@dataclass
class PerformanceRecord:
    """性能记录"""
    timestamp: str
    model_key: str
    experiment: str
    user_id: str
    makespan: float
    execution_time: float
    input_params: List[float]
    success: bool
    error_message: Optional[str] = None


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, db_path: str = "./performance.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model_key TEXT NOT NULL,
            experiment TEXT NOT NULL,
            user_id TEXT NOT NULL,
            makespan REAL NOT NULL,
            execution_time REAL NOT NULL,
            input_params TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            error_message TEXT
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON performance_records(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_key ON performance_records(model_key)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_experiment ON performance_records(experiment)')
        
        conn.commit()
        conn.close()
    
    def record_performance(self, record: PerformanceRecord):
        """记录性能数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO performance_records 
        (timestamp, model_key, experiment, user_id, makespan, execution_time, input_params, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.timestamp,
            record.model_key,
            record.experiment,
            record.user_id,
            record.makespan,
            record.execution_time,
            json.dumps(record.input_params),
            record.success,
            record.error_message
        ))
        
        conn.commit()
        conn.close()
    
    def get_performance_data(self, 
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None,
                           model_key: Optional[str] = None,
                           experiment: Optional[str] = None) -> pd.DataFrame:
        """获取性能数据"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM performance_records WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        if model_key:
            query += " AND model_key = ?"
            params.append(model_key)
        
        if experiment:
            query += " AND experiment = ?"
            params.append(experiment)
        
        query += " ORDER BY timestamp DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def generate_performance_report(self, 
                                  days: int = 7,
                                  output_path: str = "./performance_report.html") -> str:
        """生成性能报告"""
        # 获取最近N天的数据
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        df = self.get_performance_data(
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
        
        if df.empty:
            return "没有性能数据"
        
        # 生成分析报告
        report = self._analyze_performance_data(df)
        
        # 生成图表
        self._generate_performance_charts(df)
        
        # 生成HTML报告
        html_report = self._generate_html_report(report, days)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        logger.info(f"性能报告已生成: {output_path}")
        return output_path
    
    def _analyze_performance_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析性能数据"""
        analysis = {}
        
        # 基本统计
        analysis['total_requests'] = len(df)
        analysis['success_rate'] = (df['success'].sum() / len(df)) * 100
        analysis['avg_makespan'] = df['makespan'].mean()
        analysis['avg_execution_time'] = df['execution_time'].mean()
        
        # 按模型分组分析
        model_stats = df.groupby('model_key').agg({
            'makespan': ['count', 'mean', 'std', 'min', 'max'],
            'execution_time': ['mean', 'std'],
            'success': 'sum'
        }).round(2)
        analysis['model_performance'] = model_stats.to_dict()
        
        # 按实验分组分析
        if 'experiment' in df.columns:
            exp_stats = df.groupby('experiment').agg({
                'makespan': ['count', 'mean', 'std'],
                'execution_time': ['mean'],
                'success': 'sum'
            }).round(2)
            analysis['experiment_performance'] = exp_stats.to_dict()
        
        # 时间趋势分析
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        hourly_stats = df.groupby('hour').agg({
            'makespan': 'mean',
            'execution_time': 'mean'
        }).round(2)
        analysis['hourly_trends'] = hourly_stats.to_dict()
        
        return analysis
    
    def _generate_performance_charts(self, df: pd.DataFrame):
        """生成性能图表"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('模型性能监控报告', fontsize=16)
        
        # 1. Makespan分布
        axes[0, 0].hist(df['makespan'], bins=20, alpha=0.7, color='skyblue')
        axes[0, 0].set_title('Makespan分布')
        axes[0, 0].set_xlabel('Makespan')
        axes[0, 0].set_ylabel('频次')
        
        # 2. 执行时间分布
        axes[0, 1].hist(df['execution_time'], bins=20, alpha=0.7, color='lightgreen')
        axes[0, 1].set_title('执行时间分布')
        axes[0, 1].set_xlabel('执行时间(秒)')
        axes[0, 1].set_ylabel('频次')
        
        # 3. 模型性能对比
        if len(df['model_key'].unique()) > 1:
            model_perf = df.groupby('model_key')['makespan'].mean()
            axes[1, 0].bar(model_perf.index, model_perf.values, color='orange')
            axes[1, 0].set_title('各模型平均Makespan对比')
            axes[1, 0].set_xlabel('模型')
            axes[1, 0].set_ylabel('平均Makespan')
            axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 4. 时间趋势
        df['datetime'] = pd.to_datetime(df['timestamp'])
        df_sorted = df.sort_values('datetime')
        axes[1, 1].plot(df_sorted['datetime'], df_sorted['makespan'], alpha=0.7)
        axes[1, 1].set_title('Makespan时间趋势')
        axes[1, 1].set_xlabel('时间')
        axes[1, 1].set_ylabel('Makespan')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('./performance_charts.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_html_report(self, analysis: Dict[str, Any], days: int) -> str:
        """生成HTML报告"""
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>模型性能监控报告</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background-color: #e8f4f8; border-radius: 5px; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>模型性能监控报告</h1>
                <p>报告时间范围: 最近 {days} 天</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h2>总体指标</h2>
            <div class="metric">
                <h3>总请求数</h3>
                <p>{analysis.get('total_requests', 0)}</p>
            </div>
            <div class="metric">
                <h3>成功率</h3>
                <p class="{'success' if analysis.get('success_rate', 0) > 95 else 'warning'}">{analysis.get('success_rate', 0):.1f}%</p>
            </div>
            <div class="metric">
                <h3>平均Makespan</h3>
                <p>{analysis.get('avg_makespan', 0):.2f}</p>
            </div>
            <div class="metric">
                <h3>平均执行时间</h3>
                <p>{analysis.get('avg_execution_time', 0):.2f}秒</p>
            </div>
            
            <h2>性能图表</h2>
            <div class="chart">
                <img src="performance_charts.png" alt="性能图表" style="max-width: 100%;">
            </div>
            
            <h2>模型性能详情</h2>
            <p>详细的模型性能对比和分析数据...</p>
            
            <h2>建议</h2>
            <ul>
                {'<li class="success">系统运行正常</li>' if analysis.get('success_rate', 0) > 95 else '<li class="warning">成功率偏低，需要关注</li>'}
                {'<li class="success">性能表现良好</li>' if analysis.get('avg_makespan', float('inf')) < 50 else '<li class="warning">平均Makespan偏高，建议优化</li>'}
            </ul>
        </body>
        </html>
        """
        
        return html_template


class ABTestAnalyzer:
    """A/B测试分析器"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
    
    def analyze_experiment(self, experiment_name: str, days: int = 7) -> Dict[str, Any]:
        """分析A/B测试实验"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        df = self.monitor.get_performance_data(
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            experiment=experiment_name
        )
        
        if df.empty:
            return {"error": "没有实验数据"}
        
        # 按模型分组分析
        results = {}
        for model_key in df['model_key'].unique():
            model_data = df[df['model_key'] == model_key]
            
            results[model_key] = {
                "sample_size": len(model_data),
                "success_rate": (model_data['success'].sum() / len(model_data)) * 100,
                "avg_makespan": model_data['makespan'].mean(),
                "std_makespan": model_data['makespan'].std(),
                "avg_execution_time": model_data['execution_time'].mean(),
                "min_makespan": model_data['makespan'].min(),
                "max_makespan": model_data['makespan'].max()
            }
        
        # 统计显著性检验
        if len(results) == 2:
            models = list(results.keys())
            model_a_data = df[df['model_key'] == models[0]]['makespan']
            model_b_data = df[df['model_key'] == models[1]]['makespan']
            
            # 简单的t检验（需要scipy.stats.ttest_ind）
            try:
                from scipy.stats import ttest_ind
                t_stat, p_value = ttest_ind(model_a_data, model_b_data)
                
                results['statistical_test'] = {
                    "t_statistic": t_stat,
                    "p_value": p_value,
                    "is_significant": p_value < 0.05,
                    "confidence_level": 0.95
                }
            except ImportError:
                results['statistical_test'] = {
                    "error": "需要安装scipy进行统计检验"
                }
        
        return results
    
    def generate_ab_test_report(self, experiment_name: str, days: int = 7) -> str:
        """生成A/B测试报告"""
        analysis = self.analyze_experiment(experiment_name, days)
        
        # 生成可视化图表
        self._generate_ab_test_charts(experiment_name, days)
        
        # 生成报告
        report_path = f"./ab_test_report_{experiment_name}.html"
        html_content = self._generate_ab_test_html(analysis, experiment_name, days)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path
    
    def _generate_ab_test_charts(self, experiment_name: str, days: int):
        """生成A/B测试图表"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        df = self.monitor.get_performance_data(
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            experiment=experiment_name
        )
        
        if df.empty:
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle(f'A/B测试分析: {experiment_name}', fontsize=14)
        
        # 1. Makespan分布对比
        for model_key in df['model_key'].unique():
            model_data = df[df['model_key'] == model_key]
            axes[0].hist(model_data['makespan'], alpha=0.7, label=model_key, bins=15)
        
        axes[0].set_title('Makespan分布对比')
        axes[0].set_xlabel('Makespan')
        axes[0].set_ylabel('频次')
        axes[0].legend()
        
        # 2. 平均性能对比
        model_perf = df.groupby('model_key')['makespan'].agg(['mean', 'std'])
        axes[1].bar(model_perf.index, model_perf['mean'], 
                   yerr=model_perf['std'], capsize=5, alpha=0.7)
        axes[1].set_title('平均Makespan对比')
        axes[1].set_xlabel('模型')
        axes[1].set_ylabel('平均Makespan')
        
        plt.tight_layout()
        plt.savefig(f'./ab_test_charts_{experiment_name}.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_ab_test_html(self, analysis: Dict[str, Any], experiment_name: str, days: int) -> str:
        """生成A/B测试HTML报告"""
        # 简化的HTML模板
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>A/B测试报告 - {experiment_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .result {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .winner {{ background-color: #d4edda; border-color: #c3e6cb; }}
                .chart {{ text-align: center; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>A/B测试报告: {experiment_name}</h1>
                <p>分析时间范围: 最近 {days} 天</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h2>实验结果</h2>
            {self._format_ab_results(analysis)}
            
            <div class="chart">
                <img src="ab_test_charts_{experiment_name}.png" alt="A/B测试图表" style="max-width: 100%;">
            </div>
            
            <h2>结论与建议</h2>
            {self._generate_ab_conclusions(analysis)}
        </body>
        </html>
        """
        
        return html_content
    
    def _format_ab_results(self, analysis: Dict[str, Any]) -> str:
        """格式化A/B测试结果"""
        if "error" in analysis:
            return f"<p>错误: {analysis['error']}</p>"
        
        results_html = ""
        for model_key, stats in analysis.items():
            if model_key == 'statistical_test':
                continue
                
            results_html += f"""
            <div class="result">
                <h3>{model_key}</h3>
                <p>样本数量: {stats['sample_size']}</p>
                <p>成功率: {stats['success_rate']:.1f}%</p>
                <p>平均Makespan: {stats['avg_makespan']:.2f} ± {stats['std_makespan']:.2f}</p>
                <p>执行时间: {stats['avg_execution_time']:.2f}秒</p>
            </div>
            """
        
        return results_html
    
    def _generate_ab_conclusions(self, analysis: Dict[str, Any]) -> str:
        """生成A/B测试结论"""
        if "error" in analysis or len(analysis) < 2:
            return "<p>数据不足，无法得出结论</p>"
        
        # 找到最佳模型
        models = [k for k in analysis.keys() if k != 'statistical_test']
        best_model = min(models, key=lambda x: analysis[x]['avg_makespan'])
        
        conclusions = f"""
        <ul>
            <li><strong>推荐模型:</strong> {best_model}</li>
            <li><strong>性能提升:</strong> {self._calculate_improvement(analysis, models)}</li>
        """
        
        if 'statistical_test' in analysis and analysis['statistical_test'].get('is_significant'):
            conclusions += "<li><strong>统计显著性:</strong> 结果具有统计显著性 (p < 0.05)</li>"
        else:
            conclusions += "<li><strong>统计显著性:</strong> 结果不具有统计显著性，建议继续收集数据</li>"
        
        conclusions += "</ul>"
        
        return conclusions
    
    def _calculate_improvement(self, analysis: Dict[str, Any], models: List[str]) -> str:
        """计算性能改进"""
        if len(models) != 2:
            return "无法计算"
        
        model_a_perf = analysis[models[0]]['avg_makespan']
        model_b_perf = analysis[models[1]]['avg_makespan']
        
        improvement = ((model_a_perf - model_b_perf) / model_a_perf) * 100
        
        if improvement > 0:
            return f"{models[1]} 比 {models[0]} 性能提升 {improvement:.1f}%"
        else:
            return f"{models[0]} 比 {models[1]} 性能提升 {abs(improvement):.1f}%"


# 使用示例
if __name__ == "__main__":
    # 初始化监控器
    monitor = PerformanceMonitor()
    analyzer = ABTestAnalyzer(monitor)
    
    # 模拟记录一些性能数据
    import random
    
    for i in range(100):
        record = PerformanceRecord(
            timestamp=datetime.now().isoformat(),
            model_key=random.choice(["DDQN_v1.0", "DDQN_v2.0"]),
            experiment="test_experiment",
            user_id=f"user_{i}",
            makespan=random.uniform(40, 60),
            execution_time=random.uniform(1, 5),
            input_params=[random.uniform(1, 10) for _ in range(15)],
            success=random.random() > 0.05  # 95% 成功率
        )
        monitor.record_performance(record)
    
    # 生成报告
    print("生成性能报告...")
    report_path = monitor.generate_performance_report(days=7)
    print(f"报告已生成: {report_path}")
    
    print("生成A/B测试报告...")
    ab_report_path = analyzer.generate_ab_test_report("test_experiment", days=7)
    print(f"A/B测试报告已生成: {ab_report_path}")
