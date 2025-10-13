"""
针对每日调度场景的A/B测试系统
场景特点：
1. 每天只调用一次算法
2. 系统自动调用，不是用户主动调用
3. 员工只能查看调度结果
4. 需要长期数据积累来评估算法效果
"""

import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass, asdict
import hashlib
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DailySchedulingRecord:
    """每日调度记录"""
    date: str                    # 调度日期
    model_version: str          # 使用的模型版本
    experiment_group: str       # 实验分组（A/B）
    input_params: List[float]   # 输入参数
    makespan: float            # 完工时间
    resource_utilization: float # 资源利用率
    total_workers: int         # 总人数
    execution_time: float      # 算法执行时间
    schedule_details: List[Dict] # 详细调度方案
    success: bool              # 是否成功执行
    
    # 业务指标
    delayed_tasks: int = 0     # 延迟任务数
    overtime_hours: float = 0.0 # 加班时间
    employee_satisfaction: float = 0.0 # 员工满意度（后续收集）


class DailySchedulingABTest:
    """每日调度A/B测试管理器"""
    
    def __init__(self, db_path: str = "./daily_scheduling_ab_test.db"):
        self.db_path = db_path
        self.config_path = "./daily_ab_config.json"
        self.init_database()
        self.load_config()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_scheduling_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            model_version TEXT NOT NULL,
            experiment_group TEXT NOT NULL,
            input_params TEXT NOT NULL,
            makespan REAL NOT NULL,
            resource_utilization REAL NOT NULL,
            total_workers INTEGER NOT NULL,
            execution_time REAL NOT NULL,
            schedule_details TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            delayed_tasks INTEGER DEFAULT 0,
            overtime_hours REAL DEFAULT 0.0,
            employee_satisfaction REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON daily_scheduling_records(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_experiment_group ON daily_scheduling_records(experiment_group)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_version ON daily_scheduling_records(model_version)')
        
        conn.commit()
        conn.close()
    
    def load_config(self):
        """加载A/B测试配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 默认配置
            self.config = {
                "current_experiment": {
                    "name": "default_vs_optimized",
                    "start_date": datetime.now().strftime("%Y-%m-%d"),
                    "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "model_a": "DDQN_baseline_v1.0",
                    "model_b": "DDQN_optimized_v2.0",
                    "allocation_strategy": "calendar_based",  # 基于日期的分配策略
                    "allocation_ratio": {"group_a": 0.5, "group_b": 0.5},
                    "status": "active"
                },
                "evaluation_metrics": {
                    "primary": "makespan",
                    "secondary": ["resource_utilization", "delayed_tasks", "overtime_hours"]
                },
                "minimum_days": 14,  # 最少运行天数
                "significance_level": 0.05
            }
            self.save_config()
    
    def save_config(self):
        """保存配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_model_for_today(self, date: str = None) -> tuple:
        """获取今日应使用的模型和实验分组"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        experiment = self.config["current_experiment"]
        
        # 检查实验是否在有效期内
        if not self._is_experiment_active(date):
            return experiment["model_a"], "control"  # 默认使用对照组
        
        # 基于日期的确定性分配
        if experiment["allocation_strategy"] == "calendar_based":
            return self._calendar_based_allocation(date)
        
        # 基于日期哈希的分配
        elif experiment["allocation_strategy"] == "hash_based":
            return self._hash_based_allocation(date)
        
        else:
            # 默认交替分配
            return self._alternating_allocation(date)
    
    def _is_experiment_active(self, date: str) -> bool:
        """检查实验是否激活"""
        experiment = self.config["current_experiment"]
        start_date = datetime.strptime(experiment["start_date"], "%Y-%m-%d")
        end_date = datetime.strptime(experiment["end_date"], "%Y-%m-%d")
        current_date = datetime.strptime(date, "%Y-%m-%d")
        
        return (start_date <= current_date <= end_date and 
                experiment["status"] == "active")
    
    def _calendar_based_allocation(self, date: str) -> tuple:
        """基于日历的分配策略（例如：奇数日A组，偶数日B组）"""
        experiment = self.config["current_experiment"]
        day_of_month = datetime.strptime(date, "%Y-%m-%d").day
        
        if day_of_month % 2 == 1:  # 奇数日
            return experiment["model_a"], "group_a"
        else:  # 偶数日
            return experiment["model_b"], "group_b"
    
    def _hash_based_allocation(self, date: str) -> tuple:
        """基于日期哈希的分配策略"""
        experiment = self.config["current_experiment"]
        hash_value = int(hashlib.md5(date.encode()).hexdigest(), 16)
        
        if (hash_value % 100) < (experiment["allocation_ratio"]["group_a"] * 100):
            return experiment["model_a"], "group_a"
        else:
            return experiment["model_b"], "group_b"
    
    def _alternating_allocation(self, date: str) -> tuple:
        """交替分配策略"""
        experiment = self.config["current_experiment"]
        
        # 获取已有记录数量
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_scheduling_records")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count % 2 == 0:
            return experiment["model_a"], "group_a"
        else:
            return experiment["model_b"], "group_b"
    
    def record_daily_result(self, record: DailySchedulingRecord):
        """记录每日调度结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO daily_scheduling_records 
            (date, model_version, experiment_group, input_params, makespan, 
             resource_utilization, total_workers, execution_time, schedule_details, 
             success, delayed_tasks, overtime_hours, employee_satisfaction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.date,
                record.model_version,
                record.experiment_group,
                json.dumps(record.input_params),
                record.makespan,
                record.resource_utilization,
                record.total_workers,
                record.execution_time,
                json.dumps(record.schedule_details),
                record.success,
                record.delayed_tasks,
                record.overtime_hours,
                record.employee_satisfaction
            ))
            
            conn.commit()
            logger.info(f"记录每日调度结果: {record.date} - {record.experiment_group}")
            
        except Exception as e:
            logger.error(f"记录调度结果失败: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_experiment_data(self, days: int = 30) -> pd.DataFrame:
        """获取实验数据"""
        conn = sqlite3.connect(self.db_path)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = '''
        SELECT * FROM daily_scheduling_records 
        WHERE date >= ? AND date <= ?
        ORDER BY date DESC
        '''
        
        df = pd.read_sql_query(
            query, 
            conn, 
            params=[start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]
        )
        conn.close()
        
        return df
    
    def analyze_experiment_results(self, days: int = 30) -> Dict[str, Any]:
        """分析实验结果"""
        df = self.get_experiment_data(days)
        
        if df.empty:
            return {"error": "没有实验数据"}
        
        # 按实验分组分析
        analysis = {}
        
        for group in df['experiment_group'].unique():
            group_data = df[df['experiment_group'] == group]
            
            analysis[group] = {
                "sample_size": len(group_data),
                "success_rate": group_data['success'].mean(),
                "avg_makespan": group_data['makespan'].mean(),
                "std_makespan": group_data['makespan'].std(),
                "avg_resource_utilization": group_data['resource_utilization'].mean(),
                "avg_delayed_tasks": group_data['delayed_tasks'].mean(),
                "avg_overtime_hours": group_data['overtime_hours'].mean(),
                "min_makespan": group_data['makespan'].min(),
                "max_makespan": group_data['makespan'].max()
            }
        
        # 计算改进效果
        if len(analysis) >= 2:
            groups = list(analysis.keys())
            group_a_makespan = analysis[groups[0]]['avg_makespan']
            group_b_makespan = analysis[groups[1]]['avg_makespan']
            
            improvement = ((group_a_makespan - group_b_makespan) / group_a_makespan) * 100
            analysis['comparison'] = {
                "improvement_percentage": improvement,
                "better_group": groups[0] if group_a_makespan > group_b_makespan else groups[1],
                "sample_sufficient": min([analysis[g]['sample_size'] for g in groups]) >= self.config['minimum_days']
            }
            
            # 统计显著性检验
            if analysis['comparison']['sample_sufficient']:
                analysis['statistical_test'] = self._perform_statistical_test(df, groups)
        
        return analysis
    
    def _perform_statistical_test(self, df: pd.DataFrame, groups: List[str]) -> Dict[str, Any]:
        """执行统计显著性检验"""
        try:
            from scipy.stats import ttest_ind
            
            group_a_data = df[df['experiment_group'] == groups[0]]['makespan']
            group_b_data = df[df['experiment_group'] == groups[1]]['makespan']
            
            t_stat, p_value = ttest_ind(group_a_data, group_b_data)
            
            return {
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "is_significant": p_value < self.config['significance_level'],
                "confidence_level": 1 - self.config['significance_level']
            }
        except ImportError:
            return {"error": "需要安装scipy进行统计检验"}
        except Exception as e:
            return {"error": f"统计检验失败: {str(e)}"}
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日报告"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 获取今日调度结果
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM daily_scheduling_records WHERE date = ?", 
            (today,)
        )
        today_record = cursor.fetchone()
        conn.close()
        
        report = {
            "date": today,
            "experiment_status": self.config["current_experiment"]["status"],
            "today_result": None,
            "recent_trends": None,
            "recommendations": []
        }
        
        if today_record:
            # 今日结果
            report["today_result"] = {
                "model_used": today_record[2],  # model_version
                "experiment_group": today_record[3],  # experiment_group
                "makespan": today_record[5],  # makespan
                "resource_utilization": today_record[6],  # resource_utilization
                "success": bool(today_record[10])  # success
            }
            
            # 最近趋势
            recent_analysis = self.analyze_experiment_results(days=7)
            report["recent_trends"] = recent_analysis
            
            # 生成建议
            report["recommendations"] = self._generate_recommendations(recent_analysis)
        
        return report
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if "comparison" in analysis:
            comparison = analysis["comparison"]
            
            if comparison["sample_sufficient"]:
                if abs(comparison["improvement_percentage"]) > 5:
                    recommendations.append(
                        f"发现显著性能差异：{comparison['better_group']}组表现更好，"
                        f"改进幅度为{abs(comparison['improvement_percentage']):.1f}%"
                    )
                    
                    if "statistical_test" in analysis and analysis["statistical_test"]["is_significant"]:
                        recommendations.append("差异具有统计显著性，建议考虑推广更好的模型")
                else:
                    recommendations.append("两组性能差异较小，可以继续观察")
            else:
                recommendations.append("样本量不足，建议继续收集数据")
        
        # 检查性能异常
        for group, stats in analysis.items():
            if group not in ["comparison", "statistical_test"]:
                if stats["success_rate"] < 0.95:
                    recommendations.append(f"{group}组成功率偏低({stats['success_rate']:.1%})，需要关注")
                
                if stats["avg_makespan"] > 60:  # 假设60是阈值
                    recommendations.append(f"{group}组平均完工时间过长({stats['avg_makespan']:.1f})，需要优化")
        
        return recommendations
    
    def update_employee_feedback(self, date: str, satisfaction_score: float):
        """更新员工满意度反馈"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE daily_scheduling_records 
        SET employee_satisfaction = ? 
        WHERE date = ?
        ''', (satisfaction_score, date))
        
        conn.commit()
        conn.close()
        
        logger.info(f"更新员工满意度: {date} - {satisfaction_score}")


class DailySchedulingService:
    """每日调度服务"""
    
    def __init__(self):
        self.ab_test = DailySchedulingABTest()
        
    def run_daily_scheduling(self, input_params: List[float], date: str = None) -> Dict[str, Any]:
        """执行每日调度"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 获取今日应使用的模型
        model_version, experiment_group = self.ab_test.get_model_for_today(date)
        
        logger.info(f"每日调度开始: {date}, 模型: {model_version}, 分组: {experiment_group}")
        
        try:
            # 执行调度算法
            start_time = time.time()
            
            # 这里调用您的DDQN算法
            # 实际应用中需要根据model_version加载对应的模型
            from RUN import RUN
            schedule_details, img = RUN(input_params)
            
            execution_time = time.time() - start_time
            
            # 计算性能指标
            makespan = self._extract_makespan(schedule_details)
            resource_utilization = self._calculate_resource_utilization(schedule_details)
            total_workers = self._count_total_workers(schedule_details)
            
            # 创建记录
            record = DailySchedulingRecord(
                date=date,
                model_version=model_version,
                experiment_group=experiment_group,
                input_params=input_params,
                makespan=makespan,
                resource_utilization=resource_utilization,
                total_workers=total_workers,
                execution_time=execution_time,
                schedule_details=schedule_details,
                success=True
            )
            
            # 保存记录
            self.ab_test.record_daily_result(record)
            
            return {
                "status": "success",
                "date": date,
                "model_version": model_version,
                "experiment_group": experiment_group,
                "results": {
                    "makespan": makespan,
                    "resource_utilization": resource_utilization,
                    "total_workers": total_workers,
                    "execution_time": execution_time
                },
                "schedule_details": schedule_details,
                "gantt_chart": base64.b64encode(img.getvalue()).decode('utf-8')
            }
            
        except Exception as e:
            # 记录失败
            record = DailySchedulingRecord(
                date=date,
                model_version=model_version,
                experiment_group=experiment_group,
                input_params=input_params,
                makespan=float('inf'),
                resource_utilization=0.0,
                total_workers=0,
                execution_time=0.0,
                schedule_details=[],
                success=False
            )
            
            self.ab_test.record_daily_result(record)
            
            logger.error(f"每日调度失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "date": date,
                "model_version": model_version,
                "experiment_group": experiment_group
            }
    
    def _extract_makespan(self, schedule_details: List[Dict]) -> float:
        """从调度详情中提取完工时间"""
        if not schedule_details:
            return float('inf')
        
        max_end_time = max([task.get('end', 0) for task in schedule_details])
        return float(max_end_time)
    
    def _calculate_resource_utilization(self, schedule_details: List[Dict]) -> float:
        """计算资源利用率"""
        if not schedule_details:
            return 0.0
        
        # 简化计算，实际应根据您的业务逻辑
        total_work_time = sum([
            task.get('workers', 1) * (task.get('end', 0) - task.get('start', 0)) 
            for task in schedule_details
        ])
        
        makespan = self._extract_makespan(schedule_details)
        total_available_time = makespan * 50  # 假设总共50个工人
        
        return min(total_work_time / total_available_time if total_available_time > 0 else 0.0, 1.0)
    
    def _count_total_workers(self, schedule_details: List[Dict]) -> int:
        """统计参与的总人数"""
        if not schedule_details:
            return 0
        
        # 计算所有任务涉及的最大人数
        return max([task.get('workers', 1) for task in schedule_details] + [0])


# 使用示例
if __name__ == "__main__":
    import base64
    import time
    
    # 初始化服务
    service = DailySchedulingService()
    
    # 模拟每日调度
    input_params = [10, 5, 8, 6, 7, 9, 6, 7, 6, 7, 7, 7, 4, 7, 5]
    
    # 执行调度
    result = service.run_daily_scheduling(input_params)
    print(f"调度结果: {result['status']}")
    
    if result['status'] == 'success':
        print(f"使用模型: {result['model_version']}")
        print(f"实验分组: {result['experiment_group']}")
        print(f"完工时间: {result['results']['makespan']:.2f}")
        print(f"资源利用率: {result['results']['resource_utilization']:.2%}")
    
    # 生成每日报告
    ab_test = DailySchedulingABTest()
    daily_report = ab_test.generate_daily_report()
    print(f"每日报告: {json.dumps(daily_report, indent=2, ensure_ascii=False)}")


