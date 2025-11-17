package com.example.demo.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.demo.entity.PipelineCard;
import com.example.demo.entity.PipelineCardProcess;
import com.example.demo.mapper.PipelineCardMapper;
import com.example.demo.service.PipelineCardProcessService;
import com.example.demo.service.PipelineCardService;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.*;

/**
 * <p>
 * 管道开卡服务实现类
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
@Service
public class PipelineCardServiceImpl extends ServiceImpl<PipelineCardMapper, PipelineCard> implements PipelineCardService {

    @Autowired
    private PipelineCardProcessService pipelineCardProcessService;

    // Excel列名与工序代码映射关系（按Excel列顺序）
    private static final Map<Integer, ProcessMapping> PROCESS_MAPPINGS = new LinkedHashMap<>();
    
    static {
        PROCESS_MAPPINGS.put(2, new ProcessMapping("搭架子", "scaffold"));
        PROCESS_MAPPINGS.put(3, new ProcessMapping("拆保温", "remove_insulation"));
        PROCESS_MAPPINGS.put(4, new ProcessMapping("打磨", "grinding"));
        PROCESS_MAPPINGS.put(5, new ProcessMapping("宏观检查", "macro_inspection"));
        PROCESS_MAPPINGS.put(6, new ProcessMapping("壁厚测定", "thickness_test"));
        PROCESS_MAPPINGS.put(7, new ProcessMapping("RT（射线）检测", "rt_test"));
        PROCESS_MAPPINGS.put(8, new ProcessMapping("MT（磁粉）检测", "mt_test"));
        PROCESS_MAPPINGS.put(9, new ProcessMapping("PT（渗透）检测", "pt_test"));
        PROCESS_MAPPINGS.put(10, new ProcessMapping("UT（超声）检测", "ut_test"));
        PROCESS_MAPPINGS.put(11, new ProcessMapping("其他无损检测", "other_ndt"));
        PROCESS_MAPPINGS.put(12, new ProcessMapping("硬度检测", "hardness_test"));
        PROCESS_MAPPINGS.put(13, new ProcessMapping("金相检测", "metallography"));
        PROCESS_MAPPINGS.put(14, new ProcessMapping("铁素体检测", "ferrite_test"));
        PROCESS_MAPPINGS.put(15, new ProcessMapping("检验结果评定", "result_evaluation"));
        PROCESS_MAPPINGS.put(16, new ProcessMapping("返修", "rework"));
        PROCESS_MAPPINGS.put(17, new ProcessMapping("返修结果确认，合格报告出具", "final_confirm"));
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Map<String, Object> importExcel(MultipartFile file) throws Exception {
        Map<String, Object> result = new HashMap<>();
        List<String> errors = new ArrayList<>();
        int successCount = 0;
        int failCount = 0;

        try (InputStream inputStream = file.getInputStream();
             Workbook workbook = new XSSFWorkbook(inputStream)) {

            Sheet sheet = workbook.getSheetAt(0);
            int totalRows = sheet.getPhysicalNumberOfRows();

            // 验证表头（第一行）
            Row headerRow = sheet.getRow(0);
            if (headerRow == null) {
                throw new Exception("Excel文件格式错误：缺少表头行");
            }

            // 从第2行开始读取数据（第1行是表头，索引从0开始）
            for (int rowIndex = 1; rowIndex < totalRows; rowIndex++) {
                Row row = sheet.getRow(rowIndex);
                if (row == null) {
                    continue;
                }

                try {
                    // 读取管道基本信息（第1列：序号，第2列：编号）
                    String cardNo = getCellValueAsString(row.getCell(0));
                    String pipelineCode = getCellValueAsString(row.getCell(1));

                    if (pipelineCode == null || pipelineCode.trim().isEmpty()) {
                        errors.add("第" + (rowIndex + 1) + "行：管道编号为空，已跳过");
                        failCount++;
                        continue;
                    }

                    // 检查管道编号是否已存在
                    QueryWrapper<PipelineCard> queryWrapper = new QueryWrapper<>();
                    queryWrapper.eq("pipeline_code", pipelineCode);
                    if (this.count(queryWrapper) > 0) {
                        errors.add("第" + (rowIndex + 1) + "行：管道编号 " + pipelineCode + " 已存在，不允许重复导入");
                        failCount++;
                        continue;
                    }

                    // 创建管道开卡主记录
                    PipelineCard pipelineCard = new PipelineCard();
                    pipelineCard.setCardNo(cardNo);
                    pipelineCard.setPipelineCode(pipelineCode);
                    pipelineCard.setStatus("pending");

                    // 保存主记录
                    this.save(pipelineCard);

                    // 读取工序信息（从第3列开始到第18列）
                    List<PipelineCardProcess> processList = new ArrayList<>();
                    for (Map.Entry<Integer, ProcessMapping> entry : PROCESS_MAPPINGS.entrySet()) {
                        int colIndex = entry.getKey();
                        ProcessMapping mapping = entry.getValue();

                        // 读取单元格值（原样保存）
                        String cellValue = getCellValueAsString(row.getCell(colIndex));

                        // 创建工序明细记录（所有列都保存，包括空值）
                        PipelineCardProcess process = new PipelineCardProcess();
                        process.setCardId(pipelineCard.getId());
                        process.setProcessName(mapping.processName);
                        process.setProcessCode(mapping.processCode);
                        process.setRequiredCount(cellValue); // 原样保存：数字/空格/null
                        process.setProcessOrder(colIndex + 1); // Excel列号（从1开始）

                        processList.add(process);
                    }

                    // 批量保存工序明细
                    if (!processList.isEmpty()) {
                        pipelineCardProcessService.saveBatch(processList);
                    }

                    successCount++;

                } catch (Exception e) {
                    errors.add("第" + (rowIndex + 1) + "行导入失败：" + e.getMessage());
                    failCount++;
                }
            }

            result.put("success", true);
            result.put("successCount", successCount);
            result.put("failCount", failCount);
            result.put("totalCount", totalRows - 1); // 减去表头行
            result.put("errors", errors);
            result.put("message", "导入完成！成功 " + successCount + " 条，失败 " + failCount + " 条");

        } catch (Exception e) {
            result.put("success", false);
            result.put("message", "导入失败：" + e.getMessage());
            throw e;
        }

        return result;
    }

    /**
     * 获取单元格值作为字符串（原样保存）
     */
    private String getCellValueAsString(Cell cell) {
        if (cell == null) {
            return null;
        }

        switch (cell.getCellType()) {
            case STRING:
                String value = cell.getStringCellValue();
                // 将空格保留为空格，不转换为null
                return value;
            case NUMERIC:
                // 数字类型转为字符串（去除小数点）
                if (DateUtil.isCellDateFormatted(cell)) {
                    return cell.getDateCellValue().toString();
                } else {
                    double numValue = cell.getNumericCellValue();
                    // 如果是整数，去掉小数点
                    if (numValue == (long) numValue) {
                        return String.valueOf((long) numValue);
                    } else {
                        return String.valueOf(numValue);
                    }
                }
            case BOOLEAN:
                return String.valueOf(cell.getBooleanCellValue());
            case FORMULA:
                try {
                    return String.valueOf(cell.getNumericCellValue());
                } catch (Exception e) {
                    return cell.getStringCellValue();
                }
            case BLANK:
                return null;
            default:
                return null;
        }
    }

    /**
     * 工序映射类
     */
    private static class ProcessMapping {
        String processName;
        String processCode;

        ProcessMapping(String processName, String processCode) {
            this.processName = processName;
            this.processCode = processCode;
        }
    }
}

