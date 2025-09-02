<template>
    <div class="home-container">
      <!-- 顶部欢迎区域 -->
      <div class="welcome-section">
        <div class="welcome-content">
          <div class="welcome-text">
            <h1 class="welcome-title">
              <i class="el-icon-sunny welcome-icon"></i>
              {{ getGreeting() }}，{{ user.name || '用户' }}！
            </h1>
            <p class="welcome-subtitle">欢迎使用人员调度管理系统，今天也要加油工作哦！</p>
          </div>
          <div class="weather-widget">
            <DateUtils />
          </div>
        </div>
      </div>
  
      <!-- 统计卡片区域 -->
      <div class="stats-section">
        <el-row :gutter="20">
          <el-col :xs="12" :sm="6">
            <div class="stat-card stat-primary">
              <div class="stat-icon">
                <i class="el-icon-user-solid"></i>
              </div>
              <div class="stat-content">
                <h3>总人员</h3>
                <p class="stat-number">128</p>
                <span class="stat-trend">+5.2%</span>
              </div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="6">
            <div class="stat-card stat-success">
              <div class="stat-icon">
                <i class="el-icon-s-order"></i>
              </div>
              <div class="stat-content">
                <h3>活跃工序</h3>
                <p class="stat-number">24</p>
                <span class="stat-trend">+2.1%</span>
              </div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="6">
            <div class="stat-card stat-warning">
              <div class="stat-icon">
                <i class="el-icon-time"></i>
              </div>
              <div class="stat-content">
                <h3>进行中</h3>
                <p class="stat-number">16</p>
                <span class="stat-trend">-1.3%</span>
              </div>
            </div>
          </el-col>
          <el-col :xs="12" :sm="6">
            <div class="stat-card stat-info">
              <div class="stat-icon">
                <i class="el-icon-check"></i>
              </div>
              <div class="stat-content">
                <h3>已完成</h3>
                <p class="stat-number">342</p>
                <span class="stat-trend">+8.7%</span>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
  
      <!-- 主要内容区域 -->
      <el-row :gutter="20" class="main-content">
        <!-- 个人信息卡片 -->
        <el-col :xs="24" :lg="12">
          <div class="info-card">
            <div class="card-header">
              <h3><i class="el-icon-user"></i> 个人信息</h3>
            </div>
            <div class="card-content">
              <el-descriptions :column="1" size="medium" border>
                <el-descriptions-item>
                  <template slot="label">
                    <i class="el-icon-s-custom"></i> 账号
                  </template>
                  <el-tag type="info">{{ user.no || '未设置' }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item>
                  <template slot="label">
                    <i class="el-icon-mobile-phone"></i> 电话
                  </template>
                  {{ user.phone || '未设置' }}
                </el-descriptions-item>
                <el-descriptions-item>
                  <template slot="label">
                    <i class="el-icon-male"></i> 性别
                  </template>
                  <el-tag :type="user.sex == '1' ? 'primary' : 'danger'" size="small">
                    <i :class="user.sex == 1 ? 'el-icon-male' : 'el-icon-female'"></i>
                    {{ user.sex == 1 ? "男" : "女" }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item>
                  <template slot="label">
                    <i class="el-icon-star-on"></i> 角色
                  </template>
                  <el-tag 
                    :type="user.roleId == 0 ? 'danger' : (user.roleId == 1 ? 'warning' : 'success')" 
                    size="small">
                    {{ user.roleId == 0 ? "超级管理员" : (user.roleId == 1 ? "管理员" : "普通用户") }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-col>
  
        <!-- 快捷操作 -->
        <el-col :xs="24" :lg="12">
          <div class="info-card">
            <div class="card-header">
              <h3><i class="el-icon-s-operation"></i> 快捷操作</h3>
            </div>
            <div class="card-content">

                <div class="quick-actions">
                    <div class="action-item" @click="goToProcess">
                        <div class="action-icon">
                        <i class="el-icon-s-order"></i>
                        </div>
                        <span>工序管理</span>
                    </div>
                    <div class="action-item" @click="goToUser">
                        <div class="action-icon">
                        <i class="el-icon-user-solid"></i>
                        </div>
                        <span>人员管理</span>
                    </div>
                    <div class="action-item" @click="goToAlgorithm">
                        <div class="action-icon">
                        <i class="el-icon-cpu"></i>
                        </div>
                        <span>调度算法</span>
                    </div>
                    <div class="action-item" @click="showComingSoon">
                        <div class="action-icon">
                        <i class="el-icon-s-data"></i>
                        </div>
                        <span>数据统计</span>
                    </div>
                </div>
            </div>
          </div>
        </el-col>
      </el-row>
  
      <!-- 最近活动 -->
      <div class="activity-section">
        <div class="info-card">
          <div class="card-header">
            <h3><i class="el-icon-time"></i> 最近活动</h3>
          </div>
          <div class="card-content">
            <el-timeline>
              <el-timeline-item timestamp="2024-01-01 10:30" placement="top">
                <el-card>
                  <h4>工序"切割工序"已创建</h4>
                  <p>新增了切割工序，时长30分钟</p>
                </el-card>
              </el-timeline-item>
              <el-timeline-item timestamp="2024-01-01 09:15" placement="top">
                <el-card>
                  <h4>系统登录</h4>
                  <p>{{ user.name }} 登录了系统</p>
                </el-card>
              </el-timeline-item>
              <el-timeline-item timestamp="2023-12-31 16:45" placement="top">
                <el-card>
                  <h4>数据备份完成</h4>
                  <p>系统数据已成功备份</p>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import DateUtils from "./DateUtils.vue"
  
  export default {
    name: 'MyHome',
    components: { DateUtils },
    data() {
      return {
        user: {}
      }
    },
    methods: {
      init() {
        this.user = JSON.parse(sessionStorage.getItem('CurUser')) || {};
      },
      getGreeting() {
        const hour = new Date().getHours();
        if (hour < 6) return '夜深了';
        if (hour < 9) return '早上好';
        if (hour < 12) return '上午好';
        if (hour < 14) return '中午好';
        if (hour < 17) return '下午好';
        if (hour < 19) return '傍晚好';
        return '晚上好';
      },
      goToProcess() {
        this.$router.push('/ProcessManage');
      },
      goToAlgorithm() {
      this.$router.push('/Test');
      },
      goToUser() {
      this.$router.push('/UserManage');
      },
      showComingSoon() {
        this.$message.info('该功能正在开发中，敬请期待！');
      }
    },
    mounted() {
      this.init();
    }
  }
  </script>
  
  <style scoped>
  .home-container {
    min-height: 100%;
    padding: 0;
  }
  
  /* 欢迎区域 */
  .welcome-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 30px;
    margin-bottom: 24px;
    color: white;
  }
  
  .welcome-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .welcome-title {
    font-size: 32px;
    font-weight: 600;
    margin: 0 0 8px 0;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .welcome-icon {
    color: #ffd700;
    animation: rotate 3s linear infinite;
  }
  
  @keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .welcome-subtitle {
    font-size: 16px;
    opacity: 0.9;
    margin: 0;
  }
  
  /* 统计卡片 */
  .stats-section {
    margin-bottom: 24px;
  }
  
  .stat-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    display: flex;
    align-items: center;
    gap: 16px;
    transition: all 0.3s ease;
    height: 100px;
  }
  
  .stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
  }
  
  .stat-icon {
    width: 60px;
    height: 60px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    color: white;
  }
  
  .stat-primary .stat-icon { background: linear-gradient(135deg, #667eea, #764ba2); }
  .stat-success .stat-icon { background: linear-gradient(135deg, #4ecdc4, #44a08d); }
  .stat-warning .stat-icon { background: linear-gradient(135deg, #ffeaa7, #fdcb6e); }
  .stat-info .stat-icon { background: linear-gradient(135deg, #74b9ff, #0984e3); }
  
  .stat-content h3 {
    margin: 0 0 4px 0;
    font-size: 14px;
    color: #666;
    font-weight: 500;
  }
  
  .stat-number {
    margin: 0 0 4px 0;
    font-size: 28px;
    font-weight: 700;
    color: #2c3e50;
  }
  
  .stat-trend {
    font-size: 12px;
    color: #27ae60;
    background: rgba(39, 174, 96, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
  }
  
  /* 主要内容 */
  .main-content {
    margin-bottom: 24px;
  }
  
  .info-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    height: 100%;
  }
  
  .card-header {
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    padding: 20px 24px;
    border-bottom: 1px solid #e9ecef;
  }
  
  .card-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #2c3e50;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .card-content {
    padding: 24px;
  }
  
  /* 快捷操作 */
  .quick-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  
  .action-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
    border-radius: 8px;
    border: 2px solid #f1f3f4;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .action-item:hover {
    border-color: #3498db;
    background: rgba(52, 152, 219, 0.05);
    transform: translateY(-2px);
  }
  
  .action-icon {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, #3498db, #2980b9);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 8px;
    color: white;
    font-size: 20px;
  }
  
  .action-item span {
    font-size: 14px;
    font-weight: 500;
    color: #2c3e50;
  }
  
  /* 活动区域 */
  .activity-section {
    margin-bottom: 24px;
  }
  
  /* 描述列表样式调整 */
  .card-content :deep(.el-descriptions) {
    margin: 0;
  }
  
  .card-content :deep(.el-descriptions__body) {
    background: transparent;
  }
  
  .card-content :deep(.el-descriptions-item__label) {
    font-weight: 500;
    color: #606266;
    background: #f8f9fa !important;
  }
  
  /* 时间线样式 */
  .card-content :deep(.el-timeline-item__timestamp) {
    color: #909399;
    font-size: 12px;
  }
  
  .card-content :deep(.el-card) {
    border: none;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .card-content :deep(.el-card h4) {
    margin: 0 0 8px 0;
    color: #2c3e50;
    font-size: 14px;
  }
  
  .card-content :deep(.el-card p) {
    margin: 0;
    color: #666;
    font-size: 13px;
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .welcome-content {
      flex-direction: column;
      gap: 20px;
      text-align: center;
    }
    
    .welcome-title {
      font-size: 24px;
    }
    
    .stat-card {
      padding: 16px;
      height: auto;
    }
    
    .quick-actions {
      grid-template-columns: 1fr;
    }
    
    .card-content {
      padding: 16px;
    }
  }
  </style>