package com.example.demo.service;

import com.example.demo.entity.Process;
import com.baomidou.mybatisplus.extension.service.IService;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;

/**
 * <p>
 * 工序管理表 服务类
 * </p>
 *
 * @author demo
 * @since 2024-12-30
 */
public interface ProcessService extends IService<Process> {
    IPage pageCC(Page<Process> page, LambdaQueryWrapper<Process> lambdaQueryWrapper);
}