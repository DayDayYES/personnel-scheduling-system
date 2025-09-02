package com.example.demo.service.impl;

import com.example.demo.entity.Process;
import com.example.demo.mapper.ProcessMapper;
import com.example.demo.service.ProcessService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import org.springframework.stereotype.Service;

/**
 * <p>
 * 工序管理表 服务实现类
 * </p>
 *
 * @author demo
 * @since 2024-12-30
 */
@Service
public class ProcessServiceImpl extends ServiceImpl<ProcessMapper, Process> implements ProcessService {
    @Override
    public IPage pageCC(Page<Process> page, LambdaQueryWrapper<Process> lambdaQueryWrapper) {
        return baseMapper.pageCC(page, lambdaQueryWrapper);
    }
}