# 🚀 快速开始：Excel导入功能

## 一、数据库准备（3分钟）

### 1. 创建数据库表

在MySQL客户端或命令行中执行：

```sql
-- 1. 管道开卡主表
CREATE TABLE pipeline_card (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    card_no VARCHAR(50) NOT NULL COMMENT '管道序号',
    pipeline_code VARCHAR(100) NOT NULL UNIQUE COMMENT '管道编号',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_pipeline_code (pipeline_code),
    INDEX idx_card_no (card_no),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管道开卡主表';

-- 2. 管道开卡工序明细表
CREATE TABLE pipeline_card_process (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    card_id INT NOT NULL COMMENT '开卡主表ID',
    process_name VARCHAR(100) NOT NULL COMMENT '工序名称',
    process_code VARCHAR(50) NOT NULL COMMENT '工序代码',
    required_count VARCHAR(20) COMMENT '需要执行次数',
    process_order INT COMMENT '工序顺序',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (card_id) REFERENCES pipeline_card(id) ON DELETE CASCADE,
    INDEX idx_card_id (card_id),
    INDEX idx_process_code (process_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管道开卡工序明细表';
```

### 2. 验证表创建成功

```sql
SHOW TABLES LIKE 'pipeline%';
```

应该看到两张表：
- `pipeline_card`
- `pipeline_card_process`

---

## 二、后端启动（2分钟）

### 1. Maven依赖安装

打开命令行，进入项目根目录：

```bash
cd demo
mvn clean install
```

或在IDEA中点击右侧Maven工具栏的 "Reload All Maven Projects"。

### 2. 启动Spring Boot应用

**方式一：命令行**
```bash
mvn spring-boot:run
```

**方式二：IDEA**
- 右键 `DemoApplication.java`
- 选择 "Run 'DemoApplication'"

### 3. 验证启动成功

看到以下日志表示成功：
```
Started DemoApplication in X.XXX seconds
```

测试接口：
```bash
curl http://localhost:8088/pipelineCard/template
```

---

## 三、前端启动（2分钟）

### 1. 安装依赖（首次运行）

```bash
cd vuedemo2
npm install
```

### 2. 启动开发服务器

```bash
npm run serve
```

### 3. 访问页面

浏览器打开：`http://localhost:8080`

导航至 **工序管理** 页面。

---

## 四、导入测试（1分钟）

### 1. 点击导入按钮

在工序管理页面右上角，点击绿色按钮 **"导入开卡Excel"**。

### 2. 上传文件

- 拖拽或点击选择文件：`压力管道检验预定表-课题系统测试数据.xlsx`
- 点击 **"开始导入"**

### 3. 查看结果

导入完成后会显示：
- ✅ 成功导入 50 条记录
- 📊 每条记录包含 16 个工序明细

---

## 五、数据验证（1分钟）

### 在MySQL中查询导入的数据

```sql
-- 查看管道总数
SELECT COUNT(*) FROM pipeline_card;
-- 预期结果: 50

-- 查看工序明细总数
SELECT COUNT(*) FROM pipeline_card_process;
-- 预期结果: 50 * 16 = 800

-- 查看第一条管道的详细信息
SELECT 
    c.card_no,
    c.pipeline_code,
    p.process_name,
    p.required_count
FROM pipeline_card c
LEFT JOIN pipeline_card_process p ON c.id = p.card_id
WHERE c.pipeline_code = 'AV-32130'
ORDER BY p.process_order;

-- 统计各工序的需求数量
SELECT 
    process_name,
    COUNT(CASE WHEN required_count IS NOT NULL AND required_count != '' THEN 1 END) as has_requirement,
    COUNT(*) as total
FROM pipeline_card_process
GROUP BY process_name
ORDER BY has_requirement DESC;
```

---

## 六、重要提醒 ⚠️

### 数据保护
- ❌ **不要重复导入同一个Excel**（管道编号重复会报错）
- ✅ 如需重新导入，先清空数据：
  ```sql
  DELETE FROM pipeline_card_process;
  DELETE FROM pipeline_card;
  ```

### 文件要求
- 格式：`.xlsx` 或 `.xls`
- 大小：不超过 10MB
- 第一行：表头（会被跳过）
- 管道编号：不能为空，不能重复

### 错误处理
如果导入失败，检查：
1. 后端服务是否正常运行（端口8088）
2. 数据库连接是否正常
3. Excel文件格式是否符合要求
4. 浏览器控制台是否有错误信息

---

## 七、下一步

导入成功后，你可以：

1. **查看数据**：在MySQL中查询和分析数据
2. **开发可视化界面**：展示管道列表和工序统计
3. **工序调度**：基于导入的数据生成调度方案
4. **导出功能**：将数据导出为Excel或其他格式

---

## 🎉 完成！

如果一切顺利，你现在已经成功：
- ✅ 创建了数据库表
- ✅ 启动了后端和前端服务
- ✅ 导入了50条管道记录
- ✅ 验证了数据完整性

**总耗时：约10分钟**

---

## 📞 需要帮助？

查看详细文档：`Excel导入功能使用说明.md`

常见错误解决方案：
- Maven依赖问题 → `mvn clean install -U`
- 端口占用 → 修改 `application.yml` 中的端口
- 数据库连接失败 → 检查 `application.yml` 中的数据库配置

