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
import java.util.List;

/**
 * <p>
 * 管道开卡主表
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("pipeline_card")
@ApiModel(value="PipelineCard对象", description="管道开卡主表")
public class PipelineCard implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "主键")
    @TableId(value = "id", type = IdType.AUTO)
    private Integer id;

    @ApiModelProperty(value = "管道序号（Excel第1列）")
    @TableField("card_no")
    private String cardNo;

    @ApiModelProperty(value = "管道编号（Excel第2列）")
    @TableField("pipeline_code")
    private String pipelineCode;

    @ApiModelProperty(value = "状态：pending待处理/processing处理中/completed已完成")
    @TableField("status")
    private String status;

    @ApiModelProperty(value = "创建时间")
    @TableField("create_time")
    private LocalDateTime createTime;

    @ApiModelProperty(value = "更新时间")
    @TableField("update_time")
    private LocalDateTime updateTime;

    // 不映射到数据库，用于返回工序明细列表
    @TableField(exist = false)
    private List<PipelineCardProcess> processes;
}

