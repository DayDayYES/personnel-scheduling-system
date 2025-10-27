<template>
  <div class="gantt-test-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h2 class="page-title">
          <i class="el-icon-date"></i>
          调度结果可视化
        </h2>
        <p class="page-subtitle">基于DHTMLX的交互式甘特图分析平台</p>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar-section">
      <el-card shadow="never">
        <div class="toolbar-content">
          <!-- 新增：历史结果选择 -->
          <div class="result-selector">
            <label>选择调度结果：</label>
            <el-select 
              v-model="selectedTableName" 
              @change="handleTableChange"
              placeholder="请选择调度结果"
              style="width: 400px;"
              :loading="loading"
              size="small">
              <el-option
                v-for="item in scheduleResultList"
                :key="item.tableName"
                :label="`${item.createdTime} | 完工时间: ${item.makespan}h | ${item.taskCount}个任务`"
                :value="item.tableName">
              </el-option>
            </el-select>
            <el-button 
              size="small" 
              icon="el-icon-refresh" 
              @click="refreshScheduleList"
              :loading="loading"
              style="margin-left: 10px;">
              刷新
            </el-button>
          </div>
          
          <div class="view-switch">
            <label>视角切换：</label>
            <el-radio-group v-model="viewMode" @change="switchView" size="small">
              <el-radio-button label="workpoint">设备视角</el-radio-button>
              <el-radio-button label="team">团队视角</el-radio-button>
              <el-radio-button label="process">工序视角</el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="zoom-controls">
            <label>缩放级别：</label>
            <el-button-group>
              <el-button size="small" @click="changeZoom('day')">天</el-button>
              <el-button size="small" @click="changeZoom('week')">周</el-button>
              <el-button size="small" @click="changeZoom('month')">月</el-button>
            </el-button-group>
          </div>

          <div class="info-display">
            <el-tag type="success">完工时间: {{ makespan.toFixed(2) }}小时</el-tag>
            <el-tag type="info">任务数: {{ taskCount }}</el-tag>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Gantt图表容器 -->
    <div class="gantt-section">
      <el-card shadow="never" class="gantt-card">
        <div ref="ganttContainer" class="gantt-container"></div>
      </el-card>
    </div>

    <!-- 说明文档 -->
    <div class="info-section">
      <el-card shadow="never">
        <div slot="header">
          <span><i class="el-icon-info"></i> 调度数据统计</span>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="设备数量">3个（设备1、设备2、设备3）</el-descriptions-item>
          <el-descriptions-item label="任务总数">{{ taskCount }}个</el-descriptions-item>
          <el-descriptions-item label="团队数量">6个（架子班组、保温班组等）</el-descriptions-item>
          <el-descriptions-item label="完工时间">{{ makespan }}小时</el-descriptions-item>
          <el-descriptions-item label="并行任务">✅ 已包含同时进行的任务</el-descriptions-item>
          <el-descriptions-item label="时间范围">2024-01-01 至 2024-01-03</el-descriptions-item>
        </el-descriptions>
        
        <div class="test-notes">
          <h4>💡 功能说明：</h4>
          <ul>
            <li>✅ 查看并行任务是否重叠（设备1有多个同时进行的任务）</li>
            <li>✅ 三种视角切换效果</li>
            <li>✅ 鼠标双击显示详情</li>
            <li>✅ 时间轴缩放功能</li>
            <li>✅ 查看不同团队的颜色区分</li>
          </ul>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import gantt from 'dhtmlx-gantt';
import 'dhtmlx-gantt/codebase/dhtmlxgantt.css';

