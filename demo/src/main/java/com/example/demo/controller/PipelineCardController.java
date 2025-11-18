package com.example.demo.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.demo.common.QueryPageParam;
import com.example.demo.common.Result;
import com.example.demo.entity.PipelineCard;
import com.example.demo.entity.PipelineCardProcess;
import com.example.demo.service.PipelineCardProcessService;
import com.example.demo.service.PipelineCardService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.ByteArrayOutputStream;
import java.util.*;
import java.util.stream.Collectors;

/**
 * <p>
 * 管道开卡控制器
 * 处理Excel导入、数据查询等功能
 * </p>
 *
 * @author demo
 * @since 2025-01-16
 */
@RestController
@RequestMapping("/pipelineCard")
public class PipelineCardController {

    @Autowired
    private PipelineCardService pipelineCardService;

    @Autowired
    private PipelineCardProcessService pipelineCardProcessService;

    /**
     * 导入Excel文件
     * 
     * @param file Excel文件
     * @return 导入结果
     */
    @PostMapping("/import")
    public Result importExcel(@RequestParam("file") MultipartFile file) {
        try {
            // 验证文件
            if (file == null || file.isEmpty()) {
                return Result.fail("请选择要上传的文件");
            }

            // 验证文件类型
            String filename = file.getOriginalFilename();
            if (filename == null || (!filename.endsWith(".xlsx") && !filename.endsWith(".xls"))) {
                return Result.fail("只支持Excel文件格式（.xlsx或.xls）");
            }

            // 验证文件大小（限制10MB）
            if (file.getSize() > 10 * 1024 * 1024) {
                return Result.fail("文件大小不能超过10MB");
            }

            // 调用服务层导入
            Map<String, Object> result = pipelineCardService.importExcel(file);

            if ((Boolean) result.get("success")) {
                return Result.suc(result);
            } else {
                return Result.fail(result.get("message").toString());
            }

        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("导入失败：" + e.getMessage());
        }
    }

    /**
     * 分页查询管道开卡列表（带工序明细）
     * 
     * @param queryPageParam 分页查询参数
     * @return 分页结果
     */
    @PostMapping("/listPage")
    public Result listPage(@RequestBody QueryPageParam queryPageParam) {
        try {
            Map<String, Object> param = queryPageParam.getParam();
            
            // 构建查询条件
            QueryWrapper<PipelineCard> queryWrapper = new QueryWrapper<>();
            
            // 管道编号模糊查询
            if (param != null && param.get("pipelineCode") != null) {
                String pipelineCode = param.get("pipelineCode").toString();
                if (!pipelineCode.isEmpty()) {
                    queryWrapper.like("pipeline_code", pipelineCode);
                }
            }
            
            // 状态查询
            if (param != null && param.get("status") != null) {
                String status = param.get("status").toString();
                if (!status.isEmpty()) {
                    queryWrapper.eq("status", status);
                }
            }
            
            // 排序：按创建时间倒序
            queryWrapper.orderByDesc("create_time");
            
            // 分页查询
            Page<PipelineCard> page = new Page<>(queryPageParam.getPageNum(), queryPageParam.getPageSize());
            Page<PipelineCard> result = pipelineCardService.page(page, queryWrapper);
            
            // 为每个管道查询工序明细
            List<PipelineCard> records = result.getRecords();
            for (PipelineCard card : records) {
                QueryWrapper<PipelineCardProcess> processWrapper = new QueryWrapper<>();
                processWrapper.eq("card_id", card.getId());
                processWrapper.orderBy(true, true, "process_order");
                
                List<PipelineCardProcess> processes = pipelineCardProcessService.list(processWrapper);
                card.setProcesses(processes);
            }
            
            Map<String, Object> resultMap = new HashMap<>();
            resultMap.put("data", records);
            resultMap.put("total", result.getTotal());
            resultMap.put("pageNum", result.getCurrent());
            resultMap.put("pageSize", result.getSize());
            
            return Result.suc(resultMap);
            
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("查询失败：" + e.getMessage());
        }
    }

