package com.example.demo.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.demo.entity.ProcessWorkpoint;
import org.apache.ibatis.session.SqlSession;
import org.apache.ibatis.session.SqlSessionFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * <p>
 * 动态工序服务实现类 - 支持动态表名
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
@Service
public class DynamicProcessServiceImpl {

    @Autowired
    private SqlSessionFactory sqlSessionFactory;

    /**
     * 动态分页查询
     */
    public Page<Map<String, Object>> selectPage(String tableName, Page<Map<String, Object>> page, Map<String, Object> conditions) {
        try (SqlSession session = sqlSessionFactory.openSession()) {
            // 构建WHERE条件
            StringBuilder whereClause = new StringBuilder(" WHERE 1=1 ");
            
            if (conditions != null) {
                if (conditions.get("processName") != null && !"".equals(conditions.get("processName"))) {
                    whereClause.append(" AND process_name LIKE CONCAT('%', #{processName}, '%') ");
                }
                if (conditions.get("processOrder") != null && !"".equals(conditions.get("processOrder"))) {
                    whereClause.append(" AND process_order = #{processOrder} ");
                }
                if (conditions.get("isDedicated") != null && !"".equals(conditions.get("isDedicated"))) {
                    whereClause.append(" AND is_dedicated = #{isDedicated} ");
                }
                if (conditions.get("isParallel") != null && !"".equals(conditions.get("isParallel"))) {
                    whereClause.append(" AND is_parallel = #{isParallel} ");
                }
            }

            // 计算总数
            String countSql = "SELECT COUNT(*) FROM " + tableName + whereClause.toString();
            Integer total = session.selectOne("dynamicQuery.count", buildParams(countSql, conditions));
            
            // 查询数据
            long offset = (page.getCurrent() - 1) * page.getSize();
            String dataSql = "SELECT * FROM " + tableName + whereClause.toString() + 
                           " ORDER BY process_order, id LIMIT " + offset + ", " + page.getSize();
            List<Map<String, Object>> records = session.selectList("dynamicQuery.select", buildParams(dataSql, conditions));
            
            page.setTotal(total == null ? 0 : total);
            page.setRecords(records);
            
            return page;
        }
    }

    /**
     * 动态插入
     */
    public boolean insert(String tableName, ProcessWorkpoint entity) {
        try (SqlSession session = sqlSessionFactory.openSession(true)) {
            String sql = "INSERT INTO " + tableName + 
                       " (process_name, process_order, team_name, is_dedicated, team_size, duration, is_parallel, created_at) " +
                       " VALUES (#{processName}, #{processOrder}, #{teamName}, #{isDedicated}, #{teamSize}, #{duration}, #{isParallel}, NOW())";
            
            Map<String, Object> params = new HashMap<>();
            params.put("sql", sql);
            params.put("processName", entity.getProcessName());
            params.put("processOrder", entity.getProcessOrder());
            params.put("teamName", entity.getTeamName());
            params.put("isDedicated", entity.getIsDedicated());
            params.put("teamSize", entity.getTeamSize());
            params.put("duration", entity.getDuration());
            params.put("isParallel", entity.getIsParallel());
            
            int rows = session.update("dynamicQuery.execute", params);
            return rows > 0;
        }
    }

    /**
     * 动态更新
     */
    public boolean update(String tableName, ProcessWorkpoint entity) {
        try (SqlSession session = sqlSessionFactory.openSession(true)) {
            String sql = "UPDATE " + tableName + 
                       " SET process_name=#{processName}, process_order=#{processOrder}, team_name=#{teamName}, " +
                       " is_dedicated=#{isDedicated}, team_size=#{teamSize}, duration=#{duration}, " +
                       " is_parallel=#{isParallel}, updated_at=NOW() " +
                       " WHERE id=#{id}";
            
            Map<String, Object> params = new HashMap<>();
            params.put("sql", sql);
            params.put("id", entity.getId());
            params.put("processName", entity.getProcessName());
            params.put("processOrder", entity.getProcessOrder());
            params.put("teamName", entity.getTeamName());
            params.put("isDedicated", entity.getIsDedicated());
            params.put("teamSize", entity.getTeamSize());
            params.put("duration", entity.getDuration());
            params.put("isParallel", entity.getIsParallel());
            
            int rows = session.update("dynamicQuery.execute", params);
            return rows > 0;
        }
    }

    /**
     * 动态删除
     */
    public boolean delete(String tableName, Integer id) {
        try (SqlSession session = sqlSessionFactory.openSession(true)) {
            String sql = "DELETE FROM " + tableName + " WHERE id = #{id}";
            
            Map<String, Object> params = new HashMap<>();
            params.put("sql", sql);
            params.put("id", id);
            
            int rows = session.update("dynamicQuery.execute", params);
            return rows > 0;
        }
    }

    /**
     * 构建参数Map
     */
    private Map<String, Object> buildParams(String sql, Map<String, Object> conditions) {
        Map<String, Object> params = new HashMap<>();
        params.put("sql", sql);
        if (conditions != null) {
            params.putAll(conditions);
        }
        return params;
    }
}

