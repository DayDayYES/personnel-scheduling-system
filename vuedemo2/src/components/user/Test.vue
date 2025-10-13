<template>
    <div class="algorithm-container">
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="header-content">
          <div class="title-section">
            <h2 class="page-title">
              <i class="el-icon-cpu title-icon"></i>
              调度算法
            </h2>
            <p class="page-subtitle">智能调度算法平台，支持DDPG、DDQN、CGA多种算法</p>
          </div>
          <div class="header-stats">
            <div class="stat-item">
              <div class="stat-value">3</div>
              <div class="stat-label">算法类型</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ totalRuns }}</div>
              <div class="stat-label">总运行次数</div>
            </div>
          </div>
        </div>
      </div>
  
      <!-- 算法配置区域 -->
      <div class="config-section">
        <el-card class="config-card" shadow="never">
          <div class="config-header">
            <h3 class="config-title">
              <i class="el-icon-setting"></i>
              算法配置
            </h3>
          </div>
  
          <div class="config-content">
            <!-- 算法选择 -->
            <div class="config-row">
              <div class="config-item">
                <label class="config-label">选择算法：</label>
                <el-select 
                  v-model="selectedAlgorithm" 
                  placeholder="请选择调度算法" 
                  class="algorithm-select"
                  @change="onAlgorithmChange">
                  <el-option 
                    label="DDPG - 深度确定性策略梯度" 
                    value="ddpg">
                    <div class="algorithm-option">
                      <i class="el-icon-cpu"></i>
                      <span>DDPG</span>
                      <small>深度确定性策略梯度</small>
                    </div>
                  </el-option>
                  <el-option 
                    label="DDQN - 双深度Q网络" 
                    value="ddqn">
                    <div class="algorithm-option">
                      <i class="el-icon-connection"></i>
                      <span>DDQN</span>
                      <small>双深度Q网络</small>
                    </div>
                  </el-option>
                  <el-option 
                    label="CGA - 改进遗传算法" 
                    value="ga">
                    <div class="algorithm-option">
                      <i class="el-icon-s-data"></i>
                      <span>CGA</span>
                      <small>改进遗传算法</small>
                    </div>
                  </el-option>
                </el-select>
              </div>
            </div>
  
            <!-- 算法描述 -->
            <div class="algorithm-description" v-if="selectedAlgorithm">
              <div class="description-card">
                <h4>{{ getAlgorithmInfo(selectedAlgorithm).name }}</h4>
                <p>{{ getAlgorithmInfo(selectedAlgorithm).description }}</p>
                <div class="algorithm-features">
                  <el-tag 
                    v-for="feature in getAlgorithmInfo(selectedAlgorithm).features" 
                    :key="feature"
                    size="small"
                    class="feature-tag">
                    {{ feature }}
                  </el-tag>
                </div>
              </div>
            </div>
  
            <!-- 参数输入区域 -->
            <div class="params-section" v-if="selectedAlgorithm">
              <!-- DDPG 参数 -->
              <div v-if="selectedAlgorithm === 'ddpg'" class="param-group">
                <label class="param-label">
                  <i class="el-icon-time"></i>
                  训练迭代次数：
                </label>
                <el-input-number
                  v-model="inputData.max_episodes"
                  :min="1"
                  :max="10000"
                  :step="10"
                  placeholder="请输入训练的最大迭代次数"
                  class="param-input">
                </el-input-number>
                <small class="param-hint">建议范围：100-1000次</small>
              </div>
  
              <!-- DDQN 和 GA 参数 -->
              <div v-if="selectedAlgorithm === 'ddqn' || selectedAlgorithm === 'ga'" class="param-group">
                <label class="param-label">
                  <i class="el-icon-s-data"></i>
                  算法参数：
                </label>
                <el-input
                  v-model="inputData.params"
                  placeholder="请输入参数（用逗号隔开，例如：10,5,8,6,7,9,6,7,6,7,7,7,4,7,5）"
                  class="param-input-text">
                </el-input>
                <small class="param-hint">参数示例：10,5,8,6,7,9,6,7,6,7,7,7,4,7,5</small>
              </div>
            </div>
  
            <!-- 运行按钮 -->
            <div class="run-section">
              <el-button 
                type="primary" 
                size="large"
                @click="runAlgorithm" 
                :loading="isLoading"
                :disabled="!canRun"
                class="run-button">
                <i class="el-icon-video-play" v-if="!isLoading"></i>
                {{ isLoading ? '算法运行中...' : '开始运行算法' }}
              </el-button>
              <div class="run-info" v-if="selectedAlgorithm">
                <small>
                  <i class="el-icon-info"></i>
                  预计运行时间：{{ getEstimatedTime() }}
                </small>
              </div>
            </div>
          </div>
        </el-card>
      </div>
  
      <!-- 运行状态区域 -->
      <div v-if="progressVisible" class="progress-section">
        <el-card class="progress-card" shadow="never">
          <div class="progress-header">
            <h3 class="progress-title">
              <i class="el-icon-loading" v-if="isLoading" style="animation: rotate 1s linear infinite;"></i>
              <i class="el-icon-check" v-else style="color: #67c23a;"></i>
              {{ isLoading ? '算法运行中' : '算法运行完成' }}
            </h3>
            <div class="progress-info">
              <span class="current-algorithm">{{ getAlgorithmInfo(selectedAlgorithm).name }}</span>
            </div>
          </div>
          
          <div class="progress-content">
            <el-progress 
              :percentage="progressPercentage" 
              :status="progressStatus"
              :stroke-width="8"
              :show-text="false"
              class="main-progress">
            </el-progress>
            <div class="progress-details">
              <span class="progress-text">当前进度：{{ progressPercentage.toFixed(1) }}%</span>
              <span class="progress-time" v-if="startTime">
                运行时间：{{ getRunningTime() }}
              </span>
            </div>
          </div>
        </el-card>
      </div>
  
      <!-- 结果展示区域 -->
      <div v-if="result" class="result-section">
        <el-row :gutter="20">
          <!-- 调度结果 -->
          <el-col :xs="24" :lg="12">
            <el-card class="result-card" shadow="never">
              <div class="result-header">
                <h3 class="result-title">
                  <i class="el-icon-s-data"></i>
                  调度结果
                </h3>
                <el-button size="small" type="primary" @click="exportResult">
                  <i class="el-icon-download"></i>
                  导出结果
                </el-button>
              </div>
              <div class="result-content">
                <pre class="schedule-result">{{ result.result.schedule_details }}</pre>
              </div>
            </el-card>
          </el-col>
  
          <!-- 甘特图展示区域 -->
          <el-col :span="24" v-if="result.result.gantt_charts">
            <el-card class="result-card charts-card" shadow="never">
              <div class="result-header">
                <h3 class="result-title">
                  <i class="el-icon-picture"></i>
                  多视角甘特图分析
                </h3>
                <el-button size="small" type="success" @click="downloadAllCharts">
                  <i class="el-icon-download"></i>
                  下载所有图片
                </el-button>
              </div>
              
              <!-- 甘特图标签页 -->
              <el-tabs v-model="activeChartTab" class="chart-tabs">
                <!-- 工序视角甘特图 -->
                <el-tab-pane 
                  label="工序视角" 
                  name="process"
                  v-if="result.result.gantt_charts.process">
                  <div class="chart-tab-content">
                    <div class="chart-info">
                      <i class="el-icon-info"></i>
                      {{ result.result.chart_info ? result.result.chart_info.process : '工序视角甘特图 - 按工序顺序显示调度方案' }}
              </div>
              <div class="chart-container">
                <img 
                        :src="'data:image/png;base64,' + result.result.gantt_charts.process"
                        alt="工序视角甘特图"
                  class="gantt-chart"
                        @click="showFullChart('process')">
                      <div class="chart-overlay" @click="showFullChart('process')">
                  <i class="el-icon-zoom-in"></i>
                  点击查看大图
                </div>
              </div>
                    <div class="chart-actions">
                      <el-button size="mini" type="primary" @click="downloadChart('process')">
                        <i class="el-icon-download"></i>
                        下载工序视角图
                      </el-button>
                    </div>
                  </div>
                </el-tab-pane>

                <!-- 工作点视角甘特图 -->
                <el-tab-pane 
                  label="工作点视角" 
                  name="workpoint"
                  v-if="result.result.gantt_charts.workpoint">
                  <div class="chart-tab-content">
                    <div class="chart-info">
                      <i class="el-icon-info"></i>
                      {{ result.result.chart_info ? result.result.chart_info.workpoint : '工作点视角甘特图 - 按工作点分组显示任务分配' }}
                    </div>
                    <div class="chart-container">
                      <img 
                        :src="'data:image/png;base64,' + result.result.gantt_charts.workpoint"
                        alt="工作点视角甘特图"
                        class="gantt-chart"
                        @click="showFullChart('workpoint')">
                      <div class="chart-overlay" @click="showFullChart('workpoint')">
                        <i class="el-icon-zoom-in"></i>
                        点击查看大图
                      </div>
                    </div>
                    <div class="chart-actions">
                      <el-button size="mini" type="primary" @click="downloadChart('workpoint')">
                        <i class="el-icon-download"></i>
                        下载工作点视角图
                      </el-button>
                    </div>
                  </div>
                </el-tab-pane>

                <!-- 团队视角甘特图 -->
                <el-tab-pane 
                  label="团队视角" 
                  name="team"
                  v-if="result.result.gantt_charts.team">
                  <div class="chart-tab-content">
                    <div class="chart-info">
                      <i class="el-icon-info"></i>
                      {{ result.result.chart_info ? result.result.chart_info.team : '团队视角甘特图 - 按团队分组显示工作负载' }}
                    </div>
                    <div class="chart-container">
                      <img 
                        :src="'data:image/png;base64,' + result.result.gantt_charts.team"
                        alt="团队视角甘特图"
                        class="gantt-chart"
                        @click="showFullChart('team')">
                      <div class="chart-overlay" @click="showFullChart('team')">
                        <i class="el-icon-zoom-in"></i>
                        点击查看大图
                      </div>
                    </div>
                    <div class="chart-actions">
                      <el-button size="mini" type="primary" @click="downloadChart('team')">
                        <i class="el-icon-download"></i>
                        下载团队视角图
                      </el-button>
                    </div>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </el-card>
          </el-col>
        </el-row>
  
        <!-- 运行历史 -->
        <el-card class="history-card" shadow="never">
          <div class="history-header">
            <h3 class="history-title">
              <i class="el-icon-time"></i>
              运行历史
            </h3>
            <el-button size="small" @click="clearHistory">
              <i class="el-icon-delete"></i>
              清空历史
            </el-button>
          </div>
          <div class="history-content">
            <el-timeline>
              <el-timeline-item 
                v-for="(record, index) in runHistory" 
                :key="index"
                :timestamp="record.timestamp"
                placement="top">
                <el-card>
                  <div class="history-item">
                    <div class="history-info">
                      <span class="algorithm-name">{{ record.algorithm }}</span>
                      <span class="run-status" :class="record.status">{{ record.statusText }}</span>
                    </div>
                    <div class="history-params">
                      <small>参数：{{ record.params }}</small>
                    </div>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </div>
  
      <!-- 大图预览对话框 -->
      <el-dialog
        :title="getChartDialogTitle()"
        :visible.sync="showFullChartDialog"
        width="90%"
        class="chart-dialog">
        <img 
          v-if="result && result.result.gantt_charts && currentFullChartType"
          :src="'data:image/png;base64,' + result.result.gantt_charts[currentFullChartType]"
          :alt="getChartDialogTitle()"
          style="width: 100%; height: auto;">
      </el-dialog>
    </div>
  </template>
  
  <script>
  export default {
    name: "AlgorithmTest",
    data() {
      return {
        selectedAlgorithm: "ddpg",
        inputData: {
          max_episodes: 100,
          params: "10,5,8,6,7,9,6,7,6,7,7,7,4,7,5",
        },
        result: null,
        isLoading: false,
        progressVisible: false,
        progressPercentage: 0,
        progressStatus: null,
        startTime: null,
        showFullChartDialog: false,
        currentFullChartType: null,
        activeChartTab: 'process',
        totalRuns: 0,
        runHistory: [],
        algorithmInfo: {
          ddpg: {
            name: 'DDPG - 深度确定性策略梯度',
            description: '基于Actor-Critic架构的深度强化学习算法，适用于连续动作空间的调度优化问题。',
            features: ['连续控制', '策略梯度', '经验回放', '目标网络']
          },
          ddqn: {
            name: 'DDQN - 双深度Q网络',
            description: '改进的深度Q学习算法，通过双网络结构减少过估计问题，提高调度决策的稳定性。',
            features: ['双网络', 'Q学习', '离散动作', '经验回放']
          },
          ga: {
            name: 'CGA - 改进遗传算法',
            description: '基于自然选择和遗传机制的优化算法，通过进化过程寻找最优调度方案。',
            features: ['全局搜索', '并行优化', '自适应变异', '精英保留']
          }
        }
      };
    },
    computed: {
      canRun() {
        if (!this.selectedAlgorithm) return false;
        if (this.selectedAlgorithm === 'ddpg') {
          return this.inputData.max_episodes > 0;
        }
        if (this.selectedAlgorithm === 'ddqn' || this.selectedAlgorithm === 'ga') {
          return this.inputData.params.trim() !== '';
        }
        return false;
      }
    },
    methods: {
      getAlgorithmInfo(algorithm) {
        return this.algorithmInfo[algorithm] || {};
      },
      getEstimatedTime() {
        if (this.selectedAlgorithm === 'ddpg') {
          const episodes = this.inputData.max_episodes || 100;
          return `约 ${Math.ceil(episodes / 20)} 分钟`;
        }
        return '约 20 秒';
      },
      getRunningTime() {
        if (!this.startTime) return '0秒';
        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        return `${elapsed}秒`;
      },
      onAlgorithmChange() {
        this.result = null;
        this.progressVisible = false;
        this.progressPercentage = 0;
      },
      async runAlgorithm() {
        if (!this.selectedAlgorithm) {
          this.$message.error("请选择算法");
          return;
        }
  
        // 验证输入
        if (this.selectedAlgorithm === 'ddpg' && !this.inputData.max_episodes) {
          this.$message.error("请输入训练的最大迭代次数");
          return;
        }
        if ((this.selectedAlgorithm === 'ddqn' || this.selectedAlgorithm === 'ga') && !this.inputData.params) {
          this.$message.error("请输入参数");
          return;
        }
  
        this.isLoading = true;
        this.progressVisible = true;
        this.progressPercentage = 0;
        this.progressStatus = null;
        this.startTime = Date.now();
  
        try {
          let requestData = {};
          let apiUrl = "";
  
          if (this.selectedAlgorithm === 'ddpg') {
            apiUrl = "http://localhost:5000/run_rl";
            requestData = {
              algorithm_name: this.selectedAlgorithm,
              max_episodes: parseInt(this.inputData.max_episodes),
            };
          } else if (this.selectedAlgorithm === 'ddqn') {
            apiUrl = "http://localhost:5001/run_ddqn";
            requestData = {
              algorithm_name: this.selectedAlgorithm,
              params: this.inputData.params.split(",").map(Number),
            };
          } else if (this.selectedAlgorithm === 'ga') {
            apiUrl = "http://localhost:5002/run_ga";
            requestData = {
              algorithm_name: this.selectedAlgorithm,
              params: this.inputData.params.split(",").map(Number),
            };
          }
  
          // 验证数字输入
          if (this.selectedAlgorithm === 'ddpg' && isNaN(requestData.max_episodes)) {
            this.$message.error("请输入有效的整数");
            return;
          }
          if ((this.selectedAlgorithm === 'ddqn' || this.selectedAlgorithm === 'ga') && requestData.params.some(isNaN)) {
            this.$message.error("请输入有效的数字");
            return;
          }
  
          // 模拟进度更新
          const progressInterval = setInterval(() => {
            if (this.progressPercentage < 90) {
              this.progressPercentage += Math.random() * 10;
            }
          }, 1000);
  
          const response = await this.$axios.post(apiUrl, requestData, {
            headers: {
              "Content-Type": "application/json",
            },
          });
  
          clearInterval(progressInterval);
          this.progressPercentage = 100;
          this.progressStatus = "success";
  
          this.result = response.data;
          this.totalRuns++;
  
          // 添加到历史记录
          this.runHistory.unshift({
            timestamp: new Date().toLocaleString(),
            algorithm: this.getAlgorithmInfo(this.selectedAlgorithm).name,
            status: 'success',
            statusText: '运行成功',
            params: this.selectedAlgorithm === 'ddpg' ? 
              `迭代次数: ${this.inputData.max_episodes}` : 
              `参数: ${this.inputData.params}`
          });
  
          // 保留最近10条记录
          if (this.runHistory.length > 10) {
            this.runHistory = this.runHistory.slice(0, 10);
          }
  
          this.$message.success("算法运行完成！");
  
        } catch (error) {
          console.error("调用算法失败:", error);
          this.$message.error("调用算法失败，请检查输入或后端服务");
          this.progressStatus = "exception";
          
          // 添加失败记录
          this.runHistory.unshift({
            timestamp: new Date().toLocaleString(),
            algorithm: this.getAlgorithmInfo(this.selectedAlgorithm).name,
            status: 'error',
            statusText: '运行失败',
            params: this.selectedAlgorithm === 'ddpg' ? 
              `迭代次数: ${this.inputData.max_episodes}` : 
              `参数: ${this.inputData.params}`
          });
  
        } finally {
          this.isLoading = false;
        }
      },
      exportResult() {
        if (!this.result) return;
        
        const content = this.result.result.schedule_details;
        const blob = new Blob([content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `调度结果_${this.selectedAlgorithm}_${new Date().getTime()}.txt`;
        a.click();
        window.URL.revokeObjectURL(url);
        
        this.$message.success('结果导出成功！');
      },
      downloadChart(chartType) {
        if (!this.result || !this.result.result.gantt_charts || !this.result.result.gantt_charts[chartType]) return;
        
        const chartNames = {
          'process': '工序视角甘特图',
          'workpoint': '工作点视角甘特图', 
          'team': '团队视角甘特图'
        };
        
        const link = document.createElement('a');
        link.href = 'data:image/png;base64,' + this.result.result.gantt_charts[chartType];
        link.download = `${chartNames[chartType]}_${this.selectedAlgorithm}_${new Date().getTime()}.png`;
        link.click();
        
        this.$message.success(`${chartNames[chartType]}下载成功！`);
      },
      downloadAllCharts() {
        if (!this.result || !this.result.result.gantt_charts) return;
        
        const charts = this.result.result.gantt_charts;
        const chartNames = {
          'process': '工序视角甘特图',
          'workpoint': '工作点视角甘特图',
          'team': '团队视角甘特图'
        };
        
        let downloadCount = 0;
        Object.keys(charts).forEach(chartType => {
          if (charts[chartType]) {
            setTimeout(() => {
              const link = document.createElement('a');
              link.href = 'data:image/png;base64,' + charts[chartType];
              link.download = `${chartNames[chartType]}_${this.selectedAlgorithm}_${new Date().getTime()}.png`;
              link.click();
              downloadCount++;
            }, downloadCount * 500); // 间隔500ms下载，避免浏览器阻止
          }
        });
        
        this.$message.success('所有甘特图开始下载！');
      },
      showFullChart(chartType) {
        this.currentFullChartType = chartType;
        this.showFullChartDialog = true;
      },
      getChartDialogTitle() {
        const chartNames = {
          'process': '工序视角甘特图',
          'workpoint': '工作点视角甘特图',
          'team': '团队视角甘特图'
        };
        return chartNames[this.currentFullChartType] || '甘特图预览';
      },
      clearHistory() {
        this.$confirm('确定要清空运行历史吗？', '确认操作', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }).then(() => {
          this.runHistory = [];
          this.$message.success('历史记录已清空');
        });
      }
    },
  };
  </script>
  
  <style scoped>
  .algorithm-container {
    padding: 0;
    background: transparent;
  }
  
  /* 页面头部 */
  .page-header {
    margin-bottom: 24px;
  }
  
  .header-content {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: white;
  }
  
  .title-section {
    flex: 1;
  }
  
  .page-title {
    margin: 0 0 12px 0;
    font-size: 32px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .title-icon {
    color: #ffd700;
    font-size: 36px;
    animation: pulse 2s ease-in-out infinite alternate;
  }
  
  @keyframes pulse {
    from { transform: scale(1); }
    to { transform: scale(1.1); }
  }
  
  @keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .page-subtitle {
    margin: 0;
    opacity: 0.9;
    font-size: 16px;
    line-height: 1.5;
  }
  
  .header-stats {
    display: flex;
    gap: 32px;
  }
  
  .stat-item {
    text-align: center;
  }
  
  .stat-value {
    font-size: 36px;
    font-weight: 700;
    color: #ffd700;
    line-height: 1;
  }
  
  .stat-label {
    font-size: 14px;
    opacity: 0.8;
    margin-top: 4px;
  }
  
  /* 配置区域 */
  .config-section {
    margin-bottom: 24px;
  }
  
  .config-card {
    border: none;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border-radius: 12px;
  }
  
  .config-header {
    padding: 20px 24px;
    border-bottom: 1px solid #ebeef5;
  }
  
  .config-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .config-content {
    padding: 24px;
  }
  
  .config-row {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    margin-bottom: 24px;
  }
  
  .config-item {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .config-label {
    font-weight: 500;
    color: #606266;
    white-space: nowrap;
  }
  
  .algorithm-select {
    width: 300px;
  }
  
  .algorithm-option {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .algorithm-option small {
    color: #909399;
    margin-left: auto;
  }
  
  /* 算法描述 */
  .algorithm-description {
    margin-bottom: 24px;
  }
  
  .description-card {
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    border-radius: 12px;
    padding: 20px;
    border-left: 4px solid #667eea;
  }
  
  .description-card h4 {
    margin: 0 0 8px 0;
    color: #303133;
    font-size: 16px;
  }
  
  .description-card p {
    margin: 0 0 12px 0;
    color: #606266;
    line-height: 1.6;
  }
  
  .algorithm-features {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .feature-tag {
    background: rgba(102, 126, 234, 0.1);
    border-color: rgba(102, 126, 234, 0.3);
    color: #667eea;
  }
  
  /* 参数区域 */
  .params-section {
    margin-bottom: 32px;
  }
  
  .param-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 20px;
  }
  
  .param-label {
    font-weight: 500;
    color: #606266;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .param-input {
    width: 300px;
  }
  
  .param-input-text {
    width: 500px;
  }
  
  .param-hint {
    color: #909399;
    font-size: 12px;
  }
  
  /* 运行区域 */
  .run-section {
    text-align: center;
    padding: 24px;
    background: #f8f9fa;
    border-radius: 12px;
  }
  
  .run-button {
    padding: 12px 32px;
    font-size: 16px;
    font-weight: 600;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    border-radius: 25px;
    min-width: 200px;
  }
  
  .run-button:hover {
    background: linear-gradient(135deg, #5a67d8, #6b46c1);
  }
  
  .run-info {
    margin-top: 12px;
    color: #909399;
  }
  
  /* 进度区域 */
  .progress-section {
    margin-bottom: 24px;
  }
  
  .progress-card {
    border: none;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border-radius: 12px;
  }
  
  .progress-header {
    padding: 20px 24px;
    border-bottom: 1px solid #ebeef5;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .progress-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #303133;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .current-algorithm {
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 600;
  }
  
  .progress-content {
    padding: 24px;
  }
  
  .main-progress {
    margin-bottom: 16px;
  }
  
  .progress-details {
    display: flex;
    justify-content: space-between;
    color: #606266;
  }
  
  /* 结果区域 */
  .result-section {
    margin-bottom: 24px;
  }
  
  .result-card {
    border: none;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border-radius: 12px;
    margin-bottom: 20px;
  }
  
  .result-header {
    padding: 20px 24px;
    border-bottom: 1px solid #ebeef5;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .result-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .result-content {
    padding: 24px;
  }
  
  .schedule-result {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    white-space: pre;
    font-family: 'Courier New', monospace;
    line-height: 1.6;
    overflow-x: auto;
    border: 1px solid #e4e7ed;
    max-height: 400px;
    overflow-y: auto;
  }
  
  /* 甘特图 */
  .chart-container {
    position: relative;
    text-align: center;
  }
  
  .gantt-chart {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    cursor: pointer;
    transition: transform 0.3s ease;
  }
  
  .gantt-chart:hover {
    transform: scale(1.02);
  }
  
  .chart-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
    cursor: pointer;
    border-radius: 8px;
  }
  
  .chart-container:hover .chart-overlay {
    opacity: 1;
  }
  
  /* 历史记录 */
  .history-card {
    border: none;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border-radius: 12px;
  }
  
  .history-header {
    padding: 20px 24px;
    border-bottom: 1px solid #ebeef5;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .history-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #303133;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .history-content {
    padding: 24px;
    max-height: 400px;
    overflow-y: auto;
  }
  
  .history-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .history-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .algorithm-name {
    font-weight: 500;
    color: #303133;
  }
  
  .run-status {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
  }
  
  .run-status.success {
    background: #f0f9ff;
    color: #67c23a;
  }
  
  .run-status.error {
    background: #fef0f0;
    color: #f56c6c;
  }
  
  .history-params {
    color: #909399;
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .header-content {
      flex-direction: column;
      gap: 20px;
      text-align: center;
    }
    
    .header-stats {
      gap: 20px;
    }
    
    .config-row {
      flex-direction: column;
    }
    
    .algorithm-select,
    .param-input,
    .param-input-text {
      width: 100%;
    }
    
    .progress-details {
      flex-direction: column;
      gap: 8px;
    }
    
    .result-header {
      flex-direction: column;
      gap: 12px;
      align-items: flex-start;
    }
  }
  
  /* 多视角甘特图样式 */
  .charts-card {
    margin-top: 20px;
  }
  
  .chart-tabs {
    margin-top: 20px;
  }
  
  .chart-tab-content {
    padding: 20px 0;
  }
  
  .chart-info {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 20px;
    color: #0369a1;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .chart-info i {
    font-size: 16px;
  }
  
  .chart-actions {
    text-align: center;
    padding: 12px 0;
    border-top: 1px solid #ebeef5;
    background: #fafafa;
    border-radius: 0 0 8px 8px;
  }
  
  .chart-overlay i {
    font-size: 24px;
    margin-bottom: 8px;
  }
  
  .gantt-chart:hover {
    transform: scale(1.02);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }
  </style>