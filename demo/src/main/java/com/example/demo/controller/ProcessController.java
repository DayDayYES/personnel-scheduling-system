package com.example.demo.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.StringUtils;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.demo.common.QueryPageParam;
import com.example.demo.common.Result;
import com.example.demo.entity.Process;
import com.example.demo.service.ProcessService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;

/**
 * <p>
 * 工序管理表 前端控制器
 * </p>
 *
 * @author demo
 * @since 2024-12-30
 */
@RestController
@RequestMapping("/process")
public class ProcessController {

    @Autowired
    private ProcessService processService;

    @GetMapping("/list")
    public List<Process> list(){
        return processService.list();
    }

    // 添加一个简单的测试接口
    @GetMapping("/test")
    public Result test(){
        return Result.suc("Process接口正常工作!");
    }

    @GetMapping("/findByName")
    public Result findByName(@RequestParam String processName){
        List list = processService.lambdaQuery().eq(Process::getProcessName, processName).list();
        return list.size() > 0 ? Result.suc(list) : Result.fail();
    }

    //新增
    @PostMapping("/save")
    public Result save(@RequestBody Process process){
        try {
            System.out.println("接收到的工序数据: " + process);
            // 设置默认值
            if (process.getIsvalid() == null) {
                process.setIsvalid("Y");
            }
            boolean result = processService.save(process);
            System.out.println("保存结果: " + result);
            return result ? Result.suc() : Result.fail();
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail();
        }
    }

    //更新
    @PostMapping("/update")
    public Result update(@RequestBody Process process){
        return processService.updateById(process) ? Result.suc() : Result.fail();
    }

    //删除
    @GetMapping("/del")
    public Result del(@RequestParam String id){
        return processService.removeById(id) ? Result.suc() : Result.fail();
    }

    //分页查询
    @PostMapping("/listPageC1")
    public Result listPageC1(@RequestBody QueryPageParam query){
        try {
            HashMap param = query.getParam();
            String processName = (String)param.get("processName");
            String stage = (String)param.get("stage");
            String teamId = (String)param.get("teamId");
            String isShared = (String)param.get("isShared");

            Page<Process> page = new Page();
            page.setCurrent(query.getPageNum());
            page.setSize(query.getPageSize());

            LambdaQueryWrapper<Process> lambdaQueryWrapper = new LambdaQueryWrapper<>();
            // 临时简化查询条件，只添加基本的非空过滤
            if(StringUtils.isNotBlank(processName) && !"null".equals(processName)){
                lambdaQueryWrapper.like(Process::getProcessName, processName);
            }
            // LambdaQueryWrapper<Process> lambdaQueryWrapper = new LambdaQueryWrapper();
            // if(StringUtils.isNotBlank(processName) && !"null".equals(processName)){
            //     lambdaQueryWrapper.like(Process::getProcessName, processName);
            // }
            // if(StringUtils.isNotBlank(stage)){
            //     lambdaQueryWrapper.eq(Process::getStage, stage);
            // }
            // if(StringUtils.isNotBlank(teamId)){
            //     lambdaQueryWrapper.eq(Process::getTeamId, teamId);
            // }
            // if(StringUtils.isNotBlank(isShared)){
            //     lambdaQueryWrapper.eq(Process::getIsShared, isShared);
            // }

            // System.out.println("分页参数 - pageNum: " + query.getPageNum() + ", pageSize: " + query.getPageSize());
            // System.out.println("查询条件 - processName: " + processName);

            IPage result = processService.page(page, lambdaQueryWrapper);

            // System.out.println("查询结果 - 总数: " + result.getTotal() + ", 当前页数据量: " + result.getRecords().size());

            return Result.suc(result.getRecords(), result.getTotal());
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail();
        }
    }
}