    /**
     * 查询管道开卡列表（Excel展示格式）
     * 将数据转换为Excel风格的扁平结构
     * 
     * @param queryPageParam 分页查询参数
     * @return 扁平化的数据列表
     */
    @PostMapping("/listPageFlat")
    public Result listPageFlat(@RequestBody QueryPageParam queryPageParam) {
        try {
            Map<String, Object> param = queryPageParam.getParam();
            
            // 构建查询条件
            QueryWrapper<PipelineCard> queryWrapper = new QueryWrapper<>();
            
            // 管道编号模糊查询
            if (param != null && param.get("pipelineCode") != null) {
                String pipelineCode = param.get("pipelineCode").toString();
                if (!pipelineCode.isEmpty()) {
                    queryWrapper.like("pipeline_code", pipelineCode);
                }
            }
            
            // 状态查询
            if (param != null && param.get("status") != null) {
                String status = param.get("status").toString();
                if (!status.isEmpty()) {
                    queryWrapper.eq("status", status);
                }
            }
            
            // 过滤掉表头行（管道编号为"管道编号"的记录）
            queryWrapper.ne("pipeline_code", "管道编号");
            queryWrapper.ne("card_no", "管道序号");
            
            // 先查询所有符合条件的记录（不分页）
            List<PipelineCard> allCards = pipelineCardService.list(queryWrapper);
            
            // 手动排序：按管道序号数字升序
            allCards.sort((a, b) -> {
                try {
                    int numA = Integer.parseInt(a.getCardNo());
                    int numB = Integer.parseInt(b.getCardNo());
                    return Integer.compare(numA, numB);
                } catch (NumberFormatException e) {
                    return a.getCardNo().compareTo(b.getCardNo());
                }
            });
            
            // 手动分页
            int pageNum = queryPageParam.getPageNum();
            int pageSize = queryPageParam.getPageSize();
            int total = allCards.size();
            int fromIndex = (pageNum - 1) * pageSize;
            int toIndex = Math.min(fromIndex + pageSize, total);
            
            List<PipelineCard> pagedCards = new ArrayList<>();
            if (fromIndex < total) {
                pagedCards = allCards.subList(fromIndex, toIndex);
            }
            
            // 构造分页结果
            Page<PipelineCard> pageResult = new Page<>(pageNum, pageSize, total);
            pageResult.setRecords(pagedCards);
            
            // 转换为扁平结构
            List<Map<String, Object>> flatData = new ArrayList<>();
            
            for (PipelineCard card : pageResult.getRecords()) {
                Map<String, Object> row = new LinkedHashMap<>();
                
                // 基本信息
                row.put("id", card.getId());
                row.put("cardNo", card.getCardNo());
                row.put("pipelineCode", card.getPipelineCode());
                row.put("status", card.getStatus());
                
                // 查询工序明细
                QueryWrapper<PipelineCardProcess> processWrapper = new QueryWrapper<>();
                processWrapper.eq("card_id", card.getId());
                processWrapper.orderBy(true, true, "process_order");
                
                List<PipelineCardProcess> processes = pipelineCardProcessService.list(processWrapper);
                
                // 调试日志：打印第一条记录的工序信息
                // if (flatData.isEmpty() && !processes.isEmpty()) {
                //     System.out.println("===== 第一条管道的工序明细 =====");
                //     System.out.println("管道编号: " + card.getPipelineCode());
                //     System.out.println("工序数量: " + processes.size());
                //     for (PipelineCardProcess process : processes) {
                //         System.out.println("  - 工序代码: " + process.getProcessCode() + ", 需求数量: " + process.getRequiredCount());
                //     }
                //     System.out.println("================================");
                // }
                
                // 将工序转换为扁平字段
                for (PipelineCardProcess process : processes) {
                    row.put(process.getProcessCode(), process.getRequiredCount());
                }
                
                flatData.add(row);
            }
            
            Map<String, Object> resultMap = new HashMap<>();
            resultMap.put("data", flatData);
            resultMap.put("total", pageResult.getTotal());
            resultMap.put("pageNum", pageResult.getCurrent());
            resultMap.put("pageSize", pageResult.getSize());
            
            return Result.suc(resultMap);
            
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("查询失败：" + e.getMessage());
        }
    }

