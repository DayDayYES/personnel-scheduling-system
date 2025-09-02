<template>
    <div class="aside-wrapper">
      <!-- Logo区域 -->
      <div class="logo-section" :class="{ 'logo-collapsed': isCollapse }">
        <div class="logo-container">
          <div class="logo-icon">
            <i class="el-icon-s-cooperation"></i>
          </div>
          <transition name="fade">
            <div v-show="!isCollapse" class="logo-text">
              <h3>调度系统</h3>
              <span>Schedule</span>
            </div>
          </transition>
        </div>
      </div>
  
      <!-- 导航菜单 -->
      <el-menu
          class="navigation-menu"
          background-color="transparent"
          text-color="#ecf0f1"
          active-text-color="#3498db"
          :collapse="isCollapse"
          :collapse-transition="true"
          router
          :default-active="$route.path">

        <!-- 首页 -->
        <el-menu-item index="/Home" class="menu-item">
            <i class="el-icon-s-home menu-icon"></i>
            <span slot="title" class="menu-title">系统首页</span>
        </el-menu-item>

        <!-- 工序管理 -->
        <el-menu-item index="/ProcessManage" class="menu-item">
            <i class="el-icon-s-order menu-icon"></i>
            <span slot="title" class="menu-title">工序管理</span>
        </el-menu-item>

        <!-- 人员管理
        <el-menu-item index="/UserManage" class="menu-item">
            <i class="el-icon-user-solid menu-icon"></i>
            <span slot="title" class="menu-title">人员管理</span>
        </el-menu-item> -->

        <!-- 调度算法
        <el-menu-item index="/Test" class="menu-item">
            <i class="el-icon-cpu menu-icon"></i>
            <span slot="title" class="menu-title">调度算法</span>
        </el-menu-item> -->

        <!-- 动态菜单 -->
        <el-menu-item 
            v-for="(item, i) in menu" 
            :key="i"
            :index="'/' + item.menuclick" 
            class="menu-item">
            <i :class="item.menuicon || 'el-icon-menu'" class="menu-icon"></i>
            <span slot="title" class="menu-title">{{ item.menuname }}</span>
        </el-menu-item>
      </el-menu>
  
      <!-- 底部信息 -->
      <div class="aside-footer" :class="{ 'footer-collapsed': isCollapse }">
        <transition name="fade">
          <div v-show="!isCollapse" class="footer-content">
            <p>© 2025 调度系统</p>
            <p>v1.0.0</p>
          </div>
        </transition>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: "MyAside",
    props:{
      isCollapse: Boolean
    },
    computed:{
      menu(){
        return this.$store.state.menu || []
      }
    }
  }
  </script>
  
  <style scoped>
  .aside-wrapper {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: transparent;
  }
  
  /* Logo区域 */
  .logo-section {
    padding: 20px 15px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
  }
  
  .logo-collapsed {
    padding: 20px 10px;
  }
  
  .logo-container {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .logo-icon {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #3498db, #2980b9);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
  }
  
  .logo-icon i {
    font-size: 20px;
    color: white;
  }
  
  .logo-text h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #ecf0f1;
    line-height: 1.2;
  }
  
  .logo-text span {
    font-size: 12px;
    color: #bdc3c7;
    letter-spacing: 1px;
  }
  
  /* 导航菜单 */
  .navigation-menu {
    flex: 1;
    border: none;
    padding: 10px 0;
    overflow-y: auto;
  }
  
  .navigation-menu::-webkit-scrollbar {
    width: 4px;
  }
  
  .navigation-menu::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .navigation-menu::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
  }
  
  /* 菜单项样式 */
  .menu-item {
    margin: 8px 12px;
    border-radius: 10px;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
  }
  
  .menu-item:hover {
    background: linear-gradient(90deg, rgba(52, 152, 219, 0.2), rgba(52, 152, 219, 0.1)) !important;
    transform: translateX(3px);
  }
  
  .menu-item.is-active {
    background: linear-gradient(90deg, rgba(52, 152, 219, 0.3), rgba(52, 152, 219, 0.2)) !important;
    box-shadow: 0 2px 10px rgba(52, 152, 219, 0.3);
  }
  
  .menu-item.is-active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: #3498db;
    border-radius: 0 2px 2px 0;
  }
  
  .menu-icon {
    font-size: 18px;
    margin-right: 12px !important;
    color: #bdc3c7;
    transition: all 0.3s ease;
  }
  
  .menu-item:hover .menu-icon,
  .menu-item.is-active .menu-icon {
    color: #3498db;
    transform: scale(1.1);
  }
  
  .menu-title {
    font-size: 14px;
    font-weight: 500;
    color: #ecf0f1;
    transition: color 0.3s ease;
  }
  
  .menu-item:hover .menu-title,
  .menu-item.is-active .menu-title {
    color: #3498db;
  }
  
  /* 子菜单样式 */
  .submenu-item {
    margin: 8px 12px;
    border-radius: 10px;
  }
  
  .submenu-item :deep(.el-submenu__title) {
    height: 48px;
    line-height: 48px;
    padding: 0 16px !important;
    border-radius: 10px;
    transition: all 0.3s ease;
  }
  
  .submenu-item :deep(.el-submenu__title:hover) {
    background: linear-gradient(90deg, rgba(52, 152, 219, 0.2), rgba(52, 152, 219, 0.1)) !important;
  }
  
  .submenu-child {
    margin: 4px 0;
    border-radius: 8px;
    background: rgba(0, 0, 0, 0.1);
  }
  
  .submenu-child:hover {
    background: rgba(52, 152, 219, 0.1) !important;
  }
  
  /* 底部信息 */
  .aside-footer {
    padding: 15px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
  }
  
  .footer-collapsed {
    padding: 15px 5px;
  }
  
  .footer-content p {
    margin: 0;
    font-size: 12px;
    color: #7f8c8d;
    text-align: center;
    line-height: 1.4;
  }
  
  /* 过渡动画 */
  .fade-enter-active, .fade-leave-active {
    transition: opacity 0.3s ease;
  }
  
  .fade-enter, .fade-leave-to {
    opacity: 0;
  }
  
  /* 折叠状态下的特殊样式 */
  .navigation-menu.el-menu--collapse .menu-item {
    margin: 8px 6px;
  }
  
  .navigation-menu.el-menu--collapse .menu-icon {
    margin-right: 0 !important;
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .logo-section {
      padding: 15px 10px;
    }
    
    .menu-item {
      margin: 6px 8px;
    }
  }
  </style>