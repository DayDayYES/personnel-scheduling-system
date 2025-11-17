package com.example.demo.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
 * <p>
 * 管道开卡工序明细表
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("pipeline_card_process")
@ApiModel(value="PipelineCardProcess对象", description="管道开卡工序明细表")
public class PipelineCardProcess implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "主键")
    @TableId(value = "id", type = IdType.AUTO)
    private Integer id;

    @ApiModelProperty(value = "开卡主表ID")
    @TableField("card_id")
    private Integer cardId;

    @ApiModelProperty(value = "工序名称")
    @TableField("process_name")
    private String processName;

    @ApiModelProperty(value = "工序代码（英文标识）")
    @TableField("process_code")
    private String processCode;

    @ApiModelProperty(value = "需要执行次数（存储原始值）")
    @TableField("required_count")
    private String requiredCount;

    @ApiModelProperty(value = "工序在Excel中的列序号")
    @TableField("process_order")
    private Integer processOrder;

    @ApiModelProperty(value = "创建时间")
    @TableField("create_time")
    private LocalDateTime createTime;
}

