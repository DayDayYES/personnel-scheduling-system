# 管道开卡Excel导入功能使用说明

## 📋 功能概述

本功能实现将**压力管道检验预定表**（开卡Excel）数据导入到数据库中，方便后续进行工序调度和管理。

---

## 🗂️ 数据库设计

### 1. 管道开卡主表 (`pipeline_card`)

存储管道的基本信息。

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INT | 主键，自增 |
| card_no | VARCHAR(50) | 管道序号（Excel第1列） |
| pipeline_code | VARCHAR(100) | 管道编号（Excel第2列），唯一索引 |
| status | VARCHAR(20) | 状态：pending/processing/completed |
| create_time | TIMESTAMP | 创建时间 |
| update_time | TIMESTAMP | 更新时间 |

### 2. 管道开卡工序明细表 (`pipeline_card_process`)

存储每个管道的工序需求（原样保存Excel数据）。

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | INT | 主键，自增 |
| card_id | INT | 关联主表ID |
| process_name | VARCHAR(100) | 工序名称（中文） |
| process_code | VARCHAR(50) | 工序代码（英文标识） |
| required_count | VARCHAR(20) | 需要执行次数（原始值） |
| process_order | INT | 工序在Excel中的列序号 |
| create_time | TIMESTAMP | 创建时间 |

---

## 📊 Excel表格结构

### 标准格式

- **第1列**：管道序号（如：1, 2, 3...）
- **第2列**：管道编号（如：AV-32130, BD-32031...）
- **第3-18列**：各工序需求

### 工序列映射关系

| Excel列 | 列名 | 工序代码 |
|---------|------|----------|
| 3 | 搭架子 | scaffold |
| 4 | 拆保温 | remove_insulation |
| 5 | 打磨 | grinding |
| 6 | 宏观检查 | macro_inspection |
| 7 | 壁厚测定 | thickness_test |
| 8 | RT（射线）检测 | rt_test |
| 9 | MT（磁粉）检测 | mt_test |
| 10 | PT（渗透）检测 | pt_test |
| 11 | UT（超声）检测 | ut_test |
| 12 | 其他无损检测 | other_ndt |
| 13 | 硬度检测 | hardness_test |
| 14 | 金相检测 | metallography |
| 15 | 铁素体检测 | ferrite_test |
| 16 | 检验结果评定 | result_evaluation |
| 17 | 返修 | rework |
| 18 | 返修结果确认 | final_confirm |

### 数据填写规则

- **数字（1-8）**：表示该工序需要执行的次数
- **空白/NaN**：表示该工序不需要执行
- **空格(" ")**：也表示不需要执行

**示例数据：**
```
管道编号: AV-32130
- 搭架子: 1 (需要执行1次)
- 拆保温: 1 (需要执行1次)
- 打磨: 1 (需要执行1次)
- 宏观检查: 1 (需要执行1次)
- 壁厚测定: 1 (需要执行1次)
- RT检测: (空，不需要)
- MT检测: (空，不需要)
...
```

---

## 🚀 使用步骤

### 步骤1：创建数据库表

在MySQL中执行以下SQL脚本：

```bash
mysql -u your_username -p your_database < demo/src/sql/pipeline_card_table.sql
```

或手动复制SQL内容到MySQL客户端执行。

### 步骤2：启动后端服务

1. 确保Maven依赖已安装（包含Apache POI）
2. 启动Spring Boot应用：

```bash
cd demo
mvn spring-boot:run
```

或在IDEA中运行 `DemoApplication`。

### 步骤3：启动前端服务

```bash
cd vuedemo2
npm install  # 首次运行需要
npm run serve
```

### 步骤4：使用导入功能

1. 打开浏览器访问前端页面（通常是 `http://localhost:8080`）
2. 进入 **工序管理** 页面
3. 点击右上角 **"导入开卡Excel"** 按钮
4. 在弹出的对话框中：
   - 拖拽或点击选择Excel文件
   - 点击 **"开始导入"** 按钮
5. 等待导入完成，查看导入结果

---

## ⚠️ 注意事项

### 1. 文件要求

- ✅ 支持格式：`.xlsx` 或 `.xls`
- ✅ 文件大小：不超过 10MB
- ✅ 表头：第一行必须是表头（会被跳过）
- ✅ 数据从第二行开始

### 2. 数据验证

- ❌ **管道编号不能为空**
- ❌ **管道编号不能重复**（如果重复会报错并跳过该行）
- ✅ 其他字段允许为空

### 3. 导入结果

导入完成后会显示：
- ✅ 成功导入的记录数
- ❌ 失败的记录数
- 📝 详细的错误信息列表

### 4. 回滚机制

- 如果某一行导入失败，**不会影响其他行**
- 已成功的行会保存到数据库
- 失败的行会在错误列表中显示