    /**
     * 删除管道开卡记录
     * 
     * @param id 管道ID
     * @return 删除结果
     */
    @DeleteMapping("/delete/{id}")
    public Result delete(@PathVariable Integer id) {
        try {
            boolean success = pipelineCardService.removeById(id);
            if (success) {
                return Result.suc("删除成功");
            } else {
                return Result.fail("删除失败");
            }
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("删除失败：" + e.getMessage());
        }
    }

    /**
     * 批量删除管道开卡记录
     * 
     * @param ids 管道ID列表
     * @return 删除结果
     */
    @PostMapping("/deleteBatch")
    public Result deleteBatch(@RequestBody List<Integer> ids) {
        try {
            boolean success = pipelineCardService.removeByIds(ids);
            if (success) {
                return Result.suc("批量删除成功");
            } else {
                return Result.fail("批量删除失败");
            }
        } catch (Exception e) {
            e.printStackTrace();
            return Result.fail("批量删除失败：" + e.getMessage());
        }
    }

    /**
     * 下载Excel导入模板
     * 生成带示例数据的Excel模板文件供用户下载
     * 
     * @return Excel文件流
     */
    @GetMapping("/downloadTemplate")
    public ResponseEntity<byte[]> downloadTemplate() {
        try {
            // 创建工作簿
            org.apache.poi.ss.usermodel.Workbook workbook = new org.apache.poi.xssf.usermodel.XSSFWorkbook();
            org.apache.poi.ss.usermodel.Sheet sheet = workbook.createSheet("管道数据");
            
            // 创建样式
            org.apache.poi.ss.usermodel.CellStyle headerStyle = workbook.createCellStyle();
            headerStyle.setFillForegroundColor(org.apache.poi.ss.usermodel.IndexedColors.LIGHT_BLUE.getIndex());
            headerStyle.setFillPattern(org.apache.poi.ss.usermodel.FillPatternType.SOLID_FOREGROUND);
            headerStyle.setAlignment(org.apache.poi.ss.usermodel.HorizontalAlignment.CENTER);
            headerStyle.setBorderTop(org.apache.poi.ss.usermodel.BorderStyle.THIN);
            headerStyle.setBorderBottom(org.apache.poi.ss.usermodel.BorderStyle.THIN);
            headerStyle.setBorderLeft(org.apache.poi.ss.usermodel.BorderStyle.THIN);
            headerStyle.setBorderRight(org.apache.poi.ss.usermodel.BorderStyle.THIN);
            
            org.apache.poi.ss.usermodel.Font headerFont = workbook.createFont();
            headerFont.setBold(true);
            headerFont.setFontHeightInPoints((short) 11);
            headerStyle.setFont(headerFont);
            
            // 数据样式
            org.apache.poi.ss.usermodel.CellStyle dataStyle = workbook.createCellStyle();
            dataStyle.setAlignment(org.apache.poi.ss.usermodel.HorizontalAlignment.CENTER);
            dataStyle.setBorderTop(org.apache.poi.ss.usermodel.BorderStyle.THIN);
            dataStyle.setBorderBottom(org.apache.poi.ss.usermodel.BorderStyle.THIN);
            dataStyle.setBorderLeft(org.apache.poi.ss.usermodel.BorderStyle.THIN);
            dataStyle.setBorderRight(org.apache.poi.ss.usermodel.BorderStyle.THIN);
            
            // 创建表头
            org.apache.poi.ss.usermodel.Row headerRow = sheet.createRow(0);
            String[] headers = {
                "管道序号", "管道编号", "搭架子", "拆保温", "打磨", "宏观检查", "壁厚测定",
                "RT（射线）检测", "MT（磁粉）检测", "PT（渗透）检测", "UT（超声）检测", "其他无损检测",
                "硬度测试", "金相检验", "铁素体测定", "检验结果评定", "返修", "返修结果确认，合格报告出具"
            };
            
            for (int i = 0; i < headers.length; i++) {
                org.apache.poi.ss.usermodel.Cell cell = headerRow.createCell(i);
                cell.setCellValue(headers[i]);
                cell.setCellStyle(headerStyle);
                sheet.setColumnWidth(i, 15 * 256); // 设置列宽
            }
            
            // 添加示例数据（3行）
            String[][] exampleData = {
                {"1", "AV-32130", "1", "1", "1", "1", "1", "", "2", "", "", "", "1", "", "1", "1", "", "1"},
                {"2", "AV-32140", "1", "1", "1", "1", "1", "2", "", "2", "", "", "", "1", "", "1", "", "1"},
                {"3", "AV-32150", "1", "1", "1", "1", "1", "", "", "", "2", "1", "1", "1", "1", "1", "", "1"}
            };
            
            for (int i = 0; i < exampleData.length; i++) {
                org.apache.poi.ss.usermodel.Row row = sheet.createRow(i + 1);
                for (int j = 0; j < exampleData[i].length; j++) {
                    org.apache.poi.ss.usermodel.Cell cell = row.createCell(j);
                    String value = exampleData[i][j];
                    if (!value.isEmpty()) {
                        try {
                            cell.setCellValue(Integer.parseInt(value));
                        } catch (NumberFormatException e) {
                            cell.setCellValue(value);
                        }
                    }
                    cell.setCellStyle(dataStyle);
                }
            }
            
            // 添加说明行（第5行开始）
            org.apache.poi.ss.usermodel.Row noteRow1 = sheet.createRow(5);
            org.apache.poi.ss.usermodel.Cell noteCell1 = noteRow1.createCell(0);
            noteCell1.setCellValue("填写说明：");
            
            org.apache.poi.ss.usermodel.Row noteRow2 = sheet.createRow(6);
            org.apache.poi.ss.usermodel.Cell noteCell2 = noteRow2.createCell(0);
            noteCell2.setCellValue("1. 管道序号：填写数字，如1、2、3...");
            
            org.apache.poi.ss.usermodel.Row noteRow3 = sheet.createRow(7);
            org.apache.poi.ss.usermodel.Cell noteCell3 = noteRow3.createCell(0);
            noteCell3.setCellValue("2. 管道编号：填写管道的唯一编号，不能重复");
            
            org.apache.poi.ss.usermodel.Row noteRow4 = sheet.createRow(8);
            org.apache.poi.ss.usermodel.Cell noteCell4 = noteRow4.createCell(0);
            noteCell4.setCellValue("3. 工序列：填写数字表示该工序需要的次数，留空表示不需要该工序");
            
            org.apache.poi.ss.usermodel.Row noteRow5 = sheet.createRow(9);
            org.apache.poi.ss.usermodel.Cell noteCell5 = noteRow5.createCell(0);
            noteCell5.setCellValue("4. 导入时请删除说明行（第6-10行），只保留表头和数据行");
            
            // 合并说明单元格
            sheet.addMergedRegion(new org.apache.poi.ss.util.CellRangeAddress(5, 5, 0, 5));
            sheet.addMergedRegion(new org.apache.poi.ss.util.CellRangeAddress(6, 6, 0, 17));
            sheet.addMergedRegion(new org.apache.poi.ss.util.CellRangeAddress(7, 7, 0, 17));
            sheet.addMergedRegion(new org.apache.poi.ss.util.CellRangeAddress(8, 8, 0, 17));
            sheet.addMergedRegion(new org.apache.poi.ss.util.CellRangeAddress(9, 9, 0, 17));
            
            // 写入字节流
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            workbook.write(outputStream);
            workbook.close();
            
            byte[] bytes = outputStream.toByteArray();
            
            // 设置响应头
            HttpHeaders httpHeaders = new HttpHeaders();
            httpHeaders.setContentType(MediaType.APPLICATION_OCTET_STREAM);
            httpHeaders.setContentDispositionFormData("attachment", 
                java.net.URLEncoder.encode("管道数据导入模板.xlsx", "UTF-8"));
            httpHeaders.setContentLength(bytes.length);
            
            return ResponseEntity.ok()
                    .headers(httpHeaders)
                    .body(bytes);
                    
        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.internalServerError().build();
        }
    }
}
