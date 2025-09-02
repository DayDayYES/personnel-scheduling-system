# 人员调度管理系统

一个基于Spring Boot + Vue.js的人员调度管理系统，支持用户管理、工序管理和智能调度算法。

## 技术栈

### 后端
- Spring Boot 2.x
- MyBatis Plus
- MySQL
- Maven

### 前端
- Vue.js 2.x
- Element UI
- Axios
- Vue Router

## 功能特性

- 👥 **用户管理**: 完整的用户增删改查功能
- ⚙️ **工序管理**: 工序信息管理和维护
- 🤖 **调度算法**: 支持DDPG、DDQN、CGA三种智能调度算法
- 📊 **数据可视化**: 甘特图展示调度结果
- 🎨 **现代化UI**: 基于Element UI的美观界面

## 项目结构

├── demo/ # 后端Spring Boot项目
│ ├── src/main/java/
│ │ └── com/example/demo/
│ │ ├── controller/ # 控制器
│ │ ├── entity/ # 实体类
│ │ ├── mapper/ # 数据访问层
│ │ └── service/ # 业务逻辑层
│ └── src/main/resources/
│ └── mapper/ # MyBatis XML文件
└── vuedemo2/ # 前端Vue项目
├── src/
│ ├── components/ # Vue组件
│ ├── router/ # 路由配置
│ └── assets/ # 静态资源
└── public/