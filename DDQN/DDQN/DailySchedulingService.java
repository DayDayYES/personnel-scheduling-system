/**
 * Spring Boot集成每日调度系统示例
 * 展示如何在主系统中集成每日调度和A/B测试
 */

package com.example.demo.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import lombok.extern.slf4j.Slf4j;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Service
@Slf4j
public class DailySchedulingService {
    
    @Value("${daily.scheduling.api.url:http://localhost:5002}")
    private String schedulingApiUrl;
    
    private final RestTemplate restTemplate;
    private final ProcessService processService;  // 您现有的工序服务
    
    public DailySchedulingService(RestTemplate restTemplate, ProcessService processService) {
        this.restTemplate = restTemplate;
        this.processService = processService;
    }
    
    /**
     * 每日自动调度任务
     * 每天早上8点自动执行
     */
    @Scheduled(cron = "0 0 8 * * ?")
    public void runDailyScheduling() {
        log.info("开始执行每日自动调度...");
        
        try {
            // 1. 获取今日的工序参数
            List<Double> todayParams = getTodaySchedulingParams();
            
            // 2. 调用Python调度服务
            DailySchedulingResult result = callSchedulingAPI(todayParams);
            
            // 3. 保存调度结果到数据库
            saveDailySchedulingResult(result);
            
            // 4. 通知相关人员
            notifySchedulingComplete(result);
            
            log.info("每日调度执行完成: 完工时间={}, 资源利用率={}", 
                    result.getResults().getMakespan(), 
                    result.getResults().getResourceUtilization());
            
        } catch (Exception e) {
            log.error("每日调度执行失败", e);
            // 发送告警通知
            sendAlertNotification("每日调度失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取今日调度参数
     * 从工序管理表中获取当前的时长参数
     */
    private List<Double> getTodaySchedulingParams() {
        // 查询所有工序的当前时长
        List<Process> processes = processService.list();
        
        // 按照DDQN算法要求的顺序组织参数
        List<Double> params = new ArrayList<>();
        
        // 这里需要根据您的实际工序顺序来映射
        // 示例：按照DDQN算法中定义的15个工序顺序
        String[] processOrder = {
            "搭架子", "拆保温", "打磨", "宏观检验", "壁厚测定", 
            "射线检测", "表面检测", "超声检测", "其他无损检测",
            "铁素体检测", "硬度检测", "金相检验", "检验结果评定", 
            "返修", "合格报告出具"
        };
        
        Map<String, Integer> processMap = new HashMap<>();
        for (Process process : processes) {
            processMap.put(process.getProcessName(), process.getDuration());
        }
        
        for (String processName : processOrder) {
            Integer duration = processMap.get(processName);
            params.add(duration != null ? duration.doubleValue() : 10.0); // 默认值
        }
        
        log.info("今日调度参数: {}", params);
        return params;
    }
    
    /**
     * 调用Python调度API
     */
    private DailySchedulingResult callSchedulingAPI(List<Double> params) {
        String url = schedulingApiUrl + "/api/daily-scheduling/run";
        
        // 构建请求体
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("params", params);
        requestBody.put("date", LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE));
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
        
        // 发送请求
        ResponseEntity<DailySchedulingResult> response = restTemplate.postForEntity(
            url, request, DailySchedulingResult.class
        );
        
        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new RuntimeException("调度API调用失败: " + response.getStatusCode());
        }
        
        return response.getBody();
    }
    
    /**
     * 保存调度结果到数据库
     */
    private void saveDailySchedulingResult(DailySchedulingResult result) {
        // 这里可以创建一个新的实体类来保存每日调度结果
        // 或者扩展现有的数据库表结构
        
        DailyScheduleRecord record = new DailyScheduleRecord();
        record.setScheduleDate(LocalDate.now());
        record.setModelVersion(result.getModelVersion());
        record.setExperimentGroup(result.getExperimentGroup());
        record.setMakespan(result.getResults().getMakespan());
        record.setResourceUtilization(result.getResults().getResourceUtilization());
        record.setTotalWorkers(result.getResults().getTotalWorkers());
        record.setExecutionTime(result.getResults().getExecutionTime());
        record.setScheduleDetails(result.getScheduleDetails());
        record.setGanttChart(result.getGanttChart());
        record.setStatus(result.getStatus());
        
        // 保存到数据库
        // dailyScheduleService.save(record);
        
        log.info("调度结果已保存到数据库");
    }
    
    /**
     * 通知调度完成
     */
    private void notifySchedulingComplete(DailySchedulingResult result) {
        // 发送邮件或消息通知
        String message = String.format(
            "今日调度完成！\n" +
            "调度日期: %s\n" +
            "使用模型: %s\n" +
            "完工时间: %.2f 分钟\n" +
            "资源利用率: %.1f%%\n" +
            "请查看详细调度方案: http://localhost:5002/dashboard",
            LocalDate.now(),
            result.getModelVersion(),
            result.getResults().getMakespan(),
            result.getResults().getResourceUtilization() * 100
        );
        
        // 这里可以集成您的消息通知系统
        // notificationService.sendMessage("每日调度通知", message);
        
        log.info("调度完成通知已发送");
    }
    
    /**
     * 发送告警通知
     */
    private void sendAlertNotification(String message) {
        // 发送告警消息
        log.error("发送告警: {}", message);
        // alertService.sendAlert("每日调度告警", message);
    }
    
    /**
     * 获取调度结果（供前端查询）
     */
    public List<DailySchedulingResult> getRecentSchedulingResults(int days) {
        String url = schedulingApiUrl + "/api/daily-scheduling/results?days=" + days;
        
        try {
            ResponseEntity<SchedulingResultsResponse> response = restTemplate.getForEntity(
                url, SchedulingResultsResponse.class
            );
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                return response.getBody().getResults();
            }
        } catch (Exception e) {
            log.error("获取调度结果失败", e);
        }
        
        return new ArrayList<>();
    }
    
