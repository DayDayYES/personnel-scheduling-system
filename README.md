# 人员调度管理系统

一个基于Spring Boot + Vue.js的人员调度管理系统，支持用户管理、工序管理和智能调度算法。

## 🚀 后端技术栈 (demo/)

核心框架
- Spring Boot 2.6.13 - 主框架，提供自动配置和快速开发
- Spring Web - Web MVC框架，处理HTTP请求
- Spring WebFlux - 响应式编程支持

数据持久层
- MyBatis Plus 3.4.1 - 增强版MyBatis，简化数据库操作
- MySQL 8.0.33 - 关系型数据库
- 数据库名: secret，运行在 localhost:3306

开发工具
- Lombok - 减少样板代码，自动生成getter/setter
- Swagger 1.5.1 - API文档生成和测试
- Freemarker 2.3.30 - 模板引擎，用于代码生成

构建工具
- Maven - 项目管理和构建
- Java 1.8 - 运行环境

服务器配置
- 端口: 8090
- 跨域配置: 支持前后端分离开发

## 🎨 前端技术栈 (vuedemo2/)
核心框架
- Vue.js 2.6.14 - 渐进式JavaScript框架
- Vue Router 3.5.4 - 官方路由管理器
- Vuex 3.0.0 - 状态管理模式

UI框架
- Element UI 2.15.14 - 基于Vue的桌面端组件库
- 提供丰富的表单、表格、对话框等组件

HTTP通信
- Axios 1.7.9 - HTTP客户端，与后端API通信

开发工具
- Vue CLI 5.0 - Vue项目脚手架和构建工具
- Babel - JavaScript编译器，支持ES6+语法
- ESLint - 代码质量检查工具

## 功能特性

- 👥 **用户管理**: 完整的用户增删改查功能
- ⚙️ **工序管理**: 工序信息管理和维护
- 🤖 **调度算法**: 支持DDPG、DDQN、CGA三种智能调度算法
- 📊 **数据可视化**: 甘特图展示调度结果
- 🎨 **现代化UI**: 基于Element UI的美观界面

## 项目结构

后端结构 (Spring Boot分层架构)
demo/src/main/java/com/example/demo/
├── controller/          # 控制层 - 处理HTTP请求
│   ├── UserController.java      # 用户管理API
│   ├── ProcessController.java   # 工序管理API
│   └── MenuController.java      # 菜单管理API
├── service/            # 服务层 - 业务逻辑
│   ├── UserService.java
│   ├── ProcessService.java
│   └── impl/           # 服务实现类
├── mapper/             # 数据访问层 - MyBatis映射器
│   ├── UserMapper.java
│   └── ProcessMapper.java
├── entity/             # 实体类 - 数据模型
│   ├── User.java
│   └── Process.java
├── common/             # 公共组件
│   ├── Result.java           # 统一响应结果
│   ├── CorsConfig.java       # 跨域配置
│   └── MybatisPlusConfig.java # MyBatis Plus配置
└── DemoApplication.java # 启动类

前端结构 (Vue组件化架构)
vuedemo2/src/
├── components/         # Vue组件
│   ├── Login.vue           # 登录页面
│   ├── Index.vue           # 主布局
│   ├── Header.vue          # 顶部导航
│   ├── Aside.vue           # 侧边栏
│   ├── Home.vue            # 首页仪表板
│   ├── user/
│   │   ├── UserManage.vue  # 用户管理
│   │   └── Test.vue        # 调度算法
│   └── process/
│       └── ProcessManage.vue # 工序管理
├── router/             # 路由配置
│   └── index.js
├── store/              # Vuex状态管理
│   └── index.js
├── assets/             # 静态资源
└── main.js             # 入口文件


|    层级  |     技术组件                 |  作用 |
|---------|-----------------------------|------|
|    前端 |    Vue.js 2.6 + Element UI  |用户界面和交互|
|   后端  |	Spring Boot 2.6 + MyBatis Plus|业务逻辑和数据管理|
| 数据库  |MySQL 8.0           |数据持久化    |
|算法服务|Flask + PyTorch + DDQN|智能调度优化|
|可视化  |Matplotlib + 甘特图|结果展示|


##启动
###vue：
(base) PS D:\Program Files\JetBrains\IDEAProject\springboot-vue-wms_test> cd vuedemo2
(base) PS D:\Program Files\JetBrains\IDEAProject\springboot-vue-wms_test\vuedemo2> npm run serve
###Flask:
ddqn_env

