# 模型版本管理与A/B测试部署指南

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install flask gevent pandas matplotlib seaborn scipy sqlite3

# 创建目录结构
mkdir -p models/{models,metadata,configs}
mkdir -p logs
mkdir -p reports
```

### 2. 启动服务

```bash
# 启动增强的Flask服务
python enhanced_flask.py

# 服务将在 http://localhost:5001 启动
```

## 📋 API接口文档

### 模型管理接口

#### 1. 注册新模型
```bash
POST /models/register
Content-Type: application/json

{
    "model_path": "./best_model_v2.pth",
    "algorithm_name": "DDQN",
    "training_params": {
        "episodes": 1000,
        "learning_rate": 0.001,
        "batch_size": 32
    },
    "performance_metrics": {
        "makespan": 42.5,
        "resource_utilization": 0.87
    },
    "description": "改进奖励函数的DDQN模型",
    "created_by": "developer_name"
}
```

#### 2. 获取模型列表
```bash
GET /models?algorithm=DDQN
```

### A/B测试接口

#### 1. 创建实验
```bash
POST /experiments
Content-Type: application/json

{
    "experiment_name": "ddqn_v1_vs_v2",
    "model_a": "DDQN_12345678_v1.0",
    "model_b": "DDQN_87654321_v2.0",
    "traffic_split": {
        "model_a": 0.7,
        "model_b": 0.3
    },
    "success_metric": "makespan",
    "duration_days": 7
}
```

#### 2. 运行算法（支持A/B测试）
```bash
POST /run_algorithm
Content-Type: application/json

{
    "params": [10,5,8,6,7,9,6,7,6,7,7,7,4,7,5],
    "experiment": "ddqn_v1_vs_v2",
    "user_id": "user_12345"
}
```

#### 3. 获取实验结果
```bash
GET /experiments/ddqn_v1_vs_v2/results
```

## 🔧 配置说明

### 1. 模型版本管理配置

```python
# model_manager.py 配置
MODEL_BASE_PATH = "./models"  # 模型存储路径
METADATA_RETENTION_DAYS = 365  # 元数据保留天数
AUTO_CLEANUP_ENABLED = True   # 自动清理旧版本
```

### 2. A/B测试配置

```json
// ab_test_config.json
{
    "experiments": {
        "ddqn_v1_vs_v2": {
            "name": "ddqn_v1_vs_v2",
            "model_a": "DDQN_v1.0",
            "model_b": "DDQN_v2.0",
            "traffic_split": {"model_a": 0.7, "model_b": 0.3},
            "success_metric": "makespan",
            "start_time": "2024-01-01T00:00:00",
            "duration_days": 7,
            "status": "active"
        }
    },
    "default_model": "DDQN_v1.0"
}
```

## 📊 监控和报告

### 1. 生成性能报告

```python
from monitoring import PerformanceMonitor

monitor = PerformanceMonitor()
report_path = monitor.generate_performance_report(days=7)
print(f"报告生成: {report_path}")
```

### 2. A/B测试分析

```python
from monitoring import ABTestAnalyzer

analyzer = ABTestAnalyzer(monitor)
ab_report = analyzer.generate_ab_test_report("ddqn_v1_vs_v2", days=7)
print(f"A/B测试报告: {ab_report}")
```

## 🎯 最佳实践

### 1. 模型发布流程

1. **开发阶段**
   ```python
   # 训练完成后注册模型
   model_manager.register_model(
       model_path="./trained_model.pth",
       algorithm_name="DDQN",
       training_params=training_config,
       performance_metrics=validation_results
   )
   ```

2. **测试阶段**
   ```python
   # 提升模型状态
   model_manager.promote_model("DDQN_v2.0", "validated")
   ```

3. **A/B测试阶段**
   ```python
   # 创建A/B测试
   ab_manager.create_experiment(
       experiment_name="production_test",
       model_a="current_production_model",
       model_b="new_candidate_model",
       traffic_split={"model_a": 0.9, "model_b": 0.1}  # 保守分流
   )
   ```

4. **生产部署**
   ```python
   # 分析实验结果后，更新默认模型
   if experiment_results["is_significant"] and improvement > 5:
       ab_manager.config["default_model"] = "new_model"
       model_manager.promote_model("new_model", "deployed")
   ```

### 2. 监控告警设置

```python
# 设置性能阈值
PERFORMANCE_THRESHOLDS = {
    "max_makespan": 60.0,      # 最大完工时间
    "max_execution_time": 10.0, # 最大执行时间
    "min_success_rate": 0.95    # 最小成功率
}

