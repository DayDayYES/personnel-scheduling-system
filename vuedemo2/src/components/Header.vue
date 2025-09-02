<template>
    <div class="header-wrapper">
      <!-- 左侧：折叠按钮 -->
      <div class="header-left">
        <el-button 
          class="collapse-btn" 
          type="text" 
          @click="collapse">
          <i :class="icon" class="collapse-icon"></i>
        </el-button>
      </div>
  
      <!-- 中间：系统标题 -->
      <div class="header-center">
        <div class="system-info">
          <h2 class="system-title">
            <i class="el-icon-s-grid title-icon"></i>
            人员调度管理系统
          </h2>
          <span class="system-subtitle">Personnel Scheduling Management</span>
        </div>
      </div>
  
      <!-- 右侧：用户信息 -->
      <div class="header-right">
        <!-- 通知按钮 -->
        <el-badge :value="3" class="notification-badge">
          <el-button class="notification-btn" type="text">
            <i class="el-icon-bell"></i>
          </el-button>
        </el-badge>
  
        <!-- 用户下拉菜单 -->
        <el-dropdown class="user-dropdown" @command="handleCommand">
          <div class="user-info">
            <el-avatar 
              class="user-avatar" 
              :size="36"
              background-color="#3498db">
              {{ user.name ? user.name.charAt(0) : 'U' }}
            </el-avatar>
            <span class="user-name">{{ user.name || '用户' }}</span>
            <i class="el-icon-arrow-down user-arrow"></i>
          </div>
          <el-dropdown-menu slot="dropdown" class="user-menu">
            <el-dropdown-item command="profile">
              <i class="el-icon-user"></i>个人中心
            </el-dropdown-item>
            <el-dropdown-item command="settings">
              <i class="el-icon-setting"></i>系统设置
            </el-dropdown-item>
            <el-dropdown-item divided command="logout">
              <i class="el-icon-switch-button"></i>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: "MyHeader",
    data() {
      return {
        user: JSON.parse(sessionStorage.getItem('CurUser')) || {}
      }
    },
    props:{
      icon: String
    },
    methods:{
      handleCommand(command) {
        switch(command) {
          case 'profile':
            this.toUser();
            break;
          case 'settings':
            this.$message.info('系统设置功能开发中...');
            break;
          case 'logout':
            this.logout();
            break;
        }
      },
      toUser(){
        this.$router.push("/Home");
      },
      logout(){
        this.$confirm('您确定要退出登录吗？', '确认退出', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
          center: true,
        }).then(() => {
          this.$message({
            type: 'success',
            message: '退出成功！'
          });
          sessionStorage.clear();
          this.$router.push("/");
        }).catch(() => {
          this.$message({
            type: 'info',
            message: '已取消退出'
          });
        });
      },
      collapse(){
        this.$emit('doCollapse');
      }
    },
    created() {
      if (this.$route.path === '/Index') {
        this.$router.push("/Home");
      }
    }
  }
  </script>
  
  <style scoped>
  .header-wrapper {
    display: flex;
    align-items: center;
    height: 100%;
    padding: 0 20px;
    background: transparent;
  }
  
  /* 左侧折叠按钮 */
  .header-left {
    display: flex;
    align-items: center;
  }
  
  .collapse-btn {
    padding: 8px;
    border-radius: 8px;
    transition: all 0.3s ease;
  }
  
  .collapse-btn:hover {
    background: rgba(52, 152, 219, 0.1);
  }
  
  .collapse-icon {
    font-size: 20px;
    color: #2c3e50;
    transition: color 0.3s ease;
  }
  
  .collapse-btn:hover .collapse-icon {
    color: #3498db;
  }
  
  /* 中间系统标题 */
  .header-center {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .system-info {
    text-align: center;
    max-width: 100%; /* 限制最大宽度 */
  }
  
  .system-title {
    margin: 0;
    font-size: 30px;
    font-weight: 600;
    color: #2c3e50;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    line-height: 1; /* 添加行高 */
  }
  
  .title-icon {
    color: #3498db;
    font-size: 30px;
  }
  
  .system-subtitle {
    font-size: 18px;
    color: #7f8c8d;
    letter-spacing: 0.5px;
    display: block;
    margin-top: 2px; 
    line-height: 1; /* 添加行高 */
  }
  
  /* 右侧用户区域 */
  .header-right {
    display: flex;
    align-items: center;
    gap: 15px;
  }
  
  /* 通知按钮 */
  .notification-badge {
    margin-right: 10px;
  }
  
  .notification-btn {
    padding: 8px;
    border-radius: 8px;
    transition: all 0.3s ease;
  }
  
  .notification-btn:hover {
    background: rgba(52, 152, 219, 0.1);
  }
  
  .notification-btn i {
    font-size: 18px;
    color: #7f8c8d;
  }
  
  .notification-btn:hover i {
    color: #3498db;
  }
  
  /* 用户下拉菜单 */
  .user-dropdown {
    cursor: pointer;
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 20px;
    transition: all 0.3s ease;
  }
  
  .user-info:hover {
    background: rgba(52, 152, 219, 0.1);
  }
  
  .user-avatar {
    font-weight: 600;
    color: white;
  }
  
  .user-name {
    font-size: 14px;
    font-weight: 500;
    color: #2c3e50;
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .user-arrow {
    font-size: 12px;
    color: #bdc3c7;
    transition: transform 0.3s ease;
  }
  
  .user-dropdown:hover .user-arrow {
    transform: rotate(180deg);
  }
  
  /* 下拉菜单样式 */
  .user-menu {
    margin-top: 8px;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(0, 0, 0, 0.05);
  }
  
  .user-menu :deep(.el-dropdown-menu__item) {
    padding: 12px 16px;
    font-size: 14px;
    color: #2c3e50;
    transition: all 0.3s ease;
  }
  
  .user-menu :deep(.el-dropdown-menu__item:hover) {
    background: rgba(52, 152, 219, 0.1);
    color: #3498db;
  }
  
  .user-menu :deep(.el-dropdown-menu__item i) {
    margin-right: 8px;
    width: 16px;
    text-align: center;
  }
  
  /* 响应式设计 */
  @media (max-width: 1200px) {
    .system-title {
        font-size: 16px;
    }
    
    .system-subtitle {
        font-size: 9px;
    }
  }

  @media (max-width: 768px) {
    .header-wrapper {
      padding: 0 10px;
    }
    
    .system-title {
      font-size: 14px;
      gap: 3px;
    }
    
    .system-subtitle {
      font-size: 10px;
      letter-spacing: 0.5px;
    }
    
    .user-name {
      display: none;
    }
    
    .notification-badge {
      margin-right: 5px;
    }
  }

  @media (max-width: 480px) {
    .system-title {
        font-size: 14px;
    }
    
    .system-subtitle {
        display: none;  /* 超小屏幕隐藏副标题 */
    }
  }
  </style>