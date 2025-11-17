-- 工序规则配置表
-- 存储每个工序的基础配置信息（工作时长、阶段、团队等）

DROP TABLE IF EXISTS `process_rule`;

CREATE TABLE `process_rule` (
  `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `process_code` VARCHAR(50) NOT NULL COMMENT '工序代码（如scaffold、remove_insulation等）',
  `process_name` VARCHAR(100) NOT NULL COMMENT '工序名称（如搭架子、拆保温等）',
  `base_duration` DECIMAL(10, 2) DEFAULT 0 COMMENT '基础工作时长',
  `duration_unit` VARCHAR(20) DEFAULT '小时' COMMENT '时长单位（小时/分钟/天）',
  `stage_order` INT(11) DEFAULT 1 COMMENT '阶段顺序（1-10）',
  `team_name` VARCHAR(50) DEFAULT 'team1' COMMENT '所属团队（team1-team6）',
  `team_size` INT(11) DEFAULT 10 COMMENT '团队规模（总人数）',
  `description` VARCHAR(500) DEFAULT NULL COMMENT '备注说明',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_process_code` (`process_code`) COMMENT '工序代码唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工序规则配置表';

-- 插入16个工序的初始配置数据
-- 注意：同一阶段内的工序默认可并行（只要满足团队约束）
INSERT INTO `process_rule` (`process_code`, `process_name`, `base_duration`, `duration_unit`, `stage_order`, `team_name`, `team_size`) VALUES
('scaffold', '搭架子', 2.0, '小时', 1, 'team1', 10),
('remove_insulation', '拆保温', 1.5, '小时', 2, 'team1', 10),
('grinding', '打磨', 1.0, '小时', 3, 'team2', 8),
('macro_inspection', '宏观检查', 0.5, '小时', 4, 'team3', 5),
('thickness_test', '测厚', 1.0, '小时', 5, 'team3', 5),
('rt_test', 'RT检测', 2.0, '小时', 6, 'team4', 6),
('mt_test', 'MT检测', 1.5, '小时', 6, 'team4', 6),
('pt_test', 'PT检测', 1.5, '小时', 6, 'team4', 6),
('ut_test', 'UT检测', 2.0, '小时', 6, 'team4', 6),
('other_ndt', '其他NDT', 1.0, '小时', 7, 'team4', 6),
('hardness_test', '硬度测试', 1.0, '小时', 8, 'team5', 4),
('metallography', '金相检验', 2.0, '小时', 8, 'team5', 4),
('ferrite_test', '铁素体测定', 1.5, '小时', 8, 'team5', 4),
('result_evaluation', '结果评定', 0.5, '小时', 9, 'team6', 3),
('rework', '返工', 3.0, '小时', 10, 'team2', 8),
('final_confirm', '最终确认', 0.5, '小时', 11, 'team6', 3);

-- 查询验证
SELECT * FROM process_rule ORDER BY stage_order, process_code;

