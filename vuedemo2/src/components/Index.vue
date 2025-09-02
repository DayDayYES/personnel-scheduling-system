<template>
    <div class="layout-container">
      <el-container style="height: 100vh;">
        <!-- 侧边栏 -->
        <el-aside 
          :width="aside_width" 
          class="aside-container"
          :class="{ 'aside-collapsed': isCollapse }">
          <MyAside :isCollapse="isCollapse"></MyAside>
        </el-aside>
  
        <el-container class="main-container">
          <!-- 顶部导航 -->
          <el-header class="header-container">
            <MyHeader @doCollapse="doCollapse" :icon="icon"></MyHeader>
          </el-header>
  
          <!-- 主内容区 -->
          <el-main class="content-container">
            <div class="content-wrapper">
              <router-view/>
            </div>
          </el-main>
        </el-container>
      </el-container>
    </div>
  </template>
  
  <script>
  import MyAside from "@/components/Aside.vue";
  import MyHeader from "@/components/Header.vue";
  
  export default {
    name: "IndexPage",
    components: {MyAside, MyHeader},
    data() {
      return {
        isCollapse: false,
        aside_width: "240px",
        icon: "el-icon-s-fold"
      }
    },
    methods: {
      doCollapse() {
        this.isCollapse = !this.isCollapse;
        if(!this.isCollapse){
          this.aside_width = "240px"
          this.icon = "el-icon-s-fold"
        }
        else{
          this.aside_width = "64px"
          this.icon = "el-icon-s-unfold"
        }
      }
    }
  };
  </script>
  
  <style scoped>
  .layout-container {
    height: 100vh;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  }
  
  /* 侧边栏样式 */
  .aside-container {
    background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    position: relative;
    z-index: 1000;
  }
  
  .aside-container::after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 1px;
    height: 100%;
    background: linear-gradient(180deg, rgba(52, 152, 219, 0.5), rgba(155, 89, 182, 0.5));
  }
  
  .aside-collapsed {
    box-shadow: 1px 0 4px rgba(0, 0, 0, 0.1);
  }
  
  /* 主容器 */
  .main-container {
    background: transparent;
  }
  
  /* 顶部导航样式 */
  .header-container {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(52, 152, 219, 0.1);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
    padding: 0;
    height: 70px !important;
    line-height: 70px;
    position: relative;
    z-index: 999;
  }
  
  /* 主内容区样式 */
  .content-container {
    background: transparent;
    padding: 20px;
    overflow-y: auto;
  }
  
  .content-wrapper {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    padding: 24px;
    min-height: calc(100vh - 130px);
    transition: all 0.3s ease;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .content-wrapper:hover {
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  }
  
  /* 滚动条美化 */
  .content-container::-webkit-scrollbar {
    width: 8px;
  }
  
  .content-container::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 4px;
  }
  
  .content-container::-webkit-scrollbar-thumb {
    background: rgba(52, 152, 219, 0.3);
    border-radius: 4px;
    transition: background 0.3s ease;
  }
  
  .content-container::-webkit-scrollbar-thumb:hover {
    background: rgba(52, 152, 219, 0.5);
  }
  
  /* 响应式设计 */
  @media (max-width: 768px) {
    .content-container {
      padding: 10px;
    }
    
    .content-wrapper {
      padding: 16px;
      border-radius: 8px;
    }
  }
  </style>