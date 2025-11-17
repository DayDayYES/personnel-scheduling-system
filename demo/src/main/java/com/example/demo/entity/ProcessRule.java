package com.example.demo.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * <p>
 * 工序规则配置实体类
 * 存储每个工序的基础配置信息
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
@Data
@TableName("process_rule")
public class ProcessRule implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 主键ID
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Integer id;

    /**
     * 工序代码（如scaffold、remove_insulation等）
     */
    @TableField("process_code")
    private String processCode;

    /**
     * 工序名称（如搭架子、拆保温等）
     */
    @TableField("process_name")
    private String processName;

    /**
     * 基础工作时长
     */
    @TableField("base_duration")
    private BigDecimal baseDuration;

    /**
     * 时长单位（小时/分钟/天）
     */
    @TableField("duration_unit")
    private String durationUnit;

    /**
     * 阶段顺序（1-10）
     */
    @TableField("stage_order")
    private Integer stageOrder;

    /**
     * 所属团队（team1-team6）
     */
    @TableField("team_name")
    private String teamName;

    /**
     * 团队规模（总人数）
     */
    @TableField("team_size")
    private Integer teamSize;

    /**
     * 备注说明
     */
    @TableField("description")
    private String description;

    /**
     * 创建时间
     */
    @TableField("create_time")
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    @TableField("update_time")
    private LocalDateTime updateTime;
}

