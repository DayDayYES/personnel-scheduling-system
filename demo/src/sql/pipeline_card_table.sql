-- 管道开卡主表（存储管道基本信息）
-- CREATE TABLE pipeline_card (
--     id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
--     card_no VARCHAR(50) NOT NULL COMMENT '管道序号（Excel第1列）',
--     pipeline_code VARCHAR(100) NOT NULL UNIQUE COMMENT '管道编号（Excel第2列）',
--     status VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending待处理/processing处理中/completed已完成',
--     create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
--     update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
--     UNIQUE KEY uk_pipeline_code (pipeline_code),
--     INDEX idx_card_no (card_no),
--     INDEX idx_status (status)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管道开卡主表';

-- -- 管道开卡工序明细表（存储每个管道的工序需求，原样保存Excel数据）
-- CREATE TABLE pipeline_card_process (
--     id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
--     card_id INT NOT NULL COMMENT '开卡主表ID',
--     process_name VARCHAR(100) NOT NULL COMMENT '工序名称',
--     process_code VARCHAR(50) NOT NULL COMMENT '工序代码（英文标识）',
--     required_count VARCHAR(20) COMMENT '需要执行次数（存储原始值：数字/空格/NaN）',
--     process_order INT COMMENT '工序在Excel中的列序号',
--     create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
--     FOREIGN KEY (card_id) REFERENCES pipeline_card(id) ON DELETE CASCADE,
--     INDEX idx_card_id (card_id),
--     INDEX idx_process_code (process_code)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管道开卡工序明细表';

-- 插入说明数据（用于参考Excel列映射关系）
-- Excel列 -> 工序代码映射：
-- 列3: 搭架子 -> scaffold
-- 列4: 拆保温 -> remove_insulation
-- 列5: 打磨 -> grinding
-- 列6: 宏观检查 -> macro_inspection
-- 列7: 壁厚测定 -> thickness_test
-- 列8: RT（射线）检测 -> rt_test
-- 列9: MT（磁粉）检测 -> mt_test
-- 列10: PT（渗透）检测 -> pt_test
-- 列11: UT（超声）检测 -> ut_test
-- 列12: 其他无损检测 -> other_ndt
-- 列13: 硬度检测 -> hardness_test
-- 列14: 金相检测 -> metallography
-- 列15: 铁素体检测 -> ferrite_test
-- 列16: 检验结果评定 -> result_evaluation
-- 列17: 返修 -> rework
-- 列18: 返修结果确认，合格报告出具 -> final_confirm



CREATE TABLE pipeline_card (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    card_no VARCHAR(50) NOT NULL COMMENT '管道序号（Excel第1列）',
    pipeline_code VARCHAR(100) NOT NULL UNIQUE COMMENT '管道编号（Excel第2列）',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending待处理/processing处理中/completed已完成',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_pipeline_code (pipeline_code),
    INDEX idx_card_no (card_no),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管道开卡主表';