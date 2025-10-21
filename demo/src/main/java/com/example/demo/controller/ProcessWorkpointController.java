package com.example.demo.controller;

import com.example.demo.common.QueryPageParam;
import com.example.demo.common.Result;
import com.example.demo.entity.ProcessWorkpoint;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.BeanPropertyRowMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

/**
 * <p>
 * 工作点工序管理控制器
 * 处理不同工作点的工序数据
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
@RestController
@RequestMapping("/process")
public class ProcessWorkpointController {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    /**
     * 根据工作点ID获取对应的表名
     */
    private String getTableName(String workpointId) {
        if (workpointId == null || !workpointId.startsWith("workpoint_")) {
            throw new IllegalArgumentException("无效的工作点ID: " + workpointId);
        }
        return "process_" + workpointId;
    }

    /**
     * 验证工作点ID的有效性
     */
    private boolean isValidWorkpointId(String workpointId) {
        return workpointId != null && workpointId.matches("workpoint_\\d+");
    }

    /**
     * 验证表名安全性（防止SQL注入）
     */
    private String sanitizeTableName(String tableName) {
        if (tableName == null || !tableName.matches("process_workpoint_\\d+")) {
            throw new IllegalArgumentException("无效的表名");
        }
        return tableName;
    }

    /**
     * 获取所有工作点列表
     * 通过查询数据库中所有 process_workpoint_* 表
     * 
     * @return 工作点列表
     */
    @GetMapping("/workpoints")
    public Result getWorkpoints() {
        try {
            // 查询所有以 process_workpoint_ 开头的表
            String sql = "SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES " +
                       "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME LIKE 'process_workpoint_%' " +
                       "ORDER BY TABLE_NAME";
            
            List<HashMap<String, Object>> tables = (List<HashMap<String, Object>>) jdbcTemplate.query(sql, 
                (rs, rowNum) -> {
                    HashMap<String, Object> map = new HashMap<>();
                    String tableName = rs.getString("TABLE_NAME");
                    String tableComment = rs.getString("TABLE_COMMENT");
                    
                    // 从表名提取工作点ID (process_workpoint_1 -> workpoint_1)
                    String workpointId = tableName.replace("process_", "");
                    
                    // 从表注释中提取工作点名称，如果没有注释则使用默认名称
                    String workpointName = tableComment;
                    if (workpointName == null || workpointName.isEmpty()) {
                        // 从workpoint_1提取数字，生成默认名称
                        String num = workpointId.replace("workpoint_", "");
                        workpointName = "工作点" + num;
                    } else {
                        // 如果注释包含"工序信息表"等后缀，去掉它
                        // 例如："工作点1工序信息表" -> "工作点1"
                        workpointName = workpointName
                            .replace("工序信息表", "")
                            .replace("工序表", "")
                            .replace("信息表", "")
                            .trim();
                        
                        // 如果处理后为空，使用默认名称
                        if (workpointName.isEmpty()) {
                            String num = workpointId.replace("workpoint_", "");
                            workpointName = "工作点" + num;
                        }
                    }
                    
                    map.put("id", workpointId);
                    map.put("name", workpointName);
                    map.put("tableName", tableName);
                    return map;
                });
            
            // System.out.println("发现 " + tables.size() + " 个工作点表");
            return Result.suc(tables);
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("获取工作点列表失败: " + e.getMessage());
        }
    }

    /**
     * 分页查询指定工作点的工序
     * 
     * @param workpointId 工作点ID (workpoint_1, workpoint_2, workpoint_3, ...)
     * @param query 查询参数
     * @return 分页结果
     */
    @PostMapping("/{workpointId}/listPageC1")
    public Result listPageC1(@PathVariable String workpointId, @RequestBody QueryPageParam query) {
        try {
            // 验证工作点ID
            if (!isValidWorkpointId(workpointId)) {
                return Result.fail("无效的工作点ID");
            }

            String tableName = sanitizeTableName(getTableName(workpointId));
            @SuppressWarnings("unchecked")
            HashMap<String, Object> param = query.getParam();
            
            // 构建查询条件
            StringBuilder whereSql = new StringBuilder(" WHERE 1=1 ");
            List<Object> params = new ArrayList<>();
            
            String processName = (String) param.get("processName");
            if (processName != null && !"".equals(processName) && !"null".equals(processName)) {
                whereSql.append(" AND process_name LIKE ? ");
                params.add("%" + processName + "%");
            }
            
            Object processOrderObj = param.get("processOrder");
            if (processOrderObj != null && !"".equals(processOrderObj.toString())) {
                whereSql.append(" AND process_order = ? ");
                params.add(processOrderObj);
            }
            
            Object isDedicatedObj = param.get("isDedicated");
            if (isDedicatedObj != null && !"".equals(isDedicatedObj.toString())) {
                whereSql.append(" AND is_dedicated = ? ");
                params.add(isDedicatedObj);
            }
            
            Object isParallelObj = param.get("isParallel");
            if (isParallelObj != null && !"".equals(isParallelObj.toString())) {
                whereSql.append(" AND is_parallel = ? ");
                params.add(isParallelObj);
            }

            // 查询总数
            String countSql = "SELECT COUNT(*) FROM " + tableName + whereSql.toString();
            Long total = jdbcTemplate.queryForObject(countSql, Long.class, params.toArray());

            // 查询数据
            long offset = (query.getPageNum() - 1) * query.getPageSize();
            String dataSql = "SELECT * FROM " + tableName + whereSql.toString() + 
                           " ORDER BY process_order, id LIMIT ?, ?";
            params.add(offset);
            params.add((long) query.getPageSize());
            
            List<ProcessWorkpoint> records = jdbcTemplate.query(dataSql, 
                new BeanPropertyRowMapper<>(ProcessWorkpoint.class), params.toArray());
            
            // 为每条记录添加工作点ID
            records.forEach(record -> record.setWorkpointId(workpointId));

            // System.out.println("查询工作点: " + workpointId + ", 表名: " + tableName + 
            //                  ", 结果数量: " + records.size());

            return Result.suc(records, total);
        } catch (Exception e) {
            e.printStackTrace();
            System.err.println("查询失败: " + e.getMessage());
            return Result.fail("查询失败: " + e.getMessage());
        }
    }

    /**
     * 新增工序到指定工作点
     * 
     * @param workpointId 工作点ID
     * @param processWorkpoint 工序数据
     * @return 操作结果
     */
    @PostMapping("/{workpointId}/save")
    public Result save(@PathVariable String workpointId, @RequestBody ProcessWorkpoint processWorkpoint) {
        try {
            if (!isValidWorkpointId(workpointId)) {
                return Result.fail("无效的工作点ID");
            }

            String tableName = sanitizeTableName(getTableName(workpointId));
            System.out.println("保存工序到: " + tableName);
            System.out.println("工序数据: " + processWorkpoint);

            String sql = "INSERT INTO " + tableName + 
                       " (process_name, process_order, team_name, is_dedicated, team_size, duration, is_parallel, created_at) " +
                       " VALUES (?, ?, ?, ?, ?, ?, ?, NOW())";
            
            int rows = jdbcTemplate.update(sql,
                processWorkpoint.getProcessName(),
                processWorkpoint.getProcessOrder(),
                processWorkpoint.getTeamName(),
                processWorkpoint.getIsDedicated(),
                processWorkpoint.getTeamSize(),
                processWorkpoint.getDuration(),
                processWorkpoint.getIsParallel()
            );

            return rows > 0 ? Result.suc("保存成功") : Result.fail("保存失败");
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("保存失败: " + e.getMessage());
        }
    }

    /**
     * 更新指定工作点的工序
     * 
     * @param workpointId 工作点ID
     * @param processWorkpoint 工序数据
     * @return 操作结果
     */
    @PostMapping("/{workpointId}/update")
    public Result update(@PathVariable String workpointId, @RequestBody ProcessWorkpoint processWorkpoint) {
        try {
            if (!isValidWorkpointId(workpointId)) {
                return Result.fail("无效的工作点ID");
            }

            String tableName = sanitizeTableName(getTableName(workpointId));
            System.out.println("更新工序在: " + tableName);
            System.out.println("工序数据: " + processWorkpoint);

            String sql = "UPDATE " + tableName + 
                       " SET process_name=?, process_order=?, team_name=?, is_dedicated=?, " +
                       " team_size=?, duration=?, is_parallel=?, updated_at=NOW() " +
                       " WHERE id=?";
            
            int rows = jdbcTemplate.update(sql,
                processWorkpoint.getProcessName(),
                processWorkpoint.getProcessOrder(),
                processWorkpoint.getTeamName(),
                processWorkpoint.getIsDedicated(),
                processWorkpoint.getTeamSize(),
                processWorkpoint.getDuration(),
                processWorkpoint.getIsParallel(),
                processWorkpoint.getId()
            );

            return rows > 0 ? Result.suc("更新成功") : Result.fail("更新失败");
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("更新失败: " + e.getMessage());
        }
    }

    /**
     * 删除指定工作点的工序
     * 
     * @param workpointId 工作点ID
     * @param id 工序ID
     * @return 操作结果
     */
    @GetMapping("/{workpointId}/del")
    public Result del(@PathVariable String workpointId, @RequestParam Integer id) {
        try {
            if (!isValidWorkpointId(workpointId)) {
                return Result.fail("无效的工作点ID");
            }

            String tableName = sanitizeTableName(getTableName(workpointId));
            System.out.println("从 " + tableName + " 删除工序ID: " + id);

            String sql = "DELETE FROM " + tableName + " WHERE id = ?";
            int rows = jdbcTemplate.update(sql, id);

            return rows > 0 ? Result.suc("删除成功") : Result.fail("删除失败");
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("删除失败: " + e.getMessage());
        }
    }

    /**
     * 获取指定工作点的所有工序
     * 
     * @param workpointId 工作点ID
     * @return 工序列表
     */
    @GetMapping("/{workpointId}/list")
    public Result list(@PathVariable String workpointId) {
        try {
            if (!isValidWorkpointId(workpointId)) {
                return Result.fail("无效的工作点ID");
            }

            String tableName = sanitizeTableName(getTableName(workpointId));
            String sql = "SELECT * FROM " + tableName + " ORDER BY process_order, id";
            
            List<ProcessWorkpoint> list = jdbcTemplate.query(sql, 
                new BeanPropertyRowMapper<>(ProcessWorkpoint.class));
            list.forEach(record -> record.setWorkpointId(workpointId));

            return Result.suc(list);
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("查询失败: " + e.getMessage());
        }
    }
}

