package com.example.demo.mapper;

import com.example.demo.entity.Process;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import org.apache.ibatis.annotations.Mapper;

/**
 * <p>
 * 工序管理表 Mapper 接口
 * </p>
 *
 * @author demo
 * @since 2024-12-30
 */
@Mapper
public interface ProcessMapper extends BaseMapper<Process> {
    IPage pageCC(Page<Process> page, LambdaQueryWrapper<Process> lambdaQueryWrapper);
}