---

## 📁 文件清单

### 后端文件

```
demo/src/
├── sql/
│   └── pipeline_card_table.sql              # 数据库表创建脚本
├── main/java/com/example/demo/
│   ├── entity/
│   │   ├── PipelineCard.java                # 管道开卡主表实体
│   │   └── PipelineCardProcess.java         # 工序明细表实体
│   ├── mapper/
│   │   ├── PipelineCardMapper.java          # 主表Mapper
│   │   └── PipelineCardProcessMapper.java   # 明细表Mapper
│   ├── service/
│   │   ├── PipelineCardService.java         # 主表Service接口
│   │   ├── PipelineCardProcessService.java  # 明细表Service接口
│   │   └── impl/
│   │       ├── PipelineCardServiceImpl.java         # 核心Excel解析逻辑
│   │       └── PipelineCardProcessServiceImpl.java  # 明细表Service实现
│   └── controller/
│       └── PipelineCardController.java      # 导入接口Controller
└── main/resources/mapper/
    ├── PipelineCardMapper.xml               # 主表Mapper XML
    └── PipelineCardProcessMapper.xml        # 明细表Mapper XML
```

### 前端文件

```
vuedemo2/src/components/process/
└── ProcessManage.vue                        # 工序管理页面（已添加导入功能）
```

### 依赖配置

```
demo/pom.xml                                 # 已添加Apache POI依赖
```

---

## 🔧 API接口说明

### 导入Excel接口

**URL:** `POST /pipelineCard/import`

**Content-Type:** `multipart/form-data`

**请求参数:**
- `file`: Excel文件（文件类型）

**响应格式:**

```json
{
  "code": 200,
  "msg": "success",
  "data": {
    "success": true,
    "successCount": 48,
    "failCount": 2,
    "totalCount": 50,
    "message": "导入完成！成功 48 条，失败 2 条",
    "errors": [
      "第5行：管道编号 BD-12345 已存在，不允许重复导入",
      "第12行：管道编号为空，已跳过"
    ]
  }
}
```

**错误响应:**

```json
{
  "code": 500,
  "msg": "导入失败：文件格式错误",
  "data": null
}
```

---

## 🧪 测试建议

### 1. 正常导入测试

使用项目根目录下的测试文件：
```
压力管道检验预定表-课题系统测试数据.xlsx
```

预期结果：成功导入50条管道记录，每条记录包含16个工序明细。

### 2. 重复导入测试

再次导入同一个文件，预期结果：
- 所有记录失败（管道编号重复）
- 错误信息明确提示

### 3. 格式错误测试

上传非Excel文件（如.txt、.pdf），预期结果：
- 导入失败
- 提示"只支持Excel文件格式"

### 4. 查询验证

导入成功后，在MySQL中查询：

```sql
-- 查询管道主表
SELECT * FROM pipeline_card LIMIT 10;

-- 查询某个管道的工序明细
SELECT p.process_name, p.process_code, p.required_count
FROM pipeline_card_process p
INNER JOIN pipeline_card c ON p.card_id = c.id
WHERE c.pipeline_code = 'AV-32130';

-- 统计各工序出现次数
SELECT process_name, COUNT(*) as count
FROM pipeline_card_process
WHERE required_count IS NOT NULL AND required_count != ''
GROUP BY process_name
ORDER BY count DESC;
```

---

## 💡 后续扩展建议

1. **数据可视化**：在前端展示已导入的管道列表和工序统计
2. **批量操作**：支持批量删除、批量修改状态
3. **工序调度**：基于导入的数据生成工序调度方案
4. **导出功能**：将数据库中的数据导出为Excel
5. **模板下载**：提供标准Excel模板下载

---

## ❓ 常见问题

### Q1: 导入时提示"管道编号已存在"怎么办？

**A:** 这是正常的防重复机制。如果需要更新已有数据，请先删除数据库中的旧记录，或修改Excel中的管道编号。

### Q2: 某些工序列为空怎么办？

**A:** 完全正常！系统会原样保存所有列（包括空值），这样可以准确反映哪些工序需要执行，哪些不需要。

### Q3: 如何清空已导入的数据？

**A:** 执行以下SQL：

```sql
DELETE FROM pipeline_card_process;
DELETE FROM pipeline_card;
```

### Q4: 导入后在哪里查看数据？

**A:** 目前数据已存入数据库，可以通过MySQL客户端查看。后续可以在前端开发数据管理页面。

---

## 📞 技术支持

如有问题，请检查：
1. 后端服务是否正常启动（端口8088）
2. 数据库连接是否正常
3. Excel文件格式是否符合要求
4. 浏览器控制台是否有错误信息

---

**最后更新时间：** 2025-01-16

