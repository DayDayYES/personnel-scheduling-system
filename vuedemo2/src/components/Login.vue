<template>
    <div class="login-container">
      <!-- 背景装饰 -->
      <div class="background-decoration">
        <div class="floating-circle circle1"></div>
        <div class="floating-circle circle2"></div>
        <div class="floating-circle circle3"></div>
      </div>
      
      <!-- 登录卡片 -->
      <div class="login-card">
        <!-- 系统Logo和标题 -->
        <div class="login-header">
          <div class="logo-container">
            <el-icon class="system-logo"><el-icon-user-filled /></el-icon>
          </div>
          <h1 class="system-title">智能检验平台</h1>
          <p class="system-subtitle"></p>
        </div>
        
        <!-- 登录表单 -->
        <div class="login-form-container">
          <el-form 
            :model="loginForm" 
            :rules="rules" 
            ref="loginForm" 
            class="login-form"
            size="large">
            
            <el-form-item prop="no">
              <div class="input-container">
                <el-icon class="input-icon"><el-icon-user /></el-icon>
                <el-input 
                  v-model="loginForm.no" 
                  placeholder="请输入账号"
                  class="login-input"
                  clearable>
                </el-input>
              </div>
            </el-form-item>
            
            <el-form-item prop="password">
              <div class="input-container">
                <el-icon class="input-icon"><el-icon-lock /></el-icon>
                <el-input 
                  v-model="loginForm.password" 
                  type="password"
                  placeholder="请输入密码"
                  class="login-input"
                  show-password
                  @keyup.enter.native="confirm">
                </el-input>
              </div>
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="primary" 
                class="login-button"
                :loading="confirm_disabled"
                @click="confirm">
                <span v-if="!confirm_disabled">登 录</span>
                <span v-else>登录中...</span>
              </el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 页脚信息 -->
        <div class="login-footer">
          <p>© 2025 宁波市特种设备检查研究院 · 版权所有</p>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: "MyLogin",
    data() {
      return {
        confirm_disabled: false,
        loginForm: {
          no: '',
          password: ''
        },
        rules: {
          no: [
            { required: true, message: '请输入账号', trigger: 'blur' }
          ],
          password: [
            { required: true, message: '请输入密码', trigger: 'blur' }
          ],
        }
      }
    },
    methods: {
      confirm() {
        this.confirm_disabled = true;
        this.$refs.loginForm.validate((valid) => {
          if (valid) {
            // 后台验证
            this.$axios.post(this.$httpUrl + '/user/login', this.loginForm)
              .then(res => res.data)
              .then(res => {
                console.log(res)
                if (res.code == 200) {
                  sessionStorage.setItem("CurUser", JSON.stringify(res.data.user))
                  console.log(res.data.menu);
                  this.$store.commit('setMenu', res.data.menu);
                  
                  // 成功提示
                  this.$message({
                    message: '登录成功！',
                    type: 'success'
                  });
                  
                  // 跳转主页
                  this.$router.replace('/Index');
                } else {
                  this.confirm_disabled = false;
                  this.$message({
                    message: '登录失败，用户名或密码错误！',
                    type: 'error'
                  });
                }
              })
              .catch(() => {
                this.confirm_disabled = false;
                this.$message({
                  message: '网络连接失败，请检查网络后重试！',
                  type: 'error'
                });
              });
          } else {
            this.confirm_disabled = false;
            console.log('表单验证失败');
            return false
          }
        });
      }
    }
  }
  </script>
  
  <style scoped>
  /* 整体容器 */
  .login-container {
    position: relative;
    width: 100vw;
    height: 100vh;
    background: linear-gradient(135deg, rgba(30, 144, 255, 0.8) 0%, rgba(65, 105, 225, 0.9) 100%),
                url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><defs><pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse"><path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/></pattern></defs><rect width="100%" height="100%" fill="%23145a8c"/><rect width="100%" height="100%" fill="url(%23grid)"/><circle cx="200" cy="200" r="100" fill="rgba(255,255,255,0.05)"/><circle cx="800" cy="300" r="150" fill="rgba(255,255,255,0.05)"/><circle cx="300" cy="700" r="80" fill="rgba(255,255,255,0.05)"/><circle cx="700" cy="800" r="120" fill="rgba(255,255,255,0.05)"/><polygon points="100,500 200,400 300,500 200,600" fill="rgba(255,255,255,0.03)"/><polygon points="600,100 750,150 700,300 550,250" fill="rgba(255,255,255,0.03)"/></svg>');
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  /* 背景装饰 */
  .background-decoration {
    position: absolute;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
  
  .floating-circle {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
    animation: float 8s ease-in-out infinite;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .circle1 {
    width: 200px;
    height: 200px;
    top: 10%;
    left: 10%;
    animation-delay: 0s;
  }
  
  .circle2 {
    width: 300px;
    height: 300px;
    bottom: 10%;
    right: 10%;
    animation-delay: 3s;
  }
  
  .circle3 {
    width: 150px;
    height: 150px;
    top: 60%;
    left: 5%;
    animation-delay: 6s;
  }
  
  @keyframes float {
    0%, 100% {
      transform: translateY(0px) rotate(0deg);
      opacity: 0.6;
    }
    50% {
      transform: translateY(-30px) rotate(180deg);
      opacity: 0.3;
    }
  }
  
  /* 登录卡片 */
  .login-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
    padding: 40px;
    width: 420px;
    max-width: 90vw;
    animation: slideIn 1s ease-out;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateY(50px) scale(0.9);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
  
  /* 登录头部 */
  .login-header {
    text-align: center;
    margin-bottom: 40px;
  }
  
  .logo-container {
    margin-bottom: 20px;
  }
  
  .system-logo {
    font-size: 64px;
    color: #1e90ff;
    background: linear-gradient(135deg, #1e90ff, #4169e1, #0066cc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: pulse 3s ease-in-out infinite alternate;
    filter: drop-shadow(0 2px 4px rgba(30, 144, 255, 0.3));
  }
  
  @keyframes pulse {
    from { 
      transform: scale(1);
      filter: drop-shadow(0 2px 4px rgba(30, 144, 255, 0.3));
    }
    to { 
      transform: scale(1.08);
      filter: drop-shadow(0 4px 8px rgba(30, 144, 255, 0.5));
    }
  }
  
  .system-title {
    font-size: 28px;
    color: #1e3a8a;
    margin: 10px 0;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(30, 58, 138, 0.1);
  }
  
  .system-subtitle {
    color: #64748b;
    font-size: 14px;
    letter-spacing: 1.5px;
    margin: 0;
    font-weight: 500;
  }
  
  /* 表单样式 */
  .login-form-container {
    margin-bottom: 30px;
  }
  
  .input-container {
    position: relative;
    display: flex;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .input-icon {
    position: absolute;
    left: 18px;
    z-index: 10;
    color: #64748b;
    font-size: 18px;
    transition: color 0.3s ease;
  }
  
  .login-input {
    width: 100%;
  }
  
  .login-input :deep(.el-input__wrapper) {
    padding-left: 50px;
    height: 52px;
    border-radius: 26px;
    border: 2px solid #e2e8f0;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(30, 144, 255, 0.08);
    background: rgba(255, 255, 255, 0.9);
  }
  
  .login-input :deep(.el-input__wrapper:hover) {
    border-color: #1e90ff;
    box-shadow: 0 6px 20px rgba(30, 144, 255, 0.15);
    transform: translateY(-1px);
  }
  
  .login-input :deep(.el-input__wrapper.is-focus) {
    border-color: #1e90ff;
    box-shadow: 0 8px 25px rgba(30, 144, 255, 0.2);
    transform: translateY(-1px);
  }
  
  .login-input:focus-within + .input-icon {
    color: #1e90ff;
  }
  
  .login-button {
    width: 100%;
    height: 52px;
    border-radius: 26px;
    background: linear-gradient(135deg, #1e90ff 0%, #4169e1 50%, #0066cc 100%);
    border: none;
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 1px;
    transition: all 0.4s ease;
    margin-top: 25px;
    box-shadow: 0 6px 20px rgba(30, 144, 255, 0.3);
    position: relative;
    overflow: hidden;
  }
  
  .login-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: left 0.5s ease;
  }
  
  .login-button:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 35px rgba(30, 144, 255, 0.4);
  }
  
  .login-button:hover::before {
    left: 100%;
  }
  
  .login-button:active {
    transform: translateY(-1px);
  }
  
  /* 页脚 */
  .login-footer {
    text-align: center;
    color: #64748b;
    font-size: 12px;
    border-top: 1px solid #e2e8f0;
    padding-top: 20px;
    margin-top: 10px;
  }
  
  /* 额外的视觉效果
  .login-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #1e90ff, #4169e1, #0066cc, #1e90ff);
    border-radius: 20px 20px 0 0;
  } */
  
  /* 响应式设计 */
  @media (max-width: 480px) {
    .login-card {
      padding: 30px 20px;
      margin: 20px;
    }
    
    .system-title {
      font-size: 24px;
    }
    
    .system-logo {
      font-size: 48px;
    }
    
    .login-input :deep(.el-input__wrapper) {
      height: 48px;
      padding-left: 45px;
    }
    
    .login-button {
      height: 48px;
    }
  }
  
  /* 美化滚动条（如果需要） */
  ::-webkit-scrollbar {
    width: 8px;
  }
  
  ::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
  }
  
  ::-webkit-scrollbar-thumb {
    background: rgba(30, 144, 255, 0.5);
    border-radius: 4px;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: rgba(30, 144, 255, 0.7);
  }
  </style>