export default {
  name: 'GanttTest',
  data() {
    return {
      viewMode: 'workpoint', // workpoint | team | process
      makespan: 0,
      taskCount: 0,
      
      // 新增：历史结果列表
      scheduleResultList: [],
      
      // 新增：当前选中的表名
      selectedTableName: '',
      
      // 新增：加载状态
      loading: false,
      
      // 修改：testScheduleData 初始为空，从数据库加载
      testScheduleData: [],
      
      // 团队颜色映射
      teamColors: {
        'team1': '#FF6B35',  // 鲜橙色
        'team2': '#EF3950',  // 鲜红色
        'team3': '#507EF7',  // 鲜蓝色
        'team4': '#9B59B6',  // 紫罗兰色
        'team5': '#00B774',  // 鲜绿色
        'team6': '#F39C12'   // 金橙色
      },
      
      // 团队名称
      teamNames: {
        'team1': '团队1',
        'team2': '团队2',
        'team3': '团队3',
        'team4': '团队4',
        'team5': '团队5',
        'team6': '团队6'
      }
    };
  },
  mounted() {
    this.initGantt();
    // 修改：从数据库加载历史结果
    this.loadScheduleResultList();
  },
  beforeDestroy() {
    if (gantt.$initialized) {
      gantt.clearAll();
    }
  },
  methods: {
    /**
     * 加载调度结果列表
     */
    async loadScheduleResultList() {
      this.loading = true;
      try {
        console.log('📋 开始加载调度结果列表...');
        const response = await this.$axios.get(this.$httpUrl + '/schedule_results/list?limit=50');
        
        // 检查响应数据是否存在
        if (!response || !response.data) {
          this.$message.error('服务器响应异常');
          return;
        }
        
        if (response.data.code === 200) {
          this.scheduleResultList = response.data.data || [];
          console.log(`✅ 加载成功，共 ${this.scheduleResultList.length} 个调度结果`);
          
          // 默认选择最新的
          if (this.scheduleResultList.length > 0) {
            this.selectedTableName = this.scheduleResultList[0].tableName;
            await this.loadScheduleData(this.selectedTableName);
          } else {
            this.$message.warning('暂无调度结果，请先运行算法');
          }
        } else {
          const errorMsg = response.data.msg || '未知错误';
          this.$message.error('加载调度结果列表失败: ' + errorMsg);
        }
      } catch (error) {
        // 详细的错误日志
        if (error.response) {
          // 服务器返回了错误状态码
          console.error('服务器错误:', error.response.status, error.response.data);
          this.$message.error(`服务器错误: ${error.response.status}`);
        } else if (error.request) {
          // 请求已发送但没有收到响应
          console.error('网络错误:', error.request);
          this.$message.error('网络错误，请检查后端服务是否启动');
        } else {
          // 其他错误
          console.error('未知错误:', error.message);
          this.$message.error('加载失败: ' + error.message);
        }
      } finally {
        this.loading = false;
      }
    },
    
    /**
     * 加载指定表的调度数据
     */
    async loadScheduleData(tableName) {
      if (!tableName) {
        console.warn('⚠️  表名为空，无法加载数据');
        return;
      }
      
      this.loading = true;
      try {
        console.log(`📖 加载调度数据: ${tableName}`);
        const response = await this.$axios.get(`${this.$httpUrl}/schedule_results/${tableName}`);
        
        // 检查响应数据是否存在
        if (!response || !response.data) {
          this.$message.error('服务器响应异常');
          return;
        }
        
        if (response.data.code === 200) {
          this.testScheduleData = response.data.data || [];
          this.taskCount = this.testScheduleData.length;
          
          // 计算完工时间
          if (this.testScheduleData.length > 0) {
            this.makespan = Math.max(...this.testScheduleData.map(t => t.end));
          } else {
            this.makespan = 0;
          }
          
          console.log(`✅ 加载成功: ${this.taskCount} 个任务, 完工时间: ${this.makespan.toFixed(2)}h`);
          
          // 重新加载甘特图
          this.loadData();
          
          this.$message.success(`调度数据加载成功 (${this.taskCount}个任务)`);
        } else {
          const errorMsg = response.data.msg || '未知错误';
          this.$message.error('加载调度数据失败: ' + errorMsg);
        }
      } catch (error) {
        // 详细的错误日志
        if (error.response) {
          console.error('服务器错误:', error.response.status, error.response.data);
          this.$message.error(`服务器错误: ${error.response.status}`);
        } else if (error.request) {
          console.error('网络错误:', error.request);
          this.$message.error('网络错误，请检查后端服务是否启动');
        } else {
          console.error('未知错误:', error.message);
          this.$message.error('加载失败: ' + error.message);
        }
      } finally {
        this.loading = false;
      }
    },
    
    /**
     * 处理下拉框选择变化
     */
    handleTableChange(tableName) {
      console.log(`🔄 切换调度结果: ${tableName}`);
      this.loadScheduleData(tableName);
    },
    
    /**
     * 刷新调度结果列表
     */
    refreshScheduleList() {
      console.log('🔄 刷新调度结果列表');
      this.loadScheduleResultList();
    },
    
    /**
     * 初始化DHTMLX Gantt
     */
    initGantt() {
      // 中文本地化配置
      gantt.i18n.setLocale({
        date: {
          month_full: ["一月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"],
          month_short: ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
          day_full: ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"],
          day_short: ["日", "一", "二", "三", "四", "五", "六"]
        },
        labels: {
          new_task: "新任务",
          icon_save: "保存",
          icon_cancel: "取消",
          icon_details: "详情",
          icon_edit: "编辑",
          icon_delete: "删除",
          confirm_closing: "",
          confirm_deleting: "确定删除任务吗？",
          section_description: "描述",
          section_time: "时间",
          section_type: "类型",
          
          // 弹窗按钮
          button_save: "保存",
          button_cancel: "取消",
          button_delete: "删除"
        }
      });
      
      // 基础配置
      gantt.config.date_format = '%Y-%m-%d %H:%i';
      gantt.config.xml_date = '%Y-%m-%d %H:%i';
      gantt.config.scale_unit = 'day';
      gantt.config.date_scale = '%Y-%m-%d';
      gantt.config.subscales = [
        { unit: 'hour', step: 12, date: '%H:%i' }
      ];
      
      // 列配置
      gantt.config.columns = [
        { name: 'text', label: '任务名称', width: 160, tree: true },
        { name: 'start_date', label: '开始时间', width: 100, align: 'center' },
        { name: 'duration', label: '持续时间', width: 70, align: 'center' },
        { 
          name: 'teamName', 
          label: '所属团队', 
          width: 70, 
          align: 'center',
          template: function(task) {
            return task.teamName || '-';
          }
        },
        { 
          name: 'workers', 
          label: '分配人数', 
          width: 70, 
          align: 'center',
          template: function(task) {
            return task.workers ? task.workers + '人' : '-';
          }
        }
      ];
      
      // 工具提示配置
      gantt.config.tooltip_hide_timeout = 1000;
      gantt.templates.tooltip_text = (start, end, task) => {
        if (task.type === 'project') return '';
        
        const duration = ((task.end_date - task.start_date) / (1000 * 60 * 60)).toFixed(1);
        return `
          <div style="padding: 10px; min-width: 200px;">
            <strong style="font-size: 14px;">${task.text}</strong><br/>
            <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;"/>
            <div style="margin: 5px 0;">
              <span style="color: #666;">开始时间：</span>
              <strong>${this.formatDate(task.start_date)}</strong>
            </div>
            <div style="margin: 5px 0;">
              <span style="color: #666;">结束时间：</span>
              <strong>${this.formatDate(task.end_date)}</strong>
            </div>
            <div style="margin: 5px 0;">
              <span style="color: #666;">持续时间：</span>
              <strong>${duration}小时</strong>
            </div>
            <div style="margin: 5px 0;">
              <span style="color: #666;">团队：</span>
              <strong>${task.teamName || ''}</strong>
            </div>
            <div style="margin: 5px 0;">
              <span style="color: #666;">工人数：</span>
              <strong>${task.workers || 0}人</strong>
            </div>
          </div>
        `;
      };
      
      // 任务颜色配置
      gantt.templates.task_class = (start, end, task) => {
        if (task.type === 'project') return 'gantt_project';
        return `gantt_task_${task.team}`;
      };
      
      // 初始化
      gantt.init(this.$refs.ganttContainer);
      
      console.log('✅ DHTMLX Gantt 初始化完成');
    },
    
    /**
     * 加载数据
     */
    loadData() {
      let ganttData;
      
      switch (this.viewMode) {
        case 'workpoint':
          ganttData = this.prepareWorkpointView();
          break;
        case 'team':
          ganttData = this.prepareTeamView();
          break;
        case 'process':
          ganttData = this.prepareProcessView();
          break;
        default:
          ganttData = this.prepareWorkpointView();
      }
      
      gantt.clearAll();
      gantt.parse(ganttData);
      
      console.log(`✅ 加载${this.viewMode}视角数据，共${ganttData.data.length}条`);
    },
    
    /**
     * 时间单位转日期
     */
    timeUnitToDate(timeUnit) {
      const baseDate = new Date('2024-01-01T00:00:00');
      const hours = timeUnit;
      baseDate.setHours(baseDate.getHours() + hours);
      return baseDate;
    },
    
    /**
     * 格式化日期
     */
    formatDate(date) {
      if (typeof date === 'string') {
        date = new Date(date);
      }
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    
    /**
     * 检测并行任务（复用之前的逻辑）
     */
    detectParallelTasks(tasks) {
      if (!tasks || tasks.length === 0) return [];
      
      const sorted = [...tasks].sort((a, b) => a.start - b.start);
      const layers = [];
      const result = [];
      
      sorted.forEach(task => {
        let layerIndex = layers.findIndex(endTime => task.start >= endTime);
        
        if (layerIndex === -1) {
          layerIndex = layers.length;
          layers.push(task.end);
        } else {
          layers[layerIndex] = task.end;
        }
        
        result.push({
          ...task,
          layer: layerIndex,
          totalLayers: 0
        });
      });
      
      const maxLayer = Math.max(...result.map(t => t.layer));
      result.forEach(t => t.totalLayers = maxLayer + 1);
      
      return result;
    },
    
    /**
     * 准备设备视角数据
     */
    prepareWorkpointView() {
      const data = [];
      const links = [];
      
      // 按设备分组
      const grouped = {};
      this.testScheduleData.forEach(task => {
        const wpId = task.workpoint_id;
        if (!grouped[wpId]) {
          grouped[wpId] = [];
        }
        grouped[wpId].push(task);
      });
      
      // 生成DHTMLX数据
      Object.keys(grouped).sort().forEach(wpId => {
        const wpTasks = grouped[wpId];
        const wpName = wpTasks[0].workpoint_name;
        
        // 转换显示名称：工作点X -> 设备X
        const displayName = wpName.replace('工作点', '设备');
        
        // 添加父节点（设备）
        data.push({
          id: wpId,
          text: displayName,
          type: 'project',
          open: true
        });
        
        // 检测并行任务
        const layered = this.detectParallelTasks(wpTasks);
        
        // 添加任务
        layered.forEach(task => {
          data.push({
            id: `task_${task.id}`,
            text: task.name,
            start_date: this.formatGanttDate(this.timeUnitToDate(task.start)),
            end_date: this.formatGanttDate(this.timeUnitToDate(task.end)),
            duration: ((task.end - task.start) / 24).toFixed(1), // 转换为天
            parent: wpId,
            team: task.team,
            teamName: this.teamNames[task.team],
            workers: task.workers,
            layer: task.layer,
            type: 'task'
          });
        });
      });
      
      return { data, links };
    },
    
    /**
     * 准备团队视角数据
     */
    prepareTeamView() {
      const data = [];
      const links = [];
      
      // 按团队分组
      const grouped = {};
      this.testScheduleData.forEach(task => {
        const team = task.team;
        if (!grouped[team]) {
          grouped[team] = [];
        }
        grouped[team].push(task);
      });
      
      // 生成DHTMLX数据
      Object.keys(grouped).sort().forEach(team => {
        const teamTasks = grouped[team];
        const teamName = this.teamNames[team];
        
        // 添加父节点（团队）
        data.push({
          id: team,
          text: teamName,
          type: 'project',
          open: true
        });
        
        // 检测并行任务
        const layered = this.detectParallelTasks(teamTasks);
        
        // 添加任务
        layered.forEach(task => {
          data.push({
            id: `task_${task.id}`,
            text: task.name,
            start_date: this.formatGanttDate(this.timeUnitToDate(task.start)),
            end_date: this.formatGanttDate(this.timeUnitToDate(task.end)),
            duration: ((task.end - task.start) / 24).toFixed(1),
            parent: team,
            team: task.team,
            teamName: this.teamNames[task.team],
            workers: task.workers,
            layer: task.layer,
            type: 'task'
          });
        });
      });
      
      return { data, links };
    },
    
    /**
     * 准备工序视角数据
     */
    prepareProcessView() {
      const data = [];
      const links = [];
      
      // 按开始时间排序
      const sorted = [...this.testScheduleData].sort((a, b) => a.start - b.start);
      
      sorted.forEach(task => {
        data.push({
          id: `task_${task.id}`,
          text: task.name,
          start_date: this.formatGanttDate(this.timeUnitToDate(task.start)),
          end_date: this.formatGanttDate(this.timeUnitToDate(task.end)),
          duration: ((task.end - task.start) / 24).toFixed(1),
          team: task.team,
          teamName: this.teamNames[task.team],
          workers: task.workers,
          type: 'task'
        });
      });
      
      return { data, links };
    },
    
    /**
     * 格式化DHTMLX日期
     */
    formatGanttDate(date) {
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hour = String(date.getHours()).padStart(2, '0');
      const minute = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day} ${hour}:${minute}`;
    },
    
    /**
     * 切换视角
     */
    switchView() {
      this.loadData();
      this.$message.success(`已切换到${this.getViewName()}视角`);
    },
    
    /**
     * 获取视角名称
     */
    getViewName() {
      const names = {
        'workpoint': '设备',
        'team': '团队',
        'process': '工序'
      };
      return names[this.viewMode] || '未知';
    },
    
    /**
     * 改变缩放级别
     */
    changeZoom(scale) {
      switch (scale) {
        case 'day':
          gantt.config.scale_unit = 'day';
          gantt.config.date_scale = '%Y-%m-%d';
          gantt.config.subscales = [
            { unit: 'hour', step: 6, date: '%H:%i' }
          ];
          break;
        case 'week':
          gantt.config.scale_unit = 'week';
          gantt.config.date_scale = '第%W周';
          gantt.config.subscales = [
            { unit: 'day', step: 1, date: '%d日' }
          ];
          break;
        case 'month':
          gantt.config.scale_unit = 'month';
          gantt.config.date_scale = '%Y年%m月';
          gantt.config.subscales = [
            { unit: 'week', step: 1, date: '第%W周' }
          ];
          break;
      }
      gantt.render();
      this.$message.success(`已切换到${scale}视图`);
    }
  }
};
</script>

<style scoped>
.gantt-test-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  margin-bottom: 20px;
}

.header-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 30px;
  color: white;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-subtitle {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

/* 工具栏 */
.toolbar-section {
  margin-bottom: 20px;
}

.toolbar-content {
  display: flex;
  align-items: center;
  gap: 30px;
  flex-wrap: wrap;
}

.result-selector,
.view-switch,
.zoom-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.result-selector label,
.view-switch label,
.zoom-controls label {
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
}

.info-display {
  margin-left: auto;
  display: flex;
  gap: 10px;
}

/* Gantt容器 */
.gantt-section {
  margin-bottom: 20px;
}

.gantt-card {
  border-radius: 12px;
}

.gantt-container {
  width: 100%;
  height: 600px;
  position: relative;
}

/* 信息区域 */
.info-section {
  margin-bottom: 20px;
}

.test-notes {
  margin-top: 20px;
  padding: 15px;
  background: #f0f9ff;
  border-left: 4px solid #667eea;
  border-radius: 4px;
}

.test-notes h4 {
  margin: 0 0 10px 0;
  color: #667eea;
}

.test-notes ul {
  margin: 0;
  padding-left: 20px;
}

.test-notes li {
  margin: 5px 0;
  color: #606266;
}

/* DHTMLX Gantt样式定制 */
.gantt-test-container ::v-deep .gantt_task_line {
  border-radius: 4px;
}

.gantt-test-container ::v-deep .gantt_project {
  background-color: #818cf8 !important;
  border-color: #4f46e5 !important;
}

/* 团队颜色 */
.gantt-test-container ::v-deep .gantt_task_team1 { background-color: #FF6B35 !important; border-color: #CC5529 !important; }
.gantt-test-container ::v-deep .gantt_task_team2 { background-color: #EF3950 !important; border-color: #BE2E42 !important; }
.gantt-test-container ::v-deep .gantt_task_team3 { background-color: #507EF7 !important; border-color: #3F64C8 !important; }
.gantt-test-container ::v-deep .gantt_task_team4 { background-color: #9B59B6 !important; border-color: #7C4792 !important; }
.gantt-test-container ::v-deep .gantt_task_team5 { background-color: #00B774 !important; border-color: #009B62 !important; }
.gantt-test-container ::v-deep .gantt_task_team6 { background-color: #F39C12 !important; border-color: #C27D0E !important; }

.gantt-test-container ::v-deep .gantt_grid_scale {
  background-color: #667eea;
  color: white;
  font-weight: 600;
}

.gantt-test-container ::v-deep .gantt_task_scale {
  background-color: #667eea;
  color: white;
  font-weight: 600;
}

.gantt-test-container ::v-deep .gantt_grid_head_cell {
  color: white;
}
</style>