# 监控检查
def check_performance_alerts():
    recent_data = monitor.get_performance_data(
        start_time=(datetime.now() - timedelta(hours=1)).isoformat()
    )
    
    if recent_data['makespan'].mean() > PERFORMANCE_THRESHOLDS['max_makespan']:
        send_alert("性能告警: 平均完工时间超过阈值")
    
    if recent_data['success'].mean() < PERFORMANCE_THRESHOLDS['min_success_rate']:
        send_alert("可用性告警: 成功率低于阈值")
```

### 3. 模型版本策略

- **语义化版本**: `{major}.{minor}.{patch}`
- **版本标签**: 
  - `latest`: 最新稳定版本
  - `canary`: 金丝雀版本
  - `stable`: 生产稳定版本
- **自动回滚**: 性能下降时自动回滚到上一个稳定版本

### 4. A/B测试策略

- **渐进式发布**: 10% → 30% → 50% → 100%
- **统计显著性**: 至少收集100个样本，p-value < 0.05
- **业务指标**: 关注makespan、资源利用率、用户满意度
- **安全机制**: 设置性能下降阈值，自动停止实验

## 🔍 故障排除

### 1. 常见问题

**Q: 模型加载失败**
```python
# 检查模型文件是否存在
import os
if not os.path.exists(model_path):
    logger.error(f"模型文件不存在: {model_path}")

# 检查模型兼容性
try:
    torch.load(model_path, map_location='cpu')
except Exception as e:
    logger.error(f"模型加载错误: {str(e)}")
```

**Q: A/B测试流量分配不均**
```python
# 检查哈希分布
user_ids = ["user_1", "user_2", ...]
distribution = {}
for uid in user_ids:
    model = ab_manager.get_model_for_request("experiment", uid)
    distribution[model] = distribution.get(model, 0) + 1

print(f"流量分布: {distribution}")
```

### 2. 日志分析

```bash
# 查看服务日志
tail -f logs/flask_service.log

# 分析性能日志
grep "算法执行完成" logs/flask_service.log | awk '{print $NF}' | sort -n
```

## 📈 扩展功能

### 1. 集成到Spring Boot

```java
@Service
public class ModelVersionService {
    
    @Value("${model.service.url}")
    private String modelServiceUrl;
    
    public AlgorithmResult runAlgorithmWithAB(
            List<Double> params, 
            String experiment, 
            String userId) {
        
        // 调用Python服务
        RestTemplate restTemplate = new RestTemplate();
        Map<String, Object> request = Map.of(
            "params", params,
            "experiment", experiment,
            "user_id", userId
        );
        
        ResponseEntity<AlgorithmResult> response = restTemplate.postForEntity(
            modelServiceUrl + "/run_algorithm",
            request,
            AlgorithmResult.class
        );
        
        return response.getBody();
    }
}
```

### 2. 前端集成

```javascript
// Vue组件中集成A/B测试
export default {
  methods: {
    async runAlgorithm() {
      const response = await axios.post('/api/algorithm/run', {
        params: this.inputParams,
        experiment: 'ddqn_optimization_test',
        user_id: this.$store.state.user.id
      });
      
      this.result = response.data.result;
      this.modelInfo = response.data.experiment_info;
    }
  }
}
```

这套系统提供了完整的模型版本管理和A/B测试能力，帮助您的AI算法安全、可控地落地到生产环境中！
