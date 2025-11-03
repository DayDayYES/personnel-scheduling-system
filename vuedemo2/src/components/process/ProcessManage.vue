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
            <el-button type="primary" icon="el-icon-plus" @click="add" class="add-btn">
              新增工序
            </el-button>
          </div>
        </div>
      </div>

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
              }
              
              console.log('激活的工作点:', this.activeWorkpoint);
              
              // 加载第一个工作点的数据
              this.loadPost();
              
              // 加载所有工作点的数量统计
              this.loadAllWorkpointCounts();
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
  
  .add-btn {
    background: rgba(255, 255, 255, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: white;
    backdrop-filter: blur(10px);
  }
  
  .add-btn:hover {
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