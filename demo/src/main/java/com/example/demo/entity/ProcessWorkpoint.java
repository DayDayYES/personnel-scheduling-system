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
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * <p>
 * 工作点工序表 - 对应 process_workpoint_1, process_workpoint_2, process_workpoint_3
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("process_workpoint")  // 基础表名，将通过动态表名插件替换
@ApiModel(value="ProcessWorkpoint对象", description="工作点工序信息表")
public class ProcessWorkpoint implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "主键")
    @TableId(value = "id", type = IdType.AUTO)
    private Integer id;

    @ApiModelProperty(value = "工序名称")
    @TableField("process_name")
    private String processName;

    @ApiModelProperty(value = "工序顺序（阶段）")
    @TableField("process_order")
    private Integer processOrder;

    @ApiModelProperty(value = "团队名称")
    @TableField("team_name")
    private String teamName;

    @ApiModelProperty(value = "是否专用团队（1=是，0=否）")
    @TableField("is_dedicated")
    private Boolean isDedicated;

    @ApiModelProperty(value = "团队规模（人数）")
    @TableField("team_size")
    private Integer teamSize;

    @ApiModelProperty(value = "工序持续时间")
    @TableField("duration")
    private BigDecimal duration;

    @ApiModelProperty(value = "是否可并行执行（1=是，0=否）")
    @TableField("is_parallel")
    private Boolean isParallel;

    @ApiModelProperty(value = "创建时间")
    @TableField("created_at")
    private LocalDateTime createdAt;

    @ApiModelProperty(value = "更新时间")
    @TableField("updated_at")
    private LocalDateTime updatedAt;

    // 用于前端显示的工作点ID（不映射到数据库）
    @TableField(exist = false)
    private String workpointId;
}

