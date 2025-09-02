package com.example.demo.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableField;
import java.io.Serializable;
import java.time.LocalDateTime;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;
import lombok.EqualsAndHashCode;
import com.baomidou.mybatisplus.annotation.TableName;

/**
 * <p>
 * 工序管理表
 * </p>
 *
 * @author demo
 * @since 2025-9-2
 */
@Data
@EqualsAndHashCode(callSuper = false)
@TableName("process")
@ApiModel(value="Process对象", description="工序管理表")
public class Process implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "主键")
    @TableId(value = "id", type = IdType.AUTO)
    private Integer id;

    @ApiModelProperty(value = "工序名称")
    @TableField("process_name")
    private String processName;

    @ApiModelProperty(value = "时长（分钟）")
    private Integer duration;

    @ApiModelProperty(value = "阶段")
    private Integer stage;

    @ApiModelProperty(value = "所属团队")
    @TableField("team_id")
    private Integer teamId;

    @ApiModelProperty(value = "人员共用还是专用，0专用1共用")
    @TableField("is_shared")
    private Boolean isShared;

    @ApiModelProperty(value = "是否有效，Y有效，其他无效")
    @TableField("isValid")
    private String isvalid;

    @ApiModelProperty(value = "创建时间")
    @TableField("create_time")
    private LocalDateTime createTime;

    @ApiModelProperty(value = "更新时间")
    @TableField("update_time")
    private LocalDateTime updateTime;
}
