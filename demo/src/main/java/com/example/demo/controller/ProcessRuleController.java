package com.example.demo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.example.demo.common.Result;
import com.example.demo.entity.ProcessRule;
import com.example.demo.service.ProcessRuleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * <p>
 * 工序规则配置控制器
 * 处理规则的查询、更新等功能
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
@RestController
@RequestMapping("/processRule")
public class ProcessRuleController {

    @Autowired
    private ProcessRuleService processRuleService;

    /**
     * 查询所有工序规则（按阶段顺序排序）
     * 
     * @return 工序规则列表
     */
    @GetMapping("/list")
    public Result list() {
        try {
            QueryWrapper<ProcessRule> queryWrapper = new QueryWrapper<>();
            queryWrapper.orderByAsc("stage_order", "process_code");
            
            List<ProcessRule> rules = processRuleService.list(queryWrapper);
            return Result.suc(rules);
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("查询失败：" + e.getMessage());
        }
    }

    /**
     * 根据工序代码查询单个规则
     * 
     * @param processCode 工序代码
     * @return 工序规则
     */
    @GetMapping("/getByCode/{processCode}")
    public Result getByCode(@PathVariable String processCode) {
        try {
            QueryWrapper<ProcessRule> queryWrapper = new QueryWrapper<>();
            queryWrapper.eq("process_code", processCode);
            
            ProcessRule rule = processRuleService.getOne(queryWrapper);
            if (rule == null) {
                return Result.fail("工序规则不存在");
            }
            return Result.suc(rule);
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("查询失败：" + e.getMessage());
        }
    }

    /**
     * 更新工序规则
     * 
     * @param rule 工序规则对象
     * @return 更新结果
     */
    @PostMapping("/update")
    public Result update(@RequestBody ProcessRule rule) {
        try {
            if (rule.getId() == null) {
                return Result.fail("规则ID不能为空");
            }
            
            boolean success = processRuleService.updateById(rule);
            if (success) {
                return Result.suc("更新成功");
            } else {
                return Result.fail("更新失败");
            }
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("更新失败：" + e.getMessage());
        }
    }

    /**
     * 批量更新工序规则
     * 
     * @param rules 工序规则列表
     * @return 更新结果
     */
    @PostMapping("/batchUpdate")
    public Result batchUpdate(@RequestBody List<ProcessRule> rules) {
        try {
            if (rules == null || rules.isEmpty()) {
                return Result.fail("规则列表不能为空");
            }
            
            boolean success = processRuleService.updateBatchById(rules);
            if (success) {
                return Result.suc("批量更新成功");
            } else {
                return Result.fail("批量更新失败");
            }
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("批量更新失败：" + e.getMessage());
        }
    }

    /**
     * 重置所有规则为默认值
     * （可选功能，根据需要实现）
     * 
     * @return 重置结果
     */
    @PostMapping("/reset")
    public Result reset() {
        try {
            // 这里可以实现重置逻辑，比如从配置文件读取默认值
            return Result.suc("重置成功");
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("重置失败：" + e.getMessage());
        }
    }
}

