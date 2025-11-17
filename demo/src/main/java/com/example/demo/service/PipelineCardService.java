package com.example.demo.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.example.demo.entity.PipelineCard;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

/**
 * <p>
 * 管道开卡服务接口
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
public interface PipelineCardService extends IService<PipelineCard> {

    /**
     * 导入Excel文件，将管道开卡数据存入数据库
     * 
     * @param file Excel文件
     * @return 导入结果，包含成功数量、失败数量、错误信息等
     * @throws Exception 导入异常
     */
    Map<String, Object> importExcel(MultipartFile file) throws Exception;
}

