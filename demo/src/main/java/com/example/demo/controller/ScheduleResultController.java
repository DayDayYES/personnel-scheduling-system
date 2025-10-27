package com.example.demo.controller;

import com.example.demo.common.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.*;
import java.util.regex.Pattern;

/**
 * 调度结果管理控制器
 * 用于加载和展示历史调度结果
 */
@RestController
@RequestMapping("/schedule_results")
@CrossOrigin
public class ScheduleResultController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    /**
     * 获取调度结果表列表
     * @param limit 返回记录数量，默认50
     * @return 调度结果表列表
     */
    @GetMapping("/list")
    public Result listScheduleResults(@RequestParam(defaultValue = "50") int limit) {
        try {
            System.out.println("📋 获取调度结果表列表，限制: " + limit);

            // 查询所有 schedule_result_* 表
            String query = "SELECT " +
                "table_name, " +
                "table_comment, " +
                "create_time " +
                "FROM information_schema.tables " +
                "WHERE table_schema = DATABASE() " +
                "AND table_name LIKE 'schedule_result_%' " +
                "ORDER BY create_time DESC " +
                "LIMIT ?";

            List<Map<String, Object>> tables = jdbcTemplate.queryForList(query, limit);

            if (tables.isEmpty()) {
                System.out.println("⚠️  未找到调度结果表");
                return Result.suc(new ArrayList<>());
            }

            // 为每个表计算统计信息
            List<Map<String, Object>> resultList = new ArrayList<>();
            for (Map<String, Object> table : tables) {
                String tableName = (String) table.get("table_name");
                String tableComment = (String) table.get("table_comment");
                Object createTime = table.get("create_time");

                try {
                    // 查询任务数量
                    String countQuery = "SELECT COUNT(*) FROM `" + tableName + "`";
                    Integer taskCount = jdbcTemplate.queryForObject(countQuery, Integer.class);

                    // 查询完工时间（最大end_time）
                    String makespanQuery = "SELECT MAX(end_time) FROM `" + tableName + "`";
                    BigDecimal makespan = jdbcTemplate.queryForObject(makespanQuery, BigDecimal.class);

                    // 构建结果对象
                    Map<String, Object> resultItem = new HashMap<>();
                    resultItem.put("tableName", tableName);
                    resultItem.put("comment", tableComment != null ? tableComment : "调度结果");
                    resultItem.put("createdTime", createTime != null ? createTime.toString() : "");
                    resultItem.put("taskCount", taskCount != null ? taskCount : 0);
                    resultItem.put("makespan", makespan != null ? makespan.doubleValue() : 0.0);

                    resultList.add(resultItem);

                } catch (Exception e) {
                    System.err.println("❌ 查询表 " + tableName + " 统计信息失败: " + e.getMessage());
                    // 如果某个表查询失败，跳过该表继续处理其他表
                    continue;
                }
            }

            System.out.println("✅ 成功获取 " + resultList.size() + " 个调度结果表");
            return Result.suc(resultList, (long) resultList.size());

        } catch (Exception e) {
            System.err.println("❌ 获取调度结果表列表失败: " + e.getMessage());
            e.printStackTrace();
            return Result.fail("获取调度结果列表失败: " + e.getMessage());
        }
    }

    /**
     * 获取指定调度结果表的数据
     * @param tableName 表名
     * @return 调度数据列表
     */
    @GetMapping("/{tableName}")
    public Result getScheduleData(@PathVariable String tableName) {
        try {
            System.out.println("📖 读取调度结果表: " + tableName);

            // 验证表名（防止SQL注入）
            if (!isValidTableName(tableName)) {
                System.err.println("❌ 非法的表名: " + tableName);
                return Result.fail("非法的表名");
            }

            // 检查表是否存在
            String checkQuery = "SELECT COUNT(*) " +
                "FROM information_schema.tables " +
                "WHERE table_schema = DATABASE() " +
                "AND table_name = ?";
            Integer count = jdbcTemplate.queryForObject(checkQuery, Integer.class, tableName);

            if (count == null || count == 0) {
                System.err.println("❌ 表不存在: " + tableName);
                return Result.fail("调度结果表不存在");
            }

            // 检查表结构，判断是新表还是旧表
            String columnCheckQuery = "SELECT COLUMN_NAME " +
                "FROM information_schema.COLUMNS " +
                "WHERE TABLE_SCHEMA = DATABASE() " +
                "AND TABLE_NAME = ? " +
                "AND COLUMN_NAME = 'team_id'";
            List<Map<String, Object>> columns = jdbcTemplate.queryForList(columnCheckQuery, tableName);
            boolean isNewStructure = !columns.isEmpty();

            // 根据表结构选择查询SQL
            String dataQuery;
            if (isNewStructure) {
                // 新表结构（有team_id和team_name）
                dataQuery = String.format(
                    "SELECT " +
                    "task_id, " +
                    "task_name, " +
                    "workpoint_id, " +
                    "workpoint_name, " +
                    "team_id, " +
                    "team_name, " +
                    "start_time, " +
                    "end_time, " +
                    "duration, " +
                    "workers, " +
                    "process_order " +
                    "FROM `%s` " +
                    "ORDER BY start_time, task_id",
                    tableName
                );
            } else {
                // 旧表结构（有team字符串）
                dataQuery = String.format(
                    "SELECT " +
                    "task_id, " +
                    "task_name, " +
                    "workpoint_id, " +
                    "workpoint_name, " +
                    "team, " +
                    "start_time, " +
                    "end_time, " +
                    "duration, " +
                    "workers, " +
                    "process_order " +
                    "FROM `%s` " +
                    "ORDER BY start_time, task_id",
                    tableName
                );
            }

            List<Map<String, Object>> rawData = jdbcTemplate.queryForList(dataQuery);

            // 转换数据格式（适配前端）
            List<Map<String, Object>> scheduleData = new ArrayList<>();
            for (Map<String, Object> row : rawData) {
                Map<String, Object> task = new HashMap<>();

                // 基本字段
                task.put("id", row.get("task_id"));
                task.put("name", row.get("task_name"));
                task.put("workpoint_name", row.get("workpoint_name"));
                task.put("start", ((BigDecimal) row.get("start_time")).doubleValue());
                task.put("end", ((BigDecimal) row.get("end_time")).doubleValue());
                task.put("workers", row.get("workers"));
                task.put("order", row.get("process_order"));

                // 转换 workpoint_id
                if (isNewStructure) {
                    // 新表：workpoint_id 是 INT，转为 "workpoint_X"
                    Integer wpId = (Integer) row.get("workpoint_id");
                    task.put("workpoint_id", "workpoint_" + wpId);

                    // 转换 team
                    Integer teamId = (Integer) row.get("team_id");
                    task.put("team", "team" + teamId);
                } else {
                    // 旧表：直接使用原字段
                    task.put("workpoint_id", row.get("workpoint_id"));
                    task.put("team", row.get("team"));
                }

                scheduleData.add(task);
            }

            System.out.println("✅ 成功读取 " + scheduleData.size() + " 条调度数据");
            return Result.suc(scheduleData, (long) scheduleData.size());

        } catch (Exception e) {
            System.err.println("❌ 读取调度数据失败: " + e.getMessage());
            e.printStackTrace();
            return Result.fail("读取调度数据失败: " + e.getMessage());
        }
    }

    /**
     * 验证表名是否合法（防止SQL注入）
     * @param tableName 表名
     * @return 是否合法
     */
    private boolean isValidTableName(String tableName) {
        if (tableName == null || tableName.trim().isEmpty()) {
            return false;
        }

        // 只允许 schedule_result_ 开头，后面跟数字和下划线
        Pattern pattern = Pattern.compile("^schedule_result_\\d{8}_\\d{6}$");
        return pattern.matcher(tableName).matches();
    }
}