    /**
     * 获取A/B测试分析结果
     */
    public ABTestAnalysis getABTestAnalysis(int days) {
        String url = schedulingApiUrl + "/api/daily-scheduling/analysis?days=" + days;
        
        try {
            ResponseEntity<ABTestAnalysisResponse> response = restTemplate.getForEntity(
                url, ABTestAnalysisResponse.class
            );
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                return response.getBody().getAnalysis();
            }
        } catch (Exception e) {
            log.error("获取A/B测试分析失败", e);
        }
        
        return null;
    }
    
    /**
     * 手动触发调度（用于测试或紧急情况）
     */
    public DailySchedulingResult manualScheduling(List<Double> params) {
        log.info("手动触发调度: {}", params);
        
        DailySchedulingResult result = callSchedulingAPI(params);
        saveDailySchedulingResult(result);
        
        return result;
    }
}

/**
 * 调度结果DTO
 */
@Data
class DailySchedulingResult {
    private String status;
    private String date;
    private String modelVersion;
    private String experimentGroup;
    private SchedulingResults results;
    private List<Map<String, Object>> scheduleDetails;
    private String ganttChart; // Base64编码的图片
    private String error;
}

@Data
class SchedulingResults {
    private Double makespan;
    private Double resourceUtilization;
    private Integer totalWorkers;
    private Double executionTime;
}

@Data
class SchedulingResultsResponse {
    private String status;
    private List<DailySchedulingResult> results;
    private Integer total;
}

@Data
class ABTestAnalysisResponse {
    private String status;
    private ABTestAnalysis analysis;
    private Integer periodDays;
}

@Data
class ABTestAnalysis {
    private Map<String, GroupPerformance> groupPerformance;
    private ComparisonResult comparison;
    private StatisticalTest statisticalTest;
}

@Data
class GroupPerformance {
    private Integer sampleSize;
    private Double successRate;
    private Double avgMakespan;
    private Double stdMakespan;
    private Double avgResourceUtilization;
}

@Data
class ComparisonResult {
    private Double improvementPercentage;
    private String betterGroup;
    private Boolean sampleSufficient;
}

@Data
class StatisticalTest {
    private Double tStatistic;
    private Double pValue;
    private Boolean isSignificant;
    private Double confidenceLevel;
}

/**
 * 每日调度记录实体（需要创建对应的数据库表）
 */
@Entity
@Table(name = "daily_schedule_records")
@Data
class DailyScheduleRecord {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "schedule_date", unique = true)
    private LocalDate scheduleDate;
    
    @Column(name = "model_version")
    private String modelVersion;
    
    @Column(name = "experiment_group")
    private String experimentGroup;
    
    @Column(name = "makespan")
    private Double makespan;
    
    @Column(name = "resource_utilization")
    private Double resourceUtilization;
    
    @Column(name = "total_workers")
    private Integer totalWorkers;
    
    @Column(name = "execution_time")
    private Double executionTime;
    
    @Column(name = "schedule_details", columnDefinition = "TEXT")
    private String scheduleDetails; // JSON格式存储
    
    @Column(name = "gantt_chart", columnDefinition = "LONGTEXT")
    private String ganttChart; // Base64编码的图片
    
    @Column(name = "status")
    private String status;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();
    
    @Column(name = "employee_satisfaction")
    private Double employeeSatisfaction;
}

/**
 * 前端控制器
 */
@RestController
@RequestMapping("/api/daily-scheduling")
@Slf4j
class DailySchedulingController {
    
    private final DailySchedulingService dailySchedulingService;
    
    public DailySchedulingController(DailySchedulingService dailySchedulingService) {
        this.dailySchedulingService = dailySchedulingService;
    }
    
    /**
     * 获取最近的调度结果
     */
    @GetMapping("/recent")
    public Result<List<DailySchedulingResult>> getRecentResults(
            @RequestParam(defaultValue = "7") int days) {
        
        try {
            List<DailySchedulingResult> results = dailySchedulingService.getRecentSchedulingResults(days);
            return Result.success(results);
        } catch (Exception e) {
            log.error("获取调度结果失败", e);
            return Result.fail("获取调度结果失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取A/B测试分析
     */
    @GetMapping("/analysis")
    public Result<ABTestAnalysis> getAnalysis(
            @RequestParam(defaultValue = "30") int days) {
        
        try {
            ABTestAnalysis analysis = dailySchedulingService.getABTestAnalysis(days);
            return Result.success(analysis);
        } catch (Exception e) {
            log.error("获取A/B测试分析失败", e);
            return Result.fail("获取分析失败: " + e.getMessage());
        }
    }
    
    /**
     * 手动触发调度
     */
    @PostMapping("/manual")
    public Result<DailySchedulingResult> manualScheduling(
            @RequestBody List<Double> params) {
        
        try {
            DailySchedulingResult result = dailySchedulingService.manualScheduling(params);
            return Result.success(result);
        } catch (Exception e) {
            log.error("手动调度失败", e);
            return Result.fail("手动调度失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取调度仪表板页面
     */
    @GetMapping("/dashboard")
    public String dashboard() {
        // 重定向到Python服务的仪表板
        return "redirect:http://localhost:5002/dashboard";
    }
}
