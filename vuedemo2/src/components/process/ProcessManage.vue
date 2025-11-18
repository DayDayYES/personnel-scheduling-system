  <template>
    <div class="process-manage-container">
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="header-content">
          <div class="title-section">
            <h2 class="page-title">
              <i class="el-icon-s-order title-icon"></i>
              工序管理
            </h2>
            <p class="page-subtitle">管理各工作点的生产工序信息，包括时长、阶段、团队分配等</p>
          </div>
          <div class="header-actions">
            <el-button type="warning" icon="el-icon-setting" @click="showRuleConfigDialog" class="rule-btn">
              规则配置
            </el-button>
            <el-button type="success" icon="el-icon-download" @click="downloadTemplate" class="template-btn">
              下载模板
            </el-button>
            <el-button type="success" icon="el-icon-upload2" @click="showImportDialog" class="import-btn">
              导入Excel
            </el-button>
            <el-button type="primary" icon="el-icon-plus" @click="add" class="add-btn">
              新增工序
            </el-button>
          </div>
        </div>
      </div>

      <!-- 主功能标签页（工序管理 vs 开卡数据查看） -->
      <div class="main-tabs-section">
        <el-card class="main-tabs-card" shadow="never">
          <el-tabs v-model="activeMainTab" type="border-card" @tab-click="handleMainTabChange">
            <!-- 工序管理标签页 -->
            <el-tab-pane label="工序管理" name="process">
              <template #label>
                <span class="main-tab-label">
                  <i class="el-icon-s-operation"></i>
                  工序管理
                </span>
              </template>
            </el-tab-pane>
            
            <!-- 开卡数据查看标签页 -->
            <el-tab-pane label="开卡数据查看" name="pipeline">
              <template #label>
                <span class="main-tab-label">
                  <i class="el-icon-document"></i>
                  Excel数据查看
                  <el-badge :value="pipelineCardTotal" class="main-tab-badge" v-if="pipelineCardTotal > 0"></el-badge>
                </span>
              </template>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>

      <!-- 工序管理内容（原有内容） -->
      <div v-if="activeMainTab === 'process'">
        <!-- 工作点标签页 -->
        <div class="workpoint-tabs-section">
          <el-card class="tabs-card" shadow="never">
            <el-tabs v-model="activeWorkpoint" type="card" @tab-click="handleWorkpointChange">
              <el-tab-pane 
                v-for="wp in workpoints" 
                :key="wp.id" 
                :label="wp.name" 
                :name="wp.id">
                <template #label>
                  <span class="tab-label">
                    <i class="el-icon-location"></i>
                    {{ wp.name }}
                    <el-badge :value="wp.count" class="tab-badge" v-if="wp.count > 0"></el-badge>
                  </span>
                </template>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </div>
  
      <!-- 搜索过滤区域 -->
      <div class="filter-section">
        <el-card class="filter-card" shadow="never">
          <div class="filter-content">
            <div class="filter-left">
              <div class="filter-item">
                <label class="filter-label">工序名称：</label>
                <el-input 
                  v-model="processName" 
                  placeholder="请输入工序名称搜索" 
                  suffix-icon="el-icon-search" 
                  class="filter-input"
                  @keyup.enter.native="loadPost"
                  clearable>
                </el-input>
              </div>
              <div class="filter-item">
                <label class="filter-label">阶段：</label>
                <el-select v-model="stage" placeholder="请选择阶段" class="filter-select" clearable>
                  <el-option
                    v-for="item in stages"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value">
                  </el-option>
                </el-select>
              </div>
              <div class="filter-item">
                <label class="filter-label">人员类型：</label>
                <el-select v-model="isShared" placeholder="请选择人员类型" class="filter-select" clearable>
                  <el-option
                    v-for="item in sharedTypes"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value">
                  </el-option>
                </el-select>
              </div>
              <div class="filter-item">
                <label class="filter-label">并行标识：</label>
                <el-select v-model="isParallel" placeholder="请选择并行标识" class="filter-select" clearable>
                  <el-option
                    v-for="item in parallelTypes"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value">
                  </el-option>
                </el-select>
              </div>
            </div>
            <div class="filter-actions">
              <el-button type="primary" icon="el-icon-search" @click="loadPost">
                查询
              </el-button>
              <el-button icon="el-icon-refresh" @click="resetParam">
                重置
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
  
      <!-- 数据表格区域 -->
      <div class="table-section">
        <el-card class="table-card" shadow="never">
          <div class="table-header">
            <div class="table-title">
              <span class="title-text">工序列表</span>
              <el-tag type="info" class="count-tag">共 {{ total }} 条记录</el-tag>
            </div>
            <div class="table-actions">
              <el-button size="small" type="warning" icon="el-icon-download">
                导出数据
              </el-button>
            </div>
          </div>
          
          <el-table 
            :data="tableData"
            class="process-table"
            stripe
            @selection-change="handleSelectionChange">
            
            <el-table-column type="selection" width="55" align="center"></el-table-column>
            
            <el-table-column prop="id" label="ID" width="80" align="center">
              <template slot-scope="scope">
                <el-tag size="mini" type="info"># {{ scope.row.id }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="processName" label="工序名称" min-width="160" show-overflow-tooltip>
              <template slot-scope="scope">
                <div class="process-name">
                  <div class="process-icon">
                    <i class="el-icon-s-operation"></i>
                  </div>
                  <div class="process-info">
                    <div class="name-text">{{ scope.row.processName }}</div>
                    <div class="process-id">ID: {{ scope.row.id }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
  
            <el-table-column prop="duration" label="时长" width="120" align="center">
              <template slot-scope="scope">
                <div class="duration-info">
                  <i class="el-icon-time duration-icon"></i>
                  <span class="duration-text">{{ scope.row.duration }}h</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="processOrder" label="阶段" width="100" align="center">
              <template slot-scope="scope">
                <el-tag 
                  :type="getStageType(scope.row.processOrder)" 
                  size="small" 
                  class="stage-tag">
                  <i class="el-icon-s-flag"></i>
                  第{{ scope.row.processOrder }}阶段
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="teamName" label="所属团队" width="120" align="center">
              <template slot-scope="scope">
                <div class="team-info">
                  <i class="el-icon-s-custom team-icon"></i>
                  <span>{{ scope.row.teamName }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="teamSize" label="团队规模" width="100" align="center">
              <template slot-scope="scope">
                <div class="team-size-info">
                  <i class="el-icon-user"></i>
                  <span>{{ scope.row.teamSize }}人</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="isDedicated" label="人员类型" width="100" align="center">
              <template slot-scope="scope">
                <el-tag
                  :type="scope.row.isDedicated ? 'warning' : 'success'"
                  size="small"
                  class="shared-tag">
                  <i :class="scope.row.isDedicated ? 'el-icon-user-solid' : 'el-icon-s-cooperation'"></i>
                  {{ scope.row.isDedicated ? '专用' : '共用' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="isParallel" label="并行标识" width="100" align="center">
              <template slot-scope="scope">
                <el-tag
                  :type="scope.row.isParallel ? 'success' : 'info'"
                  size="small"
                  class="parallel-tag">
                  <i :class="scope.row.isParallel ? 'el-icon-finished' : 'el-icon-minus'"></i>
                  {{ scope.row.isParallel ? '可并行' : '非并行' }}
                </el-tag>
              </template>
            </el-table-column>
  
            <el-table-column prop="createTime" label="创建时间" width="160" align="center">
              <template slot-scope="scope">
                <div class="time-info">
                  <i class="el-icon-calendar time-icon"></i>
                  <span>{{ formatTime(scope.row.createTime) }}</span>
                </div>
              </template>
            </el-table-column>
  
            <el-table-column label="操作" width="160" align="center" fixed="right">
              <template slot-scope="scope">
                <div class="action-buttons">
                  <el-button 
                    size="mini" 
                    type="primary" 
                    icon="el-icon-edit"
                    @click="mod(scope.row)"
                    class="action-btn">
                    编辑
                  </el-button>
                  <el-popconfirm
                    title="确定要删除这个工序吗？"
                    @confirm="del(scope.row.id)"
                    icon="el-icon-info"
                    icon-color="red">
                    <el-button 
                      slot="reference"
                      size="mini" 
                      type="danger" 
                      icon="el-icon-delete"
                      class="action-btn">
                      删除
                    </el-button>
                  </el-popconfirm>
                </div>
              </template>
            </el-table-column>
          </el-table>
  
          <!-- 分页组件 -->
          <div class="pagination-container">
            <el-pagination
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :current-page="pageNum"
              :page-sizes="[5, 10, 20, 50]"
              :page-size="pageSize"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
              class="pagination">
            </el-pagination>
          </div>
        </el-card>
      </div>
  
      <!-- 工序表单对话框 -->
      <el-dialog
        :title="form.id ? '编辑工序' : '新增工序'"
        :visible.sync="centerDialogVisible"
        width="600px"
        :close-on-click-modal="true"
        :modal="true"
        :lock-scroll="false"
        append-to-body
        class="process-dialog">
        
        <el-form 
          ref="form" 
          :rules="rules" 
          :model="form" 
          label-width="110px"
          class="process-form">
  
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item prop="processName" label="工序名称">
                <el-input 
                  v-model="form.processName"
                  placeholder="请输入工序名称"
                  prefix-icon="el-icon-s-operation">
                </el-input>
              </el-form-item>
            </el-col>
          </el-row>
  
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item prop="duration" label="时长(小时)">
                <el-input-number
                  v-model="form.duration"
                  :min="0.5"
                  :max="999"
                  :step="0.5"
                  :precision="1"
                  controls-position="right"
                  class="duration-input">
                </el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item prop="processOrder" label="工序顺序">
                <el-input-number
                  v-model="form.processOrder"
                  :min="1"
                  :max="99"
                  controls-position="right"
                  class="stage-input">
                </el-input-number>
              </el-form-item>
            </el-col>
          </el-row>
  
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item prop="teamName" label="所属团队">
                <el-select v-model="form.teamName" placeholder="请选择团队" class="team-select">
                  <el-option label="团队1" value="team1"></el-option>
                  <el-option label="团队2" value="team2"></el-option>
                  <el-option label="团队3" value="team3"></el-option>
                  <el-option label="团队4" value="team4"></el-option>
                  <el-option label="团队5" value="team5"></el-option>
                  <el-option label="团队6" value="team6"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item prop="teamSize" label="团队规模">
                <el-input-number
                  v-model="form.teamSize"
                  :min="1"
                  :max="100"
                  controls-position="right"
                  class="team-size-input">
                </el-input-number>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="人员类型">
                <el-radio-group v-model="form.isDedicated" class="shared-radio">
                  <el-radio :label="true" class="radio-item">
                    <i class="el-icon-user-solid"></i> 专用
                  </el-radio>
                  <el-radio :label="false" class="radio-item">
                    <i class="el-icon-s-cooperation"></i> 共用
                  </el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="并行标识">
                <el-radio-group v-model="form.isParallel" class="parallel-radio">
                  <el-radio :label="false" class="radio-item">
                    <i class="el-icon-minus"></i> 非并行
                  </el-radio>
                  <el-radio :label="true" class="radio-item">
                    <i class="el-icon-finished"></i> 可并行
                  </el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
  
        <span slot="footer" class="dialog-footer">
          <el-button @click="centerDialogVisible = false" class="cancel-btn">
            取 消
          </el-button>
          <el-button type="primary" @click="save" :loading="saveLoading" class="save-btn">
            {{ saveLoading ? '保存中...' : '确 定' }}
          </el-button>
        </span>
      </el-dialog>
      </div>

      <!-- 开卡数据查看内容 -->
      <div v-if="activeMainTab === 'pipeline'" class="pipeline-section">
        <!-- 搜索过滤区域 -->
        <div class="filter-section">
          <el-card class="filter-card" shadow="never">
            <div class="filter-content">
              <div class="filter-left">
                <div class="filter-item">
                  <label class="filter-label">管道编号：</label>
                  <el-input 
                    v-model="pipelineSearchCode" 
                    placeholder="请输入管道编号搜索" 
                    suffix-icon="el-icon-search" 
                    class="filter-input"
                    @keyup.enter.native="loadPipelineCards"
                    clearable>
                  </el-input>
                </div>
                <div class="filter-item">
                  <label class="filter-label">状态：</label>
                  <el-select v-model="pipelineStatus" placeholder="请选择状态" class="filter-select" clearable>
                    <el-option label="待开始" value="0"></el-option>
                    <el-option label="进行中" value="1"></el-option>
                    <el-option label="已完成" value="2"></el-option>
                  </el-select>
                </div>
              </div>
              <div class="filter-actions">
                <el-button type="primary" icon="el-icon-search" @click="loadPipelineCards">
                  查询
                </el-button>
                <el-button icon="el-icon-refresh" @click="resetPipelineSearch">
                  重置
                </el-button>
                <el-button 
                  type="danger" 
                  icon="el-icon-delete" 
                  @click="batchDeletePipelines"
                  :disabled="pipelineSelection.length === 0">
                  批量删除 ({{ pipelineSelection.length }})
                </el-button>
              </div>
            </div>
          </el-card>
        </div>

        <!-- Excel样式表格 -->
        <div class="table-section">
          <el-card class="table-card" shadow="never">
            <div class="table-header">
              <div class="table-title">
                <i class="el-icon-document"></i>
                管道开卡数据表
              </div>
              <div class="table-info">
                共 <span class="info-number">{{ pipelineCardTotal }}</span> 条记录
              </div>
            </div>
            
            <el-table 
              ref="pipelineTable"
              :data="pipelineCardData"
              class="pipeline-table"
              stripe
              border
              height="700"
              @selection-change="handlePipelineSelectionChange">
              
              <el-table-column type="selection" width="55" align="center" fixed="left"></el-table-column>
              
              <el-table-column 
                prop="cardNo" 
                label="管道序号" 
                width="120" 
                align="center" 
                fixed="left"
                class-name="border-right-column">
              </el-table-column>
              
              <el-table-column 
                prop="pipelineCode" 
                label="管道编号" 
                width="150" 
                align="center" 
                fixed="left"
                class-name="border-right-column">
              </el-table-column>
              
              <!-- 16个工序列（根据后端实际返回的process_code） -->
              <el-table-column prop="scaffold" label="搭架子" width="100" align="center"></el-table-column>
              <el-table-column prop="remove_insulation" label="拆保温" width="100" align="center"></el-table-column>
              <el-table-column prop="grinding" label="打磨" width="100" align="center"></el-table-column>
              <el-table-column prop="macro_inspection" label="宏观检查" width="120" align="center"></el-table-column>
              <el-table-column prop="thickness_test" label="壁厚测定" width="100" align="center"></el-table-column>
              <el-table-column prop="rt_test" label="RT（射线）检测" width="100" align="center"></el-table-column>
              <el-table-column prop="mt_test" label="MT（磁粉）检测" width="100" align="center"></el-table-column>
              <el-table-column prop="pt_test" label="PT（渗透）检测" width="100" align="center"></el-table-column>
              <el-table-column prop="ut_test" label="UT（超声）检测" width="100" align="center"></el-table-column>
              <el-table-column prop="other_ndt" label="其他无损检测" width="120" align="center"></el-table-column>
              <el-table-column prop="hardness_test" label="硬度测试" width="120" align="center"></el-table-column>
              <el-table-column prop="metallography" label="金相检验" width="120" align="center"></el-table-column>
              <el-table-column prop="ferrite_test" label="铁素体测定" width="140" align="center"></el-table-column>
              <el-table-column prop="result_evaluation" label="检验结果评定" width="120" align="center"></el-table-column>
              <el-table-column prop="rework" label="返修" width="100" align="center"></el-table-column>
              <el-table-column prop="final_confirm" label="返修结果确认，合格报告出具" width="120" align="center"></el-table-column>
              
              <el-table-column label="操作" width="150" align="center" fixed="right">
                <template slot-scope="scope">
                  <el-button type="danger" size="mini" icon="el-icon-delete" @click="deletePipelineCard(scope.row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="pagination-section">
              <el-pagination
                @size-change="handlePipelineSizeChange"
                @current-change="handlePipelineCurrentChange"
                :current-page="pipelinePageNum"
                :page-sizes="[10, 20, 50, 100]"
                :page-size="pipelinePageSize"
                layout="total, sizes, prev, pager, next, jumper"
                :total="pipelineCardTotal"
                class="pagination">
              </el-pagination>
            </div>
          </el-card>
        </div>
      </div>

      <!-- Excel导入对话框 -->
      <el-dialog
        title="导入管道Excel"
        :visible.sync="importDialogVisible"
        width="600px"
        :close-on-click-modal="false"
        append-to-body
        class="import-dialog">
        
        <div class="import-content">
          <div class="import-tips">
            <el-alert
              title="导入说明"
              type="info"
              :closable="false"
              show-icon>
              <div slot="description">
                <p>1. 请确保Excel文件格式正确（.xlsx或.xls）</p>
                <p>2. 第1列：管道序号，第2列：管道编号（不可重复）</p>
                <p>3. 第3-18列：各工序需求（填写数字表示次数，留空表示不需要）</p>
                <p>4. 文件大小不超过10MB</p>
                <p style="margin-top: 10px; color: #e6a23c;">
                  <i class="el-icon-warning"></i>
                  <strong>提示：请先点击页面顶部的"下载模板"按钮获取标准模板</strong>
                </p>
              </div>
            </el-alert>
          </div>

          <div class="upload-section">
            <el-upload
              ref="upload"
              class="upload-demo"
              drag
              action="#"
              :auto-upload="false"
              :on-change="handleFileChange"
              :on-remove="handleFileRemove"
              :file-list="fileList"
              :limit="1"
              accept=".xlsx,.xls">
              <i class="el-icon-upload"></i>
              <div class="el-upload__text">
                将Excel文件拖到此处，或<em>点击选择</em>
              </div>
              <div class="el-upload__tip" slot="tip">
                支持 .xlsx 和 .xls 格式，文件不超过10MB
              </div>
            </el-upload>
          </div>

          <!-- 导入进度 -->
          <div v-if="importing" class="import-progress">
            <el-progress :percentage="importProgress" :status="importStatus"></el-progress>
            <p class="progress-text">{{ importMessage }}</p>
          </div>

          <!-- 导入结果 -->
          <div v-if="importResult" class="import-result">
            <el-alert
              :title="importResult.success ? '导入成功' : '导入失败'"
              :type="importResult.success ? 'success' : 'error'"
              :closable="false"
              show-icon>
              <div slot="description">
                <p v-if="importResult.success">
                  成功导入 {{ importResult.successCount }} 条记录
                  <span v-if="importResult.failCount > 0">，失败 {{ importResult.failCount }} 条</span>
                </p>
                <div v-if="importResult.errors && importResult.errors.length > 0" class="error-list">
                  <p><strong>错误详情：</strong></p>
                  <ul>
                    <li v-for="(error, index) in importResult.errors" :key="index">{{ error }}</li>
                  </ul>
                </div>
              </div>
            </el-alert>
          </div>
        </div>

        <span slot="footer" class="dialog-footer">
          <el-button @click="closeImportDialog" :disabled="importing">
            取 消
          </el-button>
          <el-button 
            type="primary" 
            @click="doImport" 
            :loading="importing"
            :disabled="fileList.length === 0">
            {{ importing ? '导入中...' : '开始导入' }}
          </el-button>
        </span>
      </el-dialog>

      <!-- 规则配置对话框 -->
      <el-dialog
        title="工序规则配置"
        :visible.sync="ruleConfigDialogVisible"
        width="90%"
        :close-on-click-modal="false"
        append-to-body
        class="rule-config-dialog">
        
        <div class="rule-config-content">
          <!-- 操作按钮 -->
          <div class="rule-actions">
            <el-alert
              v-if="!ruleEditable"
              title="当前为只读模式，点击'编辑'按钮进行修改"  
              type="info"
              :closable="false"
              show-icon>
            </el-alert>
            <el-alert
              v-else
              title="当前为编辑模式，修改后请点击'保存'按钮"
              type="warning"
              :closable="false"
              show-icon>
            </el-alert>
            
            <div class="action-buttons">
              <el-button 
                v-if="!ruleEditable" 
                type="primary" 
                icon="el-icon-edit" 
                @click="enableRuleEdit">
                编辑
              </el-button>
              <template v-else>
                <el-button 
                  type="success" 
                  icon="el-icon-check" 
                  @click="saveRuleConfig"
                  :loading="ruleSaving">
                  {{ ruleSaving ? '保存中...' : '保存' }}
                </el-button>
                <el-button 
                  type="info" 
                  icon="el-icon-close" 
                  @click="cancelRuleEdit">
                  取消
                </el-button>
              </template>
            </div>
          </div>

          <!-- 规则配置表格 -->
          <el-table
            :data="processRules"
            class="rule-config-table"
            border
            stripe
            max-height="600">
            
            <el-table-column 
              prop="processName" 
              label="工序名称" 
              width="150" 
              align="center"
              fixed>
            </el-table-column>

            <el-table-column label="基础工作时长" width="180" align="center">
              <template slot-scope="scope">
                <el-input-number
                  v-if="ruleEditable"
                  v-model="scope.row.baseDuration"
                  :min="0"
                  :max="999"
                  :precision="2"
                  :step="0.5"
                  size="small"
                  style="width: 100px">
                </el-input-number>
                <span v-else>{{ scope.row.baseDuration }}</span>
              </template>
            </el-table-column>

            <el-table-column label="时长单位" width="120" align="center">
              <template slot-scope="scope">
                <el-select
                  v-if="ruleEditable"
                  v-model="scope.row.durationUnit"
                  size="small"
                  style="width: 100%">
                  <el-option label="小时" value="小时"></el-option>
                  <el-option label="分钟" value="分钟"></el-option>
                  <el-option label="天" value="天"></el-option>
                </el-select>
                <span v-else>{{ scope.row.durationUnit }}</span>
              </template>
            </el-table-column>

            <el-table-column label="阶段顺序" width="120" align="center">
              <template slot-scope="scope">
                <el-input-number
                  v-if="ruleEditable"
                  v-model="scope.row.stageOrder"
                  :min="1"
                  :max="20"
                  size="small"
                  style="width: 100px">
                </el-input-number>
                <span v-else>{{ scope.row.stageOrder }}</span>
              </template>
            </el-table-column>

            <el-table-column label="所属团队" width="140" align="center">
              <template slot-scope="scope">
                <el-select
                  v-if="ruleEditable"
                  v-model="scope.row.teamName"
                  size="small"
                  style="width: 100%">
                  <el-option label="团队1" value="team1"></el-option>
                  <el-option label="团队2" value="team2"></el-option>
                  <el-option label="团队3" value="team3"></el-option>
                  <el-option label="团队4" value="team4"></el-option>
                  <el-option label="团队5" value="team5"></el-option>
                  <el-option label="团队6" value="team6"></el-option>
                </el-select>
                <span v-else>{{ formatTeamName(scope.row.teamName) }}</span>
              </template>
            </el-table-column>

            <el-table-column label="团队规模（人数）" width="150" align="center">
              <template slot-scope="scope">
                <el-input-number
                  v-if="ruleEditable"
                  v-model="scope.row.teamSize"
                  :min="1"
                  :max="100"
                  size="small"
                  style="width: 100px">
                </el-input-number>
                <span v-else>{{ scope.row.teamSize }} 人</span>
              </template>
            </el-table-column>

            <el-table-column label="备注说明" min-width="250" align="center">
              <template slot-scope="scope">
                <el-input
                  v-if="ruleEditable"
                  v-model="scope.row.description"
                  type="textarea"
                  :rows="2"
                  placeholder="请输入备注"
                  size="small"
                  maxlength="200"
                  show-word-limit>
                </el-input>
                <span v-else>{{ scope.row.description || '-' }}</span>
              </template>
            </el-table-column>

          </el-table>
        </div>

        <span slot="footer" class="dialog-footer">
          <el-button @click="ruleConfigDialogVisible = false">关闭</el-button>
        </span>
      </el-dialog>
    </div>
  </template>
  
  <script>
  export default {
    name: "ProcessManage",
    data() {
      let checkDuration = (rule, value, callback) => {
        if (value <= 0) {
          callback(new Error('时长必须大于0'));
        } else {
          callback();
        }
      };
      
      return {
        // 工作点数据
        workpoints: [], // 动态加载工作点列表
        activeWorkpoint: '', // 当前激活的工作点（动态设置为第一个）
        
        tableData: [],
        pageSize: 20,
        pageNum: 1,
        total: 0,
        processName: '',
        stage: '',
        isShared: '',
        isParallel: '',
        saveLoading: false,
        multipleSelection: [],
        stages: [
          {value: '1', label: '第1阶段'},
          {value: '2', label: '第2阶段'},
          {value: '3', label: '第3阶段'},
          {value: '4', label: '第4阶段'},
          {value: '5', label: '第5阶段'},
          {value: '6', label: '第6阶段'},
          {value: '7', label: '第7阶段'},
          {value: '8', label: '第8阶段'},
          {value: '9', label: '第9阶段'},
          {value: '10', label: '第10阶段'}
        ],
        sharedTypes: [
          {value: 'false', label: '专用'},
          {value: 'true', label: '共用'}
        ],
        parallelTypes: [
          {value: 'false', label: '非并行'},
          {value: 'true', label: '可并行'}
        ],
        centerDialogVisible: false,
        form: {
          id: '',
          processName: '',
          processOrder: 1,
          teamName: 'team1',
          isDedicated: false,
          teamSize: 10,
          duration: 10,
          isParallel: false,
          workpointId: ''
        },
        rules: {
          processName: [
            {required: true, message: '请输入工序名称', trigger: 'blur'},
            {min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur'}
          ],
          duration: [
            {required: true, message: '请输入时长', trigger: 'blur'},
            {validator: checkDuration, trigger: 'blur'}
          ],
          processOrder: [
            {required: true, message: '请输入阶段顺序', trigger: 'blur'}
          ],
          teamName: [
            {required: true, message: '请选择团队', trigger: 'blur'}
          ],
          teamSize: [
            {required: true, message: '请输入团队规模', trigger: 'blur'}
          ]
        },
        // Excel导入相关
        importDialogVisible: false,
        fileList: [],
        importing: false,
        importProgress: 0,
        importStatus: '',
        importMessage: '',
        importResult: null,
        
        // 主标签页相关
        activeMainTab: 'process', // 当前激活的主标签：process或pipeline
        
        // 开卡数据查看相关
        pipelineCardData: [], // 开卡数据列表
        pipelineCardTotal: 0, // 开卡数据总数
        pipelinePageNum: 1, // 当前页码
        pipelinePageSize: 20, // 每页数量
        pipelineSearchCode: '', // 管道编号搜索
        pipelineStatus: '', // 状态筛选
        pipelineSelection: [], // 选中的开卡数据
        
        // 规则配置相关
        ruleConfigDialogVisible: false, // 规则配置对话框显示状态
        ruleEditable: false, // 是否可编辑
        ruleSaving: false, // 是否正在保存
        processRules: [], // 工序规则列表
        processRulesBackup: [] // 工序规则备份（用于取消编辑时恢复）
      };
    },
    methods: {
      handleWorkpointChange() {
        // 切换工作点时重置分页并重新加载数据
        this.pageNum = 1;
        this.resetParam();
      },
      handleSelectionChange(val) {
        this.multipleSelection = val;
      },
      getStageType(stage) {
        const types = ['', 'primary', 'success', 'info', 'warning', 'danger'];
        return types[stage] || 'info';
      },
      formatTime(time) {
        if (!time) return '--';
        const date = new Date(time);
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit'
        });
      },
      resetForm() {
        this.$refs.form.resetFields();
      },
      add() {
        this.centerDialogVisible = true;
        this.$nextTick(() => {
          this.resetForm();
          this.form = {
            id: '',
            processName: '',
            processOrder: 1,
            teamName: 'team1',
            isDedicated: false,
            teamSize: 10,
            duration: 10,
            isParallel: false,
            workpointId: this.activeWorkpoint
          };
        });
      },
      del(id){
        this.$axios.get(this.$httpUrl + `/process/${this.activeWorkpoint}/del?id=` + id).then(res => res.data).then(res => {
          if (res.code == 200) {
            this.$message({
              message: '删除成功!',
              type: 'success'
            });
            this.loadPost();
          } else {
            this.$message({
              message: '删除失败!',
              type: 'error'
            });
          }
        });
      },
      mod(row){
        this.centerDialogVisible = true;
        this.$nextTick(() => {
          this.form.id = row.id;
          this.form.processName = row.processName;
          this.form.processOrder = row.processOrder;
          this.form.teamName = row.teamName;
          this.form.isDedicated = row.isDedicated;
          this.form.teamSize = row.teamSize;
          this.form.duration = row.duration;
          this.form.isParallel = row.isParallel;
          this.form.workpointId = this.activeWorkpoint;
        });
      },
      doSave(){
        this.saveLoading = true;
        this.form.workpointId = this.activeWorkpoint;
        this.$axios.post(this.$httpUrl + `/process/${this.activeWorkpoint}/save`, this.form).then(res => res.data).then(res => {
          this.saveLoading = false;
          if (res.code == 200) {
            this.$message({
              message: '保存成功!',
              type: 'success'
            });
            this.centerDialogVisible = false;
            this.loadPost();
          } else {
            this.$message({
              message: '保存失败!',
              type: 'error'
            });
          }
        });
      },
      doMod(){
        this.saveLoading = true;
        this.form.workpointId = this.activeWorkpoint;
        this.$axios.post(this.$httpUrl + `/process/${this.activeWorkpoint}/update`, this.form).then(res => res.data).then(res => {
          this.saveLoading = false;
          if (res.code == 200) {
            this.$message({
              message: '修改成功!',
              type: 'success'
            });
            this.centerDialogVisible = false;
            this.loadPost();
          } else {
            this.$message({
              message: '修改失败!',
              type: 'error'
            });
          }
        });
      },
      save() {
        this.$refs.form.validate((valid) => {
          if (valid) {
            if(this.form.id){
              this.doMod();
            }else{
              this.doSave();
            }
          } else {
            this.$message.warning('请检查表单填写是否正确');
            return false;
          }
        });
      },
      resetParam() {
        this.processName = '';
        this.stage = '';
        this.isShared = '';
        this.isParallel = '';
        this.loadPost();
      },
      loadPost() {
        // 使用新的动态API
        this.$axios.post(this.$httpUrl + `/process/${this.activeWorkpoint}/listPageC1`, {
          pageNum: this.pageNum,
          pageSize: this.pageSize,
          param: {
            processName: this.processName,
            processOrder: this.stage,
            isDedicated: this.isShared === 'false' ? true : (this.isShared === 'true' ? false : ''),
            isParallel: this.isParallel
          }
        }).then(res => res.data).then(res => {
          if (res.code == 200) {
            this.tableData = res.data;
            this.total = res.total;
            
            // 更新工作点的工序数量
            const wp = this.workpoints.find(w => w.id === this.activeWorkpoint);
            if (wp) {
              wp.count = res.total;
            }
          } else {
            this.$message.error('获取数据失败');
            this.tableData = [];
            this.total = 0;
          }
        }).catch(error => {
          console.error('加载数据失败:', error);
          this.$message.error('加载数据失败，请检查后端服务');
          this.tableData = [];
          this.total = 0;
        });
      },
      // 加载工作点列表（动态从数据库获取）
      loadWorkpoints() {
        this.$axios.get(this.$httpUrl + '/process/workpoints').then(res => res.data).then(res => {
          console.log('工作点列表响应:', res);
          
          if (res.code == 200) {
            // 后端返回格式：{ code: 200, data: [...], total: 5 }
            // 需要判断 data 是数组还是在 data 字段中
            let workpointList = Array.isArray(res.data) ? res.data : [];
            
            console.log('解析的工作点列表:', workpointList);
            
            if (workpointList.length > 0) {
              // 为每个工作点初始化count
              this.workpoints = workpointList.map(wp => ({
                id: wp.id,
                name: wp.name,
                count: 0
              }));
              
              console.log('设置的workpoints:', this.workpoints);
              
              // 设置第一个工作点为激活状态
              if (!this.activeWorkpoint && this.workpoints.length > 0) {
                this.activeWorkpoint = this.workpoints[0].id;
                console.log('激活的工作点:', this.activeWorkpoint);
                
                // 只有在 activeWorkpoint 被设置后才加载数据
                this.$nextTick(() => {
                  // 加载第一个工作点的数据
                  this.loadPost();
                  
                  // 加载所有工作点的数量统计
                  this.loadAllWorkpointCounts();
                });
              }
            } else {
              this.$message.warning('未找到任何工作点表，请先在数据库中创建 process_workpoint_* 表');
              this.workpoints = [];
            }
          } else {
            this.$message.error('获取工作点列表失败: ' + (res.msg || '未知错误'));
            this.workpoints = [];
          }
        }).catch(error => {
          console.error('加载工作点列表失败:', error);
          this.$message.error('加载工作点列表失败，请检查后端服务');
          this.workpoints = [];
        });
      },
      
      // 加载所有工作点的工序数量
      loadAllWorkpointCounts() {
        this.workpoints.forEach(wp => {
          this.$axios.post(this.$httpUrl + `/process/${wp.id}/listPageC1`, {
            pageNum: 1,
            pageSize: 1,
            param: {}
          }).then(res => res.data).then(res => {
            if (res.code == 200) {
              wp.count = res.total;
            }
          }).catch(() => {
            wp.count = 0;
          });
        });
      },
      handleSizeChange(val) {
        this.pageNum = 1;
        this.pageSize = val;
        this.loadPost();
      },
      handleCurrentChange(val) {
        this.pageNum = val;
        this.loadPost();
      },
      
      // ========== Excel导入相关方法 ==========
      
      // 显示导入对话框
      showImportDialog() {
        this.importDialogVisible = true;
        this.fileList = [];
        this.importResult = null;
        this.importing = false;
        this.importProgress = 0;
        this.importMessage = '';
      },
      
      // 下载Excel模板
      downloadTemplate() {
        this.$message.info('正在生成Excel模板，请稍候...');
        
        // 调用后端API下载模板
        this.$axios({
          method: 'get',
          url: this.$httpUrl + '/pipelineCard/downloadTemplate',
          responseType: 'blob'
        }).then(response => {
          // 创建blob对象
          const blob = new Blob([response.data], {
            type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
          });
          
          // 创建下载链接
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          
          // 设置文件名（带时间戳）
          const timestamp = new Date().toISOString().slice(0, 10);
          link.download = `管道数据导入模板_${timestamp}.xlsx`;
          
          // 触发下载
          document.body.appendChild(link);
          link.click();
          
          // 清理
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          
          this.$message.success('模板下载成功！');
        }).catch(error => {
          console.error('下载模板失败:', error);
          this.$message.error('下载模板失败，请稍后重试');
        });
      },
      
      // 关闭导入对话框
      closeImportDialog() {
        this.importDialogVisible = false;
        this.fileList = [];
        this.importResult = null;
        this.importing = false;
        this.importProgress = 0;
        this.importMessage = '';
      },
      
      // 文件选择变化
      handleFileChange(file, fileList) {
        this.fileList = fileList;
        this.importResult = null;
      },
      
      // 文件移除
      handleFileRemove(file, fileList) {
        this.fileList = fileList;
      },
      
      // 执行导入
      doImport() {
        if (this.fileList.length === 0) {
          this.$message.warning('请先选择要导入的Excel文件');
          return;
        }

        const file = this.fileList[0].raw;
        
        // 验证文件类型
        const fileName = file.name;
        if (!fileName.endsWith('.xlsx') && !fileName.endsWith('.xls')) {
          this.$message.error('只支持Excel文件格式（.xlsx或.xls）');
          return;
        }

        // 验证文件大小（10MB）
        if (file.size > 10 * 1024 * 1024) {
          this.$message.error('文件大小不能超过10MB');
          return;
        }

        // 开始导入
        this.importing = true;
        this.importProgress = 0;
        this.importStatus = '';
        this.importMessage = '正在上传文件...';
        this.importResult = null;

        // 构建FormData
        const formData = new FormData();
        formData.append('file', file);

        // 模拟进度
        const progressInterval = setInterval(() => {
          if (this.importProgress < 90) {
            this.importProgress += 10;
          }
        }, 200);

        // 发送请求
        this.$axios.post(this.$httpUrl + '/pipelineCard/import', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }).then(res => res.data).then(res => {
          clearInterval(progressInterval);
          this.importProgress = 100;
          this.importing = false;

          if (res.code === 200) {
            this.importStatus = 'success';
            this.importMessage = '导入完成！';
            this.importResult = res.data;

            // 如果完全成功，2秒后关闭对话框
            if (res.data.failCount === 0) {
              setTimeout(() => {
                this.closeImportDialog();
                this.$message.success('导入成功！');
              }, 2000);
            }
          } else {
            this.importStatus = 'exception';
            this.importMessage = '导入失败';
            this.importResult = {
              success: false,
              message: res.msg || '导入失败',
              errors: [res.msg || '未知错误']
            };
            this.$message.error(res.msg || '导入失败');
          }
        }).catch(error => {
          clearInterval(progressInterval);
          this.importProgress = 100;
          this.importStatus = 'exception';
          this.importing = false;
          this.importMessage = '导入失败';
          
          console.error('导入失败:', error);
          
          this.importResult = {
            success: false,
            message: '网络错误或服务器异常',
            errors: [error.message || '未知错误']
          };
          this.$message.error('导入失败：' + (error.message || '网络错误'));
        });
      },
      
      // ========== 开卡数据查看相关方法 ==========
      
      // 主标签页切换
      handleMainTabChange(tab) {
        if (tab.name === 'pipeline') {
          // 切换到开卡数据查看时，加载数据
          this.loadPipelineCards();
        }
      },
      
      // 加载开卡数据
      loadPipelineCards() {
        this.$axios.post(this.$httpUrl + '/pipelineCard/listPageFlat', {
          pageNum: this.pipelinePageNum,
          pageSize: this.pipelinePageSize,
          param: {
            pipelineCode: this.pipelineSearchCode,
            status: this.pipelineStatus
          }
        }).then(res => res.data).then(res => {
          if (res.code === 200) {
            // 获取原始数据
            let data = res.data.data || [];
            
            // 调试：打印第一条数据的所有字段
            if (data.length > 0) {
              console.log('===== 开卡数据第一行 =====');
              console.log('所有字段：', Object.keys(data[0]));
              console.log('完整数据：', data[0]);
              console.log('========================');
            }
            
            // 过滤掉表头行（管道编号为"管道编号"的记录）
            this.pipelineCardData = data.filter(item => 
              item.pipelineCode !== '管道编号' && 
              item.cardNo !== '管道序号'
            );
            
            console.log(`原始数据：${data.length}条，过滤后：${this.pipelineCardData.length}条`);
            console.log(`后端总数：${res.data.total}`);
            
            // 不调整总数，直接使用后端返回的总数
            // 因为后端已经知道实际的总记录数
            this.pipelineCardTotal = res.data.total;
            
            // 强制刷新表格布局（多次刷新确保对齐）
            this.$nextTick(() => {
              if (this.$refs && this.$refs.pipelineTable) {
                this.$refs.pipelineTable.doLayout();
                // 延迟再次刷新确保固定列对齐
                setTimeout(() => {
                  this.$refs.pipelineTable.doLayout();
                }, 100);
                setTimeout(() => {
                  this.$refs.pipelineTable.doLayout();
                }, 300);
              }
            });
          } else {
            this.$message.error('加载开卡数据失败：' + res.msg);
          }
        }).catch(error => {
          console.error('加载开卡数据失败:', error);
          this.$message.error('加载开卡数据失败');
        });
      },
      
      // 重置搜索
      resetPipelineSearch() {
        this.pipelineSearchCode = '';
        this.pipelineStatus = '';
        this.pipelinePageNum = 1;
        this.loadPipelineCards();
      },
      
      // 分页-每页数量变化
      handlePipelineSizeChange(val) {
        this.pipelinePageSize = val;
        this.pipelinePageNum = 1;
        this.loadPipelineCards();
      },
      
      // 分页-页码变化
      handlePipelineCurrentChange(val) {
        this.pipelinePageNum = val;
        this.loadPipelineCards();
      },
      
      // 选择变化
      handlePipelineSelectionChange(val) {
        this.pipelineSelection = val;
      },
      
      // 删除单条开卡数据
      deletePipelineCard(row) {
        this.$confirm(`确定要删除管道编号为 "${row.pipelineCode}" 的开卡数据吗？`, '删除确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          this.$axios.delete(this.$httpUrl + '/pipelineCard/delete/' + row.id)
            .then(res => res.data)
            .then(res => {
              if (res.code === 200) {
                this.$message.success('删除成功');
                this.loadPipelineCards();
              } else {
                this.$message.error('删除失败：' + res.msg);
              }
            }).catch(error => {
              console.error('删除失败:', error);
              this.$message.error('删除失败');
            });
        }).catch(() => {
          // 取消删除
        });
      },
      
      // 批量删除
      batchDeletePipelines() {
        if (this.pipelineSelection.length === 0) {
          this.$message.warning('请先选择要删除的数据');
          return;
        }
        
        this.$confirm(`确定要删除选中的 ${this.pipelineSelection.length} 条开卡数据吗？`, '批量删除确认', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          const ids = this.pipelineSelection.map(item => item.id);
          this.$axios.post(this.$httpUrl + '/pipelineCard/deleteBatch', ids)
            .then(res => res.data)
            .then(res => {
              if (res.code === 200) {
                this.$message.success('批量删除成功');
                this.loadPipelineCards();
              } else {
                this.$message.error('批量删除失败：' + res.msg);
              }
            }).catch(error => {
              console.error('批量删除失败:', error);
              this.$message.error('批量删除失败');
            });
        }).catch(() => {
          // 取消删除
        });
      },
      
      // ========== 规则配置相关方法 ==========
      
      // 显示规则配置对话框
      showRuleConfigDialog() {
        this.ruleConfigDialogVisible = true;
        this.ruleEditable = false;
        this.loadProcessRules();
      },
      
      // 加载工序规则
      loadProcessRules() {
        this.$axios.get(this.$httpUrl + '/processRule/list')
          .then(res => res.data)
          .then(res => {
            if (res.code === 200) {
              this.processRules = res.data;
              // 备份原始数据
              this.processRulesBackup = JSON.parse(JSON.stringify(res.data));
            } else {
              this.$message.error('加载规则失败：' + res.msg);
            }
          }).catch(error => {
            console.error('加载规则失败:', error);
            this.$message.error('加载规则失败');
          });
      },
      
      // 启用编辑模式
      enableRuleEdit() {
        this.ruleEditable = true;
        // 备份当前数据
        this.processRulesBackup = JSON.parse(JSON.stringify(this.processRules));
      },
      
      // 取消编辑
      cancelRuleEdit() {
        this.$confirm('确定要取消编辑吗？未保存的修改将丢失。', '取消确认', {
          confirmButtonText: '确定',
          cancelButtonText: '继续编辑',
          type: 'warning'
        }).then(() => {
          // 恢复备份数据
          this.processRules = JSON.parse(JSON.stringify(this.processRulesBackup));
          this.ruleEditable = false;
        }).catch(() => {
          // 继续编辑
        });
      },
      
      // 保存规则配置
      saveRuleConfig() {
        // 验证数据
        for (let rule of this.processRules) {
          if (!rule.baseDuration || rule.baseDuration < 0) {
            this.$message.error(`工序"${rule.processName}"的基础工作时长无效`);
            return;
          }
          if (!rule.stageOrder || rule.stageOrder < 1) {
            this.$message.error(`工序"${rule.processName}"的阶段顺序无效`);
            return;
          }
          if (!rule.teamSize || rule.teamSize < 1) {
            this.$message.error(`工序"${rule.processName}"的团队规模无效`);
            return;
          }
        }
        
        this.ruleSaving = true;
        
        this.$axios.post(this.$httpUrl + '/processRule/batchUpdate', this.processRules)
          .then(res => res.data)
          .then(res => {
            if (res.code === 200) {
              this.$message.success('保存成功');
              this.ruleEditable = false;
              // 重新加载数据
              this.loadProcessRules();
            } else {
              this.$message.error('保存失败：' + res.msg);
            }
          }).catch(error => {
            console.error('保存失败:', error);
            this.$message.error('保存失败');
          }).finally(() => {
            this.ruleSaving = false;
          });
      },
      
      // 格式化团队名称
      formatTeamName(teamName) {
        const teamMap = {
          'team1': '团队1',
          'team2': '团队2',
          'team3': '团队3',
          'team4': '团队4',
          'team5': '团队5',
          'team6': '团队6'
        };
        return teamMap[teamName] || teamName;
      }
    },
    beforeMount() {
      // 首先加载工作点列表（动态获取）
      // loadWorkpoints 内部会自动调用 loadPost 和 loadAllWorkpointCounts
      this.loadWorkpoints();
    }
  };
  </script>
  
  <style scoped>
  .process-manage-container {
    padding: 0;
    background: transparent;
  }
  
  /* 页面头部 */
  .page-header {
    margin-bottom: 20px;
  }

  /* 工作点标签页 */
  .workpoint-tabs-section {
    margin-bottom: 20px;
  }

  .tabs-card {
    border: none;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  }

  .tabs-card :deep(.el-card__body) {
    padding: 16px 20px;
  }

  .tabs-card :deep(.el-tabs__header) {
    margin: 0;
  }

  .tabs-card :deep(.el-tabs__item) {
    height: 45px;
    line-height: 45px;
    font-size: 15px;
    font-weight: 500;
    padding: 0 24px;
  }

  .tabs-card :deep(.el-tabs__item.is-active) {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white !important;
    border-radius: 8px 8px 0 0;
  }

  .tabs-card :deep(.el-tabs__item:hover) {
    color: #4facfe;
  }

  .tab-label {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .tab-badge {
    margin-left: 4px;
  }

  .tab-badge :deep(.el-badge__content) {
    background-color: #f56c6c;
    border-radius: 10px;
    padding: 0 6px;
    height: 18px;
    line-height: 18px;
  }
  
  .header-content {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    border-radius: 12px;
    padding: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: white;
  }
  
  .title-section {
    flex: 1;
  }
  
  .page-title {
    margin: 0 0 8px 0;
    font-size: 28px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .title-icon {
    color: #ffd700;
    font-size: 32px;
    animation: rotate 4s linear infinite;
  }
  
  @keyframes rotate {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  
  .page-subtitle {
    margin: 0;
    opacity: 0.9;
    font-size: 14px;
  }
  
  .header-actions {
    display: flex;
    gap: 12px;
  }
  
  .import-btn, .add-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    backdrop-filter: blur(10px);
  }
  
  .import-btn:hover, .add-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.5);
  }
  
  /* 过滤区域 */
  .filter-section {
    margin-bottom: 20px;
  }
  
  .filter-card {
    border: none;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  }
  
  .filter-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .filter-left {
    display: flex;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
  }
  
  .filter-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .filter-label {
    font-weight: 500;
    color: #606266;
    white-space: nowrap;
  }
  
  .filter-input {
    width: 200px;
  }
  
  .filter-select {
    width: 150px;
  }
  
  .filter-actions {
    display: flex;
    gap: 12px;
  }
  
  /* 表格区域 */
  .table-section {
    margin-bottom: 20px;
  }
  
  .table-card {
    border: none;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  }
  
  .table-header {
    padding: 16px 0;
    border-bottom: 1px solid #ebeef5;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .table-title {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .title-text {
    font-size: 16px;
    font-weight: 600;
    color: #303133;
  }
  
  .count-tag {
    font-size: 12px;
  }
  
  .table-actions {
    display: flex;
    gap: 12px;
  }
  
  /* 表格样式 */
  .process-table {
    width: 100%;
  }
  
  .process-table :deep(.el-table__header) {
    background: #f8f9fa;
  }
  
  .process-table :deep(.el-table th) {
    background: #f8f9fa !important;
    color: #606266;
    font-weight: 600;
  }
  
  .process-name {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .process-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #4facfe, #00f2fe);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 16px;
  }
  
  .process-info {
    flex: 1;
  }
  
  .name-text {
    font-weight: 500;
    font-size: 14px;
    color: #303133;
  }
  
  .process-id {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
  }
  
  .duration-info, .team-info, .team-size-info, .time-info {
    display: flex;
    align-items: center;
    gap: 6px;
    justify-content: center;
  }
  
  .duration-icon {
    color: #67c23a;
  }
  
  .duration-text {
    font-weight: 500;
  }
  
  .team-icon {
    color: #e6a23c;
  }
  
  .time-icon {
    color: #909399;
  }

  .team-size-info {
    color: #606266;
    font-weight: 500;
  }
  
  .stage-tag, .shared-tag, .parallel-tag {
    display: flex;
    align-items: center;
    gap: 4px;
  }
  
  .action-buttons {
    display: flex;
    gap: 8px;
    justify-content: center;
  }
  
  .action-btn {
    padding: 5px 12px;
    border-radius: 6px;
  }
  
  /* 分页 */
  .pagination-container {
    display: flex;
    justify-content: center;
    padding: 20px 0;
    border-top: 1px solid #ebeef5;
    margin-top: 16px;
  }
  
  /* 对话框样式 */
  .process-dialog :deep(.el-dialog) {
    border-radius: 12px;
    overflow: hidden;
  }
  
  .process-dialog :deep(.el-dialog__header) {
    background: linear-gradient(135deg, #4facfe, #00f2fe);
    color: white;
    padding: 20px 24px;
  }
  
  .process-dialog :deep(.el-dialog__title) {
    color: white;
    font-weight: 600;
  }
  
  .process-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
    color: white;
  }
  
  .process-form {
    padding: 24px;
  }
  
  .duration-input, .stage-input, .team-input, .team-size-input {
    width: 100%;
  }

  .team-select {
    width: 100%;
  }
  
  /* 人员类型和并行标识的表单项对齐 */
  .shared-radio, .parallel-radio {
    display: inline-flex;
    gap: 20px;
    align-items: center;
  }
  
  .shared-radio :deep(.el-radio),
  .parallel-radio :deep(.el-radio) {
    margin-right: 0;
    display: inline-flex;
    align-items: center;
    height: 32px;
  }
  
  .radio-item {
    display: inline-flex;
    align-items: center;
  }
  
  .radio-item :deep(.el-radio__input) {
    display: inline-flex;
    align-items: center;
  }
  
  .radio-item :deep(.el-radio__label) {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding-left: 8px;
  }
  
  .dialog-footer {
    padding: 16px 24px;
    border-top: 1px solid #ebeef5;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
  
  .cancel-btn {
    padding: 10px 20px;
  }
  
  .save-btn {
    padding: 10px 20px;
    background: linear-gradient(135deg, #4facfe, #00f2fe);
    border: none;
  }
  
  .save-btn:hover {
    background: linear-gradient(135deg, #3b8bfe, #00d4fe);
  }
  
  .process-dialog :deep(.el-dialog__wrapper) {
    z-index: 2000;
  }

  .process-dialog :deep(.el-overlay) {
    z-index: 1999;
  }

  .process-dialog :deep(.el-dialog) {
    position: relative;
    z-index: 2001;
  }

  /* Excel导入对话框样式 */
  .import-dialog :deep(.el-dialog) {
    border-radius: 12px;
  }

  .import-dialog :deep(.el-dialog__header) {
    background: linear-gradient(135deg, #67c23a, #85ce61);
    color: white;
    padding: 20px 24px;
  }

  .import-dialog :deep(.el-dialog__title) {
    color: white;
    font-weight: 600;
  }

  .import-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
    color: white;
  }

  .import-content {
    padding: 20px;
  }

  .import-tips {
    margin-bottom: 20px;
  }

  .import-tips :deep(.el-alert__description p) {
    margin: 5px 0;
    line-height: 1.8;
  }

  .upload-section {
    margin: 20px 0;
  }

  .upload-demo :deep(.el-upload-dragger) {
    width: 100%;
    height: 180px;
  }

  .import-progress {
    margin: 20px 0;
    text-align: center;
  }

  .progress-text {
    margin-top: 10px;
    color: #606266;
    font-size: 14px;
  }

  .import-result {
    margin-top: 20px;
  }

  .error-list {
    margin-top: 10px;
  }

  .error-list ul {
    margin: 10px 0;
    padding-left: 20px;
    max-height: 200px;
    overflow-y: auto;
  }

  .error-list li {
    margin: 5px 0;
    color: #f56c6c;
    font-size: 13px;
    line-height: 1.6;
  }

  /* 模板下载按钮样式 */
  .template-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
  }

  .template-btn:hover {
    background: rgba(255, 255, 255, 0.3);
    border-color: rgba(255, 255, 255, 0.5);
    transform: translateY(-2px);
  }

  /* 主标签页样式 */
  .main-tabs-section {
    margin-bottom: 20px;
  }

  .main-tabs-card {
    border: none;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  }

  .main-tabs-card :deep(.el-card__body) {
    padding: 0;
  }

  .main-tabs-card :deep(.el-tabs--border-card) {
    border: none;
    box-shadow: none;
  }

  .main-tabs-card :deep(.el-tabs__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    margin: 0;
  }

  .main-tabs-card :deep(.el-tabs__nav) {
    border: none;
  }

  .main-tabs-card :deep(.el-tabs__item) {
    color: rgba(255, 255, 255, 0.7);
    border: none;
    font-size: 16px;
    font-weight: 500;
    padding: 0 30px;
    height: 50px;
    line-height: 50px;
    transition: all 0.3s ease;
  }

  .main-tabs-card :deep(.el-tabs__item.is-active) {
    color: #fff;
    background: rgba(255, 255, 255, 0.2);
    border-bottom: 3px solid #ffd700 !important;
  }

  .main-tabs-card :deep(.el-tabs__item:hover) {
    color: #fff;
    background: rgba(255, 255, 255, 0.1);
  }

  .main-tab-label {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .main-tab-badge {
    margin-left: 8px;
  }

  .main-tab-badge :deep(.el-badge__content) {
    background-color: #f56c6c;
    border: 2px solid #fff;
    border-radius: 12px;
    padding: 0 6px;
    height: 20px;
    line-height: 16px;
  }

  /* 开卡数据表格样式 */
  .pipeline-section {
    margin-top: 20px;
  }

  .pipeline-table {
    width: 100%;
    font-size: 14px;
  }

  .pipeline-table :deep(.el-table__header-wrapper) {
    background: #f5f7fa;
  }

  .pipeline-table :deep(.el-table th) {
    background: #f5f7fa !important;
    color: #303133;
    font-weight: 600;
    font-size: 14px;
    padding: 12px 0;
    height: 48px;
  }

  .pipeline-table :deep(.el-table td) {
    padding: 10px 0;
    height: 48px;
    line-height: 28px;
  }

  /* 固定列右边框 */
  .pipeline-table :deep(.border-right-column) {
    border-right: 2px solid #dfe6ec !important;
  }

  .pipeline-table :deep(.el-table__fixed) {
    box-shadow: 2px 0 6px rgba(0, 0, 0, 0.08);
  }

  .pipeline-table :deep(.el-table__fixed-right) {
    box-shadow: -2px 0 6px rgba(0, 0, 0, 0.08);
  }

  /* 确保固定列表头和主表头高度一致 */
  .pipeline-table :deep(.el-table__fixed-header-wrapper .el-table__header thead) {
    height: 48px;
  }

  .pipeline-table :deep(.el-table__header-wrapper .el-table__header thead) {
    height: 48px;
  }

  /* 确保所有行高度一致 */
  .pipeline-table :deep(.el-table__row) {
    height: 48px !important;
  }

  .pipeline-table :deep(.el-table__fixed-body-wrapper .el-table__row) {
    height: 48px !important;
  }

  /* 规则配置对话框样式 */
  .rule-config-dialog :deep(.el-dialog__body) {
    padding: 20px;
  }

  .rule-config-content {
    width: 100%;
  }

  .rule-actions {
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
  }

  .rule-actions .el-alert {
    flex: 1;
  }

  .action-buttons {
    flex-shrink: 0;
    display: flex;
    gap: 10px;
  }

  .rule-config-table {
    width: 100%;
    font-size: 14px;
  }

  .rule-config-table :deep(.el-table th) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
  }

  .rule-config-table :deep(.el-input-number) {
    width: 100%;
  }

  .rule-config-table :deep(.el-switch) {
    display: inline-block;
  }

  .rule-btn {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    border: none;
    color: white;
    transition: all 0.3s ease;
  }

  .rule-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);
  }

  /* 响应式设计 */
  @media (max-width: 768px) {
    .header-content {
      flex-direction: column;
      gap: 16px;
      text-align: center;
    }
    
    .filter-content {
      flex-direction: column;
      align-items: stretch;
    }
    
    .filter-left {
      justify-content: center;
    }
    
    .filter-actions {
      justify-content: center;
    }
    
    .table-header {
      flex-direction: column;
      gap: 12px;
      align-items: flex-start;
    }
    
    .process-dialog {
      width: 90% !important;
    }
  }
  </style>